"""Hand-made open-loop shuffle gait for the simple biped, with BAM servo models (C044 hips, C046 ankles).

This is not a trained policy: the hips swing like scissors and the ankles follow with a fixed amplitude and phase.
  --search : grid-search amplitude, frequency and ankle phase for forward progress while staying upright
  --video  : render an MP4 of one gait (default: the best one found by --search, saved in gait_best.json)

Run inside a Rhoban/bam checkout with `uv sync --extra mujoco`:
  MUJOCO_GL=cgl uv run python sim/biped/gait.py --search
  MUJOCO_GL=cgl uv run python sim/biped/gait.py --video walk.mp4
"""
import argparse, itertools, json, os
import numpy as np
import mujoco
from bam.model import load_model
from bam.mujoco import MujocoController

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HIP = os.path.join(REPO, "fits", "C044", "m6.json")
ANKLE = os.path.join(REPO, "fits", "C046", "m4.json")
NAMES = ["hip_L", "hip_R", "ankle_L", "ankle_R"]


def make():
    m = mujoco.MjModel.from_xml_path(os.path.join(HERE, "biped.xml"))
    d = mujoco.MjData(m)
    hips, ankles = load_model(HIP), load_model(ANKLE)
    for mod in (hips, ankles):
        mod.actuator.kp = 32; mod.actuator.vin = 7.4
    c = [MujocoController(hips, ["hip_L", "hip_R"], m, d), MujocoController(ankles, ["ankle_L", "ankle_R"], m, d)]
    mujoco.mj_forward(m, d)
    return m, d, c


def targets(t, g):
    ramp = min(1.0, t / 1.0)
    s = np.sin(2 * np.pi * g["f"] * t)
    a = np.sin(2 * np.pi * g["f"] * t + g["phi"])
    return {"hip_L": ramp * g["A"] * s, "hip_R": -ramp * g["A"] * s,
            "ankle_L": ramp * (g["B"] * a + g["lean"]), "ankle_R": ramp * (-g["B"] * a + g["lean"])}


def tilt(q):
    w, x, y, z = q
    roll = np.degrees(np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))
    pitch = np.degrees(np.arcsin(np.clip(2 * (w * y - z * x), -1, 1)))
    yaw = np.degrees(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    return roll, pitch, yaw


def simulate(g, T=8.0, on_frame=None, fps=30):
    m, d, c = make()
    x0, y0 = d.qpos[0], d.qpos[1]
    worst = 0.0; next_frame = 0.0
    while d.time < T:
        tg = targets(d.time, g)
        for ctrl, ns in ((c[0], ["hip_L", "hip_R"]), (c[1], ["ankle_L", "ankle_R"])):
            for n in ns:
                ctrl.set_q_target(n, tg[n])
            ctrl.update()
        mujoco.mj_step(m, d)
        r, p, _ = tilt(d.qpos[3:7]); worst = max(worst, abs(r), abs(p))
        if on_frame and d.time >= next_frame:
            on_frame(m, d); next_frame += 1.0 / fps
        if d.qpos[2] < 0.09 or worst > 40:
            return dict(dx=d.qpos[0] - x0, dy=d.qpos[1] - y0, fell=True, worst=worst, t=d.time)
    _, _, yaw = tilt(d.qpos[3:7])
    return dict(dx=d.qpos[0] - x0, dy=d.qpos[1] - y0, fell=False, worst=worst, t=d.time, yaw=yaw)


p = argparse.ArgumentParser()
p.add_argument("--search", action="store_true")
p.add_argument("--video")
a = p.parse_args()
best_file = os.path.join(HERE, "gait_best.json")

if a.search:
    results = []
    grid = itertools.product([1.5, 2.5, 3.5], [0.25, 0.4], [0.1, 0.25], [0, np.pi / 2, np.pi, 3 * np.pi / 2], [0.0])
    for f, A, B, phi, lean in grid:
        g = dict(f=f, A=A, B=B, phi=phi, lean=lean)
        r = simulate(g, T=6.0)
        score = (abs(r["dx"]) if not r["fell"] else -1) - 0.5 * abs(r["dy"])
        results.append((score, g, r))
        print(f"f={f} A={A} B={B} phi={phi:.2f}: dx={r['dx']*100:+.1f} cm dy={r['dy']*100:+.1f} cm worst tilt {r['worst']:.0f} deg {'FELL' if r['fell'] else ''}", flush=True)
    results.sort(key=lambda x: -x[0])
    s, g, r = results[0]
    g["direction"] = 1 if r["dx"] > 0 else -1
    json.dump(dict(gait=g, result={k: float(v) if not isinstance(v, bool) else v for k, v in r.items()}), open(best_file, "w"), indent=2)
    print("BEST", g, r)

if a.video:
    import imageio.v2 as imageio
    g = json.load(open(best_file))["gait"]
    frames = []
    state = {}

    def grab(m, d):
        if "r" not in state:
            state["r"] = mujoco.Renderer(m, 540, 960)
            cam = mujoco.MjvCamera(); cam.distance = 0.75; cam.azimuth = 120; cam.elevation = -14
            state["cam"] = cam
        cam = state["cam"]; cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.10]
        state["r"].update_scene(d, camera=cam)
        frames.append(state["r"].render())

    r = simulate(g, T=10.0, on_frame=grab, fps=30)
    imageio.mimsave(a.video, frames, fps=30, quality=8, macro_block_size=1)
    print(f"video {a.video}: {len(frames)} frames, dx={r['dx']*100:+.1f} cm, dy={r['dy']*100:+.1f} cm, worst tilt {r['worst']:.0f} deg, fell={r['fell']}")
