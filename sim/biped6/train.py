"""Train a walking policy for one 6-servo biped sketch with PPO on CPU, and export it to ONNX.

    uv run --project ~/projects/bam python sim/biped6/train.py --variant knee --steps 5000000 --envs 4 --out sim/biped6/runs/knee1
"""
import argparse, os, sys, time
import numpy as np
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import Biped6Env
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
import importlib.util
_spec = importlib.util.spec_from_file_location("pend_train", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pendulum_policy", "train.py"))
OnnxPolicy = None  # loaded in main (the pendulum trainer parses its own CLI at import, so only its class is taken)

ap = argparse.ArgumentParser()
ap.add_argument("--variant", required=True, help="roll, knee (sketches), v2, v2_50, v2_100 (CAD, grams on top) or v3_12v, v3_knee, v3_roll (8 servos; where the C044s go)")
ap.add_argument("--steps", type=int, default=5_000_000); ap.add_argument("--envs", type=int, default=4); ap.add_argument("--out", required=True)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)


class Progress(BaseCallback):
    def __init__(self, every=250_000):
        super().__init__(); self.every, self.next, self.t0 = every, every, time.time()

    def _on_step(self):
        if self.num_timesteps >= self.next:
            eps = list(self.model.ep_info_buffer)
            r = np.mean([e["r"] for e in eps]) if eps else float("nan"); l = np.mean([e["l"] for e in eps]) if eps else float("nan")
            print(f"{a.variant} {self.num_timesteps:>8d} steps {time.time()-self.t0:6.0f}s ep_reward {r:7.1f} ep_len {l:5.0f}/500", flush=True)
            self.model.save(os.path.join(a.out, "model")); self.training_env.save(os.path.join(a.out, "vecnorm.pkl"))
            self.next += self.every
        return True


if __name__ == "__main__":
    env = VecNormalize(VecMonitor(SubprocVecEnv([lambda: Biped6Env(a.variant, randomize=True) for _ in range(a.envs)])), norm_obs=True, norm_reward=True, clip_obs=10.0)
    model = PPO("MlpPolicy", env, n_steps=1024, batch_size=2048, n_epochs=8, learning_rate=3e-4, gamma=0.99, gae_lambda=0.95,
                ent_coef=0.002, policy_kwargs=dict(net_arch=[128, 128], log_std_init=-1.0), device="cpu", seed=0, verbose=0)
    model.learn(total_timesteps=a.steps, callback=Progress())
    model.save(os.path.join(a.out, "model")); env.save(os.path.join(a.out, "vecnorm.pkl"))
    import ast, types
    src = open(_spec.origin).read(); tree = ast.parse(src)
    cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OnnxPolicy"][0]
    mod = types.ModuleType("onnxpol"); exec("import numpy as np\nimport torch\n" + ast.unparse(cls), mod.__dict__)
    net = mod.OnnxPolicy(model.policy, env.obs_rms.mean, env.obs_rms.var, env.clip_obs).eval()
    torch.onnx.export(net, torch.zeros(1, env.observation_space.shape[0]), os.path.join(a.out, "policy.onnx"), input_names=["obs"], output_names=["action"], dynamo=False)
    print("done", a.variant, flush=True)
