# Record one BAM trajectory on a Feetech STS3215 using rustypot.
# Positions are logged relative to the hanging zero from sts_zero.json.

import argparse
import datetime
import json
import os
import time
import numpy as np
from bam.trajectory import trajectories
from bam.feetech.sts import STS, STEP, load_zero  # noqa: F401

p = argparse.ArgumentParser()
p.add_argument("--port", default="/dev/cu.usbmodem5B421351891")
p.add_argument("--id", type=int, default=3)
p.add_argument("--mass", type=float, required=True)
p.add_argument("--arm-mass", type=float, required=True)
p.add_argument("--length", type=float, required=True)
p.add_argument("--kp", type=int, default=32)
p.add_argument("--vin", type=float, default=7.4)
p.add_argument("--motor", default="sts3215")
p.add_argument("--trajectory", default="lift_and_drop")
p.add_argument("--logdir", required=True)
p.add_argument("--replay", help="Rhoban raw log: replay its exact goal_position/torque_enable sequence")
p.add_argument("--accel-profile", type=int, nargs=2, default=[0, 0], metavar=("R85", "R41"),
               help="firmware accel profile during recording; default 0 0 = off (as Rhoban)")
p.add_argument("--zero-here", action="store_true",
               help="Use current position as zero (no-load runs only, no gravity reference needed)")
a = p.parse_args()


class Replay:
    """Zero-order hold of a recorded command sequence (same as the original recorder saw it)."""

    def __init__(self, fn):
        d = json.load(open(fn))
        self.src = d
        self.t = np.array([e["timestamp"] for e in d["entries"]])
        self.g = [e["goal_position"] for e in d["entries"]]
        self.en = [e["torque_enable"] for e in d["entries"]]
        self.duration = float(self.t[-1])

    def __call__(self, t):
        i = max(0, int(np.searchsorted(self.t, t, side="right")) - 1)
        return self.g[i], self.en[i]


if a.replay:
    traj = Replay(a.replay)
    a.trajectory = traj.src["trajectory"]
    a.kp = int(traj.src["kp"])
else:
    if a.trajectory not in trajectories:
        raise ValueError(f"Unknown trajectory {a.trajectory}, options: {list(trajectories)}")
    traj = trajectories[a.trajectory]
os.makedirs(a.logdir, exist_ok=True)

m = STS(a.port, a.id)
zero = m.read_raw()[0] if a.zero_here else load_zero()
if not (1250 <= zero <= 2850):
    raise RuntimeError(f"zero={zero}: +-1.8 rad around it would wrap the encoder. Rotate the shaft towards 2048.")
orig_p = m.c.read_p_coefficient(a.id)[0]
orig_d = m.c.read_d_coefficient(a.id)[0]
orig_acc = m.read_accel_profile()


def goal(q):
    m.goal_raw(zero + q / STEP)


def read():
    pos, speed, load, volts, temp = m.read_raw()
    return {
        "position": float((pos - zero) * STEP),
        "speed": float(speed * STEP),
        "load": float(load),
        "input_volts": float(volts),
        "temp": float(temp),
    }


try:
    m.open_limits()
    m.accel_profile(*a.accel_profile)
    m.set_gains(a.kp, 0)

    # Move gently to the trajectory start
    q0, en = traj(0)
    q = read()["position"]
    goal(q)
    m.torque(True)
    while abs(q - q0) > 1e-3:
        q += np.clip(q0 - q, -0.01, 0.01)
        goal(q)
        time.sleep(0.01)
    time.sleep(0.5)
    if not en:
        m.torque(False)
    torque = en

    data = dict(mass=a.mass, arm_mass=a.arm_mass, length=a.length, kp=a.kp, vin=a.vin,
                motor=a.motor, trajectory=a.trajectory, servo_id=a.id, zero_raw=int(zero), accel_profile_85_41=list(a.accel_profile),
                replay_of=os.path.basename(a.replay) if a.replay else None, entries=[])
    start = time.time()
    while (t := time.time() - start) < traj.duration:
        g, en = traj(t)
        if en != torque:
            m.torque(en)
            torque = en
        if torque:
            goal(g)
        t0 = time.time() - start
        e = read()
        t1 = time.time() - start
        e.update(timestamp=(t0 + t1) / 2, goal_position=float(g), torque_enable=bool(torque))
        data["entries"].append(e)

    # Return slowly to zero
    q = read()["position"]
    goal(q)
    m.torque(True)
    while abs(q) > 1e-3:
        q -= np.clip(q, -0.01, 0.01)
        goal(q)
        time.sleep(0.01)
    time.sleep(0.5)
finally:
    m.torque(False)
    m.set_gains(orig_p, orig_d)
    m.accel_profile(*orig_acc)

n = len(data["entries"])
fn = f"{a.logdir}/{datetime.datetime.now():%Y-%m-%d_%Hh%Mm%S}_{a.trajectory}_kp{a.kp}.json"
data["bus_timeouts"] = STS.timeouts
json.dump(data, open(fn, "w"))
print(f"{fn}: {n} samples ({n/traj.duration:.0f} Hz), bus timeouts retried: {STS.timeouts}")
