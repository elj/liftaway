#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liftaway main business logic."""

import logging
import queue
import random
import sys
import time
from collections import deque
from functools import partial
from threading import Lock
from typing import Callable, NamedTuple

import liftaway.constants as constants
import liftaway.liftsound as liftsound
import liftaway.low_level as low_level
import RPi.GPIO as GPIO
from liftaway.actions import Floor, Movement
from liftaway.audio import Music


logger = logging.getLogger(__name__)

GPIOInput = NamedTuple(
    "GPIOInput",
    [("gpio", int), ("bouncetime", int), ("callback", Callable[[int], None])],
)
GPIOOutput = NamedTuple("GPIOOutput", [("gpio", int), ("label", str)])


class Controller:
    """Main Controller (Singleton)."""

    def __init__(self):
        """Initializer."""
        self.gpio_inputs = tuple([
            GPIOInput(gpio=4, bouncetime=1000, callback=partial(self.floor, 1)),
            GPIOInput(gpio=5, bouncetime=1000, callback=partial(self.floor, 2)),
            GPIOInput(gpio=6, bouncetime=1000, callback=partial(self.floor, 3)),
            GPIOInput(gpio=12, bouncetime=1000, callback=partial(self.floor, 4)),
            GPIOInput(gpio=13, bouncetime=1000, callback=partial(self.floor, 5)),
            GPIOInput(gpio=16, bouncetime=1000, callback=partial(self.floor, 6)),
            GPIOInput(gpio=17, bouncetime=1000, callback=partial(self.floor, 7)),
            GPIOInput(gpio=18, bouncetime=1000, callback=partial(self.floor, 8)),
            GPIOInput(gpio=19, bouncetime=1000, callback=partial(self.floor, 9)),
            GPIOInput(gpio=20, bouncetime=1000, callback=partial(self.floor, 10)),
            GPIOInput(gpio=21, bouncetime=1000, callback=partial(self.floor, 11)),
            GPIOInput(gpio=22, bouncetime=1000, callback=partial(self.floor, 0)),
            GPIOInput(gpio=23, bouncetime=15000, callback=partial(self.call_help, 0)),
            GPIOInput(gpio=26, bouncetime=1000, callback=partial(self.squeaker, 0)),
            GPIOInput(gpio=25, bouncetime=20000, callback=partial(self.emergency, 0)),
            GPIOInput(gpio=24, bouncetime=1000, callback=partial(self.no_press, 0)),
            GPIOInput(gpio=27, bouncetime=3000, callback=partial(self.cancel, 0)),
        ])
        # self.gpio_outputs = list([
        #     GPIOOutput(gpio=7, label="nothing"),
        #     GPIOOutput(gpio=8, label="door_close"),
        #     GPIOOutput(gpio=9, label="door_open"),
        #     GPIOOutput(gpio=10, label="cancel_call"),
        #     GPIOOutput(gpio=11, label="emergency_call"),
        #     GPIOOutput(gpio=14, label="direction_up"),
        #     GPIOOutput(gpio=15, label="direction_dn"),
        # ])
        self.gpio_outputs = tuple([
            GPIOOutput(gpio=v, label=k) for k, v in constants.control_outputs.items()
        ])
        self.movement = Movement()
        self.muzak = Music(**constants.in_between_audio.get("muzak"))
        floor_count = 12
        self.floors = [Floor(i, muzak=self.muzak) for i in range(floor_count)]
        self.action = None
        self.lock = Lock()
        self.queue = deque()
        self.running = False
        self.gpio_init()

    def gpio_init(self) -> None:
        """Initialize GPIO."""
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        # Setup GPIO Outputs
        for g in self.gpio_outputs:
            logger.debug(f"Set GPIO_PIN({g.gpio}) as GPIO.OUT")
            GPIO.setup(g.gpio, GPIO.OUT)

        # Setup GPIO Inputs
        for g in self.gpio_inputs:
            logger.debug(f"Set GPIO_PIN({g.gpio}) as GPIO.IN with PUD_UP")
            GPIO.setup(g.gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                gpio=g.gpio,
                edge=GPIO.RISING,
                callback=g.callback,
                bouncetime=g.bouncetime,
            )

    def _pop_action(self) -> bool:
        """Pop Action (Movement or Floor) from Queue."""
        self.lock.acquire(blocking=True)
        try:
            self.action = self.queue.popleft()
        except IndexError:
            self.action = None
        self.lock.release()
        return bool(self.action)

    def _push_floor(self, floor) -> bool:
        """Push requested Floor onto Queue."""
        if not self.lock.acquire(blocking=False):
            # TODO(tkalus) Buzzer sound?
            logger.debug("Could not get floor lock")
            return False
        # We have the mutex
        if self.action == floor or floor in self.queue:
            logger.debug("Floor already in queue")
            # TODO(tkalus) Blink floor light?
            self.lock.release()
            return False
        self.queue.append(self.movement)
        floor.activate()
        self.queue.append(floor)
        self.lock.release()
        return True

    def floor(self, requested_floor: int) -> None:
        """Run Handler for Floor GPIO."""
        if requested_floor >= len(self.floors):
            logger.error(f"requested_floor({requested_floor}) out of range")
            return
        floor = self.floors[requested_floor]
        if not self._push_floor(floor):
            logger.error(f"Could not queue floor({requested_floor})")

    def call_help(self, _: int) -> None:
        """Run Call for Help Routine."""
        pass

    def squeaker(self, _: int) -> None:
        """Run Squeaker Routine."""
        pass

    def emergency(self, _: int) -> None:
        """Run Emergency/Remain Calm Routine."""
        pass

    def no_press(self, _: int) -> None:
        """Run Don't Press This Button Routine."""
        pass

    def cancel(self, _: int) -> None:
        """
        Run Call Cancel Routine.

        Dequeue's all selected motions and floors without playing them.
        """
        pass

    def run(self) -> None:
        """Run Controller."""
        self.running = True
        self.paused = False
        while self.running:
            while not self.paused:
                if self._pop_action():
                    self.action.run()
                else:
                    time.sleep(0.1)
                self.muzak.play() or self.muzak.fadein()
            self.muzak.play() or self.muzak.fadein()
            time.sleep(0.1)

    def interrupt(self) -> None:
        """Interrupt! (Call Cancel)."""
        self.paused = True
        if self.action:
            self.action.interrupt()
        while self._pop_action():
            self.action.run(intrrupted=True)
        self.paused = False


