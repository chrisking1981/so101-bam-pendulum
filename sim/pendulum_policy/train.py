"""Train the pendulum policy with PPO on CPU and export it to ONNX (normaliser baked in).

    uv run --project ~/projects/bam python sim/pendulum_policy/train.py --steps 400000
"""
import argparse, os, sys, time
import numpy as np
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pend_env import PendEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback

HERE = os.path.dirname(os.path.abspath(__file__))


class Progress(BaseCallback):
    def __init__(self, every=50_000):
        super().__init__(); self.every, self.next, self.t0 = every, every, time.time()

    def _on_step(self):
        if self.num_timesteps >= self.next:
            eps = list(self.model.ep_info_buffer)
            r = np.mean([e["r"] for e in eps]) if eps else float("nan")
            print(f"{self.num_timesteps:>8d} steps {time.time()-self.t0:5.0f}s  ep_reward {r:7.2f}", flush=True)
            self.next += self.every
        return True


class OnnxPolicy(torch.nn.Module):
    """obs -> deterministic action in [-1, 1], with the VecNormalize statistics inside."""
    def __init__(self, policy, mean, var, clip):
        super().__init__()
        self.policy = policy
        self.register_buffer("mean", torch.tensor(mean, dtype=torch.float32))
        self.register_buffer("std", torch.tensor(np.sqrt(var + 1e-8), dtype=torch.float32))
        self.clip = clip

    def forward(self, obs):
        o = torch.clamp((obs - self.mean) / self.std, -self.clip, self.clip)
        feat = self.policy.mlp_extractor.forward_actor(self.policy.extract_features(o, self.policy.pi_features_extractor))
        return torch.clamp(self.policy.action_net(feat), -1.0, 1.0)


def export(model, vecnorm, path):
    net = OnnxPolicy(model.policy, vecnorm.obs_rms.mean, vecnorm.obs_rms.var, vecnorm.clip_obs).eval()
    torch.onnx.export(net, torch.zeros(1, 7), path, input_names=["obs"], output_names=["action"], dynamo=False)
    print("onnx ->", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=400_000)
    ap.add_argument("--envs", type=int, default=6)
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "p1"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    env = VecNormalize(VecMonitor(SubprocVecEnv([lambda: PendEnv(randomize=True) for _ in range(a.envs)])), norm_obs=True, norm_reward=True, clip_obs=10.0)
    model = PPO("MlpPolicy", env, n_steps=512, batch_size=1024, n_epochs=8, learning_rate=3e-4, gamma=0.98, ent_coef=0.0,
                policy_kwargs=dict(net_arch=[64, 64], log_std_init=-1.0), device="cpu", seed=0, verbose=0)
    model.learn(total_timesteps=a.steps, callback=Progress())
    model.save(os.path.join(a.out, "model")); env.save(os.path.join(a.out, "vecnorm.pkl"))
    export(model, env, os.path.join(a.out, "policy.onnx"))
