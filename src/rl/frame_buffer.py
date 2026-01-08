import cv2
import numpy as np
from typing import Optional

class AsyncFrameBuffer:
    def __init__(self, acquisition_speed_fps:int, max_buffer_size:int=0, fake_camera:bool = False):
        self.last_acquisition_s: int = 0
        self.acquisition_speed_fps = acquisition_speed_fps
        self.max_buffer_size = max_buffer_size
        self.image_buffer: list[cv2.Mat] = []
        self.fake_camera = fake_camera
        if not fake_camera:
            self.vc = cv2.VideoCapture(0)

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
                    self.image_buffer.append(frame)
                    return 1
                else:
                    return -1
        return 0

    def get_image(self) -> Optional[cv2.Mat]:
        if len(self.image_buffer)>0:
            return self.image_buffer.pop(0)
        else:
            return None
        
    def clean(self) -> None:
        self.image_buffer.clear()

    def close(self) -> None:
        self.vc.release()

    def __len__(self) -> int:
        return len(self.image_buffer)