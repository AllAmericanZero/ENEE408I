
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

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)


MOV_STILL = 0
MOV_FOLLOW = 1
MOV_WANDER = 2



@ask.launch
def startup():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)


@ask.intent("follow")
def follow():
    msg = render_template('follow')
    f= open('flags','w')
    f.write(str(MOV_FOLLOW))
    f.close()
    return statement(msg)



@ask.intent("stopfollow")
def stopfollow():
    msg = render_template('stopfollow')
    f= open('flags','w')
    f.write(str(MOV_WANDER))
    f.close()

    return statement(msg)

@ask.intent("backward")
def backward():
    msg = render_template('backward')
    return statement(msg)


@ask.intent("freeze")
def freeze():
    msg = render_template('freeze')
    f= open('flags','w')
    f.write(str(MOV_STILL))
    f.close()
    return statement(msg)



@ask.intent("forward")
def forward():
    msg = render_template('forward')
    f= open('flags','w')
    f.write(str(SER_FWD))
    f.close()
    return statement(msg)





if __name__ == '__main__':
    app.run(debug=True)


