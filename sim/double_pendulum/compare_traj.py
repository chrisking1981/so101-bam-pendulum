"""Replay the real goal sequences in MuJoCo with BAM 12 V m5 on both joints and compare with the real encoders.

    uv run --project ~/projects/bam python sim/double_pendulum/compare_traj.py sim/double_pendulum/data/real_traj.npz [--plot out.png]
"""
import argparse, os, sys
import numpy as np
import mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_model import build, PARAMS
from bam.model import load_model
from bam.mujoco import MujocoController

ap = argparse.ArgumentParser(); ap.add_argument("real"); ap.add_argument("--plot"); ap.add_argument("--md")
ap.add_argument("--scale", nargs="*", default=[], help="mass scales, e.g. upper_link=1.2 cable=0.5")
a = ap.parse_args()
R = np.load(a.real); kp = int(R["kp"])
scale = {k: float(v) for k, v in (s.split("=") for s in a.scale)}


def replay(L):
    m = build(scale=scale); d = mujoco.MjData(m)
    model = load_model(PARAMS); model.actuator.kp = kp; model.actuator.vin = float(np.median(L[:, 6]))
    d.qpos[:] = [L[0, 3], L[0, 7]]; mujoco.mj_forward(m, d)
    ctrl = MujocoController(model, ["hip", "knee"], m, d)
    t, out, i = L[:, 0], [], 0
    while d.time < t[-1]:
        while i + 1 < len(t) and t[i + 1] <= d.time: i += 1
        ctrl.set_q_target("hip", L[i, 1]); ctrl.set_q_target("knee", L[i, 2]); ctrl.update()
        mujoco.mj_step(m, d); out.append((d.time, d.qpos[0], d.qpos[1]))
    o = np.array(out)
    return np.interp(t, o[:, 0], o[:, 1]), np.interp(t, o[:, 0], o[:, 2])


names = [k for k in R.files if k not in ("columns", "kp", "zero")]
lines = ["| trajectory | hip: real tracking error | hip: sim vs real | knee: real tracking error | knee: sim vs real |", "|---|---:|---:|---:|---:|"]
res = {}
for n in names:
    L = R[n]; sh, sk = replay(L)
    eh, ek = np.degrees(np.abs(L[:, 3] - L[:, 1])).mean(), np.degrees(np.abs(L[:, 7] - L[:, 2])).mean()
    dh, dk = np.degrees(np.abs(sh - L[:, 3])).mean(), np.degrees(np.abs(sk - L[:, 7])).mean()
    res[n] = (L, sh, sk); lines.append(f"| {n} | {eh:.2f}° | **{dh:.2f}°** | {ek:.2f}° | **{dk:.2f}°** |")
txt = "\n".join(lines); print(txt)
if a.md: open(a.md, "w").write(txt + "\n")
if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(len(names), 2, figsize=(13, 2.3 * len(names)), squeeze=False)
    for r, n in enumerate(names):
        L, sh, sk = res[n]
        for c, (gi, qi, s, lab) in enumerate([(1, 3, sh, "hip (ID 6)"), (2, 7, sk, "knee (ID 2)")]):
            x = ax[r, c]; x.plot(L[:, 0], np.degrees(L[:, gi]), "k:", lw=1, label="goal")
            x.plot(L[:, 0], np.degrees(L[:, qi]), "C0", lw=1.5, label="real"); x.plot(L[:, 0], np.degrees(s), "C1", lw=1.1, label="MuJoCo + BAM")
            x.set_title(f"{n}: {lab}", fontsize=9); x.grid(alpha=.3)
    ax[0, 0].legend(fontsize=8); fig.tight_layout(); fig.savefig(a.plot, dpi=90); print("plot", a.plot)
