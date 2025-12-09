import cv2
from ultralytics import YOLO
import time
vc = cv2.VideoCapture(0)
m=YOLO("yolo11m")
while True:
    ret, frame = vc.read()
    out = m(frame)
    print(out)
    time.sleep(1)
vc.release()