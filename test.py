# USAGE
# python recognize_video.py --detector face_detection_model \
#	--embedding-model openface_nn4.small2.v1.t7 \
#	--recognizer output/recognizer.pickle \
#	--le output/le.pickle

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import mes
import tracking_func
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

# Set up serial communication
# for i in range(0,10):
#     try:
#         ser = serial.Serial('/dev/ttyUSB' + str(i),9600)
#     except:
#         continue
#     else:
#         break

# mes.open_service("Twitchy")

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
tracker2 = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

green = (0,255,0)
blue  = (255,0,0)
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
while True:
    master_found = False
    while not master_found:
        # grab the current frame, then handle if we are using a
        # VideoStream or VideoCapture object
        frame = vs.read()

        # resize the frame (so we can process it faster) and grab the
        # frame dimensions
        frame = imutils.resize(frame, width=600)
        [initBB, frame,master_found] = tracking_func.facial_rec("alex",vs,detector,args,embedder,recognizer,fps,le,frame)
        # show the output frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
    # loop over frames from the video stream
    tracker.init(frame, initBB)
    tracker2.init(frame,initBB)

    fps = FPS().start()
    print("Found Master! :)")
    master_found = True
    coords_last = 0
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
            [initBB2, frame2, master_found2] = tracking_func.facial_rec("alex",vs,detector,args,embedder,recognizer,fps,le,frame)
            tracker2.init(frame,initBB2)
        [master_found2, coords2,frame] = tracking_func.facial_fol(tracker2,initBB2,vs,fps,args,frame,blue)
        # show the output frame
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        i = (i + 1) % 50
        print(initBB2[2])
        #
        #
        # if coords[0] > x_center+error_dist:
        #     #Turn right 3
        #     # ser.write(struct.pack('>B',SER_RIGHT))
        #     print("Move Left")
        # elif coords[0] < x_center-error_dist:
        #     #Turn Left 2
        #     # ser.write(struct.pack('>B',SER_LEFT))
        #     print("Move Right")
        if initBB2[2] > 100:
            # Move servo down
            print("Don't get closer")
            # ser.write(struct.pack('>B',SER_FWD))
        elif initBB2[2] < 100:
            # Move servo up
            print("Get closer")
            # ser.write(struct.pack('>B',SER_STOP))
        # else:
        #     print("Y Good!")
            # ser.write(struct.pack('>B',SER_STOP))
        # if coords[1] - coords_last < -100:
        #     mes.send_alert()
        coords_last = coords[1]
    # ser.write(struct.pack('>B',SER_STOP))
    print("Lost Master! :(")
    tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
