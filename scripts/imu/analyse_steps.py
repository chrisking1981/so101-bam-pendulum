"""Latency from a step recording made with servo_imu_sweep.py --mode steps.

For every step it reports, in host time: command sent -> encoder first moves (> 0.5 deg),
command sent -> IMU gyro first sees the motion (> 20 deg/s) as it ARRIVES on the Mac,
and the encoder-vs-IMU delay from cross-correlating encoder velocity with the gyro.
    uv run python scripts/imu/analyse_steps.py steps.npz steps.png
"""
import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = np.load(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else None
te, pos, gl = d["t_enc"], np.degrees(d["pos"]), d["goal_deg"]
th, tdev, g = d["t_imu"], d["t_imu_dev"], np.degrees(d["gyro"])
t0 = te[0]; te, th = te - t0, th - t0
gz = g[:, 2] - g[(tdev - tdev[0]) < 1.2, 2].mean()
sg = np.sign(np.corrcoef(np.interp(th, te, np.gradient(pos, te)), gz)[0, 1]); w = sg * gz
# arrival time per sample: samples of one USB batch share th; the Arduino clock gives their true spacing
tarr = th
tdev_h = tdev - tdev[0] + np.min(th - (tdev - tdev[0]))   # best-case (zero-transport) time on the host clock
cmd_idx = np.where(np.abs(np.diff(gl)) > 1)[0] + 1
rows = []
for i in cmd_idx:
    tc = te[i]; p0 = pos[i - 1]; dirn = np.sign(gl[i] - gl[i - 1])
    me = np.where((te > tc) & (dirn * (pos - p0) > 0.5))[0]
    mi = np.where((tarr > tc) & (dirn * w > 20))[0]
    mi2 = np.where((tdev_h > tc) & (dirn * w > 20))[0]
    if len(me) and len(mi):
        rows.append((gl[i - 1], gl[i], (te[me[0]] - tc) * 1e3, (tarr[mi[0]] - tc) * 1e3, (tdev_h[mi2[0]] - tc) * 1e3))
r = np.array(rows)
print("| step | cmd -> encoder moves (ms) | cmd -> gyro sees it, on arrival (ms) | same, best-case sample time (ms) |")
print("|---|---:|---:|---:|")
for a_, b_, e_, i_, i2 in r:
    print(f"| {a_:+.0f} -> {b_:+.0f} | {e_:.1f} | {i_:.1f} | {i2:.1f} |")
print(f"| **median** | **{np.median(r[:,2]):.1f}** | **{np.median(r[:,3]):.1f}** | **{np.median(r[:,4]):.1f}** |")
# cross-correlation encoder velocity vs gyro (arrival time base)
tt = np.arange(1.0, te[-1] - 1.0, 0.0005)
ve = np.interp(tt, te, np.gradient(pos, te)); lags = np.arange(-0.03, 0.06, 0.0005)
cc = [np.corrcoef(ve, np.interp(tt + L, tarr, w))[0, 1] for L in lags]
print(f"IMU (arrival) lags the encoder by {lags[int(np.argmax(cc))]*1e3:.1f} ms (cross-correlation of velocities, peak r = {max(cc):.3f})")
dt_arr = np.diff(np.unique(th)) * 1e3
print(f"USB batches arrive every {np.median(dt_arr):.2f} ms (p99 {np.percentile(dt_arr, 99):.1f}, max {dt_arr.max():.1f})")
if out:
    k = cmd_idx[1]; m1 = (te > te[k] - 0.05) & (te < te[k] + 0.4); m2 = (th > te[k] - 0.05) & (th < te[k] + 0.4)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].plot(te, gl, "k:", label="goal"); ax[0].plot(te, pos, label="encoder"); ax[0].set_ylabel("deg"); ax[0].legend(); ax[0].grid(alpha=.3); ax[0].set_xlabel("s")
    ax[1].axvline(0, color="k", lw=.8, label="command sent")
    ax[1].plot((te[m1] - te[k]) * 1e3, np.gradient(pos, te)[m1], label="encoder velocity (deg/s)")
    ax[1].plot((th[m2] - te[k]) * 1e3, w[m2], ".", ms=2, label="gyro (deg/s), at arrival")
    ax[1].set_xlabel("ms after command"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out, dpi=100); print("plot", out)
