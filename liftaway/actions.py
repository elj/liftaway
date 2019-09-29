#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway floor (and betwen floor) objects."""

import logging
import random
import time

import liftaway.low_level
from liftaway.audio import Sound
from liftaway.constants import floor_audio, in_between_audio

logger = logging.getLogger(__name__)


class Base:
    """Base class for floors and between floors."""

    def push(self):
        """Object is pushed onto the queue."""
        raise NotImplementedError("push")

    def pop(self, interrupted: bool = False):
        """Object is popped off the queue."""
        raise NotImplementedError("pop")

    def interrupt(self):
        """If we're running, we've been interrupted."""
        raise NotImplementedError("interrupt")


class Movement(Base):
    """The space between floors."""

    def __init__(self):
        """initializer."""
        self._travel = Sound(**in_between_audio.get("travel", {}))
        self._halt = Sound(**in_between_audio.get("halt", {}))

    def halt(self):
        """We've halted mid-travel."""
        logger.info(f"Movement: Elevator Halted!")
        self._halt.play(interrupt=True)
        self._halt.fadeout(fadeout_ms=500)

    def travel(self):
        """We're traveling between floors."""
        logger.info(f"Movement: Elevator Traveling")
        liftaway.low_level.direction_led(on=True)
        self._travel.play(blocking=True)

    def push(self):
        """Between Floor dealie gets pushed onto the queue."""
        pass

    def pop(self, interrupted: bool = False):
        """Movement gets popped off the queue."""
        logger.info(f"Movement: Popped off queue; Interrupted({interrupted})")
        if not interrupted:
            self.travel()
            # Randomize the travel time from 2 to 7 seconds
            time.sleep(random.choice(tuple(range(2, 8))))  # noqa
        else:
            # Take some time to dequeue the floors
            time.sleep(0.5)

    def interrupt(self):
        """Movement gets interrupted... stop audio and play screech."""
        logger.info(f"Movement: Interrupted")
        self.halt()


class Floor(Base):
    """Floor Ambiance and Behavior."""

    def __init__(self, floor_number: int):
        """initilizer."""
        self.floor_number = floor_number
        audios = []
        for f in floor_audio.get(floor_number, {}):
            audios.append(Sound(**f))
        self._audios = tuple(audios)
        self._audios_i = 0
        self._ding = Sound(**in_between_audio.get("ding"))
        self._open = Sound(**in_between_audio.get("open"))
        self._close = Sound(**in_between_audio.get("close"))
        self._muzak = Sound(**in_between_audio.get("muzak"))
        self._queued = False

    @property
    def is_queued(self):
        """Object thinks it's queued or not."""
        return self._queued

    def ding(self):
        """Ding!."""
        logger.info(f"Floor({self.floor_number}): Ding!")
        self._ding.play(blocking=True)

    def no_direction(self):
        """Kill direction lights."""
        logger.info(f"Floor({self.floor_number}): Direction off")
        liftaway.low_level.direction_led(on=False)

    def door_open(self):
        """Door opened!."""
        logger.info(f"Floor({self.floor_number}): Opening Door")
        self._open.play(blocking=True)

    def floor_sounds(self):
        """We've arrived."""
        logger.info(f"Floor({self.floor_number}): Playing floor audio")
        self.audios_i = (self.audios_i + 1) % len(self.audios)
        self.audios[self.audios_i].play()
        # hold the doors open to hear the sounds
        time.sleep(15)
        self.audios[self.audios_i].fadeout(1700)
        time.sleep(1)

    def door_close(self):
        """Door closed!."""
        logger.info(f"Floor({self.floor_number}): Closing Door")
        self._close.play()

    def muzak(self):
        """Muzak!."""
        logger.info(f"Floor({self.floor_number}): Muzak")
        self._muzak.play(fadein_ms=1000, loop=-1)

    def push(self):
        """Floor gets pushed onto the queue."""
        logger.info(f"Floor({self.floor_number}): Pushed onto queue")
        liftaway.low_level.floor_button_led(self.floor_number, on=True)
        self._queued = True

    def pop(self, interrupted: bool = False):
        """Floor gets popped off the queue."""
        logger.info(
            f"Floor({self.floor_number}): Popped off queue; Interrupted({interrupted})"
        )
        liftaway.low_level.floor_button_led(self.floor_number, on=False)
        if not interrupted:
            self.no_direction()
            self.ding()
            self.door_open()
            self.floor_sounds()
            self.door_close()
            self.muzak()
        self._queued = False

    def interrupt(self):
        """Floor gets interrupted... noop for floors."""
        logger.info(f"Floor({self.floor_number}): Interrupted")
        pass
