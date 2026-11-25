"""Replay the real goal sequences in MuJoCo with BAM 12 V m5 on both joints and compare with the real encoders.

    uv run --project ~/projects/bam python sim/double_pendulum/compare_traj.py sim/double_pendulum/data/real_traj.npz [--plot out.png]
"""
import argparse, os, sys
import numpy as np
import mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_model import build
import rig as rigmod
from bam.model import load_model
from bam.mujoco import MujocoController

ap = argparse.ArgumentParser(); ap.add_argument("real"); ap.add_argument("--plot"); ap.add_argument("--md")
ap.add_argument("--scale", nargs="*", default=[], help="mass scales, e.g. upper_link=1.2 cable=0.5")
ap.add_argument("--rig", default="12v"); ap.add_argument("--knee-id", type=int)
ap.add_argument("--vin", type=float, help="override the supply voltage in the model (default: the median the servos report)")
a = ap.parse_args()
R = np.load(a.real); kp = int(R["kp"])
scale = {k: float(v) for k, v in (s.split("=") for s in a.scale)}
RIG = rigmod.get(a.rig, a.knee_id if a.rig == "c044knee" else None)


def replay(L):
    m = build(scale=scale, servo2=RIG["knee"]["mass"]); d = mujoco.MjData(m)
    ctrls = []
    for j, vcol in (("hip", 6), ("knee", 10)):
        model = load_model(RIG[j]["params"]); model.actuator.kp = kp; model.actuator.vin = a.vin if a.vin else float(np.median(L[:, vcol]))
        ctrls.append(model)
    d.qpos[:] = [L[0, 3], L[0, 7]]; mujoco.mj_forward(m, d)
    ch, ck = MujocoController(ctrls[0], ["hip"], m, d), MujocoController(ctrls[1], ["knee"], m, d)
    t, out, i = L[:, 0], [], 0
    while d.time < t[-1]:
        while i + 1 < len(t) and t[i + 1] <= d.time: i += 1
        ch.set_q_target("hip", L[i, 1]); ck.set_q_target("knee", L[i, 2]); ch.update(); ck.update()
        mujoco.mj_step(m, d); out.append((d.time, d.qpos[0], d.qpos[1]))
    o = np.array(out)
    return np.interp(t, o[:, 0], o[:, 1]), np.interp(t, o[:, 0], o[:, 2])


names = [k for k in R.files if k not in ("columns", "kp", "zero", "rig")]
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
        for c, (gi, qi, s, lab) in enumerate([(1, 3, sh, f"hip (ID {RIG['hip']['id']})"), (2, 7, sk, f"knee (ID {RIG['knee']['id']})")]):
            x = ax[r, c]; x.plot(L[:, 0], np.degrees(L[:, gi]), "k:", lw=1, label="goal")
            x.plot(L[:, 0], np.degrees(L[:, qi]), "C0", lw=1.5, label="real"); x.plot(L[:, 0], np.degrees(s), "C1", lw=1.1, label="MuJoCo + BAM")
            x.set_title(f"{n}: {lab}", fontsize=9); x.grid(alpha=.3)
    ax[0, 0].legend(fontsize=8); fig.tight_layout(); fig.savefig(a.plot, dpi=90); print("plot", a.plot)
