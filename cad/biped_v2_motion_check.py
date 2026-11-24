"""Sweep every joint of the v2 biped over its range and check that no two links (printed parts + the servos they carry) collide.

    uv run --no-project --with trimesh --with manifold3d --with networkx python cad/biped_v2_motion_check.py
"""
import json, itertools
from pathlib import Path
import numpy as np, trimesh

D = Path(__file__).resolve().parent / "biped_v2"
P = json.load(open(D / "biped_v2_params.json"))
parts = {k: trimesh.load(D / f"{k}.stl") for k in ["torso", "hip_l", "hip_r", "leg_l", "leg_r", "foot_l", "foot_r"]}
def servo_mesh(name):
    return trimesh.load(D / f"servo_{name}.stl")
links = {"torso": [parts["torso"], servo_mesh("roll_l"), servo_mesh("roll_r")]}
for s in "lr":
    links[f"hip_{s}"] = [parts[f"hip_{s}"]]                                              # cross bracket only
    links[f"leg_{s}"] = [parts[f"leg_{s}"], servo_mesh(f"pitch_{s}"), servo_mesh(f"ankle_{s}")]  # hip-pitch servo hangs in the leg
    links[f"foot_{s}"] = [parts[f"foot_{s}"]]
links = {k: trimesh.boolean.union(v, engine="manifold") if len(v) > 1 else v[0] for k, v in links.items()}
for k, m in links.items():
    assert m.is_watertight and m.volume > 1000, (k, m.is_watertight, m.volume)


def rot(axis, ang, about):
    T = trimesh.transformations.rotation_matrix(np.radians(ang), axis, about); return T


def pose(roll, pitch, ankle, s):
    y = (1 if s == "l" else -1) * P["HY"]
    Th = rot([1, 0, 0], roll, [0, y, P["Z_ROLL"]])
    Tl = Th @ rot([0, 1, 0], pitch, [0, y, P["Z_PITCH"]])
    Tf = Tl @ rot([0, 1, 0], ankle, [0, y, P["Z_ANKLE"]])
    return {f"hip_{s}": Th, f"leg_{s}": Tl, f"foot_{s}": Tf}


pairs = [("torso", "hip_{s}"), ("torso", "leg_{s}"), ("hip_{s}", "leg_{s}"), ("hip_{s}", "foot_{s}"), ("leg_{s}", "foot_{s}"), ("torso", "foot_{s}")]
worst = {}
grid = dict(roll=[-30, -15, 0, 15, 30], pitch=[-60, -30, 0, 30, 60], ankle=[-45, -20, 0, 20, 45])
for s in "lr":
    for r, p_, a in itertools.product(grid["roll"], grid["pitch"], grid["ankle"]):
        T = pose(r, p_, a, s); T["torso"] = np.eye(4)
        for A, B in pairs:
            A, B = A.format(s=s), B.format(s=s)
            ma = links[A].copy(); ma.apply_transform(T[A]); mb = links[B].copy(); mb.apply_transform(T[B])
            if not (np.all(ma.bounds[1] > mb.bounds[0]) and np.all(mb.bounds[1] > ma.bounds[0])):
                continue
            try:
                v = ma.intersection(mb, engine="manifold").volume
            except Exception:
                v = -1
            if v > 1.0:
                key = f"{A}/{B}"; worst.setdefault(key, []).append((r, p_, a, round(float(v), 1)))
for k, v in worst.items():
    print(k, len(v), "colliding poses, e.g.", sorted(v, key=lambda x: -x[3])[:4])
if not worst:
    print("no collisions over roll +-30, pitch +-60, ankle +-45 (both legs)")
json.dump(worst, open(D / "motion_check.json", "w"), indent=1)
