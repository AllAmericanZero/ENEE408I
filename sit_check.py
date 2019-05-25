# USAGE
# python recognize_video.py --detector face_detection_model \
#	--embedding-model openface_nn4.small2.v1.t7 \
#	--recognizer output/recognizer.pickle \
#	--le output/le.pickle

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
from collections import deque
import tracking_func
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

# Set up serial communication
for i in range(0,10):
    try:
        ser = serial.Serial('/dev/ttyUSB' + str(i),9600)
    except:
        continue
    else:
        break
x_center = 300
y_center = 250
error_dist = 50
# Commands
SER_STOP  = 0
SER_FWD   = 1
SER_LEFT  = 2
SER_RIGHT = 3
SER_LON   = 6
SER_LOFF  = 7

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--detector", required=True,
	help="path to OpenCV's deep learning face detector")
ap.add_argument("-m", "--embedding-model", required=True,
	help="path to OpenCV's deep learning face embedding model")
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

# initialize the video stream, then allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

# start the FPS throughput estimator
fps = FPS().start()
pts = deque(maxlen=200)
start_time = time.time()

while True:
    [initBB, frame] = tracking_func.facial_rec("alex",vs,detector,args,embedder,recognizer,fps,le)
    # loop over frames from the video stream
    tracker.init(frame, initBB)
    fps = FPS().start()
    print("Found Master! :)")
    master_found = True

    curr_state = 0;
    # Calculate the center of the face as the first point
    coords = (int(((2*initBB[0] + initBB[2])/2)),int((2*initBB[1] + initBB[3])/2))
    start_pos = coords
    while master_found:

        [master_found, coords,H,W,frame] = tracking_func.check_sitting(tracker,initBB,vs,fps,args)
        # loop over the info tuples and draw them on our frame
        coords = (int(coords[0]),int(coords[1]))
        if all(v == 0 for v in coords):
            coords = pts[-1]
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
            change_state = (abs(pts[1][1] - pts[10][1]) < 1)
        except:
            change_state = 0
        else:
            print(pts[1][1])
            if change_state == 1 and (pts[1][1]-start_pos[1]) < -50:
                #We know that they have stood up!
                end_time = time.time()
                break
    #ser.write(struct.pack('>B',SER_STOP))
    if (master_found):
        break
    print("Lost Master! :(")
    tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

sit_stand = end_time-start_time
print("It took you "+str(int(sit_stand))+" seconds to stand up!")
# stop the timer and display FPS information
fps.stop()

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
