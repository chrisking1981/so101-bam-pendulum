"""Run the simple biped in MuJoCo with BAM actuator models (C044 hips, C046 ankles).

Usage (inside a Rhoban/bam checkout with `uv sync --extra mujoco`):
    uv run python /path/to/sim/biped/run_biped.py [--render out_dir]

Tests:
  stand   : all targets 0 for 4 s; the robot must stay upright.
  lean    : ankles tilt the body slowly forward and back (+-0.2 rad).
  scissor : hips swing in opposite phase with the ankles compensating, like a shuffle.
Prints pelvis height and pitch/roll; with --render it saves a few PNG frames.
"""
import argparse
import os
import numpy as np
import mujoco
from bam.model import load_model
from bam.mujoco import MujocoController

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

p = argparse.ArgumentParser()
p.add_argument("--hip-params", default=os.path.join(REPO, "fits", "C044", "m6.json"))
p.add_argument("--ankle-params", default=os.path.join(REPO, "fits", "C046", "m4.json"))
p.add_argument("--kp", type=float, default=32, help="firmware P register used on the real servos")
p.add_argument("--vin", type=float, default=7.4)
p.add_argument("--render", help="directory for PNG frames")
a = p.parse_args()


def make():
    m = mujoco.MjModel.from_xml_path(os.path.join(HERE, "biped.xml"))
    d = mujoco.MjData(m)
    hips, ankles = load_model(a.hip_params), load_model(a.ankle_params)
    for mod in (hips, ankles):
        mod.actuator.kp = a.kp
        mod.actuator.vin = a.vin
    ctrl = [MujocoController(hips, ["hip_L", "hip_R"], m, d), MujocoController(ankles, ["ankle_L", "ankle_R"], m, d)]
    mujoco.mj_forward(m, d)
    return m, d, ctrl


def euler(q):
    w, x, y, z = q
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    return np.degrees(roll), np.degrees(pitch)


def run(name, targets, T, frames=()):
    m, d, ctrl = make()
    pz, rolls, pitches, err = [], [], [], []
    renderer = mujoco.Renderer(m, 480, 640) if a.render and frames else None
    cam = mujoco.MjvCamera(); cam.lookat[:] = [0, 0, 0.10]; cam.distance = 0.48; cam.azimuth = 140; cam.elevation = -12
    saved = []
    while d.time < T:
        tg = targets(d.time)
        for c, names in ((ctrl[0], ["hip_L", "hip_R"]), (ctrl[1], ["ankle_L", "ankle_R"])):
            for n in names:
                c.set_q_target(n, tg[n])
            c.update()
        mujoco.mj_step(m, d)
        pz.append(d.qpos[2]); r, pt = euler(d.qpos[3:7]); rolls.append(r); pitches.append(pt)
        err.append(max(abs(tg[n] - d.joint(n).qpos[0]) for n in tg))
        if renderer is not None and frames and len(saved) < len(frames) and d.time >= frames[len(saved)]:
            renderer.update_scene(d, camera=cam)
            from PIL import Image
            fn = os.path.join(a.render, f"{name}_{d.time:.1f}s.png")
            Image.fromarray(renderer.render()).save(fn); saved.append(fn)
    pz = np.array(pz)
    fell = pz.min() < 0.10 or max(abs(np.array(rolls)).max(), abs(np.array(pitches)).max()) > 45
    print(f"{name:8s}: pelvis z {pz.min():.3f}-{pz.max():.3f} m, max |roll| {abs(np.array(rolls)).max():.1f} deg, "
          f"max |pitch| {abs(np.array(pitches)).max():.1f} deg, max joint error {np.degrees(max(err[500:])):.1f} deg, "
          f"{'FELL' if fell else 'upright'}")
    return saved


if a.render:
    os.makedirs(a.render, exist_ok=True)
m, d, _ = make()
print(f"model: {m.nbody} bodies, {m.njnt} joints, total mass {sum(m.body_mass):.3f} kg")
zero = lambda t: {"hip_L": 0, "hip_R": 0, "ankle_L": 0, "ankle_R": 0}
run("stand", zero, 4.0, frames=(1.0,))
lean = lambda t: {"hip_L": 0, "hip_R": 0, "ankle_L": 0.2 * np.sin(1.2 * t), "ankle_R": 0.2 * np.sin(1.2 * t)}
run("lean", lean, 6.0, frames=(1.3, 3.9))
def scissor(t):
    s = 0.25 * np.sin(2.0 * t) * min(1, t / 1.0)
    return {"hip_L": s, "hip_R": -s, "ankle_L": -s, "ankle_R": s}
run("scissor", scissor, 6.0, frames=(2.0, 3.6))
