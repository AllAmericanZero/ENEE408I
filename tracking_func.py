from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
from collections import deque
#import serial
import pickle
import struct
import time
import math
import cv2
import os

SER_STOP  = 0
SER_FWD   = 1
SER_LEFT  = 2
SER_RIGHT = 3
SER_BACK  = 5
SER_LON   = 6
SER_LOFF  = 7
SER_FWD_LFT = 8
SER_FWD_RGT = 9
SER_START_THEATRE = 20
SER_END_THEATRE = 21
SER_TO_RIGHT = 24
SER_TO_CENTER = 25
SER_TO_LEFT = 26


def speak (engine, phrase):
    engine.say(phrase)
    engine.runAndWait()

def facial_rec (master_name, vs, detector,args,embedder,recognizer,fps,le,frame):
    master_found = False
    green = (0, 255, 0)
    red   = (0, 0, 255)
    (startX, startY, endX, endY) = (0,0,0,0)
    # loop over frames from the video file stream
    # grab the frame from the threaded video stream
    frame = vs.read()

    # resize the frame to have a width of 600 pixels (while
	# maintaining the aspect ratio), and then grab the image
	# dimensions
    frame = imutils.resize(frame, width=600)
    (h, w) = frame.shape[:2]

    # construct a blob from the image
    imageBlob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 1.0, (300, 300),
        (104.0, 177.0, 123.0), swapRB=False, crop=False)

    # apply OpenCV's deep learning-based face detector to localize
    # faces in the input image
    detector.setInput(imageBlob)
    detections = detector.forward()

    # loop over the detections
    for i in range(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]

        # filter out weak detections
        if confidence > args["confidence"]:
            # compute the (x, y)-coordinates of the bounding box for
            # the face
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # extract the face ROI
            face = frame[startY:endY, startX:endX]
            (fH, fW) = face.shape[:2]

            # ensure the face width and height are sufficiently large
            if fW < 20 or fH < 20:
                continue

            # construct a blob for the face ROI, then pass the blob
            # through our face embedding model to obtain the 128-d
            # quantification of the face
            faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255,
            (96, 96), (0, 0, 0), swapRB=True, crop=False)
            embedder.setInput(faceBlob)
            vec = embedder.forward()

            # perform classification to recognize the face
            preds = recognizer.predict_proba(vec)[0]
            j = np.argmax(preds)
            proba = preds[j]
            color = red
            if int(proba*100) > 80:
                if master_name == le.classes_[j]:
                    color = green
                    master_found = True
                    break
            else:
                name = "unknown"

            # draw the bounding box of the face along with the
            # associated probability
            cv2.rectangle(frame, (startX, startY), (endX, endY),
                color, 2)

	# Send back (x,y,w,h), the frame, and if master was found or not
    return [(startX,startY,endX-startX,endY-startY), frame, master_found]

def facial_fol (tracker, initBB,vs,fps,args,frame, color):

	(H, W) = frame.shape[:2]

	# check to see if we are currently tracking an object
	# grab the new bounding box coordinates of the object
	(success, box) = tracker.update(frame)

	# check to see if the tracking was a success
	if success:
		(x, y, w, h) = [int(v) for v in box]
		cv2.rectangle(frame, (x, y), (x + w, y + h),
			color, 2)
	else:
		(x, y, w, h) = (0, 0, 0, 0)
	# update the FPS counter
	fps.update()
	fps.stop()

	# initialize the set of information we'll be displaying on
	# the frame
	info = [
		("FPS", "{:.2f}".format(fps.fps()))
	]

	# loop over the info tuples and draw them on our frame
	for (i, (k, v)) in enumerate(info):
		text = "{}: {}".format(k, v)
		cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
			cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

	return [success, ((x + x + w)/2,(y + y + h)/2), frame]

def check_sitting (tracker, initBB,vs,fps,args):

	# grab the current frame, then handle if we are using a
	# VideoStream or VideoCapture object
	frame = vs.read()


	# resize the frame (so we can process it faster) and grab the
	# frame dimensions
	frame = imutils.resize(frame, width=600)
	(H, W) = frame.shape[:2]

	# check to see if we are currently tracking an object
	# grab the new bounding box coordinates of the object
	(success, box) = tracker.update(frame)

	# check to see if the tracking was a success
	if success:
		(x, y, w, h) = [int(v) for v in box]
	else:
		(x, y, w, h) = (0, 0, 0, 0)

	return [success, ((x + x + w)/2,(y + y + h)/2),H,W,frame]

def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def run_sit_check(master,detector,args,embedder,recognizer,le,tracker,engine,OPENCV_OBJECT_TRACKERS,vs,ser):
	# start the FPS throughput estimator
	fps = FPS().start()
	pts = []
	pts = deque(maxlen=200)
	tracker2 = OPENCV_OBJECT_TRACKERS[args["tracker"]]()
	while True:
		master_found = False
		while not master_found:
			# grab the current frame, then handle if we are using a
			# VideoStream or VideoCapture object
			frame = vs.read()
			# Check if Alexa gave us a new command
			with open('flags','r') as f:
				read_flag = int(f.read())

			# resize the frame (so we can process it faster) and grab the
			# frame dimensions
			frame = imutils.resize(frame, width=600)
			[initBB, frame,master_found] = facial_rec(master,vs,detector,args,embedder,recognizer,fps,le,frame)
			# show the output frame
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF

		# loop over frames from the video stream
		tracker.init(frame, initBB)
		tracker2.init(frame,initBB)

		fps = FPS().start()
		master_found = True
		coords_last = (0,0)
		i = 0
		coords = (int(((2*initBB[0] + initBB[2])/2)),int((2*initBB[1] + initBB[3])/2))
		start_pos = coords
		start_time = time.time()
		speak(engine,"Stand!")
		while (master_found):
		
			# grab the current frame, then handle if we are using a
			# VideoStream or VideoCapture object
			frame = vs.read()
			# resize the frame (so we can process it faster) and grab the
			# frame dimensions
			frame = imutils.resize(frame, width=600)
			[master_found, coords,H,W,frame] = check_sitting(tracker,initBB,vs,fps,args)
			# loop over the info tuples and draw them on our frame
			coords = (int(coords[0]),int(coords[1]))
			if all(v == 0 for v in coords):
				try:
					coords = pts[-1]
				except:
					print("Nope")
			pts.appendleft(coords)

			# loop over the set of tracked points
			for i in range(1, len(pts)):
				# if either of the tracked points are None, ignore
				# them
				if pts[i - 1] is None or pts[i] is None:
					continue
				# otherwise, compute the thickness of the line and
				# draw the connecting lines
				thickness = 10
				cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF
			try:
				change_state = (abs(pts[1][1] - pts[10][1]) < 1.5)
			except:
				change_state = 0
			else:
				print(str(abs(pts[1][1] - pts[10][1])) + ' ' + str(pts[1][1]-start_pos[1]))
			if change_state == 1 and (pts[1][1]-start_pos[1] < -50):
				#We know that they have stood up!
				end_time = time.time()
				break
		#ser.write(struct.pack('>B',SER_STOP))
		if (master_found):
			break
		speak(engine,"Sit!")
		print("Lost Master! :(")
		tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

	sit_stand = end_time-start_time
	speak(engine,"It took you "+str(int(sit_stand))+" seconds to stand up!")

	# stop the timer and display FPS information
	fps.stop()
