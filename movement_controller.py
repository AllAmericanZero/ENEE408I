from imutils.object_detection import non_max_suppression
from flask_ask import Ask, statement, question, session
from flask import Flask, render_template
from imutils.video import VideoStream
from playsound import playsound
from twilio.rest import Client
from collections import deque
from imutils.video import FPS
import tracking_func
import numpy as np
import pytesseract
import argparse
import imutils
import logging
import serial
import pyttsx
import random
import pickle
import struct
import time
import math
import cv2
import mes
import os

green = (0,255,0)
blue  = (255,0,0)

# Set up serial communication
# for i in range(0,10):
#     try:
#         ser = serial.Serial('COM' + str(i),9600,timeout=0)
#         # ser = serial.Serial('/dev/ttyUSB' + str(i),9600)
#     except:
#         continue
#     else:
#         print('COM' + str(i))
#         break
for com in ['COM3','COM4','COM5']:
    try:
        ser = serial.Serial(com,9600,timeout=0)
    except:
        continue
    else:
        break
# Center of the camera frame
x_center = 300
y_center = 250

# Amount of error in pixels we are willing to tolerate
error_dist = 50

R2C_DELAY = 843/1000
R2L_DELAY = 1686/1000
L2C_DELAY = 833/1000
L2R_DELAY = 1666/1000

# Commands
SER_STOP  = 0
SER_FWD   = 1
SER_LEFT  = 2
SER_RIGHT = 3
SER_LON   = 6
SER_LOFF  = 7
SER_FWD_LFT = 8
SER_FWD_RGT = 9
SER_START_THEATRE = 20
SER_END_THEATRE = 21
SER_TO_RIGHT = 24
SER_TO_CENTER = 25
SER_TO_LEFT = 26

MOV_STILL = 0
MOV_FORWARD = 1
MOV_RIGHT = 2
MOV_FOLLOW = 3
MOV_ACT = 4
MOV_SIT = 5
CHECK_MESSAGES = 6
LONELY = 7
INVITE = 8

try:
	mes.open_service("Twitchy")
except:
	print("Timed out")

account_sid = 'AC73b795f32902823dc799b09856fe41c9'
auth_token = 'c3beb617b2227f80e574a886461cae26'
client = Client(account_sid, auth_token)
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--detector", required=True,
	help="path to OpenCV's deep learning face detector")
ap.add_argument("-east", "--east", type=str,
	help="path to input EAST text detector")
ap.add_argument("-m", "--embedding-model", required=True,
	help="path to OpenCV's deep learning face embedding model")
ap.add_argument("-w", "--width", type=int, default=320,
	help="nearest multiple of 32 for resized width")
ap.add_argument("-e", "--height", type=int, default=320,
	help="nearest multiple of 32 for resized height")
ap.add_argument("-p", "--padding", type=float, default=0.0,
	help="amount of padding to add to each border of ROI")
ap.add_argument("-r", "--recognizer", required=True,
	help="path to model trained to recognize faces")
ap.add_argument("-l", "--le", required=True,
	help="path to label encoder")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
ap.add_argument("-t", "--tracker", type=str, default="kcf",
	help="OpenCV object tracker type")
args = vars(ap.parse_args())

# initialize a dictionary that maps strings to their corresponding
# OpenCV object tracker implementations
OPENCV_OBJECT_TRACKERS = {
	"csrt": cv2.TrackerCSRT_create,
	"kcf": cv2.TrackerKCF_create,
	"boosting": cv2.TrackerBoosting_create,
	"mil": cv2.TrackerMIL_create,
	"tld": cv2.TrackerTLD_create,
	"medianflow": cv2.TrackerMedianFlow_create,
	"mosse": cv2.TrackerMOSSE_create
}

# grab the appropriate object tracker using our dictionary of
# OpenCV object tracker objects
tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()
tracker2 = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

# load our serialized face detector from disk
print("[INFO] loading face detector...")
protoPath = os.path.sep.join([args["detector"], "deploy.prototxt"])
modelPath = os.path.sep.join([args["detector"],
	"res10_300x300_ssd_iter_140000.caffemodel"])
detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

# load our serialized face embedding model from disk
print("[INFO] loading face recognizer...")
embedder = cv2.dnn.readNetFromTorch(args["embedding_model"])

# load the actual face recognition model along with the label encoder
recognizer = pickle.loads(open(args["recognizer"], "rb").read())
le = pickle.loads(open(args["le"], "rb").read())

