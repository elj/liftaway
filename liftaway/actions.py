#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway floor (and betwen floor) objects."""

import logging
import time
from typing import Dict, Tuple, Union

import liftaway.low_level
from liftaway.audio import Music, Sound
from liftaway.constants import floor_audio, in_between_audio

logger = logging.getLogger(__name__)


class Base:
    """Base class for floors and between floors."""

    def activate(self) -> None:
        """Object is activated (pushed onto the queue)."""
        raise NotImplementedError("queued")

    def run(self, interrupted: bool = False) -> None:
        """Object is doing it's action (popped off the queue)."""
        raise NotImplementedError("run")

    def interrupt(self) -> None:
        """If we're running, we've been interrupted."""
        raise NotImplementedError("interrupt")


class Movement(Base):
    """The space between floors."""

    def __init__(self) -> None:
        """initializer."""
        self._travel = Sound(**in_between_audio.get("travel", {}))
        self._halt = Sound(**in_between_audio.get("halt", {}))

    def halt(self) -> None:
        """We've halted mid-travel."""
        logger.info(f"Movement: Elevator Halted!")
        self._halt.play(interrupt=True)
        self._halt.fadeout(fadeout_ms=500)

    def travel(self) -> None:
        """We're traveling between floors."""
        logger.info(f"Movement: Elevator Traveling")
        liftaway.low_level.direction_led(on=True)
        self._travel.play(blocking=True)

    def activate(self) -> None:
        """Between Floor dealie gets pushed onto the queue."""
        pass

    def run(self, interrupted: bool = False) -> None:
        """Movement gets popped off the queue."""
        logger.info(f"Movement: Popped off queue; Interrupted({interrupted})")
        if not interrupted:
            time.sleep(1.1)
            self.travel()
            # Randomize the travel time from 2 to 7 seconds
            # time.sleep(random.choice(tuple(range(2, 8))))  # noqa

    def interrupt(self) -> None:
        """Movement gets interrupted... stop audio and play screech."""
        logger.info(f"Movement: Interrupted")
        self.halt()


class Floor(Base):
    """Floor Ambiance and Behavior."""

    def __init__(self, floor_number: int, muzak: Union[None, Music]) -> None:
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
        self._muzak = muzak

    def ding(self) -> None:
        """Ding!."""
        logger.info(f"Floor({self.floor_number}): Ding!")
        self._ding.play(blocking=False)
        if self._muzak:
            self._muzak.fadeout()

    def no_direction(self) -> None:
        """Kill direction lights."""
        logger.info(f"Floor({self.floor_number}): Direction off")
        liftaway.low_level.direction_led(on=False)

    def door_open(self) -> None:
        """Door opened!."""
        logger.info(f"Floor({self.floor_number}): Opening Door")
        self._open.play(blocking=True)

    def floor_sounds(self) -> None:
        """We've arrived."""
        logger.info(f"Floor({self.floor_number}): Playing floor audio")
        self._audios_i = (self._audios_i + 1) % len(self._audios)
        self._audios[self._audios_i].play(blocking=True)
        # hold the doors open to hear the sounds
        # sleep n - 1 and then fadeout.

    def door_close(self) -> None:
        """Door closed!."""
        logger.info(f"Floor({self.floor_number}): Closing Door")
        self._close.play(blocking=True)
        if self._muzak:
            # TODO(tkalus) verify
            # self._muzak.fadein()
            self._muzak.stop()

    def activate(self) -> None:
        """Floor gets pushed onto the queue."""
        logger.info(f"Floor({self.floor_number}): Pushed onto queue")
        liftaway.low_level.floor_button_led(self.floor_number, on=True)

    def run(self, interrupted: bool = False) -> None:
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
        else:
            # Take some time to dequeue the floors
            time.sleep(0.2)

    def interrupt(self) -> None:
        """Floor gets interrupted... noop for floors."""
        logger.info(f"Floor({self.floor_number}): Interrupted")
        pass


class Flavour:
    """Somebody call Guy Fieri!."""

    def __init__(
        self,
        sounds: Tuple[Dict[str, Union[str, float]]],
        self_interruptable: bool = True,
    ):
        """Initialize."""
        self.irqable = self_interruptable
        audios = []
        for f in sounds:
            audios.append(Sound(**f))
        self._audios = tuple(audios)
        self._audios_i = 0

    def run(self):
        """Welcome to Flavourtown."""
        if not self.irqable and self._audios[self._audios_i].is_busy:
            logger.error(f"Flavour: Already playing audio")
            return
        self._audios_i = (self._audios_i + 1) % len(self._audios)
        logger.info(f"Flavour: Playing audio({self._audios_i})")
        self._audios[self._audios_i].play(blocking=False)
