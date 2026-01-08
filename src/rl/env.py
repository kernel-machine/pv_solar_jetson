import gymnasium
import numpy as np
import random

from ultralytics import YOLO
from rl.solar import Solar
from math import floor
from time import sleep, time
from rl.frame_buffer import AsyncFrameBuffer
from tegrastats import Tegrastats

class Environment(gymnasium.Env):
    def __init__(self,
                 solar: Solar,
                 acquisition_speed_fps:int,
                 step_size_s:int,
                 fake_camera:bool=False
                 ):
        super().__init__()
        self.time_s = 10*60*60
        self.battery_energy_j = 0
        self.max_battery_energy_j = 50000
        self.acquisition_speed_fps = acquisition_speed_fps
        self.step_size_s = step_size_s
        self.solar = solar

        self.render_mode = "ansi"
        self.action_space = gymnasium.spaces.Box(low=0, high=1, shape=(1,), dtype=float)
        self.observation_space = gymnasium.spaces.Box(low=0, high=1, shape=(3,), dtype=float)

        self.model = YOLO("yolo11m")
        self.frame_buffer = AsyncFrameBuffer(acquisition_speed_fps, max_buffer_size=1000, fake_camera=fake_camera)
        self.ts = Tegrastats(50)
        self.reset()
        sleep(0.5) #Wait for tegrastats to start to collect some data


    def step(self, action): #For each batch
        done = False
        solar_power_w = self.solar.get_solar_w(self.time_s)
        solar_energy_j = max(0,solar_power_w*self.step_size_s)
        self.battery_energy_j += solar_energy_j

        terminated = solar_energy_j <= 0

        # Action is not the amount of processed images, but the time of processing in the step
        action = action[0]
        action = max(0,min(action, 1))

        start_time = time()
        end_step_time_s = start_time + self.step_size_s

        processing_time_t = start_time + self.step_size_s*action #How much time should process

        processed_images = 0
        unprocessed_images = 0

        while time() < end_step_time_s: #Untill the end of the step
            self.ts.start_measurement()
            start_image_time = time() 

            # The image is acquired respecting the FPS
            # The image is acquired and stored in the buffer
            if self.frame_buffer.acquire_and_bufferize(start_image_time) < 0:
                # Frame skipped for full memory
                unprocessed_images += 1

            if time() < processing_time_t : #In processing time
                image = self.frame_buffer.get_image()
                if image is not None:
                    self.model.predict(image, verbose=False)
                    processed_images += 1

            step_consumed_energy_j = self.ts.end_measurement_j()
            self.battery_energy_j -= step_consumed_energy_j

            if self.battery_energy_j <= 0:
                reward = -len(self.frame_buffer)
                done = True
                break
        
        if self.battery_energy_j > 0:
            reward = processed_images - unprocessed_images

        info = {
            "Battery":self.battery_energy_j,
            "Buffer":len(self.frame_buffer),
            "Solar":solar_energy_j,
        }
        obs = self._get_obs()
        self.time_s += self.step_size_s
        return obs, reward, done, terminated, info
    
    def _get_obs(self):
        obs = [
            self.battery_energy_j/self.max_battery_energy_j,
            len(self.frame_buffer)/self.frame_buffer.max_buffer_size,
            self.solar.get_solar_w(self.time_s)/self.solar.max_power_w
        ]
        obs = np.asarray(obs, dtype=np.float32)
        return obs
    
    def reset(self, *, seed = None, options = None):
        self.battery_energy_j = 0
        self.frame_buffer.clean()
        self.time_s = 7*60*60+24*60*60*random.randint(0,30)
        obs = self._get_obs()
        info = {}
        return obs, info

    def close(self) -> None:
        self.frame_buffer.close()

    def render(self):
        print("Battery",self.battery_energy_j/self.max_battery_energy_j)
        return super().render()
