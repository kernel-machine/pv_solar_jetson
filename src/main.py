import cv2
from ultralytics import YOLO
from vidgear.gears import WriteGear
from tegrastats import Tegrastats

vc = cv2.VideoCapture(0)
input_fps = 15
model = YOLO("yolo11m")
ts = Tegrastats(100)

output_params = {
    "-f": "rtsp",
    "-rtsp_transport": "tcp",
    "-input_framerate": input_fps,
    "-r": input_fps,
    "-bf": "0",
}
writer = WriteGear(
    output="rtsp://192.168.0.131:8554/mystream", logging=False, **output_params
)
try:
    index = 0
    while True:
        ret, frame = vc.read()
        if not ret:
            break
        if (index // 10) % 2 == 0:
            results = model.predict(frame, verbose=False)
            frame = results[0].plot()
        consumtpion_w = ts.get_last_consumption()
        frame = cv2.putText(
            frame,
            str(consumtpion_w) + "W",
            (5, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            1,
        )
        writer.write(frame)
        index += 1
finally:
    writer.close()
    vc.release()
    ts.stop()
