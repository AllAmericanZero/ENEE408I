from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
#import serial
import pickle
import struct
import time
import math
import cv2
import os

def facial_rec (master_name, vs, detector,args,embedder,recognizer,fps,le):
    master_found = False
    green = (0, 255, 0)
    red   = (0, 0, 255)

    # loop over frames from the video file stream
    while not master_found:
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

        # update the FPS counter
        fps.update()

        # show the output frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

    return [(startX,startY,endX-startX,endY-startY), frame]

def facial_fol (tracker, initBB,vs,fps,args):

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
		cv2.rectangle(frame, (x, y), (x + w, y + h),
			(0, 255, 0), 2)
	else:
		(x, y, w, h) = (0, 0, 0, 0)
	# update the FPS counter
	fps.update()
	fps.stop()

	# initialize the set of information we'll be displaying on
	# the frame
	info = [
		("Tracker", args["tracker"]),
		("Success", "Yes" if success else "No"),
		("FPS", "{:.2f}".format(fps.fps())),
	]

	# loop over the info tuples and draw them on our frame
	for (i, (k, v)) in enumerate(info):
		text = "{}: {}".format(k, v)
		cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
			cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	return [success, ((x + x + w)/2,(y + y + h)/2)]

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




