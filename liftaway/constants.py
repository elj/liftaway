#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Constants and Definitions."""


# RPi GPIO Pin to Floor Mapping
gpio_to_floor_mapping = {
    22: 0,
    4: 1,
    5: 2,
    6: 3,
    12: 4,
    13: 5,
    16: 6,
    17: 7,
    18: 8,
    19: 9,
    20: 10,
    21: 11,
}
floor_to_gpio_mapping = {(v, k) for k, v in gpio_to_floor_mapping.items()}

control_inputs = [23, 24, 25, 26, 27]
control_outputs = {
    "nothing": 7,
    "door_close": 8,
    "door_open": 9,
    "cancel_call": 10,
    "emergency_call": 11,
    "direction_up": 14,
    "direction_dn": 15,
}