print("[INFO] starting video stream...")
vs = VideoStream(src=1).start()
time.sleep(2.0)

engine  = pyttsx.init()
romeo   = pyttsx.init()
juliet  = pyttsx.init()
juliet.setProperty("voice",juliet.getProperty("voices")[1].id)
r_s = False
j_s = False
n_s = False
scene = ["scene.txt","scene2.txt","scene3.txt","script3.txt"]
guy = ["ROMEO", "ANAKIN","MARTY","MARLIN"]
girl = ["JULIET","PADME","LORAINE","DORY"]
last_flag = 0
master = "alex"

messages = []

while 1:
    with open('flags','r') as f:
        read_flag = int(f.read())

    # Stop
    if read_flag == MOV_STILL:
        try:
            ser.write(struct.pack('>B',SER_STOP))
        except:
            tracking_func.speak(engine,"Stop!")
    # Forward
    elif read_flag == MOV_FORWARD:
        try:
            ser.write(struct.pack('>B',SER_FWD))
        except:
            tracking_func.speak(engine,"Forward!")
    # Right
    elif read_flag == MOV_RIGHT:
        try:
            ser.write(struct.pack('>B',SER_RIGHT))
        except:
            tracking_func.speak(engine,"Right!")
    # Follow
    elif read_flag == MOV_FOLLOW:
        # start the FPS throughput estimator
        ser.write(struct.pack('>B',SER_STOP))

        fps = FPS().start()
        while (read_flag == 3):
            master_found = False
            while not master_found and read_flag == 3:
                # grab the current frame, then handle if we are using a
                # VideoStream or VideoCapture object
                frame = vs.read()
                # Check if Alexa gave us a new command
                with open('flags','r') as f:
                    read_flag = int(f.read())

                # resize the frame (so we can process it faster) and grab the
                # frame dimensions
                frame = imutils.resize(frame, width=600)
                [initBB, frame,master_found] = tracking_func.facial_rec(master,vs,detector,args,embedder,recognizer,fps,le,frame)
                # show the output frame
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF

            # loop over frames from the video stream
            tracker2.init(frame,initBB)
            start_x = initBB[0] - initBB[2]
            start_y = initBB[1]
            width   = 3*initBB[2]
            height	= 3*initBB[3]
            initBB 	= (start_x,start_y,width,500-start_y)
            print(initBB)
            tracker.init(frame, initBB)
            fps = FPS().start()
            master_found = True
            coords_last = (0,0)
            i = 0
            while (master_found and read_flag == 3):
           	    # grab the current frame, then handle if we are using a
           	    # VideoStream or VideoCapture object
                frame = vs.read()
                # resize the frame (so we can process it faster) and grab the
                # frame dimensions
                frame = imutils.resize(frame, width=600)
                if i == 0 or not master_found:
                    [master_found2, coords,frame] = tracking_func.facial_fol(tracker,initBB,vs,fps,args,frame,green)
                    if master_found2:
                        start_x = initBB[0] - initBB[2]
                        start_y = initBB[1]
                        width   = 3*initBB[2]
                        height	= 3*initBB[3]
                        initBB 	= (start_x,start_y,width,500-start_y)
                        print(initBB)
                        tracker.init(frame, initBB)
                elif master_found:
                    [initBB2, frame, master_found] = tracking_func.facial_rec(master,vs,detector,args,embedder,recognizer,fps,le,frame)

                # show the output frame
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF
                i = (i + 1) % 10
                print(coords)
				
                if coords[0] <= 0:
                    ser.write(struct.pack('>B',SER_STOP))
                elif coords[0] > x_center+error_dist and master_found:
                    #Turn right 3
                    print("Right")
                    ser.write(struct.pack('>B',SER_RIGHT))
                elif coords[0] < x_center-error_dist and master_found:
                    #Turn Left 2
                    print("Left")
                    ser.write(struct.pack('>B',SER_LEFT))
                elif initBB2[2] < 80 and master_found2:
                    # Move servo up
                    print("Forward")
                    ser.write(struct.pack('>B',SER_FWD))
                else:
                    ser.write(struct.pack('>B',SER_STOP))
                    print("Stop")

                # Check if Alexa gave us a new command
                with open('flags','r') as f:
                    read_flag = int(f.read())
                if coords[1] - coords_last[1] < -100:
                    ser.write(struct.pack('>B',SER_STOP))
                    try:
                        mes.send_alert()
                    except:
                        print("Send alert!")
                        print("Sending message!")
                        message = client.messages \
                                    .create(
                                        body='Alex has fallen!',
                                        from_='+14436376388',
                                        to='+14107393906'
                                    )
                        print(message.sid)
                coords_last = coords
            # ser.write(struct.pack('>B',SER_STOP))
            try:
                ser.write(struct.pack('>B',SER_STOP))
            except:
                print("Stop!")
            tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()
            tracker2 = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

			# stop the timer and display FPS information
        fps.stop()

    # Act
    elif read_flag == MOV_ACT:
        number = random.randint(0,3)
        with open(scene[number],"r") as play:
            line = play.readline()
            while line:
                with open('flags','r') as f:
                    read_flag = int(f.read())
                    if read_flag != 4:
                        break
                if line.startswith(guy[number],0,len(guy[number])):
                    try:
                        ser.write(struct.pack('>B',SER_TO_LEFT))
                    except:
                        print("To the left!")
                    if j_s:
                        time.sleep(R2L_DELAY)
                    elif n_s:
                        time.sleep(R2C_DELAY)
                    r_s = True
                    j_s = False
                    n_s = False
                    try:
                        line = line.split(':',1)[1]
                    except:
                        break
                    juliet.setProperty("voice",juliet.getProperty("voices")[0].id)

                elif line.startswith(girl[number],0,len(girl[number])):
                    try:
                        ser.write(struct.pack('>B',SER_TO_RIGHT))
                    except:
                        print("To the right!")

                    if r_s:
                        time.sleep(L2R_DELAY)
                    elif n_s:
                        time.sleep(L2C_DELAY)
                    r_s = False
                    j_s = True
                    n_s = False
                    try:
                        line = line.split(':',1)[1]
                    except:
                        break
                    juliet.setProperty("voice",juliet.getProperty("voices")[1].id)

                elif line.startswith("STAGE",0,5):
                    try:
                        ser.write(struct.pack('>B',SER_TO_CENTER))
                    except:
                        print("To the fore!")
                    if r_s:
                        time.sleep(L2C_DELAY)
                    elif j_s:
                        time.sleep(R2C_DELAY)
                    r_s = False
                    j_s = False
                    n_s = True
                    try:
                        line = line.split(':',1)[1]
                    except:
                        break
                    juliet.setProperty("voice",juliet.getProperty("voices")[0].id)
                tracking_func.speak(engine,line)
                line = play.readline()
        juliet.setProperty("voice",juliet.getProperty("voices")[1].id)
        try:
            ser.write(struct.pack('>B',SER_TO_CENTER))
        except:
            print("Reset to center!")
    # Sit check
    elif read_flag == MOV_SIT:
        tracking_func.run_sit_check(master,detector,args,embedder,recognizer,le,tracker,engine,OPENCV_OBJECT_TRACKERS,vs,ser)
        while read_flag == 5:
            with open('flags','r') as f:
                read_flag = int(f.read())
    elif read_flag == CHECK_MESSAGES:
        for message in messages:
            engine.say(message)
            engine.runAndWait()
        messages = []
    elif read_flag == LONELY:
        try:
            mes.send_room_message("Alex is lonely!")
        except:
            print("Oops, no message")
    elif read_flag == INVITE:
        try:
            with open("day.txt","r") as f:
                day = f.read()
                mes.send_room_message("Please come over to " +master+ "'s " + day.lower())
        except:
            print("Oops, no message")	
    elif read_flag == FOL_CHRIS:
        master = "chris"
    elif read_flag == FOL_GIL:
        master = "gil"
    elif read_flag == FOL_ALEX:
        master = "alex"
	
    new_messages = []
    try:
        new_messages = mes.get_messages()
    except:
        print("Nope")
    else:
        if new_messages:
            if any("dead" in x[2].lower() for x in new_messages) or any("fallen" in x[2].lower() for x in new_messages):
                print("Uh oh!")
                playsound("funeral_march.mp3")
            if any("birthday" in x[2].lower() for x in new_messages):
                for entry in new_messages:
                    if "birthday" in entry:
        				tracking_func.speak(engine,"Happy birthday to " + entry[1])
            for entry in new_messages:
                messages.append(entry[1] + " said " + entry[2])
    time.sleep(1)
    new_messages = []
    last_flag = read_flag
    time.sleep(.1)
vs.stop()
