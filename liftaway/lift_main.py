#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Liftaway main business logic."""

import time
from collections import deque

import liftaway.constants as constants
import liftaway.leds as leds
import liftaway.liftsound as liftsound
import RPi.GPIO as GPIO


q = deque()
current_floor = -1


def floor_queue_callback(channel):
    global current_floor
    print("Detected pin", channel)  # debug

    # find out which floor number it is
    requested_floor = constants.gpio_to_floor_mapping.get(channel)
    if requested_floor < 0:
        print("Not a valid floor")
        return

    # turn the button light on
    leds.floor_button_on(requested_floor)

    # determine whether it's the current floor. TODO: Open door?
    # ~ if(requested_floor == current_floor):
    # ~ print("Not adding current floor")
    # ~ time.sleep(0.5)
    # ~ leds.floor_button_off(requested_floor)

    # if it's a different floor, add that floor to the queue
    # else:
    print("[queue] Adding to queue floor", requested_floor)  # debug
    q.append(requested_floor)  # add this floor to the queue


# When there are floors in the queue, travel to those floors
def process_floor_queue():
    global current_floor
    print("[queue] Processing queue...")
    next_floor = q.popleft()
    if next_floor == current_floor:
        print("Skipping redundant floor")
        return

    direction = next_floor - current_floor

    current_floor = next_floor

    # all the important elevator stuff happens here:
    this_floor = liftsound.go_to_floor(next_floor, direction)
    print("[elev] Doors closed on floor", this_floor)


# stop elevator and clear the queue
def control_cancel_callback(channel):
    global current_floor
    if channel != 27:
        return
    # turn on the call cancel button light
    GPIO.output(10, GPIO.HIGH)
    print("[queue] **Clearing floor queue!**")
    # TODO: turn off all the floor button lights
    global current_floor
    liftsound.cancel_call_on(current_floor)
    if q:
        while q:
            f = q.popleft()
            print("[queue] ***removing floor ", f)
            leds.floor_button_off(f)
            time.sleep(0.2)
    current_floor = -1
    GPIO.output(10, GPIO.LOW)


# do all the emergency stuff
def control_emergency_callback(channel):
    # turn on the emergency button light
    print("[control] **Emergency button pressed!**")
    liftsound.start_emergency()
    time.sleep(1)
    # print("Emergency complete")


def control_help_callback(channel):
    print("[control] **Call for help button pressed!**")
    liftsound.play_voicemail()


def control_door_open_callback(channel):
    if channel != 26:
        return
    else:
        # turn on the door open button light
        GPIO.output(9, GPIO.HIGH)
        print("**Door open button pressed!**")
        liftsound.play_squeak()
        time.sleep(0.5)
        GPIO.output(9, GPIO.LOW)


def control_door_close_callback(channel):
    if channel != 24:
        return
    else:
        # turn on the door close button light
        GPIO.output(8, GPIO.HIGH)
        print("[control] **Don't push this button pressed!**")
        liftsound.dont_push_this_button()
        time.sleep(0.5)
        GPIO.output(8, GPIO.LOW)


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    GPIO.setup(
        list(constants.gpio_to_floor_mapping.keys()), GPIO.IN, pull_up_down=GPIO.PUD_UP
    )
    GPIO.setup(constants.control_inputs, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(constants.control_outputs, GPIO.OUT)

    for i in constants.gpio_to_floor_mapping.keys():
        GPIO.add_event_detect(
            i, GPIO.RISING, callback=floor_queue_callback, bouncetime=1000
        )
    GPIO.add_event_detect(
        23, GPIO.RISING, callback=control_help_callback, bouncetime=15000
    )
    GPIO.add_event_detect(
        24, GPIO.RISING, callback=control_door_close_callback, bouncetime=1000
    )
    GPIO.add_event_detect(
        25, GPIO.RISING, callback=control_emergency_callback, bouncetime=20000
    )
    GPIO.add_event_detect(
        26, GPIO.RISING, callback=control_door_open_callback, bouncetime=1000
    )
    GPIO.add_event_detect(
        27, GPIO.RISING, callback=control_cancel_callback, bouncetime=3000
    )
    leds.init()

    print("ready...")
    try:
        while True:
            if len(q) > 0:
                process_floor_queue()
            else:
                # print("N")
                time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt has been caught.")
        leds.all_lights_off()
        for i in constants.control_outputs:
            GPIO.output(i, GPIO.LOW)
        GPIO.cleanup()


if __name__ == "__main__":
    main()
