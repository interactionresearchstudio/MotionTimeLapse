#define mac

import cv2
import imutils
import json
import time
import datetime


# load configuration file
conf = json.load(open("conf.json"))

# new window and start capture
cv2.namedWindow("preview")

capture = cv2.VideoCapture(0)
capture.set(3, 320)
capture.set(4, 240)
if capture.isOpened():
    rval, frame = capture.read()
else:
    rval = False


time.sleep(0.1)

# buttons

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
while rval:
    if mode is 0:
        # standby.
        rval, frame = capture.read()
        cv2.imshow("preview", frame)
        
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
        cv2.imshow("preview", frameDelta)
        rval, frame = capture.read()

    if mode is 2:
        currentTime = time.time()
        # show previous timelapse
        if currentTime - previousPictureTime >= conf["timelapse_preview_speed"]:
            if imageIndex > numOfPhotos - 1:
                imageIndex = 0
            currentFileName = startPicture + "-%d.jpg" % imageIndex
            currentFrame = cv2.imread(currentFileName, cv2.IMREAD_COLOR)
            cv2.imshow("preview", currentFrame)
            print("[INFO] Showing picture %d" % imageIndex)
            imageIndex = imageIndex + 1
            previousPictureTime = currentTime

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
