#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway floor (and betwen floor) objects."""

import logging
import os
import time

import liftaway.low_level
import pygame
from liftaway.constants import floor_audio, in_between_audio
from pkg_resources import Requirement, resource_filename

logger = logging.getLogger(__name__)


def data_resource_filename(filename):
    """Return the filename of a data resource."""
    return resource_filename(
        Requirement.parse("liftaway"), os.path.join("liftaway/data", filename)
    )


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
        self._travel = pygame.mixer.Sound(
            data_resource_filename(in_between_audio.get("travel").filename)
        )
        self._travel.set_volume(in_between_audio.get("travel").volume)
        self._halt = pygame.mixer.Sound(
            data_resource_filename(in_between_audio.get("halt").filename)
        )
        self._halt.set_volume(in_between_audio.get("halt").volume)

    def push(self):
        """Between Floor dealie gets pushed onto the queue."""
        pass

    def pop(self, interrupted: bool = False):
        """Movement gets popped off the queue."""
        logger.info(f"Movement: Popped off queue; Interrupted({interrupted})")
        if not interrupted:
            logger.info(f"Movement: Elevator Traveling")
            liftaway.low_level.direction_led(on=True)
            self._travel.play()
            time.sleep(1.5)
        else:
            # Take some time to dequeue the floors
            time.sleep(0.5)

    def interrupt(self):
        """Movement gets interrupted... stop audio and play screech."""
        logger.info(f"Movement: Elevator Stopped!")
        self._halt.play()
        self._travel.stop()


class Floor(Base):
    """Floor Ambiance and Behavior."""

    def __init__(self, floor_number: int):
        """initilizer."""
        self.floor_number = floor_number
        audios = []
        for f in floor_audio.get(floor_number):
            audios.append(pygame.mixer.Sound(data_resource_filename(f.filename)))
        self.audios = tuple(audios)
        self.audios_i = 0
        self._ding = pygame.mixer.Sound(
            data_resource_filename(in_between_audio.get("ding").filename)
        )
        self._ding.set_volume(in_between_audio.get("ding").volume)
        self._open = pygame.mixer.Sound(
            data_resource_filename(in_between_audio.get("open").filename)
        )
        self._open.set_volume(in_between_audio.get("open").volume)
        self._close = pygame.mixer.Sound(
            data_resource_filename(in_between_audio.get("close").filename)
        )
        self._close.set_volume(in_between_audio.get("close").volume)

    def ding(self):
        """Ding!."""
        logger.info(f"Floor({self.floor_number}): Ding!")
        self._ding.play()

    def no_direction(self):
        """Kill direction lights."""
        logger.info(f"Floor({self.floor_number}): Direction off")
        liftaway.low_level.direction_led(on=False)

    def door_open(self):
        """Door opened!."""
        logger.info(f"Floor({self.floor_number}): Opening Door")
        self._open.play()
        time.sleep(1.5)

    def floor_sounds(self):
        """We've arrived."""
        logger.info(f"Floor({self.floor_number}): Playing floor audio")
        self.audios_i = (self.audios_i + 1) % len(self.audios)
        self.audios[self.audios_i].play()
        # hold the doors open to hear the sounds
        time.sleep(15)

    def door_close(self):
        """Door closed!."""
        logger.info(f"Floor({self.floor_number}): Closing Door")
        self._close.play()
        self.audios[self.audios_i].fadeout(1700)

    def push(self):
        """Floor gets pushed onto the queue."""
        logger.info(f"Floor({self.floor_number}): Pushed onto queue")
        liftaway.low_level.floor_button_led(self.floor_number, on=True)

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

    def interrupt(self):
        """Floor gets interrupted... noop for floors."""
        pass
