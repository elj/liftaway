#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway LED module."""

import busio
from adafruit_pca9685 import PCA9685
from board import SCL, SDA


i2c_bus = busio.I2C(SCL, SDA)
pca = PCA9685(i2c_bus)


def init():
    """Initialize LEDs."""
    pca.frequency = 60
    # Turn all lights off
    all_lights_off()

    # Init Overhead/Ceiling Light
    green = pca.channels[13]
    red = pca.channels[14]
    blue = pca.channels[15]

    # TODO: make this changable
    red.duty_cycle = 0xFFFF
    green.duty_cycle = 0x4000
    blue.duty_cycle = 0x0000


def floor_button_on(floor):
    """Turn on floor LED."""
    pca.channels[floor].duty_cycle = 0xFFFF


def floor_button_off(floor):
    """Turn off floor LED."""
    pca.channels[floor].duty_cycle = 0


def all_lights_off():
    """Turn all LEDS off."""
    for i in range(0, 15):
        pca.channels[i].duty_cycle = 0
