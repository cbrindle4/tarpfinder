import argparse
import cv2
import numpy as np
import time

# intrinsic = np.array(
#     [[299.39646639, 0., 419.96165812],
#      [0., 302.5602385, 230.25411049],
#      [0., 0., 1.]])
#
# distortion = np.array(
#     [-0.16792771, 0.03121603, 0.00218195, -0.00026904, -0.00263317]
# )

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

    ret, img = camera.read()

count = 0

while True:

    ret, img = camera.read()

    width = int(camera.get(3))
    height = int(camera.get(4))

    if img is None:
        print('End of Stream')
        break

    # img = cv2.undistort(img, intrinsic, distortion)
    edges = cv2.Canny(
        cv2.resize(img, (width, height), 0, 0, cv2.INTER_NEAREST),
        200, 600, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)

    if lines is not None:
        for rho, theta in lines[0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1500 * (-b))
            y1 = int(y0 + 1500 * (a))
            x2 = int(x0 - 1500 * (-b))
            y2 = int(y0 - 1500 * (a))

        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

    cv2.putText(img, str(count), (25, 25), font, 1, (255, 0, 0))

    count += 1

    cv2.imshow("Frame", img)
    key = cv2.waitKey(1) & 0xFF

    if args["output"]:
        out.write(img)

cv2.destroyAllWindows()
if args["output"]:
    out.release()
camera.release()
