import gymnasium
import numpy as np
import random
import torch
import matplotlib.pyplot as plt

from ultralytics import YOLO
from rl.solar import Solar
from math import floor
from time import sleep, time, gmtime, strftime
from rl.frame_buffer import AsyncFrameBuffer
from rl.scheduler import Scheduler
from tegrastats import Tegrastats
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from threading import Thread, Lock
from datetime import datetime

YOLO_BATCH_SIZE = 8
TERMINATE_THRESHOLD_M = 30

class Environment(gymnasium.Env):
    def __init__(self,
                 solar: Solar,
                 acquisition_speed_fps:int,
                 step_size_s:int,
                 fake_camera:bool=False,
                 speed_factor:int = 1
                 ):
        super().__init__()
        self.time_s = 7*60*60
        self.boot_time_s = self.time_s
        self.max_battery_energy_j = 1000
        self.battery_energy_j = self.max_battery_energy_j/2
        self.speed_factor = speed_factor
        self.acquisition_speed_fps = acquisition_speed_fps
        self.step_size_s = step_size_s
        self.solar = solar

        self.device = torch.device("cuda")
        self.model = YOLO("yolo11m").to(self.device)
        self.frame_buffer = AsyncFrameBuffer(acquisition_speed_fps, max_buffer_size=1000, fake_camera=fake_camera)
        self.ts = Tegrastats(50, get_instant=True)
        self.start_offset = 0
        self.start_time_s = 0
        self.reset()
        sleep(0.5) #Wait for tegrastats to start to collect some data

        self.render_mode = "ansi"
        self.action_space = gymnasium.spaces.Box(low=0, high=1, shape=(1,), dtype=float)
        self.observation_space = gymnasium.spaces.Box(low=0, high=1, shape=(4,), dtype=float)
        self.scheduler = Scheduler(lambda: self.inference_callback())
        self.proccessing_is_started = False
        self.pair_action_energy:list[tuple[float, float]] = []

        # Threading / concurrency controls
        self._processing_thread = None
        self._processing_thread_running = False
        self._model_lock = Lock()

    def inference_callback(self):
        try:
            images = self.frame_buffer.get_image(amount=YOLO_BATCH_SIZE)
            if len(images) > 0:
                images = np.array(images).transpose(0,3,1,2)/255
                images = torch.from_numpy(images).float().to(self.device)
                with self._model_lock:
                    with torch.no_grad():
                        try:
                            self.model.predict(images, verbose=False)
                        except Exception as e:
                            # Capture any model-side exceptions and continue
                            print("Warning: inference failed:", e)
        except Exception as e:
            print("Warning: inference_callback exception:", e)

    def start_processing(self):
        def processing_thread():
            while self._processing_thread_running:
                try:
                    self.frame_buffer.acquire_and_bufferize(time())
                    self.scheduler.run(time())
                except Exception as e:
                    print("Warning: processing thread exception:", e)
                sleep(0.01)

        # start a non-daemon thread and keep reference so we can stop it cleanly
        self._processing_thread_running = True
        self._processing_thread = Thread(target=processing_thread, daemon=False)
        self._processing_thread.start()

    def step(self, action): #For each batch
        if not self.proccessing_is_started:
            self.start_processing()
            self.proccessing_is_started = True

        now = datetime.now()
        beginning_of_year = datetime(now.year, 1, 1)
        time_s = (now - beginning_of_year).total_seconds()
        solar_power_w = self.solar.get_solar_w(time_s+self.start_offset)
        solar_energy_j = max(0,solar_power_w)*self.step_size_s

        #terminated = solar_energy_j <= 0

        # Action is not the amount of processed images, but the time of processing in the step
        action = action[0]
        action = max(0,min(action, 1))
        self.scheduler.reset_processing_count()
        self.scheduler.set_processing_rate(action)
        self.ts.start_measurement()
        sleep(self.step_size_s / self.speed_factor)

        energy_used_j = self.ts.end_measurement_j() * self.speed_factor
        #self.pair_action_energy.append((action, energy_used_j))
        processed_images = self.scheduler.get_processing_count()*YOLO_BATCH_SIZE*self.speed_factor
        reward = processed_images / (self.acquisition_speed_fps * self.step_size_s)

        # Clamp the battery
        self.battery_energy_j = self.battery_energy_j + solar_energy_j - energy_used_j
        self.battery_energy_j = min(self.battery_energy_j, self.max_battery_energy_j)

        print(f"Action: {action:.2f}, Reward: {reward:.4f}, Battery: {self.battery_energy_j:.2f}J, Solar: {solar_energy_j:.2f}J, Energy Used: {energy_used_j:.2f}J, Processed Images: {processed_images}")

        obs = self.get_obs_array()
        obs.append(energy_used_j/100)
        obs = np.asarray(obs, dtype=np.float32)

        # Gymnasium API: (obs, reward, terminated, truncated, info)
        terminated = self.battery_energy_j <= 0
        truncated = time() - self.start_time_s >= TERMINATE_THRESHOLD_M*60  # time limit

        # Avoid saving the plot every single step to reduce I/O and memory pressure
        # if len(self.pair_action_energy) % 50 == 0:
        #     self.plot_pair_action_energy()

        return obs, reward, terminated, truncated, {}
    
    def get_obs_array(self) -> list:
        now = datetime.now()
        beginning_of_year = datetime(now.year, 1, 1)
        time_s = (now - beginning_of_year).total_seconds()
        solar_power_w = self.solar.get_solar_w(time_s+self.start_offset)
        return [
            self.battery_energy_j/self.max_battery_energy_j,
            (solar_power_w/self.solar.max_power_w) if self.solar.max_power_w else 0.0,
            (len(self.frame_buffer)/self.frame_buffer.max_buffer_size) if self.frame_buffer.max_buffer_size else 0.0,
        ]
    
    def plot_pair_action_energy(self):
        if len(self.pair_action_energy) == 0:
            return
        actions, energies = zip(*self.pair_action_energy)
        plt.figure()
        plt.scatter(actions, energies)
        plt.xlabel("Action (Processing Time)")
        plt.ylabel("Energy Used (Joules)")
        plt.title("Action vs Energy Used")
        plt.grid()
        plt.savefig("action_energy_plot.png")
        plt.close()

    
    def reset(self, *, seed = None, options = None):
        self.frame_buffer.clean()
        self.start_offset = random.randint(0,365)*random.randint(1,23)*60*60
        self.start_time_s = time()
        # if options is not None and \
        #     isinstance(options, dict) and \
        #     "noreset" in options.keys() and \
        #     options["noreset"]:
        #     day = 0
            
        # else:
        #     day = random.randint(0,30)
        self.battery_energy_j = self.max_battery_energy_j/2
        #self.time_s = day*24*60*60
        #self.boot_time_s = self.time_s
        # while self.battery_energy_j/self.max_battery_energy_j <= 0.05:
        #     self.time_s += self.step_size_s
        #     solar_power_w = self.solar.get_solar_w(self.time_s)
        #     solar_energy_j = max(0,solar_power_w*self.step_size_s)
        #     self.battery_energy_j += solar_energy_j
        obs = self.get_obs_array()
        obs.append(0)
        obs = np.asarray(obs, dtype=np.float32)

        info = {}
        return obs, info

    def close(self) -> None:
        # Stop background processing thread cleanly
        try:
            self._processing_thread_running = False
            if self._processing_thread is not None and self._processing_thread.is_alive():
                self._processing_thread.join(timeout=1.0)
        except Exception:
            pass

        self.frame_buffer.close()
        try:
            self.ts.stop()
        except Exception:
            pass



    def render(self):
        print("Battery",self.battery_energy_j/self.max_battery_energy_j)
        print("Buffer",self.frame_buffer)

    def get_uptime_s(self) -> int:
        return self.time_s-self.boot_time_s

    def get_human_uptime(self) -> str:
        days = self.get_uptime_s() // 86400
        output = f"{days} days, "
        output += strftime("%H hours, %M minutes, %S seconds",
                                gmtime(self.get_uptime_s()))
        return output