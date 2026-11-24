"""Run the ONNX pendulum policy on the real servo + Nano IMU at 50 Hz (the robot's control loop, on one joint).

    uv run --project ~/projects/bam python sim/pendulum_policy/run_real.py --onnx sim/pendulum_policy/runs/p1/policy.onnx --out real.npz
The arm must hang still at the start: the Nano recalibrates its gyro bias (2 s), and q = 0 / tilt = 0 are taken there.
Observation and action exactly as in pend_env.py. Logs every tick, including the loop timing.
"""
import argparse, os, sys, time
import numpy as np
import onnxruntime as ort
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(REPO, "scripts", "imu"))
from pend_env import test_targets, ACTION_SCALE, KP_FW
from nano_imu import NanoIMU
from bam.feetech.sts import STS, STEP

ap = argparse.ArgumentParser()
ap.add_argument("--onnx", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--port", default="/dev/cu.usbmodem5B421346401")
ap.add_argument("--imu", default="/dev/cu.usbmodem1301")
ap.add_argument("--id", type=int, default=6)
a = ap.parse_args()

sess = ort.InferenceSession(a.onnx)
imu = NanoIMU(a.imu)
imu.s.write(b"c"); time.sleep(2.6); imu.read_all()          # gyro bias recalibration, arm hanging still
m = STS(a.port, a.id)
orig = (m.c.read_p_coefficient(a.id)[0], m.c.read_d_coefficient(a.id)[0])
zero = m.read_raw()[0]


def tilt_of(up):  # same sign as the encoder (measured on the sweep: tilt = -atan2(uy, ux))
    return -np.arctan2(up[1], up[0])


S = []
while len(S) < 50:
    S += imu.read_all()
tilt0 = np.median([tilt_of(x[4]) for x in S]); last = S[-1]
sched = test_targets(); T_END = sched[-1][0] + 1.5
log = []; last_a = 0.0
try:
    m.open_limits(); m.set_gains(KP_FW, 0); m.goal_raw(zero); m.torque(True)
    t0 = time.perf_counter(); k = 0
    while True:
        t_tick = t0 + 0.02 * k
        while time.perf_counter() < t_tick:
            pass
        ts = time.perf_counter(); t = ts - t0
        if t > T_END:
            break
        new = imu.read_all()
        if new:
            last = new[-1]
        pos, spd, load, v, temp = m.read_raw()
        q, qd = (pos - zero) * STEP, spd * STEP
        tilt, gyro = tilt_of(last[4]) - tilt0, last[2][2]
        tg = [x for tt, x in sched if tt <= t + 1e-9][-1]
        obs = np.array([[q, 0.1 * qd, tilt, 0.1 * gyro, tg, q - tg, last_a]], np.float32)
        act = float(sess.run(None, {"obs": obs})[0][0, 0])
        m.goal_raw(zero + ACTION_SCALE * act / STEP)
        te = time.perf_counter()
        log.append((t, q, qd, tilt, gyro, tg, act, load, len(new), (te - ts) * 1e3, time.time() - last[1]))
        last_a = act; k += 1
finally:
    m.torque(False); m.set_gains(*orig)
L = np.array(log)
np.savez(a.out, t=L[:, 0], q=L[:, 1], qd=L[:, 2], tilt=L[:, 3], gyro=L[:, 4], target=L[:, 5], action=L[:, 6], load=L[:, 7],
         imu_new=L[:, 8], work_ms=L[:, 9], imu_age_s=L[:, 10])
dt = np.diff(L[:, 0]) * 1e3
print(f"ticks {len(L)}; period {np.median(dt):.2f} ms (max {dt.max():.2f}); work per tick {np.median(L[:,9]):.2f} ms (max {L[:,9].max():.2f}); "
      f"IMU sample age {np.median(L[:,10])*1e3:.1f} ms (max {L[:,10].max()*1e3:.1f}); ticks without new IMU data {(L[:,8]==0).sum()}")
print(f"tracking |q - target| mean {np.degrees(np.abs(L[:,1]-L[:,5])).mean():.2f} deg; |tilt - q| mean {np.degrees(np.abs(L[:,3]-L[:,1])).mean():.2f} deg")
