#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Low-Level (GPIO and PCA) module."""

import busio
import RPi.GPIO as GPIO
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


def cancel_call_led(on: bool = True):
    """Turn on/off the cancel call LED."""
    if on:
        GPIO.output(10, GPIO.HIGH)
    else:
        GPIO.output(10, GPIO.LOW)


def direction_led(on: bool = True):
    """Turn on/off the direction lights; pick a rando direction..."""
    if on:
        GPIO.output(14, GPIO.HIGH)
        GPIO.output(15, GPIO.HIGH)
    else:
        GPIO.output(14, GPIO.LOW)
        GPIO.output(15, GPIO.LOW)


def door_close_led(on: bool = True):
    """Turn on/off the door close LED."""
    if on:
        GPIO.output(8, GPIO.HIGH)
    else:
        GPIO.output(8, GPIO.LOW)


def door_open_led(on: bool = True):
    """Turn on/off the door open LED."""
    if on:
        GPIO.output(9, GPIO.HIGH)
    else:
        GPIO.output(9, GPIO.LOW)


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
    GPIO.output(14, GPIO.LOW)
    GPIO.output(15, GPIO.LOW)
