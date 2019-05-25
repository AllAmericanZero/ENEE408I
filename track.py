import logging
from imutils.video import VideoStream
from imutils.object_detection import non_max_suppression
from collections import deque
from imutils.video import FPS
import tracking_func
import numpy as np
import pytesseract
import argparse
import pyttsx
import imutils
import serial
from twilio.rest import Client
import pickle
import struct
import time
import math
import cv2
import random
import os
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session

green = (0,255,0)
blue  = (255,0,0)

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
vs = VideoStream(src=0).start()
time.sleep(2.0)

engine  = pyttsx.init()
romeo   = pyttsx.init()
juliet  = pyttsx.init()
juliet.setProperty("voice",juliet.getProperty("voices")[1].id)
r_s = False
j_s = False
n_s = False
scene = ["scene.txt","scene2.txt"]
guy = ["ROMEO", "ANAKIN"]
girl = ["JULIET","PADME"]
last_flag = 0
master = "alex"
while 1:

	# start the FPS throughput estimator
	fps = FPS().start()
	while True:
		master_found = False
		while not master_found:
			# grab the current frame, then handle if we are using a
			# VideoStream or VideoCapture object
			frame = vs.read()
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
		width	= 3*initBB[2]
		height	= 3*initBB[3]
		initBB 	= (start_x,start_y,width,500-start_y)
		print(initBB)
		tracker.init(frame, initBB)

		fps = FPS().start()
		master_found = True
		coords_last = (0,0)
		i = 0
		while (master_found):
			# grab the current frame, then handle if we are using a
			# VideoStream or VideoCapture object
			frame = vs.read()
			# resize the frame (so we can process it faster) and grab the
			# frame dimensions
			frame = imutils.resize(frame, width=600)
			[master_found, coords,frame] = tracking_func.facial_fol(tracker,initBB,vs,fps,args,frame,green)
			if i==0:
				tracker2 = OPENCV_OBJECT_TRACKERS[args["tracker"]]()
				[initBB2, frame2, master_found2] = tracking_func.facial_rec(master,vs,detector,args,embedder,recognizer,fps,le,frame)
				tracker2.init(frame,initBB2)
			[master_found2, coords2,frame] = tracking_func.facial_fol(tracker2,initBB2,vs,fps,args,frame,blue)
			# show the output frame
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF
			i = (i + 1) % 10
			if coords[0] == 0 and coords[1] == 0:
				coords = coords_last
				break
			if coords[0] > x_center+error_dist:
				#Turn right 3
				print("RIGHT!")
			elif coords[0] < x_center-error_dist:
				#Turn Left 2
				print("LEFT!")
			elif initBB2[2] < 100:
				# Move servo up
				print("FORWARD!")
			else:
				print("STOP!")
			coords_last = coords
		# ser.write(struct.pack('>B',SER_STOP))
		try:
			ser.write(struct.pack('>B',SER_STOP))
		except:
			print("Stop!")
		tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()
		print("LOST MASTER!")
	# stop the timer and display FPS information
	fps.stop()
vs.stop()