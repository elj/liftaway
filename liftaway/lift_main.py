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
import liftaway.low_level as low_level
import RPi.GPIO as GPIO
from liftaway.actions import Flavour, Floor, Movement
from liftaway.audio import init as audio_init, Music


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
        audio_init()
        self.movement = Movement()
        self.muzak = Music(**constants.in_between_audio.get("muzak"))
        self.muzak.play()
        floor_count = 12
        self.floors = [Floor(i, muzak=self.muzak) for i in range(floor_count)]
        self.action = None
        self.lock = Lock()
        self.queue = deque()
        self._emergency = Flavour(
            sounds=constants.emergency_button_audio, self_interruptable=False
        )
        self._voicemail = Flavour(
            sounds=constants.voicemail_button_audio, self_interruptable=False
        )
        self._no_press = Flavour(
            sounds=constants.no_press_button_audio, self_interruptable=True
        )
        self._squeaker = Flavour(
            sounds=constants.squeaker_button_audio, self_interruptable=True
        )
        self.gpio_init()
        low_level.init()
        self.running = False

    def gpio_init(self) -> None:
        """Initialize GPIO."""
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        # Setup GPIO Inputs
        gpio_inputs = [
            GPIOInput(gpio=v, bouncetime=1000, callback=partial(self.floor, k))
            for k, v in constants.floor_to_gpio_mapping.items()
        ]
        gpio_inputs.append(
            GPIOInput(
                gpio=constants.flavor_to_gpio_mapping.get("cancel"),
                bouncetime=1000,
                callback=partial(self.cancel, 0),
            )
        )
        gpio_inputs.append(
            GPIOInput(
                gpio=constants.flavor_to_gpio_mapping.get("emergency"),
                bouncetime=1000,
                callback=partial(self.emergency, 0),
            )
        )
        gpio_inputs.append(
            GPIOInput(
                gpio=constants.flavor_to_gpio_mapping.get("no_press"),
                bouncetime=400,
                callback=partial(self.no_press, 0),
            )
        )
        gpio_inputs.append(
            GPIOInput(
                gpio=constants.flavor_to_gpio_mapping.get("squeaker"),
                bouncetime=400,
                callback=partial(self.squeaker, 0),
            )
        )
        gpio_inputs.append(
            GPIOInput(
                gpio=constants.flavor_to_gpio_mapping.get("voicemail"),
                bouncetime=1000,
                callback=partial(self.voicemail, 0),
            )
        )
        gpio_inputs = tuple(gpio_inputs)

        for g in gpio_inputs:
            logger.debug(f"Set GPIO_PIN({g.gpio}) as GPIO.IN with PUD_UP")
            GPIO.setup(g.gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                gpio=g.gpio,
                edge=GPIO.RISING,
                callback=g.callback,
                bouncetime=g.bouncetime,
            )

        # Setup GPIO Outputs
        gpio_outputs = tuple(  # noqa
            [
                GPIOOutput(gpio=v, label=k)
                for k, v in constants.control_outputs.items()
            ]
        )

        for g in gpio_outputs:
            logger.debug(f"Set GPIO_PIN({g.gpio}) as GPIO.OUT")
            GPIO.setup(g.gpio, GPIO.OUT)

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
        # Don't care if the floor is self.action, just re-queue
        if floor in self.queue:
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
        logger.debug(f"floor_gpio({gpio})")
        if requested_floor >= len(self.floors):
            logger.error(f"requested_floor({requested_floor}) out of range")
            return
        floor = self.floors[requested_floor]
        if not self._push_floor(floor):
            logger.error(f"Could not queue floor({requested_floor})")

    def voicemail(self, _: int, gpio: int) -> None:
        """Run Call for Help Routine."""
        logger.debug(f"voicemail({gpio})")
        self._voicemail.run()
        pass

    def squeaker(self, _: int, gpio: int) -> None:
        """Run Squeaker Routine."""
        logger.debug(f"squeaker({gpio})")
        self._squeaker.run()
        pass

    def emergency(self, _: int, gpio: int) -> None:
        """Run Emergency/Remain Calm Routine."""
        logger.debug(f"emergency({gpio})")
        self._emergency.run()
        pass

    def no_press(self, _: int, gpio: int) -> None:
        """Run Don't Press This Button Routine."""
        logger.debug(f"no_press({gpio})")
        self._no_press.run()
        pass

    def cancel(self, _: int, gpio: int) -> None:
        """
        Run Call Cancel Routine.

        Dequeue's all selected motions and floors without playing them.
        """
        logger.debug(f"cancel({gpio})")
        low_level.cancel_call_led(on=True)
        self.interrupt()

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
            while self._pop_action():
                self.action.run(interrupted=True)
            low_level.cancel_call_led(on=False)
            self.paused = False

    def interrupt(self) -> None:
        """Interrupt! (Call Cancel)."""
        self.paused = True
        if self.action:
            self.action.interrupt()


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
