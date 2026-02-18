from time import time, sleep

class Scheduler:
    def __init__(self, task:callable):
        self._task = task
        self._processing_rate = 1.0
        self._next_trigger_time_s = 0
        self._processing_count = 0

    def set_processing_rate(self, rate: float):
        self._processing_rate = rate
        
    def run(self, time_s:int) -> float:
        if self._processing_rate > 0 and time_s >= self._next_trigger_time_s:
            start_time_s = time()
            self._task()
            elapsed_time_s = time() - start_time_s
            self._processing_count += 1
            self._next_trigger_time_s = time() + max(0, elapsed_time_s * (1 - self._processing_rate))
            return elapsed_time_s
        return 0.0
    
    def reset_processing_count(self):
        self._processing_count = 0
    
    def get_processing_count(self):
        return self._processing_count