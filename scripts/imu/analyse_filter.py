"""Compare the Nano's on-board filtered tilt (firmware v2 up vector) with the servo encoder.

    uv run python scripts/imu/analyse_filter.py sweep.npz steps.npz out.png
Reports, for a slow sweep and for fast steps: the filtered angle error against the encoder, the raw accelerometer
angle error, a 20 ms box-averaged accelerometer angle error (what a 50 Hz loop would get by averaging), and the lag.
"""
import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def load(fn):
    d = np.load(fn)
    te, pos = d["t_enc"], np.degrees(d["pos"])
    ti = d["t_imu_dev"] + np.min(d["t_imu"] - d["t_imu_dev"])
    t0 = te[0]; te, ti = te - t0, ti - t0
    up, acc = d["up"], d["acc"]
    enc = np.interp(ti, te, pos)
    still = ti < 1.2
    out = {}
    for name, ang in [("filtered", np.degrees(np.arctan2(up[:, 1], up[:, 0]))), ("raw accel", np.degrees(np.arctan2(acc[:, 1], acc[:, 0])))]:
        s = np.sign(np.corrcoef(ang[~still], enc[~still])[0, 1]); ang = s * ang; ang -= np.median(ang[still] - enc[still])
        out[name] = ang
    n = 9  # ~20 ms at 442 Hz
    out["accel, 20 ms average"] = np.convolve(out["raw accel"], np.ones(n) / n, mode="same")
    return ti, enc, out, te, pos


def lag_ms(ti, enc, ang):
    tt = np.arange(ti[0] + 1, ti[-1] - 1, 0.0005); e = np.interp(tt, ti, enc)
    L = np.arange(-0.02, 0.08, 0.0005); c = [np.mean(np.abs(np.interp(tt + l, ti, ang) - e)) for l in L]
    return L[int(np.argmin(c))] * 1e3


figs = []
for fn, label in [(sys.argv[1], "slow sweep 20 deg/s"), (sys.argv[2], "steps +-30 deg")]:
    ti, enc, out, te, pos = load(fn)
    moving = np.abs(np.gradient(enc, ti)) > 5
    print(f"== {label}")
    for k, ang in out.items():
        err = ang - enc
        print(f"  {k:22s}: |error| mean {np.abs(err).mean():5.2f} deg, while moving {np.abs(err[moving]).mean():5.2f}, p99 {np.percentile(np.abs(err),99):5.2f}, max {np.abs(err).max():5.2f}; lag {lag_ms(ti, enc, ang):+.1f} ms")
    figs.append((label, ti, enc, out))
fig, ax = plt.subplots(2, 2, figsize=(13, 6.5))
for j, (label, ti, enc, out) in enumerate(figs):
    ax[0, j].plot(ti, enc, "k", lw=1.5, label="servo encoder")
    for k, c in [("raw accel", "C1"), ("accel, 20 ms average", "C2"), ("filtered", "C0")]:
        ax[0, j].plot(ti, out[k], c, lw=.8, alpha=.8, label=k)
        ax[1, j].plot(ti, out[k] - enc, c, lw=.8, alpha=.8, label=k + " - encoder")
    ax[0, j].set_title(label); ax[0, j].set_ylabel("deg"); ax[1, j].set_ylabel("deg"); ax[1, j].set_xlabel("s")
    ax[1, j].set_ylim(-15, 15); ax[0, j].legend(fontsize=7); ax[1, j].legend(fontsize=7)
    for a in ax[:, j]: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(sys.argv[3], dpi=100); print("plot", sys.argv[3])
