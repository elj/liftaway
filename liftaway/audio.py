#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Audio Abstractions."""

import logging
import time

import pygame
from liftaway.util import data_resource_filename


logger = logging.getLogger(__name__)

# PyGame Channels
audio_channels = {
    "default": 0,
    "movement": 1,
    "no_press": 2,
    "voicemail": 3,
    "emergency": 4,
    "squeaker": 5,
}


class Music:
    """Music Track abstraction."""

    def __init__(self, filename: str, volume: float = 1.0):
        """Initializer."""
        logger.debug(f"Init Music {filename}, volume:{volume}")
        self._filename = filename
        self._music = pygame.mixer.music
        self.volume = volume
        if not self._music.get_busy():
            self._music.load(data_resource_filename(filename))
            self._music.set_volume(volume)
            self._music.play(loops=-1)

    @property
    def filename(self):
        """Fully qualified data pathname."""
        return data_resource_filename(self._filename)

    def fadein(self):
        """
        Fade in music.

        Returns False if not already Playing.
        """
        if not self._music.get_busy():
            logger.error(f"Fadein Music {self.filename} not playing")
            return False
        s_vol = self._music.get_volume()
        e_vol = self.volume
        if s_vol == e_vol:
            return True
        logger.debug(f"Fadein Music {self.filename}")
        for i in range(1, 11):
            vol = ((e_vol - s_vol) * i / 10) + s_vol
            self._music.set_volume(round(vol, 2))
            time.sleep(0.2)
        return True

    def fadeout(self, fadeout_ms: int = 0):
        """Fade out music."""
        logger.debug(f"Fadeout Music {self.filename}")
        s_vol = self._music.get_volume()
        for i in range(10, -1, -1):
            vol = ((s_vol) * i / 10)
            self._music.set_volume(round(vol, 2))
            time.sleep(0.1)

    def play(self):
        """Play Music."""
        if not self._music.get_busy():
            logger.debug(f"Play Music {self.filename}")
            self._music.set_volume(self.volume)
            self._music.play(loops=-1)
            return True
        else:
            # already playing; fadein
            return False

    def stop(self):
        """Stop Music."""
        if self._music.get_busy():
            self._music.stop()

    def zero(self):
        logger.debug(f"Kill Music {self.filename}")
        self._music.set_volume(0)



class Sound:
    """Audio Track abstraction."""

    def __init__(
        self,
        filename: str,
        loops: int = 0,
        maxtime: int = -1,
        fade_ms: int = 0,
        volume: float = 1.0,
        audio_channel: str = "default",
    ):
        """Initializer."""
        logger.debug(f"Init Sound {filename}, volume:{volume}")
        self._filename = filename
        self._loops = loops
        self._maxtime = maxtime
        self._fade_ms = fade_ms
        self._sound = pygame.mixer.Sound(data_resource_filename(filename))
        self._sound.set_volume(volume)
        self._channel_num = audio_channels[audio_channel]  # KeyError Exception
        self._channel = pygame.mixer.Channel(self._channel_num)
        self._volume = volume

    @property
    def filename(self):
        """Fully qualified data pathname."""
        return data_resource_filename(self._filename)

    @property
    def is_busy(self) -> bool:
        """Boolean saying whether the channel is busy."""
        return self._channel.get_busy()

    def fadein(self, fadein_ms: int = 0, loop: int = 0):
        """
        Fadein Sound.
        :param fadein_ms: milliseconds to fade in.
        :param loop: number of loops to play.
        """
        ms = fadein_ms or self._fade_ms
        self.play(fadein_ms=ms)

    def fadeout(self, fadeout_ms: int = 100):
        """
        Fadeout Sound.
        :param fadeout_ms: milliseconds to run fadeout.
        """
        ms = fadeout_ms or self._fade_ms
        logger.debug(f"Fadeout Sound {self.filename}, fadeout_ms:{ms}")
        self._sound.fadeout(fadeout_ms)

    def play(self, interrupt: bool = True, blocking: bool = False, fadein_ms: int = 0):
        """
        Play Sound.
        :param interrupt: interrupt sounds already on channel.
        :param blocking: block until playing sound is finished.
        :param fadein_ms: millisecond fadein.
        """
        busy = self.is_busy
        logger.info(
            f"Play Sound {self.filename} on channel:{self._channel_num}, fadein:{fadein_ms}"
        )
        if not busy or (busy and interrupt):
            self._channel.play(self._sound, maxtime=self._maxtime, fade_ms=fadein_ms)
        else:
            logger.warn(
                f"Channel {self._channel_num} Busy; couldn't play {self.filename}"
            )
            return
        if blocking:
            while self._channel.get_sound() == self._sound:
                time.sleep(0.1)
            logger.info(f"Sound {self.filename} finished (blocked)")

    def queue(self, blocking: bool = True):
        """
        Queue Sound.
        :param blocking: block until able to queue.
        """
        if blocking:
            logger.info(f"Queue Sound {self.filename} waiting")
            while self._channel.get_queue():
                time.sleep(0.1)
        elif self._channel.get_queue():
            logger.info(f"Queue Sound {self.filename} kicked somebody out")
        self._channel.queue(self._sound)
        logger.info(f"Queue Sound {self.filename} queued")


def init():
    pygame.mixer.pre_init(44100, -16, 2, 3072)  # setup mixer to avoid sound lag
    # (freq, bits, channels, buffer)
    pygame.init()  # initialize pygame - this is where terrible things happen
    pygame.mixer.set_num_channels(len(audio_channels))  # must come *after* .init
