#define pi

import cv2
import imutils
import json
import time
import datetime

from picamera.array import PiRGBArray
from picamera import PiCamera
import RPi.GPIO as GPIO

# load configuration file
conf = json.load(open("conf.json"))

cv2.namedWindow("Output", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, 1)


camera = PiCamera()
camera.resolution=(320,240)
camera.framerate=32
rawCapture = PiRGBArray(camera, size=(320,240))

time.sleep(0.1)

# buttons
btn1 = 17
btn2 = 22
btn3 = 23
btn4 = 27
btnShutter = 21
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(btn1, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(btn2, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(btn3, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(btn4, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(btnShutter, GPIO.IN, GPIO.PUD_UP)

avg = None

previousPictureTime = 0
previousCheckTime = 0
pictureFrequency = 1
previousMotionFactor = 0.0
startPicture = ""
imageIndex = 0
numOfPhotos = 0

# modes:
# 0 - Standby
# 1 - Recording
# 2 - Stopped
mode = 0

# map
def mapFactor(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# start rec
def startRecording():
    global mode
    global previousPictureTime
    global previousCheckTime
    global pictureFrequency
    global previousMotionFactor
    global startPicture
    global imageIndex
    global numOfPhotos
    imageIndex = 0
    numOfPhotos = 0
    previousPictureTime = 0
    previousCheckTime = 0
    pictureFrequency = 1
    previousMotionFactor = 0.0
    timestamp = datetime.datetime.now()
    startPicture = timestamp.strftime('%Y-%m-%d-%H-%M-%S')
    print("[INFO] Start picture: " + startPicture)
    mode = 1
    print("[INFO] Started recording")
    return

def stopRecording():
    global numOfPhotos
    numOfPhotos = imageIndex
    print("Finished with a total of %d photos" % numOfPhotos)

def showTimelapse():
    global mode
    global imageIndex
    mode = 2
    imageIndex = 0

# main cv loop
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    if mode is 0:
        # standby.
        if GPIO.input(btnShutter) == False:
            # start recording. 
            startRecording()
        cv2.imshow("Output", frame)
        
    if mode is 1:
        # grab frame, resize and convert to gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)

        # capture first frame of background model
        if avg is None:
            print "[INFO] First frame of background model."
            avg = gray.copy().astype("float")
    
        # accumulate new frame
        cv2.accumulateWeighted(gray, avg, conf["delta_threshold"])
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
        motionFactor = 1 - ((cv2.countNonZero(frameDelta) + 0.0) / (frameDelta.shape[0] * frameDelta.shape[1]))
        #print("[CALC] Motion factor: %f") % motionFactor
        # keep motion factor within limits
        if motionFactor < conf["min_motion_factor"]:
            motionFactor = conf["min_motion_factor"]
        if motionFactor > conf["max_motion_factor"]:
            motionFactor = conf["max_motion_factor"]

        # change picture frequency
        pictureFrequency = mapFactor(motionFactor, conf["min_motion_factor"], conf["max_motion_factor"], conf["min_timelapse_frequency"], conf["max_timelapse_frequency"])

        #print("[CALC] Picture frequency: %f") % pictureFrequency

        currentTime = time.time()
        if currentTime - previousPictureTime > pictureFrequency:
            fileName = "-%d.jpg" % imageIndex
            cv2.imwrite(startPicture + fileName, frame)
            imageIndex = imageIndex + 1
            previousPictureTime = currentTime
            print("[INFO] Picture saved.")

        # show delta
        cv2.imshow("Output", frameDelta)
        rval, frame = capture.read()
        
        if GPIO.input(btnShutter) == False:
            # start recording. 
            stopRecording()
            showTimeLapse()
            time.sleep(0.5)

    if mode is 2:
        currentTime = time.time()
        # show previous timelapse
        if currentTime - previousPictureTime >= conf["timelapse_preview_speed"]:
            if imageIndex > numOfPhotos - 1:
                imageIndex = 0
            currentFileName = startPicture + "-%d.jpg" % imageIndex
            currentFrame = cv2.imread(currentFileName, cv2.IMREAD_COLOR)
            cv2.imshow("Output", currentFrame)
            print("[INFO] Showing picture %d" % imageIndex)
            imageIndex = imageIndex + 1
            previousPictureTime = currentTime

        if GPIO.input(btnShutter) == False:
            # back to standby
            mode = 0
            time.sleep(0.5)

    # keys
    key = cv2.waitKey(10)
    if key == ord("0"):
        mode = 0
    if key == ord("1"):
        startRecording()
    if key == ord("2"):
        stopRecording()
        showTimelapse()
    if key == 27:
        break

cv2.destroyWindow("preview")
