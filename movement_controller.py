import logging
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import serial
import pickle
import struct
import time
import math
import cv2
import os
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session



# Set up serial communication
for i in range(0,10):
    try:
        ser = serial.Serial('/dev/ttyUSB' + str(i),9600)
    except:
        continue
    else:
        break
# Commands
SER_STOP  = 0
SER_FWD   = 1
SER_LEFT  = 2
SER_RIGHT = 3
SER_LON   = 6
SER_LOFF  = 7

MOV_STILL = 0
MOV_FOLLOW = 1
MOV_WANDER = 2


while 1:
    f= open('flags','r')
    read_flag = int(f.read())
    
    f.close()
    
    if read_flag == 0:
        ser.write(struct.pack('>B',SER_STOP))
    elif read_flag == 1:
        ser.write(struct.pack('>B',SER_FWD))
    elif read_flag == 2:
        ser.write(struct.pack('>B',SER_RIGHT))
    
    time.sleep(.1)
