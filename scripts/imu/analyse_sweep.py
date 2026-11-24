import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = np.load(sys.argv[1]); out = sys.argv[2]
te, pos = d["t_enc"], np.degrees(d["pos"]); g, acc = np.degrees(d["gyro"]), d["acc"]
# IMU samples arrive in USB batches that share one host time stamp: put them on the Arduino clock, shifted so the earliest arrival has zero lag
ti = d["t_imu_dev"] + np.min(d["t_imu"] - d["t_imu_dev"])
t0 = te[0]; te = te - t0; ti = ti - t0
bias = g[ti < 1.2].mean(0)                     # torque on at 0 for 1.5 s: arm still
gz = g - bias
ang_raw = np.degrees(np.arctan2(acc[:, 1], acc[:, 0]))
enc_i = np.interp(ti, te, pos)
sgn_a = np.sign(np.corrcoef(ang_raw, enc_i)[0, 1]); ang = sgn_a * ang_raw
off = np.median(ang[ti < 1.2] - enc_i[ti < 1.2]); ang -= off
venc = np.gradient(enc_i, ti)
k = int(np.argmax(np.abs([np.corrcoef(gz[:, j], venc)[0, 1] for j in range(3)])))
sg = np.sign(np.corrcoef(gz[:, k], venc)[0, 1]); w = sg * gz[:, k]
gint = np.concatenate([[0], np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(ti))])
slow = np.abs(venc) < 25
err = ang - enc_i
print(f"gyro axis along the shaft: {'xyz'[k]} (sign {sg:+.0f}); gyro bias at rest {np.round(bias,2)} deg/s")
print(f"accel angle vs encoder: offset {off:+.2f} deg; difference over the sweep: mean {err.mean():+.2f}, std {err.std():.2f}, max |{np.abs(err).max():.2f}| deg")
for lo, hi in [(-95, -60), (-60, -20), (-20, 20), (20, 60), (60, 95)]:
    mm = (enc_i > lo) & (enc_i < hi)
    if mm.sum(): print(f"  encoder {lo:+4d}..{hi:+4d} deg: accel-encoder {err[mm].mean():+.2f} deg (n={mm.sum()})")
print(f"gyro-integrated angle vs encoder at end: {gint[-1]-(enc_i[-1]-enc_i[0]):+.2f} deg drift; max |diff| {np.abs(gint-(enc_i-enc_i[0])).max():.2f} deg")
print(f"peak rate: encoder {np.abs(venc).max():.1f} deg/s, gyro {np.abs(w).max():.1f} deg/s")
fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax[0].plot(te, np.degrees(d['goal_deg']) if False else d['goal_deg'], 'k:', label='goal')
ax[0].plot(te, pos, label='servo encoder'); ax[0].plot(ti, ang, label='IMU angle (gravity)', alpha=.8); ax[0].plot(ti, gint, label='IMU angle (gyro integrated)', alpha=.8)
ax[0].set_ylabel('deg'); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
ax[1].plot(ti, err, label='IMU gravity angle - encoder'); ax[1].plot(ti, gint - (enc_i - enc_i[0]), label='IMU gyro angle - encoder')
ax[1].set_ylabel('deg'); ax[1].set_xlabel('s'); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(out, dpi=100); print('plot', out)
