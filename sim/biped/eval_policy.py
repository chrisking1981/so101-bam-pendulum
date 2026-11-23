"""Evaluate a trained PPO policy for the simple biped and render a video.

    MUJOCO_GL=cgl uv run python sim/biped/eval_policy.py --run sim/biped/runs/ppo1 --video sim/biped/biped_rl_walk.mp4
Reports distance, drift and falls on the nominal model and on 20 randomized episodes (unseen seeds).
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from biped_env import BipedEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--video")
p.add_argument("--episodes", type=int, default=20)
a = p.parse_args()

model = PPO.load(os.path.join(a.run, "model"), device="cpu")


def make_norm(env):
    v = VecNormalize.load(os.path.join(a.run, "vecnorm.pkl"), DummyVecEnv([lambda: env]))
    v.training = False; v.norm_reward = False
    return v


def episode(randomize, seed, frames=None):
    env = BipedEnv(randomize=randomize)
    norm = make_norm(env)
    obs, _ = env.reset(seed=seed)
    x0, y0 = env.d.qpos[0], env.d.qpos[1]
    fell = False
    for k in range(env.max_steps):
        act, _ = model.predict(norm.normalize_obs(obs[None]), deterministic=True)
        obs, r, term, trunc, _ = env.step(act[0])
        if frames is not None and k % 2 == 0:
            frames.append(env.render())          # 25 fps
        if term:
            fell = True; break
    return env.d.qpos[0] - x0, env.d.qpos[1] - y0, fell, (k + 1) * 0.02


dx, dy, fell, T = episode(False, 0)
print(f"nominal model : {dx*100:+.1f} cm forward, {dy*100:+.1f} cm sideways in {T:.1f} s, fell={fell}")
res = [episode(True, 1000 + i) for i in range(a.episodes)]
d = np.array([r[0] for r in res]); s = np.array([r[1] for r in res]); f = sum(r[2] for r in res)
print(f"randomized x{a.episodes}: forward {d.mean()*100:.1f} cm mean (min {d.min()*100:.1f}, max {d.max()*100:.1f}), "
      f"sideways |{np.abs(s).mean()*100:.1f}| cm mean, falls {f}/{a.episodes}")
if a.video:
    import imageio.v2 as imageio
    frames = []
    dx, dy, fell, T = episode(False, 0, frames)
    imageio.mimsave(a.video, frames, fps=25, quality=8, macro_block_size=1)
    print(f"video {a.video}: {len(frames)} frames")
