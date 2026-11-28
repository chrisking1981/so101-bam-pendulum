"""Walking video of a trained v3 policy with the real CAD parts drawn (visual only; the physics is the same as in training).

    MUJOCO_GL=cgl uv run --project ~/projects/bam python sim/biped6/walk_video.py --variant v3_pitch --run sim/biped6/runs/v3b_pitch
"""
import argparse, os, sys
import numpy as np, onnxruntime as ort, imageio.v2 as imageio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import Biped6Env
ap = argparse.ArgumentParser(); ap.add_argument("--variant", required=True); ap.add_argument("--run", required=True)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out"); a = ap.parse_args()
s = ort.InferenceSession(os.path.join(a.run, "policy.onnx")); e = Biped6Env(a.variant, randomize=False, render=True); o, _ = e.reset(seed=a.seed)
frames = []
for k in range(e.max_steps):
    o, r, term, tr, info = e.step(s.run(None, {"obs": o[None]})[0][0]); frames.append(e.render())
    if term: break
out = a.out or os.path.join(a.run, f"walk_{a.variant}_cad.mp4")
imageio.mimsave(out, frames, fps=50, quality=8, macro_block_size=1); print(out, f"{info['x']*100:+.0f} cm forward, fell: {term}")
