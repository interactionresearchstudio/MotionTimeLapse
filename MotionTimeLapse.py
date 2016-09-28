import cv2
import imutils
import json
import time

# load configuration file
conf = json.load(open("conf.json"))

# new window and start capture
cv2.namedWindow("preview")
capture = cv2.VideoCapture(0)

# open capture
if capture.isOpened():
    rval, frame = capture.read()
else:
    rval = False

avg = None
previousPictureTime = 0
previousCheckTime = 0
pictureFrequency = 1
previousMotionFactor = 0.0

# map
def mapFactor(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# main cv loop
while rval:
    # grab frame, resize and convert to gray
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21,21), 0)

    # capture first frame of background model
    if avg is None:
        print "[INFO] First frame of background model."
        avg = gray.copy().astype("float")
    
    # accumulate new frame
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    motionFactor = 1 - ((cv2.countNonZero(frameDelta) + 0.0) / (frameDelta.shape[0] * frameDelta.shape[1]))

    # keep motion factor within limits
    if motionFactor < conf["min_motion_factor"]:
        motionFactor = conf["min_motion_factor"]
    if motionFactor > conf["max_motion_factor"]:
        motionFactor = conf["max_motion_factor"]

    currentTime = time.time()
    if currentTime - previousCheckTime >= conf["check_frequency"]:
        # change picture frequency
        pictureFrequency = mapFactor(motionFactor, conf["min_motion_factor"], conf["max_motion_factor"], conf["min_timelapse_frequency"], conf["max_timelapse_frequency"])

        print("[CALC] Picture frequency: %f") % pictureFrequency

    if currentTime - previousPictureTime > pictureFrequency:
        print("[INFO] Time to take a picture!")
        previousPictureTime = currentTime

    # show image
    cv2.imshow("preview", frameDelta)
    rval, frame = capture.read()

    # exit keys
    key = cv2.waitKey(10)
    if key == 27:
        break

cv2.destroyWindow("preview")
