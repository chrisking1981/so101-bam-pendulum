"""Find the true vertical (gravity zero) of a pendulum on a servo that cannot be back-driven.

The servo sweeps slowly from -A to +A and back (P = 32). The load register (PWM, 1/1000) is the motor effort:
    load(theta) = k * sin(theta - theta0) + friction * sign(velocity)
Averaging the up and down sweeps removes the friction term; fitting a*sin(theta) + b*cos(theta) gives theta0 = atan2(-b, a).

    uv run python -m bam.feetech.find_vertical --port /dev/cu.usbmodem5B421346401 --id 2 --amp 60
Positions are relative to the zero stored in sts_zero.json. Prints theta0 in degrees and raw steps.
"""
import argparse, json, time
import numpy as np
from bam.feetech.sts import STS, STEP, load_zero, ZERO_FILE

p = argparse.ArgumentParser()
p.add_argument("--port", required=True)
p.add_argument("--id", type=int, required=True)
p.add_argument("--amp", type=float, default=60.0)
p.add_argument("--speed", type=float, default=10.0, help="deg/s")
p.add_argument("--update-zero", action="store_true", help="write the corrected zero to sts_zero.json")
a = p.parse_args()

m = STS(a.port, a.id)
zero = load_zero()
orig = (m.c.read_p_coefficient(a.id)[0], m.c.read_d_coefficient(a.id)[0])
rows = []
try:
    m.open_limits(); m.set_gains(32, 0)
    q = (m.read_raw()[0] - zero) * STEP
    m.goal_raw(zero + q / STEP); m.torque(True)

    def move(to, record):
        global q
        step = np.radians(a.speed) * 0.01
        while abs(q - to) > 1e-4:
            q += np.clip(to - q, -step, step)
            m.goal_raw(zero + q / STEP)
            t0 = time.time()
            while time.time() - t0 < 0.01:
                pos, spd, load, v, temp = m.read_raw()
                if record:
                    rows.append((np.degrees(q), np.degrees((pos - zero) * STEP), load, np.sign(to - q)))

    move(np.radians(-a.amp), False); time.sleep(0.5)
    move(np.radians(a.amp), True); time.sleep(0.5)
    move(np.radians(-a.amp), True); time.sleep(0.3)
    move(0.0, False)
finally:
    m.torque(False); m.set_gains(*orig)

r = np.array(rows)
bins = np.arange(-a.amp + 5, a.amp - 5 + 1e-9, 2.0)
up, dn = r[r[:, 3] > 0], r[r[:, 3] < 0]
avg = []
for b in bins:
    u = up[np.abs(up[:, 1] - b) < 1.0][:, 2]; d = dn[np.abs(dn[:, 1] - b) < 1.0][:, 2]
    if len(u) and len(d):
        avg.append((b, 0.5 * (u.mean() + d.mean()), 0.5 * (u.mean() - d.mean())))
avg = np.array(avg)
th = np.radians(avg[:, 0])
X = np.stack([np.sin(th), np.cos(th)], 1)
(ka, kb), *_ = np.linalg.lstsq(X, avg[:, 1], rcond=None)
# The load register has the opposite sign of the gravity torque it holds (load < 0 when holding the arm at +90 deg),
# so load = -k sin(theta - theta0) with k > 0:  ka = -k cos(theta0), kb = k sin(theta0)
theta0 = np.degrees(np.arctan2(kb, -ka))
resid = avg[:, 1] - X @ np.array([ka, kb])
print(f"fit residual {np.std(resid):.1f}/1000 over {len(avg)} angle bins")
print(f"gravity zero is at {theta0:+.2f} deg ({theta0 / np.degrees(STEP):+.0f} raw steps) from the stored zero {zero}")
print(f"gravity load amplitude {np.hypot(ka, kb):.0f}/1000 PWM, friction half-band {np.abs(avg[:, 2]).mean():.0f}/1000")
if a.update_zero:
    new = int(round(zero + np.radians(theta0) / STEP))
    d = json.load(open(ZERO_FILE)); d["zero"] = new; d["note"] = d.get("note", "") + f"; corrected by find_vertical ({theta0:+.2f} deg)"
    json.dump(d, open(ZERO_FILE, "w")); print("new zero", new)
