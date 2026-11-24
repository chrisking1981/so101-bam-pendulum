"""Run the two-joint ONNX policy in simulation on the test schedule (nominal + 10 randomized) and compare with a real run.

    uv run --project ~/projects/bam python sim/double_pendulum/run_sim.py --onnx .../policy.onnx [--real real.npz] [--plot out.png]
"""
import argparse, os, sys
import numpy as np
import onnxruntime as ort
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_env import DPEnv, test_targets, ACTION_SCALE

ap = argparse.ArgumentParser(); ap.add_argument("--onnx", required=True); ap.add_argument("--real"); ap.add_argument("--plot")
a = ap.parse_args()
sess = ort.InferenceSession(a.onnx); sched = test_targets(); steps = int((sched[-1][0] + 1.5) / 0.02)


def episode(randomize, seed):
    e = DPEnv(randomize=randomize, episode_s=steps * 0.02 + 1, schedule=sched); o, _ = e.reset(seed=seed); out = []
    for k in range(steps):
        act = sess.run(None, {"obs": o[None].astype(np.float32)})[0][0]
        o, r, _, _, info = e.step(act); out.append((0.02 * (k + 1), *info["q"], *info["target"], *np.clip(act, -1, 1)))
    return np.array(out)


nom = episode(False, 0); rnd = [episode(True, 300 + i) for i in range(10)]
err = lambda x, j: np.degrees(np.abs(x[:, 1 + j] - x[:, 3 + j])).mean()
hold = lambda x, j: np.degrees(x[10:70, 5 + j] * ACTION_SCALE).std()
print(f"sim nominal: tracking hip {err(nom,0):.2f}, knee {err(nom,1):.2f} deg; randomized x10: hip {np.mean([err(x,0) for x in rnd]):.2f}, knee {np.mean([err(x,1) for x in rnd]):.2f}")
print(f"hold oscillation (action std in first hold): nominal {hold(nom,0):.2f}/{hold(nom,1):.2f} deg, randomized max {max(hold(x,0) for x in rnd):.2f}/{max(hold(x,1) for x in rnd):.2f} deg")
if a.real:
    R = np.load(a.real)["L"]; t = R[:, 0]
    for j, n in enumerate(["hip", "knee"]):
        qs = np.interp(t, nom[:, 0], nom[:, 1 + j])
        lo = np.min([np.interp(t, x[:, 0], x[:, 1 + j]) for x in rnd], 0); hi = np.max([np.interp(t, x[:, 0], x[:, 1 + j]) for x in rnd], 0)
        inside = np.mean((R[:, 1 + j] >= lo - np.radians(1)) & (R[:, 1 + j] <= hi + np.radians(1)))
        print(f"real {n}: tracking {np.degrees(np.abs(R[:,1+j]-R[:,7+j])).mean():.2f} deg; |real - sim| mean {np.degrees(np.abs(R[:,1+j]-qs)).mean():.2f}, "
              f"max {np.degrees(np.abs(R[:,1+j]-qs)).max():.2f} deg; inside randomized band {inside*100:.0f}%; hold action std {np.degrees(R[10:70,9+j]*ACTION_SCALE).std():.2f} deg")
if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(13, 6), sharex=True)
    for j, n in enumerate(["hip (ID 6)", "knee (ID 2)"]):
        for x in rnd: ax[0, j].plot(x[:, 0], np.degrees(x[:, 1 + j]), color="C1", alpha=.25, lw=.8)
        ax[0, j].plot(nom[:, 0], np.degrees(nom[:, 3 + j]), "k:", label="target"); ax[0, j].plot(nom[:, 0], np.degrees(nom[:, 1 + j]), "C1", label="sim")
        ax[1, j].plot(nom[:, 0], np.degrees(nom[:, 5 + j] * ACTION_SCALE), "C1", label="sim action (goal deg)")
        if a.real:
            ax[0, j].plot(R[:, 0], np.degrees(R[:, 1 + j]), "C0", label="real")
            ax[1, j].plot(R[:, 0], np.degrees(R[:, 9 + j] * ACTION_SCALE), "C0", label="real action (goal deg)")
        if j == 1 and a.real: ax[0, j].plot(R[:, 0], np.degrees(R[:, 5] - R[:, 1]), "C2", lw=.8, label="Nano tilt - hip")
        ax[0, j].set_title(n); ax[0, j].legend(fontsize=7); ax[1, j].legend(fontsize=7)
        for x in ax[:, j]: x.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(a.plot, dpi=95); print("plot", a.plot)
