#Multiscale (single angle) face detection for front and side faces, using Haar face detection which is CRAP please use a different algorithm


import numpy as np
import cv2
import os

cwd = os.getcwd()
face_cascade = cv2.CascadeClassifier('C:/Users/chris/PycharmProjects/webcamTest/venv/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
face_side_cascade = cv2.CascadeClassifier('C:/Users/chris/PycharmProjects/webcamTest/venv/Lib/site-packages/cv2/data/haarcascade_profileface.xml')
lowerbod_cascade = cv2.CascadeClassifier('C:/Users/chris/PycharmProjects/webcamTest/venv/Lib/site-packages/cv2/data/haarcascade_lowerbody.xml')
eye_cascade = cv2.CascadeClassifier('C:/Users/chris/PycharmProjects/webcamTest/venv/Lib/site-packages/cv2/data/haarcascade_eye.xml')

cap = cv2.VideoCapture(0)



faceROI = cap.read()



while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


    img = frame

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    sidefaces = face_side_cascade.detectMultiScale(gray,1.3,5)


    for (x, y, w, h) in faces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        #roi_gray = gray[y:y + h, x:x + w]
        #roi_color = img[y:y + h, x:x + w]

    for (x, y, w, h) in sidefaces:
        img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)


      #  eyes = eye_cascade.detectMultiScale(roi_gray)
      #  for (ex, ey, ew, eh) in eyes:
      #      cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

 #   lowerbods = lowerbod_cascade.detectMultiScale(gray,1.3,5)
 #   for (x,y,w,h) in lowerbods:
 #       img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)


    # Display the resulting frame
    cv2.imshow('frame',img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
