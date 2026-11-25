"""Evaluate the four v3 layouts (where the two C044s sit): walking result and how hard each joint type works while walking.

Per layout: distance and falls on the nominal model and N randomized episodes, then per joint type (roll / pitch / knee / ankle,
both legs together) the mean and 95th-percentile |torque| and the 95th-percentile duty cycle (share of full motor voltage the servo
needs). Duty near 1.0 means the servo is at its limit. The C044 joint of each layout is marked.

    MUJOCO_GL=cgl uv run --project ~/projects/bam python sim/biped6/eval_v3.py [--prefix v3b_] [--episodes 20] [--md eval_v3b.md] [--video]
"""
import argparse, os, sys
import numpy as np
import onnxruntime as ort
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import Biped6Env, C044_AT, KIND

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--episodes", type=int, default=20); ap.add_argument("--md"); ap.add_argument("--video", action="store_true")
ap.add_argument("--prefix", default="v3b_", help="run folder prefix: v3_ (first runs) or v3b_ (goal clip + duty penalty)")
a = ap.parse_args()
TYPES = ["roll", "pitch", "knee", "ankle"]


def episode(sess, variant, randomize, seed, frames=None):
    e = Biped6Env(variant, randomize=randomize); o, _ = e.reset(seed=seed); D, T = [], []; fell = False
    for k in range(e.max_steps):
        o, r, term, trunc, info = e.step(sess.run(None, {"obs": o[None]})[0][0])
        D.append(info["duty"]); T.append(np.abs(info["tau"]))
        if frames is not None and k % 2 == 0: frames.append(e.render())
        if term: fell = True; break
    return info["x"], abs(info["y"]), fell, np.array(D), np.array(T), e.joints


walk = ["| layout | C044 at | nominal: forward / fell | randomized: forward mean (min) | sideways | falls |", "|---|---|---|---|---:|---:|"]
load = ["| layout | joint | servo | torque mean | torque p95 | duty p95 | duty max |", "|---|---|---|---:|---:|---:|---:|"]
for variant in ["v3_12v", "v3_knee", "v3_roll", "v3_pitch"]:
    run = os.path.join(HERE, "runs", a.prefix + variant[3:]); sess = ort.InferenceSession(os.path.join(run, "policy.onnx"))
    nx, _, nf, *_ = episode(sess, variant, False, 0)
    R = [episode(sess, variant, True, 1000 + i) for i in range(a.episodes)]
    d = np.array([x[0] for x in R]); s = np.array([x[1] for x in R]); f = sum(x[2] for x in R)
    walk.append(f"| {variant} | {', '.join(C044_AT[variant]) or '-'} | {nx*100:+.0f} cm / {'yes' if nf else 'no'} | {d.mean()*100:.0f} cm ({d.min()*100:.0f}) | {s.mean()*100:.0f} cm | {f}/{a.episodes} |")
    joints = R[0][5]; D = np.concatenate([x[3] for x in R]); T = np.concatenate([x[4] for x in R])
    for t in TYPES:
        idx = [i for i, j in enumerate(joints) if KIND(j) == t]
        c = t in C044_AT[variant]
        dd, tt = D[:, idx].ravel(), T[:, idx].ravel()
        name = f"**{t}**" if c else t
        load.append(f"| {variant} | {name} | {'C044 5 V' if c else '12 V'} | {tt.mean():.2f} Nm | {np.percentile(tt,95):.2f} Nm | "
                    f"{'**' if c else ''}{np.percentile(dd,95):.2f}{'**' if c else ''} | {dd.max():.2f} |")
    if a.video:
        import imageio.v2 as imageio
        frames = []; episode(sess, variant, False, 0, frames)
        imageio.mimsave(os.path.join(run, f"walk_{variant}.mp4"), frames, fps=25, quality=8, macro_block_size=1)
    print(walk[-1], flush=True)
txt = "Walking (10 s episodes, command 15 cm/s, so 150 cm is the target):\n\n" + "\n".join(walk) + "\n\nLoad while walking (all randomized episodes):\n\n" + "\n".join(load)
print(txt)
if a.md: open(a.md, "w").write(txt + "\n")
