"""Slow, small moves of the two-link pendulum while printing what the servos and the Nano report.

The Nano sits on the lower link, so its tilt should equal hip + knee, and its gyro the sum of both joint speeds.
    uv run --project ~/projects/bam python sim/double_pendulum/manual_check.py
"""
import copy, os, sys, time
import numpy as np
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts", "imu"))
from nano_imu import NanoIMU
from bam.feetech.sts import STS, STEP

imu = NanoIMU("/dev/cu.usbmodem1301"); imu.s.write(b"c"); time.sleep(2.6); imu.read_all()
hip = STS("/dev/cu.usbmodem5B421346401", 6); knee = copy.copy(hip); knee.id = 2
ms = [hip, knee]; orig = [(m.c.read_p_coefficient(m.id)[0], m.c.read_d_coefficient(m.id)[0]) for m in ms]
zero = [m.read_raw()[0] for m in ms]
S = []
while len(S) < 40: S += imu.read_all()
up0 = np.mean([x[4] for x in S], 0); a0 = np.arctan2(up0[1], up0[0])
D = np.radians
plan = [("rust", 1.0, 0, 0), ("heup -> +30", 2.0, 30, 0), ("vasthouden", 1.0, 30, 0), ("heup terug", 2.0, 0, 0),
        ("knie -> +30", 2.0, 0, 30), ("vasthouden", 1.0, 0, 30), ("knie terug", 2.0, 0, 0),
        ("beide -> +20/+30", 2.0, 20, 30), ("vasthouden", 1.0, 20, 30), ("beide terug", 2.0, 0, 0)]
rows = []; last = S[-1]
try:
    for m, z in zip(ms, zero): m.open_limits(); m.set_gains(32, 0); m.goal_raw(z); m.torque(True)
    g_prev = np.zeros(2); t0 = time.time(); nxt = 0.0
    print(f"{'fase':18s} {'tijd':>5s} | {'heup':>7s} {'knie':>7s} {'heup+knie':>9s} | {'Nano kanteling':>14s} {'Nano gyro':>10s} | {'last heup':>9s} {'last knie':>9s}")
    for name, dur, gh, gk in plan:
        ts = time.time(); g_to = np.array([D(gh), D(gk)])
        while (u := (time.time() - ts) / dur) < 1:
            s = 3 * u * u - 2 * u ** 3; g = g_prev + (g_to - g_prev) * s
            for m, z, gi in zip(ms, zero, g): m.goal_raw(z + gi / STEP)
            q, ld = [], []
            for m, z in zip(ms, zero):
                pos, spd, load, v, temp = m.read_raw(); q.append((pos - z) * STEP); ld.append(load)
            new = imu.read_all()
            if new: last = new[-1]
            tilt = np.arctan2(last[4][1], last[4][0]) - a0; gyro = last[2][2]
            t = time.time() - t0
            rows.append((t, q[0], q[1], tilt, gyro))
            if t >= nxt:
                print(f"{name:18s} {t:5.1f} | {np.degrees(q[0]):+6.1f}° {np.degrees(q[1]):+6.1f}° {np.degrees(q[0]+q[1]):+8.1f}° | {np.degrees(tilt):+13.1f}° {np.degrees(gyro):+8.1f}°/s | {ld[0]:+8.0f} {ld[1]:+8.0f}", flush=True)
                nxt += 0.5
        g_prev = g_to
finally:
    for m, o in zip(ms, orig): m.torque(False); m.set_gains(*o)
R = np.array(rows); s = np.sign(np.corrcoef(R[:, 3], R[:, 1] + R[:, 2])[0, 1]) or 1
err = s * R[:, 3] - (R[:, 1] + R[:, 2])
print(f"\nNano kanteling (teken {s:+.0f}) tegen heup+knie: gemiddeld verschil {np.degrees(np.abs(err)).mean():.2f}°, max {np.degrees(np.abs(err)).max():.2f}°")
np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_check.npy"), R)
