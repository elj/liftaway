#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liftaway Constants and Definitions."""

# Floor to RPi GPIO Input Pin Mapping
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
flavor_to_gpio_mapping = {
    "voicemail": 23,
    "no_press": 24,
    "emergency": 25,
    "squeaker": 26,
    "cancel": 27,
}

# RPi GPIO output pin to led mappings
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
    0: ({"filename": "train.wav"},),
    1: ({"filename": "rocket.wav"},),
    2: ({"filename": "obnoxious_frogs.wav"},),
    3: ({"filename": "waves_2ch.wav"},),
    4: ({"filename": "popcorn.wav"},),
    5: ({"filename": "orchestra.wav"},),
    6: ({"filename": "baseball_2ch.wav"},),
    7: ({"filename": "diner_2ch.wav"},),
    8: ({"filename": "thunderstorm.wav"},),
    9: ({"filename": "pinball.wav"},),
    10: ({"filename": "submarine.wav"},),
    11: ({"filename": "wharf.wav"},),
}

# Audio played in-between floor audio
in_between_audio = {
    "muzak": {"filename": "muzak.wav", "volume": 0.5},
    "ding": {"filename": "lift_ding.wav"},
    "open": {"filename": "elevator_open.wav"},
    "close": {"filename": "elevator_close.wav"},
    "travel": {"filename": "elevator_travel.wav", "audio_channel": "movement"},
    "halt": {"filename": "elevator_stop.wav", "audio_channel": "movement"},
}

# Button A - Call for Help
voicemail_button_audio = tuple(  # noqa
    [{"filename": "voice_vm_dutch.wav", "volume": 0.6, "audio_channel": "voicemail"}]
)

# Button B - Door Open
squeaker_button_audio = tuple(  # noqa
    [{"filename": "squeak2.wav", "volume": 0.3, "audio_channel": "squeaker"}]
)

# Button C - Emergency
emergency_button_audio = tuple(  # noqa
    [{"filename": "emergency.wav", "volume": 0.8, "audio_channel": "emergency"}]
)

# Button D - Door Close
no_press_button_audio = tuple(  # noqa
    [
        {
            "filename": "voice_button_different.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_dontpress.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_mad.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_notlike.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_notpressing.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_outofservice.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_stop.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
        {
            "filename": "voice_button_sure.wav",
            "volume": 0.8,
            "audio_channel": "no_press",
        },
    ]
)
