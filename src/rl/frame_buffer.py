import cv2
import numpy as np
from typing import Optional
from threading import Lock

class AsyncFrameBuffer:
    def __init__(self, acquisition_speed_fps:int, max_buffer_size:int=0, fake_camera:bool = False):
        self.last_acquisition_s: int = 0
        self.acquisition_speed_fps = acquisition_speed_fps
        self.max_buffer_size = max_buffer_size
        self.image_buffer: list[cv2.Mat] = []
        self.fake_camera = fake_camera
        if not fake_camera:
            self.vc = cv2.VideoCapture(0)
        self.lock = Lock()

    def acquire_and_bufferize(self, time_s:int) -> int:
        if time_s - self.last_acquisition_s > (1/self.acquisition_speed_fps):
            if self.fake_camera:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                ret = True
            else:
                ret, frame = self.vc.read()
            if ret:
                if len(self.image_buffer) < self.max_buffer_size:
                    self.last_acquisition_s = time_s
                    with self.lock:
                        self.image_buffer.append(frame)
                    return 1
                else:
                    return -1
        return 0

    def get_image(self, amount:int=1) -> list[cv2.Mat]:
        images = []
        for _ in range(amount):
            if len(self.image_buffer)>0:
                with self.lock:
                    images.append(self.image_buffer.pop(0))
        return images
        
    def clean(self) -> None:
        with self.lock:
            self.image_buffer.clear()

    def close(self) -> None:
        if not self.fake_camera:
            self.vc.release()

    def __len__(self) -> int:
        with self.lock:
            return len(self.image_buffer)

    def __del__(self):
        self.close()