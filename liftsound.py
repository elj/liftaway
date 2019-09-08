#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division

import RPi.GPIO as GPIO
import pygame
import os
import sys
import time

from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

### custom variables for this file ###

cancelled = 0
lift_is_moving = 0

# set number of desired asynchronous audio channels (referenced later in mixer setup)
number_of_channels = 8

# set final fadeout time
exitfade = 1000

# setup adafruit I2C LED controller

i2c_bus = busio.I2C(SCL, SDA)
pca = PCA9685(i2c_bus)
pca.frequency = 60

for i in range(0,15):
        pca.channels[i].duty_cycle = 0 
        
red = pca.channels[14]
blue = pca.channels[15]
green = pca.channels[13]

### end custom variables ###
    
### functions and stuff go here ###

def go_to_floor(floor,direction):
    print ("[elev] Going to floor ", floor)
    global cancelled
    
    #if direction is positive turn on UP arrow, otherwise DOWN arrow
    if(direction>0):
        GPIO.output(14,GPIO.HIGH)
    if(direction<0):
        GPIO.output(15,GPIO.HIGH)
    ch6.play(e_travel)
    #time.sleep(6)		#TODO: randomize this time
    
    #try and see if call cancel button has been activated
    while(ch6.get_sound() == e_travel):
        if(cancelled==1):
            cancel_call_off()
            print("Travel cancelled")
            return -1
        time.sleep(0.5)
    
    #else:
    print ("[elev] Arriving...Ding!")
    ding.play()
    floor_button_off(floor)
    GPIO.output(14,GPIO.LOW)
    GPIO.output(15,GPIO.LOW)
    
    #open door and fade out music
    e_open.play()
    pygame.mixer.music.fadeout(1000)
    time.sleep(1.5)
    print ("[elev] Opening door at floor", floor)
    floors[floor][0].play()
    
    #hold the doors open to hear the sounds
    time.sleep(15)
    
    #close door, fade out the floor sounds and restart music
    print ("[elev] Closing door")
    e_close.play()
    floors[floor][0].fadeout(1700)
    time.sleep(2.5)
    pygame.mixer.music.play(-1)
    time.sleep(1)
    return floor

def floor_button_on(floor):
    pca.channels[floor].duty_cycle = 0xffff
        
def floor_button_off(floor):
    pca.channels[floor].duty_cycle = 0
        
def cancel_call_on(floor):
    global cancelled
    cancelled = 1
    if(floor<0):
        return
    floor_button_off(floor)
    if(ch6.get_sound() == e_travel):
        e_stop.play()
        ch6.fadeout(500)
    print("[control] Cancel ACTIVATED")
        
def cancel_call_off():
    global cancelled
    cancelled = 0
    GPIO.output(10,GPIO.LOW)
    print("[control] Cancel DEACTIVATED")
    
def start_emergency():
    #print("Starting emergency...")
    pygame.mixer.music.set_volume(0.0)
    ch7.play(e_emer)
    while(ch7.get_sound() == e_emer):
        time.sleep(0.5)

    for i in range(0,6):
        pygame.mixer.music.set_volume(pygame.mixer.music.get_volume() + 0.1)
        #print("Music volume:", pygame.mixer.music.get_volume())
        time.sleep(0.5)

def dont_push_this_button():
    global button_cycle
    ch7.play(buttons[button_cycle])
    button_cycle+=1
    if(button_cycle>7):
        button_cycle = 0
    
def play_voicemail():
    ch7.play(vm_r)
    ch7.queue(voicemail)
    while(ch7.get_sound == vm_r):
        time.sleep(0.5)
    while(ch7.get_sound == voicemail):
        pca.channels[12].duty_cycle = 0xffff
        time.sleep(0.5)
        pca.channels[12].duty_cycle = 0
        time.sleep(0)
        
def play_squeak():
    ch7.play(squeak)
    
def ceiling_light_on():
    red.duty_cycle = 0xffff
    green.duty_cycle = 0x4000
    
def all_lights_off():
    for i in range(0,15):
        pca.channels[i].duty_cycle = 0

### end functions ###

pygame.mixer.pre_init(44100, -16, 2, 3072) # setup mixer to avoid sound lag
## (freq, bits, channels, buffer)

pygame.init()						#initialize pygame - this is where terrible things happen
pygame.mixer.set_num_channels(number_of_channels)	# must come *after* .init
pygame.mixer.set_reserved(2)

ch7 = pygame.mixer.Channel(7)
ch6 = pygame.mixer.Channel(6)
button_cycle = 0

# look for sound & music files in subfolder 'data'
pygame.mixer.music.load("data/muzak.wav") #load music
ding = pygame.mixer.Sound("data/lift_ding.wav")
e_travel = pygame.mixer.Sound(os.path.join('data', 'elevator_travel.wav'))
e_open = pygame.mixer.Sound(os.path.join('data', 'elevator_open.wav'))
e_close = pygame.mixer.Sound(os.path.join('data', 'elevator_close2.wav'))
e_stop = pygame.mixer.Sound(os.path.join('data', 'elevator_stop.wav'))
e_emer = pygame.mixer.Sound("data/emergency.wav")
squeak = pygame.mixer.Sound("data/squeak1.wav")
e_emer.set_volume(0.8)
squeak.set_volume(0.3)


pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

###	LOAD FLOOR SOUNDS HERE	###

# floor = sound,                                               fadeout_ms, loops]

floor0 = [pygame.mixer.Sound("data/train.wav"),     0,        0]
floor1 = [pygame.mixer.Sound("data/rocket.wav"),   100,        0]
floor2 = [pygame.mixer.Sound("data/obnoxious_frogs.wav"),   100,        0]
floor3 = [pygame.mixer.Sound("data/Waves.wav"),   	100,        0]
floor4 = [pygame.mixer.Sound("data/popcorn.wav"),   100,        0]
floor5 = [pygame.mixer.Sound("data/orchestra.wav"),   100,        0]
floor6 = [pygame.mixer.Sound("data/baseball_2ch.wav"),   100,        0]
floor7 = [pygame.mixer.Sound("data/diner_2ch.wav"),   100,        0]
floor8 = [pygame.mixer.Sound("data/thunderstorm.wav"),   100,        0]
floor9 = [pygame.mixer.Sound("data/pinball.wav"),   100,        0]
floor10 = [pygame.mixer.Sound("data/submarine.wav"),  100,        0]
floor11 = [pygame.mixer.Sound("data/wharf.wav"),  100,        0]


floors = [floor0, floor1, floor2, floor3, floor4, floor5, floor6, floor7, floor8, floor9, floor10,
         floor11]

buttons = [pygame.mixer.Sound("data/voice/button_different.wav"),
            pygame.mixer.Sound("data/voice/button_dontpress.wav"),
            pygame.mixer.Sound("data/voice/button_mad.wav"),
            pygame.mixer.Sound("data/voice/button_notlike.wav"),
            pygame.mixer.Sound("data/voice/button_notpressing.wav"),
            pygame.mixer.Sound("data/voice/button_outofservice.wav"),
            pygame.mixer.Sound("data/voice/button_stop.wav"),
            pygame.mixer.Sound("data/voice/button_sure.wav"),
            ]
            
for i in range(0,7):
    buttons[i].set_volume(0.8)

voicemail = pygame.mixer.Sound("data/voice/vm_dutch.wav")
vm_r = pygame.mixer.Sound("data/voice/vm_ringing.wav")
voicemail.set_volume(0.6)
vm_r.set_volume(0.7)
