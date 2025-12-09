import cv2
from ultralytics import YOLO
from vidgear.gears import WriteGear
from tegrastats import Tegrastats

vc = cv2.VideoCapture(0)
input_fps = 15
model=YOLO("yolo11m")
ts = Tegrastats(1000//input_fps)

output_params = {
    "-f": "rtsp", 
    "-rtsp_transport": "tcp",
    "-input_framerate": input_fps,  
    "-r": input_fps,
    #"-c:v":"h264_nvenc",
    "-bf":"0",
    "-preset":"ultrafast"
}
writer = WriteGear(
    output="rtsp://192.168.0.131:8554/mystream", logging=True, **output_params
)
try:
    index = 0
    while True:
        ret, frame = vc.read()
        if not ret:
            break
        if (index//100)%2==0:
            results = model.predict(frame,verbose=False)
            frame = results[0].plot()
        writer.write(frame)
        consumtpion_w = ts.last_consumption()
        print("Consumption",consumtpion_w)
        index+=1
finally:
    writer.close()
    vc.release()