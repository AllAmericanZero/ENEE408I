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
import json
import cv2
import os
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

MOV_STILL = 0
MOV_FORWARD = 1
MOV_RIGHT = 2
MOV_FOLLOW = 3
MOV_ACT = 4
MOV_SIT = 5
CHECK_MESSAGES = 6
LONELY = 7
INVITE = 8

@ask.launch
def startup():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)


@ask.intent("follow")
def follow():
    msg = render_template('follow')
    with open('flags','w') as f:
        f.write(str(MOV_FOLLOW))
    return statement(msg)

@ask.intent("stopfollow")
def stopfollow():
    msg = render_template('stopfollow')
    with open('flags','w') as f:
        f.write(str(MOV_WANDER))

    return statement(msg)

@ask.intent("backward")
def backward():
    msg = render_template('backward')
    return statement(msg)

@ask.intent("freeze")
def freeze():
    msg = render_template('freeze')
    with open('flags','w') as f:
        f.write(str(MOV_STILL))
    return statement(msg)

@ask.intent("forward")
def forward():
    msg = render_template('forward')
    with open('flags','w') as f:
        f.write(str(SER_FWD))
    return statement(msg)

@ask.intent("act")
def act():
    msg = render_template('act')
    print("Act!")
    with open('flags','w') as f:
        f.write(str(MOV_ACT))
    return statement(msg)

@ask.intent("sit")
def sit():
    msg = render_template('sit')
    print("Sit!")
    with open('flags','w') as f:
        f.write(str(MOV_SIT))
    return statement(msg)

@ask.intent("messages")
def messages():
    msg = render_template('messages')
    with open('flags','w') as f:
        f.write(str(CHECK_MESSAGES))
    return statement(msg)

@ask.intent("lonely")
def lonely():
    msg = render_template('lonely')
    with open('flags','w') as f:
        f.write(str(LONELY))
    return statement(msg)

@ask.intent("invite")
def invite(day):
    msg = render_template('invite')
    with open('flags','w') as f:
        f.write(str(INVITE))
    with open('day.txt','w') as f:
        f.write(day.lower())
    return statement("I invited everyone over for "+ day.lower())	
@ask.intent("folchris")
def folchris():
    msg = render_template('folchris')
    with open('flags','w') as f:
        f.write(str(FOL_CHRIS))
    return statement(msg)

@ask.intent("folgil")
def folgil():
    msg = render_template('folgil')
    with open('flags','w') as f:
        f.write(str(FOL_GIL))
    return statement(msg)	

@ask.intent("folalex")
def folalex():
    msg = render_template('folalex')
    with open('flags','w') as f:
        f.write(str(FOL_ALEX))
    return statement(msg)

@ask.intent("addevent")
def addevent(event,day,time):
    msg = render_template('addevent')
    print(event)
    print(day.lower())
    hour = int(time.split(':',1)[0])
    minute = int(time.split(':',1)[1])
    print(hour)
    print(minute)
    if day.lower() == "monday":
        key = "mon"
    elif day.lower() == "tuesday":
        key = "tues"
    elif day.lower() == "wednesday":
        key = "wed"
    elif day.lower() == "thursday":
        key = "thurs"
    elif day.lower() == "friday":
        key = "fri"
    elif day.lower() == "saturday":
        key = "sat"
    else:
        key = "sun"
    print(key)
    with open('schedule.json','r') as jsonfile:
        sched = json.loads(jsonfile.read())
		
    message = "Reminder that you have " + event
    with open('schedule.json','w') as jsonfile:
        sched[key].append({"hour":hour,"min":minute,"message":message})
        json.dump(sched,jsonfile,sort_keys=True,indent=4, separators=(',',': '))
    return statement("I added "+ event+ " on "+day+" at "+time)

if __name__ == '__main__':
    app.run(debug=True)
