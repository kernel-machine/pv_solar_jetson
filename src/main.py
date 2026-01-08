from rl.env import Environment
from rl.solar import Solar
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3 import PPO

def main():
    panel_area_m2 = 1*0.55*0.51 #m2
    efficiency = 0.1426
    max_power_w = 40 #W

    solar = Solar("solcast2025_full.csv", max_power_w=max_power_w, scale_factor=panel_area_m2*efficiency)

    def make_env_factory(env_id: int):
        def env_create():
            return Environment(acquisition_speed_fps=10,
                step_size_s=5, 
                solar=solar,
                fake_camera=True)
        return env_create
    env_fns = [make_env_factory(i) for i in range(4)]
    vec_env = SubprocVecEnv(env_fns)

    model = PPO("MlpPolicy", vec_env, verbose=1)
    model.learn(total_timesteps=25000, progress_bar=True)

if __name__ == "__main__":
    main()