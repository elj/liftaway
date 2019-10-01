#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liftaway main business logic."""

import logging
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
from liftaway.actions import Flavour, Floor, Movement
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
        self.gpio_inputs = tuple(
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
            GPIOInput(gpio=23, bouncetime=15000, callback=partial(self.voicemail, 0)),
            GPIOInput(gpio=26, bouncetime=1000, callback=partial(self.squeaker, 0)),
            GPIOInput(gpio=25, bouncetime=20000, callback=partial(self.emergency, 0)),
            GPIOInput(gpio=24, bouncetime=1000, callback=partial(self.no_press, 0)),
            GPIOInput(gpio=27, bouncetime=3000, callback=partial(self.cancel, 0)),
        )
        # self.gpio_outputs = list([
        #     GPIOOutput(gpio=7, label="nothing"),
        #     GPIOOutput(gpio=8, label="door_close"),
        #     GPIOOutput(gpio=9, label="door_open"),
        #     GPIOOutput(gpio=10, label="cancel_call"),
        #     GPIOOutput(gpio=11, label="emergency_call"),
        #     GPIOOutput(gpio=14, label="direction_up"),
        #     GPIOOutput(gpio=15, label="direction_dn"),
        # ])
        self.gpio_outputs = tuple(
            GPIOOutput(gpio=v, label=k) for k, v in constants.control_outputs.items()
        )
        self.movement = Movement()
        self.muzak = Music(**constants.in_between_audio.get("muzak"))
        floor_count = 12
        self.floors = [Floor(i, muzak=self.muzak) for i in range(floor_count)]
        self.action = None
        self.lock = Lock()
        self.queue = deque()
        self._emergency = Flavour(
            constants.emergency_button_audio, self_interruptable=False
        )
        self._voicemail = Flavour(
            constants.voicemail_button_audio, self_interruptable=False
        )
        self._no_press = Flavour(
            constants.no_press_button_audio, self_interruptable=True
        )
        self._squeaker = Flavour(
            constants.squeaker_button_audio, self_interruptable=True
        )
        self.running = False
        self.gpio_init()
        low_level.init()

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

    def floor(self, requested_floor: int, gpio: int) -> None:
        """Run Handler for Floor GPIO."""
        if requested_floor >= len(self.floors):
            logger.error(f"requested_floor({requested_floor}) out of range")
            return
        floor = self.floors[requested_floor]
        if not self._push_floor(floor):
            logger.error(f"Could not queue floor({requested_floor})")

    def voicemail(self, _: int, gpio: int) -> None:
        """Run Call for Help Routine."""
        self._voicemail.run()
        pass

    def squeaker(self, _: int, gpio: int) -> None:
        """Run Squeaker Routine."""
        self._squeaker.run()
        pass

    def emergency(self, _: int, gpio: int) -> None:
        """Run Emergency/Remain Calm Routine."""
        self._emergency.run()
        pass

    def no_press(self, _: int, gpio: int) -> None:
        """Run Don't Press This Button Routine."""
        self._no_press.run()
        pass

    def cancel(self, _: int, gpio: int) -> None:
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


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Debug
    floors = list(range(12))
    for _ in range(2):
        f = random.choice(floors)  # noqa
        floors.remove(f)
        controller.floor(f, 4)

    try:
        controller.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")
        low_level.all_lights_off()
        for i in constants.control_outputs.values():
            GPIO.output(i, GPIO.LOW)
        GPIO.cleanup()


controller = Controller()


if __name__ == "__main__":
    main()
