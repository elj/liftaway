#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Low-Level (GPIO and PCA) module."""

import random

import busio
import RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
from liftaway.constants import control_outputs


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


def gpio_output(gpio: int, high: bool = True):
    """Set a GPIO Output High or Low."""
    if high:
        GPIO.output(gpio, GPIO.HIGH)
    else:
        GPIO.output(gpio, GPIO.LOW)


def cancel_call_led(on: bool = True):
    """Turn on/off the cancel call LED."""
    gpio_output(control_outputs.get("cancel_call"), on)


def direction_led(on: bool = True):
    """Turn on/off the direction lights; pick a rando direction..."""
    if on:
        if random.choice((True, False)):  # noqa
            gpio_output(control_outputs.get("direction_up"), on)
        else:
            gpio_output(control_outputs.get("direction_dn"), on)
    else:
        gpio_output(control_outputs.get("direction_up"), on)
        gpio_output(control_outputs.get("direction_dn"), on)


def door_close_led(on: bool = True):
    """Turn on/off the door close LED."""
    gpio_output(control_outputs.get("door_close"), on)


def door_open_led(on: bool = True):
    """Turn on/off the door open LED."""
    gpio_output(control_outputs.get("door_open"), on)


def floor_button_led(floor, on: bool = True):
    """Turn on/off floor LED."""
    if on:
        pca.channels[floor].duty_cycle = 0xFFFF
    else:
        pca.channels[floor].duty_cycle = 0


def all_lights_off():
    """Turn all Lights/LEDS off."""
    for i in range(0, 15):
        pca.channels[i].duty_cycle = 0
    for i in control_outputs.values():
        gpio_output(i, False)
