"""Run the ONNX policy in simulation on the same target schedule, and compare with a real run.

    uv run --project ~/projects/bam python sim/pendulum_policy/run_sim.py --onnx .../policy.onnx [--real real.npz] [--plot out.png]
Simulates the nominal model plus 10 randomized episodes.
"""
import argparse, os, sys
import numpy as np
import onnxruntime as ort
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pend_env import PendEnv, test_targets

ap = argparse.ArgumentParser()
ap.add_argument("--onnx", required=True); ap.add_argument("--real"); ap.add_argument("--plot")
a = ap.parse_args()
sess = ort.InferenceSession(a.onnx)
sched = test_targets(); steps = int((sched[-1][0] + 1.5) / 0.02)


def episode(randomize, seed):
    e = PendEnv(randomize=randomize, episode_s=steps * 0.02 + 1, schedule=sched); o, _ = e.reset(seed=seed); out = []
    for k in range(steps):
        act = sess.run(None, {"obs": o[None].astype(np.float32)})[0][0]
        o, r, _, _, info = e.step(act); out.append((0.02 * (k + 1), info["q"], info["target"], float(act[0])))
    return np.array(out)


nom = episode(False, 0); rnd = [episode(True, 100 + i) for i in range(10)]
err = lambda x: np.degrees(np.abs(x[:, 1] - x[:, 2])).mean()
print(f"sim nominal: tracking error {err(nom):.2f} deg; randomized x10: {np.mean([err(x) for x in rnd]):.2f} deg (max {max(err(x) for x in rnd):.2f})")
if a.real:
    R = np.load(a.real)
    q_sim = np.interp(R["t"], nom[:, 0], nom[:, 1])
    lo = np.min([np.interp(R["t"], x[:, 0], x[:, 1]) for x in rnd], 0); hi = np.max([np.interp(R["t"], x[:, 0], x[:, 1]) for x in rnd], 0)
    inside = np.mean((R["q"] >= lo - np.radians(1)) & (R["q"] <= hi + np.radians(1)))
    print(f"real: tracking error {np.degrees(np.abs(R['q'] - R['target'])).mean():.2f} deg; |real - sim nominal| mean {np.degrees(np.abs(R['q'] - q_sim)).mean():.2f} deg, "
          f"max {np.degrees(np.abs(R['q'] - q_sim)).max():.2f}; real inside the randomized sim band (+-1 deg) {inside*100:.0f}% of the time")
if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for x in rnd: ax[0].plot(x[:, 0], np.degrees(x[:, 1]), color="C1", alpha=.25, lw=.8)
    ax[0].plot(nom[:, 0], np.degrees(nom[:, 2]), "k:", label="target")
    ax[0].plot(nom[:, 0], np.degrees(nom[:, 1]), "C1", label="sim (nominal; thin: randomized)")
    if a.real:
        ax[0].plot(R["t"], np.degrees(R["q"]), "C0", label="real servo (encoder)")
        ax[0].plot(R["t"], np.degrees(R["tilt"]), "C2", lw=.8, label="real Nano tilt")
        ax[1].plot(R["t"], np.degrees(R["action"] * 1.5), "C0", label="real action (goal deg)")
    ax[1].plot(nom[:, 0], np.degrees(nom[:, 3] * 1.5), "C1", label="sim action (goal deg)")
    ax[0].set_ylabel("deg"); ax[1].set_ylabel("deg"); ax[1].set_xlabel("s"); ax[0].legend(fontsize=8); ax[1].legend(fontsize=8)
    for x in ax: x.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(a.plot, dpi=100); print("plot", a.plot)
