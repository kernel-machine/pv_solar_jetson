from tegrastats import Tegrastats
from ultralytics import YOLO
from rl.frame_buffer import AsyncFrameBuffer
from time import sleep, time
import torch
import numpy as np
from rl.scheduler import Scheduler
from threading import Thread

def main():
    ts = Tegrastats(50, get_instant=True)
    yolo = YOLO("yolo11m").to("cuda")
    fb = AsyncFrameBuffer(25, max_buffer_size=1000, fake_camera=False)

    def thread():
        while True:
            fb.acquire_and_bufferize(time())
            sleep(0.01)
    Thread(target=thread, daemon=True).start()

    print("\nFilling completed, images in the buffer:", len(fb))
    processed_images = 0
    def callback():
        nonlocal processed_images
        images = fb.get_image(amount=4)
        if len(images)>0:
            images = np.array(images).transpose(0,3,1,2)/255
            images = torch.from_numpy(images).float().to("cuda")
            yolo.predict(images, verbose=False)
            processed_images += len(images)

    tui_bar_size = 40
    s = Scheduler(lambda: callback())
    for i in range(1,11):
        processed_images = 0
        s.set_processing_rate(i/10)
        ts.start_measurement()
        start_time = time()
        while time() - start_time < 5: #Process images for 5 seconds
            s.run(time())
            bar_progress = len(fb)*tui_bar_size//fb.max_buffer_size
            print(f"Buff: [{'='*bar_progress}{' '*(tui_bar_size-bar_progress)}] {len(fb)}/{fb.max_buffer_size}",end="\r")
            sleep(0.01)
        print(f"\nProcessing rate: {i/10}, images in the buffer: {len(fb)}, processed images: {processed_images}, energy: {ts.end_measurement_j()} J")
        



    fb.close()
    ts.stop()

if __name__ == "__main__":
    main()