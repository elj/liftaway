#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway Constants and Definitions."""

from typing import NamedTuple


AudioTrack = NamedTuple("AudioTrack", [("filename", str), ("volume", float)])

# Floor to RPi GPIO Pin Mapping
floor_to_gpio_mapping = {
    0: 22,
    1: 4,
    2: 5,
    3: 6,
    4: 12,
    5: 13,
    6: 16,
    7: 17,
    8: 18,
    9: 19,
    10: 20,
    11: 21,
}
gpio_to_floor_mapping = {v: k for k, v in floor_to_gpio_mapping.items()}

control_inputs = [23, 24, 25, 26, 27]

# RPi GPIO output to pin mappings
control_outputs = {
    "nothing": 7,
    "door_close": 8,
    "door_open": 9,
    "cancel_call": 10,
    "emergency_call": 11,
    "direction_up": 14,
    "direction_dn": 15,
}

# Audio played when a floor floor is active
floor_audio = {
    0: (AudioTrack("train.wav", 1.0),),
    1: (AudioTrack("rocket.wav", 1.0),),
    2: (AudioTrack("obnoxious_frogs.wav", 1.0),),
    3: (AudioTrack("Waves.wav", 1.0),),
    4: (AudioTrack("popcorn.wav", 1.0),),
    5: (AudioTrack("orchestra.wav", 1.0),),
    6: (AudioTrack("baseball_2ch.wav", 1.0),),
    7: (AudioTrack("diner_2ch.wav", 1.0),),
    8: (AudioTrack("thunderstorm.wav", 1.0),),
    9: (AudioTrack("pinball.wav", 1.0),),
    10: (AudioTrack("submarine.wav", 1.0),),
    11: (AudioTrack("wharf.wav", 1.0),),
}

# Audio played in-between floor audio
in_between_audio = {
    "ding": AudioTrack("lift_ding.wav", 1.0),
    "open": AudioTrack("elevator_open.wav", 1.0),
    "close": AudioTrack("elevator_close2.wav", 1.0),
    "travel": AudioTrack("elevator_travel.wav", 1.0),
    "halt": AudioTrack("elevator_stop.wav", 1.0),
    "emer": AudioTrack("emergency.wav", 0.8),
}

letter_a_button_audio = (
    AudioTrack("voice_button_different.wav", 0.8),
    AudioTrack("voice_button_dontpress.wav", 0.8),
    AudioTrack("voice_button_mad.wav", 0.8),
    AudioTrack("voice_button_notlike.wav", 0.8),
    AudioTrack("voice_button_notpressing.wav", 0.8),
    AudioTrack("voice_button_outofservice.wav", 0.8),
    AudioTrack("voice_button_stop.wav", 0.8),
    AudioTrack("voice_button_sure.wav", 0.8),
)

letter_d_button_audio = (AudioTrack("squeak1.wav", 0.3),)
