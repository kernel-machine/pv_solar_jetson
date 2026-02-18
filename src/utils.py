from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import HParam

def linear_schedule(initial_value: float, start_from: float = 0.0, end_value: float = 0.0):
    def func(progress_remaining: float) -> float:
        elapsed_progress = 1.0 - progress_remaining

        if elapsed_progress < start_from:
            return initial_value
        else:
            progress_in_decay_window = elapsed_progress - start_from
            decay_window_duration = 1.0 - start_from
            
            if decay_window_duration == 0:
                fraction_scaling = 1.0 # Avoid 0 division
            else:
                fraction_scaling = progress_in_decay_window / decay_window_duration
            
            valore_scalato = initial_value + fraction_scaling * (end_value - initial_value)
            
            return max(valore_scalato, end_value) 
            
    return func

class HParamCallback(BaseCallback):
    def __init__(self, hparam:dict, verbose = 0):
        self.hparam = hparam
        super().__init__(verbose)

    def _on_training_start(self):
        metric_dict = {
            "rollout/ep_len_mean": 0,
            "train/value_loss": 0.0,
        }
        self.logger.record(
            "hparams",
            HParam(self.hparam, metric_dict),
            exclude=("stdout", "log", "json", "csv"),
        )
    def _on_step(self):
        return True