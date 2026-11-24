"""Play fixed goal trajectories on both real servos (hip = ID 6, knee = ID 2) and log at the highest rate. No policy.

    uv run --project ~/projects/bam python sim/double_pendulum/run_traj_real.py --out sim/double_pendulum/data/real_traj.npz
Zero = the hanging position at the start for both joints. Goals are clamped to +-80 deg (cable to servo 2).
"""
import argparse, copy, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bam.feetech.sts import STS, STEP
from trajectories import TRAJ, goals

ap = argparse.ArgumentParser(); ap.add_argument("--port", default="/dev/cu.usbmodem5B421346401"); ap.add_argument("--kp", type=int, default=32)
ap.add_argument("--out", required=True); ap.add_argument("--only", nargs="*")
a = ap.parse_args()
LIM = np.radians(80)
hip = STS(a.port, 6); knee = copy.copy(hip); knee.id = 2
assert hip.c.ping(2) and hip.c.read_lock(2)[0]
ms = [hip, knee]
orig = [(m.c.read_p_coefficient(m.id)[0], m.c.read_d_coefficient(m.id)[0]) for m in ms]
zero = [m.read_raw()[0] for m in ms]
logs = {}
try:
    for m, z in zip(ms, zero):
        m.open_limits(); m.set_gains(a.kp, 0); m.goal_raw(z); m.torque(True)
    time.sleep(0.5)
    for name in (a.only or list(TRAJ)):
        rows = []; t0 = time.time()
        while (t := time.time() - t0) < TRAJ[name][0]:
            g = np.clip(goals(name, t), -LIM, LIM)
            for m, z, gi in zip(ms, zero, g):
                m.goal_raw(z + gi / STEP)
            r = [t, *g]
            for m, z in zip(ms, zero):
                pos, spd, load, v, temp = m.read_raw(); r += [(pos - z) * STEP, spd * STEP, load, v]
            r.append(time.time() - t0)
            rows.append(r)
        logs[name] = np.array(rows)
        # back to zero slowly between trajectories
        q = [rows[-1][3], rows[-1][7]]
        for k in range(50):
            for m, z, qi in zip(ms, zero, q):
                m.goal_raw(z + qi * (1 - (k + 1) / 50) / STEP)
            time.sleep(0.02)
        time.sleep(0.8)
        L = logs[name]; print(f"{name}: {len(L)} samples, {len(L)/L[-1,0]:.0f} Hz, max |hip| {np.degrees(np.abs(L[:,3]).max()):.0f} deg, max |knee| {np.degrees(np.abs(L[:,7]).max()):.0f} deg", flush=True)
finally:
    for m, o in zip(ms, orig):
        m.torque(False); m.set_gains(*o)
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
np.savez(a.out, **logs, columns=np.array("t goal_hip goal_knee hip_q hip_qd hip_load hip_v knee_q knee_qd knee_load knee_v t_end".split()), kp=a.kp, zero=np.array(zero))
print("saved", a.out)
