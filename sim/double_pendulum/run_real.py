"""Run the two-joint ONNX policy on the real arm (hip ID 6, knee ID 2, Nano on the lower link) at 50 Hz.

    uv run --project ~/projects/bam python sim/double_pendulum/run_real.py --onnx sim/double_pendulum/runs/d1/policy.onnx --out real.npz
Both links must hang still at the start: the Nano recalibrates its gyro bias (2 s), q = 0 and tilt = 0 are taken there.
Nano mounting on the lower link (measured with manual_check.py): tilt = wrap(atan2(uy, ux) - start), gyro = -gz.
Every goal is clamped to +-80 deg (cable to servo 2), whatever the policy asks.
"""
import argparse, copy, os, sys, time
import numpy as np
import onnxruntime as ort
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "scripts", "imu"))
from dp_env import test_targets, ACTION_SCALE, KP_FW, LIM
from nano_imu import NanoIMU
from bam.feetech.sts import STS, STEP

ap = argparse.ArgumentParser(); ap.add_argument("--onnx", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
sess = ort.InferenceSession(a.onnx)
imu = NanoIMU("/dev/cu.usbmodem1301"); imu.s.write(b"c"); time.sleep(2.6); imu.read_all()
hip = STS("/dev/cu.usbmodem5B421346401", 6); knee = copy.copy(hip); knee.id = 2
assert hip.c.ping(2) and hip.c.read_lock(2)[0]
ms = [hip, knee]; orig = [(m.c.read_p_coefficient(m.id)[0], m.c.read_d_coefficient(m.id)[0]) for m in ms]
zero = [m.read_raw()[0] for m in ms]
S = []
while len(S) < 50: S += imu.read_all()
a0 = np.arctan2(np.mean([x[4][1] for x in S]), np.mean([x[4][0] for x in S])); last = S[-1]
wrap = lambda x: (x + np.pi) % (2 * np.pi) - np.pi
sched = test_targets(); T_END = sched[-1][0] + 1.5
log = []; last_a = np.zeros(2)
try:
    for m, z in zip(ms, zero): m.open_limits(); m.set_gains(KP_FW, 0); m.goal_raw(z); m.torque(True)
    t0 = time.perf_counter(); k = 0
    while True:
        tt = t0 + 0.02 * k
        while time.perf_counter() < tt: pass
        ts = time.perf_counter(); t = ts - t0
        if t > T_END: break
        new = imu.read_all()
        if new: last = new[-1]
        q, qd = [], []
        for m, z in zip(ms, zero):
            pos, spd, load, v, temp = m.read_raw(); q.append((pos - z) * STEP); qd.append(spd * STEP)
        q, qd = np.array(q), np.array(qd)
        tilt, gyro = wrap(np.arctan2(last[4][1], last[4][0]) - a0), -last[2][2]
        row = [r for r in sched if r[0] <= t + 1e-9][-1]; tg = np.array(row[1:])
        obs = np.concatenate([q, 0.1 * qd, [tilt, 0.1 * gyro], tg, q - tg, last_a, [1.0]]).astype(np.float32)[None]
        act = np.clip(sess.run(None, {"obs": obs})[0][0], -1, 1)
        goal = np.clip(ACTION_SCALE * act, -LIM, LIM)
        for m, z, g in zip(ms, zero, goal): m.goal_raw(z + g / STEP)
        log.append((t, *q, *qd, tilt, gyro, *tg, *act, (time.perf_counter() - ts) * 1e3, len(new)))
        last_a = act; k += 1
finally:
    for m, o in zip(ms, orig): m.torque(False); m.set_gains(*o)
L = np.array(log)
np.savez(a.out, L=L, columns=np.array("t q_hip q_knee qd_hip qd_knee tilt gyro tg_hip tg_knee a_hip a_knee work_ms imu_new".split()))
dt = np.diff(L[:, 0]) * 1e3
print(f"ticks {len(L)}; period {np.median(dt):.2f} ms (max {dt.max():.2f}); work {np.median(L[:,11]):.2f} ms (max {L[:,11].max():.2f}); ticks without IMU data {(L[:,12]==0).sum()}")
print(f"tracking |q - target|: hip {np.degrees(np.abs(L[:,1]-L[:,7])).mean():.2f} deg, knee {np.degrees(np.abs(L[:,2]-L[:,8])).mean():.2f} deg; "
      f"|tilt - (hip+knee)| {np.degrees(np.abs(L[:,5]-L[:,1]-L[:,2])).mean():.2f} deg")
