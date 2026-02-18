import time
import argparse

from rl.env import Environment
from rl.solar import Solar
from utils import linear_schedule, HParamCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize
from stable_baselines3 import PPO,SAC
from stable_baselines3.common.logger import configure

def main():
    panel_area_m2 = 0.5*0.55*0.51 #m2
    efficiency = 0.13
    max_power_w = 20 #W

    solar = Solar("solcast2025_full.csv", max_power_w=max_power_w, scale_factor=panel_area_m2*efficiency)

    parser = argparse.ArgumentParser()
    parser.add_argument("--buffer_size", default=100000, type=int, help="buffer size")
    parser.add_argument("--train_freq", default=1, type=int)
    parser.add_argument("--batch_size", default=8, type=int)
    parser.add_argument("--lr", default=3e-4, type=float, help="Learning rate")
    parser.add_argument("--lr_decay", default=None, choices=["lin"])
    parser.add_argument("--learning_starts", default=0, type=int)
    parser.add_argument("--speed_factor", default=1, type=int)
    parser.add_argument("--target_update_interval", default=1, type=int)
    parser.add_argument("--training_steps", default=15000, type=int)
    parser.add_argument("--step_size", default=5, type=int)
    parser.add_argument("--tau", default=0.005, type=float, help="Coefficient to update the network at every step")
    parser.add_argument("--model_path", default=None, type=str, help="Path to a pretrained model")
    args = parser.parse_args()

    for k in args.__dict__.keys():
        print(f"{k}: {args.__dict__[k]}")

    env = Environment(acquisition_speed_fps=25,
                step_size_s=args.step_size,
                solar=solar,
                fake_camera=True,
                speed_factor=args.speed_factor)
    #env = VecNormalize(env)

    if args.lr_decay == "lin":
        lr = linear_schedule(args.lr, end_value=args.lr/100)
    else:
        lr = args.lr

    model = SAC("MlpPolicy", env, verbose=1,
                buffer_size=args.buffer_size,
                train_freq=args.train_freq,
                batch_size=args.batch_size,
                learning_rate=lr,
                learning_starts=args.learning_starts,
                target_update_interval=args.target_update_interval,
                tau=args.tau,
                tensorboard_log="./tb_logs",
                device="cuda")
    try:
        if args.model_path is not None:
            model = SAC.load(args.model_path, env=env)
        else:
            model.learn(total_timesteps=args.training_steps, progress_bar=True, callback=HParamCallback(args.__dict__))
            model.save("best.pth")
        obs, _ = env.reset(options={"noreset":True})
        while True:
            action, _ = model.predict(obs, deterministic=True)
            test_obs, reward, done, terminated, info = env.step(action)
            if done:
                break
        print("Duration", env.get_human_uptime())

    finally:
        env.close()

if __name__ == "__main__":
    main()
    exit()