import argparse
import cv2
import numpy as np
import time

if True:
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontscale = 1
    fontcolor = (0, 255, 255)

    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default=13,
                    help='Specify camera port number or path to video file')
    ap.add_argument('--output', help='will output .avi with specified filename')
    ap.add_argument('--width', default=1280, type=int,
                    help='image width [1280]')
    ap.add_argument('--height', default=720, type=int,
                    help='image height [720]')
    ap.add_argument("-t", "--tracker", type=str, default="kcf",
                    help="OpenCV object tracker type")

    args = vars(ap.parse_args())

    if args["output"]:
        print("writing to file:{}.avi".format(args["output"]))

    camera = cv2.VideoCapture(args["input"])
    fps = camera.get(cv2.CAP_PROP_FPS)
    fps = fps if fps < 60 else 60
    frame_width = int(camera.get(3))
    frame_height = int(camera.get(4))

    if args["output"]:
        fps = camera.get(cv2.CAP_PROP_FPS)
        fps = fps if fps < 60 else 60

    if args["output"]:
        out = cv2.VideoWriter('{}.avi'.format(args["output"]), cv2.VideoWriter_fourcc(*'MJPG'), fps,
                              (frame_width, frame_height))

    # blue
    lowerBound = np.array([100, 50, 50])
    upperBound = np.array([130, 255, 255])


    class Tracker:
        def __init__(self, box, center, ID, area, removeDelay):
            self.box = box
            self.center = center
            self.ID = ID
            self.area = area
            self.removeDelay = removeDelay


    class NewBox:
        def __init__(self, box, center, area, used):
            self.box = box
            self.center = center
            self.area = area
            self.used = used


    ret, img = camera.read()
    height = img.shape[0]
    width = img.shape[1]
    trackerList = []
    ID = 0

    cycle = 0

while True:

    ret, img = camera.read()

    if img is None:
        print('End of Stream')
        break

    imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(imgHSV, lowerBound, upperBound)
    maskOpen = cv2.morphologyEx(mask, cv2.MORPH_OPEN, (5, 5), iterations=3)
    maskClose = cv2.morphologyEx(maskOpen, cv2.MORPH_CLOSE, (20, 20), iterations=1)
    maskFinal = maskClose
    conts, h = cv2.findContours(maskFinal.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    newBoxList = []

    for i in range(len(conts)):  # check each box with current tracker
        x, y, w, h = cv2.boundingRect(conts[i])

        if (1000 < (w * h)) and (
                y > 250):  # filters small/large detections and horizon CONFIDENCE VALUES CAN BE ADDED HERE
            center = ((x + (w / 2)), (y + (h / 2)))
            box = (x, y, w, h)  # add edge to help capture close over laps
            area = w * h
            used = False
            newBoxList.append(NewBox(box, center, area, used))

            # Would like to add box morphing here for new box adding

    # list sorting
    newBoxList.sort(key=lambda newBox: newBox.area, reverse=False)  # Sorts list by area to search (Smallest first)
    trackerList.sort(key=lambda trackerBox: trackerBox.area,
                     reverse=True)  # Sorts list by area to search (Biggest first)

    if len(trackerList) < 1:  # runs the first time to populate the tracker list
        for newBox in newBoxList:
            ID = ID + 1
            trackerList.append(Tracker(newBox.box, newBox.center, ID, newBox.box[2] * newBox.box[3], 0))

    else:  # check new boxes vs "tracked Boxes"
        removeTrackerList = []
        for tracker in trackerList:

            # Adds delay for removing tracker if it is not updated so many times
            tracker.removeDelay += 1
            if tracker.removeDelay > 30:
                removeTrackerList.append(tracker)
                continue

            updateTracker = []
            for newBox in newBoxList:  # Checks the current
                if (tracker.box[0] < newBox.center[0] < tracker.box[0] + tracker.box[2]) and \
                        (tracker.box[1] < newBox.center[1] < tracker.box[1] + tracker.box[3]) and (
                        not newBox.used):  # checks to see if newBox is inside tracker box and not used already
                    newBox.used = True
                    updateTracker.append(newBox)

            if len(updateTracker) > 0:  # Takes all boxes with centroid inside current tracker box and forms one large box and updates the tracker
                updateX = (max(updateX.box[0] for updateX in updateTracker))
                updateY = (max(updateY.box[1] for updateY in updateTracker))
                updateW = (max(updateW.box[2] for updateW in updateTracker))
                updateH = (max(updateH.box[3] for updateH in updateTracker))
                tracker.box = (updateX, updateY, updateW, updateH)

                updateCenterX = updateX + updateW / 2
                updateCenterY = updateY + updateH / 2
                tracker.center = (updateCenterX, updateCenterY)

                tracker.removeDelay = 0

        for removeTracker in removeTrackerList:
            trackerList.remove(removeTracker)

        for newBox in newBoxList:  # Adds any non used box from new box list to trackerList
            if not newBox.used:
                ID = ID + 1
                trackerList.append(Tracker(newBox.box, newBox.center, ID, newBox.box[2] * newBox.box[3], 0))

    cv2.putText(img, 'cycle = ' + str(cycle), (25, 25), font, 1, (0, 0, 255))
    cycle += 1

    for tracker in trackerList:
        cv2.rectangle(img, (tracker.box[0], tracker.box[1]),
                      (tracker.box[0] + tracker.box[2], tracker.box[1] + tracker.box[3]), (0, 255, 0), 2)
        cv2.putText(img, str(tracker.ID), (tracker.box[0], (tracker.box[1] + tracker.box[3])), font, fontscale,
                    fontcolor)

    # for newBox in newBoxList:
    #     if newBox.used:
    #         cv2.rectangle(img, (newBox.box[0] - 5, newBox.box[1] - 5),
    #                       (newBox.box[0] + newBox.box[2] + 5, newBox.box[1] + newBox.box[3] + 5), (0, 0, 255), 2)
    #         cv2.circle(img, (newBox.center[0], newBox.center[1]), 5, (0, 0, 255), -1)
    #     else:
    #         cv2.rectangle(img, (newBox.box[0] - 10, newBox.box[1] - 10),
    #                       (newBox.box[0] + newBox.box[2] + 10, newBox.box[1] + newBox.box[3] + 10), (255, 255, 255), 8)
    #         cv2.circle(img, (newBox.center[0], newBox.center[1]), 5, (255, 255, 255), -1)

    cv2.imshow("Frame", img)
    key = cv2.waitKey(1) & 0xFF

    if args["output"]:
        out.write(img)

cv2.destroyAllWindows()
if args["output"]:
    out.release()
camera.release()
