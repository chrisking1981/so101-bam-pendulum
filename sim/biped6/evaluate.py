"""Compare the trained layouts: distance, falls, drift and power on the nominal model and 20 randomized episodes, plus a video each.

    MUJOCO_GL=cgl uv run --project ~/projects/bam python sim/biped6/evaluate.py --runs roll=sim/biped6/runs/roll1 knee=sim/biped6/runs/knee1
"""
import argparse, os, sys
import numpy as np
import onnxruntime as ort
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import Biped6Env

ap = argparse.ArgumentParser(); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--episodes", type=int, default=20)
ap.add_argument("--md")
a = ap.parse_args()


def episode(sess, variant, randomize, seed, frames=None):
    e = Biped6Env(variant, randomize=randomize); o, _ = e.reset(seed=seed); P = []; fell = False
    for k in range(e.max_steps):
        act = sess.run(None, {"obs": o[None]})[0][0]
        o, r, term, trunc, info = e.step(act); P.append(info["power"])
        if frames is not None and k % 2 == 0: frames.append(e.render())
        if term: fell = True; break
    return info["x"], info["y"], fell, (k + 1) * 0.02, float(np.mean(P))


lines = ["| layout | nominal: forward / sideways / fell | randomized x%d: forward mean (min) | sideways mean | falls | mean power (W) |" % a.episodes,
         "|---|---|---|---:|---:|---:|"]
for spec in a.runs:
    variant, run = spec.split("=")
    sess = ort.InferenceSession(os.path.join(run, "policy.onnx"))
    nx, ny, nf, nT, nP = episode(sess, variant, False, 0)
    R = [episode(sess, variant, True, 1000 + i) for i in range(a.episodes)]
    d = np.array([x[0] for x in R]); s = np.array([abs(x[1]) for x in R]); f = sum(x[2] for x in R); p = np.mean([x[4] for x in R])
    lines.append(f"| {variant} | {nx*100:+.0f} cm / {ny*100:+.0f} cm / {nf} | {d.mean()*100:.0f} cm ({d.min()*100:.0f}) | {s.mean()*100:.0f} cm | {f}/{a.episodes} | {p:.2f} |")
    import imageio.v2 as imageio
    frames = []; episode(sess, variant, False, 0, frames)
    imageio.mimsave(os.path.join(run, f"walk_{variant}.mp4"), frames, fps=25, quality=8, macro_block_size=1)
txt = "\n".join(lines); print(txt)
if a.md: open(a.md, "w").write(txt + "\n")
