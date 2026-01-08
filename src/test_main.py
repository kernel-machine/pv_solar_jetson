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
enable_inference = True
CELL_PHONE_CLASS = 67
next_index_to_reset_inference = 0
try:
    index = 0
    while True:
        ret, frame = vc.read()
        if not ret:
            break
        if enable_inference:
            results = model.predict(frame, verbose=False)
            cell_phone_detected = \
                CELL_PHONE_CLASS in results[0].boxes.cls.tolist()
            if cell_phone_detected:
                enable_inference = False
                next_index_to_reset_inference = index + 100

            frame = results[0].plot()
        consumtpion_w = ts.get_last_consumption_w()
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
        if index > next_index_to_reset_inference:
            enable_inference = True
        index += 1
finally:
    writer.close()
    vc.release()
    ts.stop()
