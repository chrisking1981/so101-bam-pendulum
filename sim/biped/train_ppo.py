"""Train a walking policy for the simple biped with PPO (stable-baselines3), on CPU (works on an M1 MacBook).

    uv run python sim/biped/train_ppo.py --steps 3000000 --envs 6 --out sim/biped/runs/ppo1
"""
import argparse, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from biped_env import BipedEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback

p = argparse.ArgumentParser()
p.add_argument("--steps", type=int, default=3_000_000)
p.add_argument("--envs", type=int, default=6)
p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs", "ppo1"))
p.add_argument("--seed", type=int, default=0)
a = p.parse_args()
os.makedirs(a.out, exist_ok=True)


class Progress(BaseCallback):
    def __init__(self, every=100_000):
        super().__init__(); self.every, self.next, self.t0 = every, every, time.time()

    def _on_step(self):
        if self.num_timesteps >= self.next:
            eps = [e for e in self.model.ep_info_buffer]
            r = np.mean([e["r"] for e in eps]) if eps else float("nan")
            l = np.mean([e["l"] for e in eps]) if eps else float("nan")
            print(f"{self.num_timesteps:>9d} steps  {time.time() - self.t0:6.0f}s  ep_reward {r:7.1f}  ep_len {l:5.0f}/500", flush=True)
            self.model.save(os.path.join(a.out, "model"))
            self.training_env.save(os.path.join(a.out, "vecnorm.pkl"))
            self.next += self.every
        return True


if __name__ == "__main__":
    env = SubprocVecEnv([lambda i=i: BipedEnv(randomize=True) for i in range(a.envs)])
    env = VecNormalize(VecMonitor(env), norm_obs=True, norm_reward=True, clip_obs=10.0)
    model = PPO("MlpPolicy", env, n_steps=1024, batch_size=2048, n_epochs=8, learning_rate=3e-4, gamma=0.99,
                gae_lambda=0.95, clip_range=0.2, ent_coef=0.002, policy_kwargs=dict(net_arch=[128, 128]),
                seed=a.seed, device="cpu", verbose=0)
    model.learn(total_timesteps=a.steps, callback=Progress())
    model.save(os.path.join(a.out, "model")); env.save(os.path.join(a.out, "vecnorm.pkl"))
    print("done", flush=True)
