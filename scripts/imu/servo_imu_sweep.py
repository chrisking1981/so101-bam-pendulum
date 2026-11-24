"""Move a servo (pendulum arm with the Nano 33 IoT taped on it) and record encoder + IMU together.

    uv run python scripts/imu/servo_imu_sweep.py --id 6 --mode sweep --out sweep.npz     # slow 0 -> +A -> -A -> 0
    uv run python scripts/imu/servo_imu_sweep.py --id 6 --mode steps --out steps.npz     # fast steps for latency
The zero is the position at start (arm hanging). Encoder samples and IMU samples are both stamped with the host clock.
"""
import argparse, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nano_imu import NanoIMU
from bam.feetech.sts import STS, STEP

ap = argparse.ArgumentParser()
ap.add_argument("--port", default="/dev/cu.usbmodem5B421346401")
ap.add_argument("--imu", default="/dev/cu.usbmodem1301")
ap.add_argument("--id", type=int, required=True)
ap.add_argument("--mode", choices=["sweep", "steps"], default="sweep")
ap.add_argument("--amp", type=float, default=90.0)
ap.add_argument("--speed", type=float, default=20.0, help="deg/s for the sweep")
ap.add_argument("--kp", type=int, default=32)
ap.add_argument("--out", required=True)
a = ap.parse_args()

imu = NanoIMU(a.imu); time.sleep(0.3); imu.read_all()
m = STS(a.port, a.id)
zero = m.read_raw()[0]
orig = (m.c.read_p_coefficient(a.id)[0], m.c.read_d_coefficient(a.id)[0])
enc, ims, goals = [], [], []


def goal(deg):
    m.goal_raw(int(round(zero + np.radians(deg) / STEP)))


def run_for(secs, gdeg_fn):
    t0 = time.time()
    while (t := time.time() - t0) < secs:
        g = gdeg_fn(t); goal(g)
        pos, spd, load, v, temp = m.read_raw()
        th = time.time()
        enc.append((th, (pos - zero) * STEP, spd * STEP, load, g))
        ims.extend(imu.read_all())


try:
    m.open_limits(); m.set_gains(a.kp, 0); goal(0); m.torque(True)
    run_for(1.5, lambda t: 0.0)
    if a.mode == "sweep":
        T = a.amp / a.speed
        for x0, x1 in [(0, a.amp), (a.amp, -a.amp), (-a.amp, 0)]:
            dur = abs(x1 - x0) / a.speed
            run_for(dur, lambda t, x0=x0, x1=x1, dur=dur: x0 + (x1 - x0) * min(t / dur, 1.0))
            run_for(1.0, lambda t, x1=x1: x1)
    else:
        for tgt in [30, 0, -30, 0, 30, 0, -30, 0]:
            run_for(1.5, lambda t, tgt=tgt: tgt)
    run_for(1.0, lambda t: 0.0)
finally:
    m.torque(False); m.set_gains(*orig)

e = np.array(enc)
np.savez(a.out, t_enc=e[:, 0], pos=e[:, 1], spd=e[:, 2], load=e[:, 3], goal_deg=e[:, 4], zero=zero,
         t_imu=np.array([x[1] for x in ims]), t_imu_dev=np.array([x[0] for x in ims]),
         gyro=np.array([x[2] for x in ims]), acc=np.array([x[3] for x in ims]))
print(f"encoder samples {len(e)}, IMU samples {len(ims)}, saved {a.out}")