q = deque()
current_floor = -1


def floor_queue_callback(channel):
    global current_floor
    print("Detected pin", channel)  # debug

    # find out which floor number it is
    requested_floor = constants.gpio_to_floor_mapping.get(channel)
    if requested_floor < 0:
        print("Not a valid floor")
        return

    # turn the button light on
    low_level.floor_button_led(requested_floor, on=True)

    # determine whether it's the current floor. TODO: Open door?
    # ~ if(requested_floor == current_floor):
    # ~ print("Not adding current floor")
    # ~ time.sleep(0.5)
    # ~ low_level.floor_button_led(requested_floor, on=False)

    # if it's a different floor, add that floor to the queue
    # else:
    print("[queue] Adding to queue floor", requested_floor)  # debug
    q.append(requested_floor)  # add this floor to the queue


# When there are floors in the queue, travel to those floors
def process_floor_queue():
    global current_floor
    print("[queue] Processing queue...")
    next_floor = q.popleft()
    if next_floor == current_floor:
        print("Skipping redundant floor")
        return

    direction = next_floor - current_floor

    current_floor = next_floor

    # all the important elevator stuff happens here:
    this_floor = liftsound.go_to_floor(next_floor, direction)
    print("[elev] Doors closed on floor", this_floor)


# stop elevator and clear the queue
def control_cancel_callback(channel):
    global current_floor
    if channel != 27:
        return
    # turn on the call cancel button light
    low_level.cancel_call_led(on=True)
    print("[queue] **Clearing floor queue!**")
    # TODO: turn off all the floor button lights
    global current_floor
    liftsound.cancel_call_on(current_floor)
    if q:
        while q:
            f = q.popleft()
            print("[queue] ***removing floor ", f)
            low_level.floor_button_led(f, on=False)
            time.sleep(0.2)
    current_floor = -1
    low_level.cancel_call_led(on=False)


# do all the emergency stuff
def control_emergency_callback(channel):
    # turn on the emergency button light
    print("[control] **Emergency button pressed!**")
    liftsound.start_emergency()
    time.sleep(1)
    # print("Emergency complete")


def control_help_callback(channel):
    print("[control] **Call for help button pressed!**")
    liftsound.play_voicemail()


def control_door_open_callback(channel):
    if channel != 26:
        return
    else:
        # turn on the door open button light
        low_level.door_open_led(on=True)
        print("**Door open button pressed!**")
        liftsound.play_squeak()
        time.sleep(0.5)
        low_level.door_open_led(on=False)


def control_door_close_callback(channel):
    if channel != 24:
        return
    else:
        # turn on the door close button light
        low_level.door_close_led(on=True)
        print("[control] **Don't push this button pressed!**")
        liftsound.dont_push_this_button()
        time.sleep(0.5)
        low_level.door_close_led(on=False)


def main2():
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()

    # Setup GPIO Inputs
    GPIO.setup(
        list(constants.gpio_to_floor_mapping.keys()), GPIO.IN, pull_up_down=GPIO.PUD_UP
    )

    # Setup GPIO Outputs
    GPIO.setup(list(constants.control_outputs.values()), GPIO.OUT)

    for i in constants.gpio_to_floor_mapping.keys():
        GPIO.add_event_detect(
            gpio=i, edge=GPIO.RISING, callback=floor_queue_callback, bouncetime=1000
        )
    GPIO.add_event_detect(
        gpio=23, edge=GPIO.RISING, callback=control_help_callback, bouncetime=15000
    )
    GPIO.add_event_detect(
        gpio=24, edge=GPIO.RISING, callback=control_door_close_callback, bouncetime=1000
    )
    GPIO.add_event_detect(
        gpio=25, edge=GPIO.RISING, callback=control_emergency_callback, bouncetime=20000
    )
    GPIO.add_event_detect(
        gpio=26, edge=GPIO.RISING, callback=control_door_open_callback, bouncetime=1000
    )
    GPIO.add_event_detect(
        gpio=27, edge=GPIO.RISING, callback=control_cancel_callback, bouncetime=3000
    )
    low_level.init()


    task_queue = queue.SimpleQueue()

    floors = []
    for i in range(12):
        floors.append(Floor(i))

    for _ in range(3):
        f = random.choice(floors)  # noqa
        floors.remove(f)
        if not f.is_queued:
            f.push()
            task_queue.put(Movement())
            task_queue.put(f)

    print("ready...")
    time.sleep(5)
    try:
        while True:
            if not task_queue.empty():
                task = task_queue.get_nowait()
                task.pop()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")
        low_level.all_lights_off()
        for i in constants.control_outputs.values():
            GPIO.output(i, GPIO.LOW)
        GPIO.cleanup()


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout
    )
    floors = list(range(12))
    for _ in range(3):
        f = random.choice(floors)
        floors.remove(f)
        controller.floor(f)
    controller.run()


controller = Controller()

if __name__ == "__main__":
    main()
