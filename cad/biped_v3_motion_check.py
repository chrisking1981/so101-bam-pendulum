"""Sweep every joint of the 8-servo biped (v3) and check that no two links collide.

    uv run --no-project --with trimesh --with manifold3d --with networkx python cad/biped_v3_motion_check.py
"""
import json, itertools
from pathlib import Path
import numpy as np, trimesh

D = Path(__file__).resolve().parent / "biped_v3"
P = json.load(open(D / "biped_v3_params.json"))
L = lambda n: trimesh.load(D / f"{n}.stl")
links = {"torso": [L("torso"), L("servo_roll_l"), L("servo_roll_r")]}
for s in "lr":
    links[f"hip_{s}"] = [L(f"hip_{s}")]
    links[f"thigh_{s}"] = [L(f"thigh_{s}"), L(f"servo_pitch_{s}"), L(f"servo_knee_{s}")]
    links[f"shank_{s}"] = [L(f"shank_{s}"), L(f"servo_ankle_{s}")]
    links[f"foot_{s}"] = [L(f"foot_{s}")]
links = {k: trimesh.boolean.union(v, engine="manifold") if len(v) > 1 else v[0] for k, v in links.items()}
R = lambda ax, a, p: trimesh.transformations.rotation_matrix(np.radians(a), ax, p)


def pose(roll, pitch, knee, ankle, s):
    y = (1 if s == "l" else -1) * P["HY"]
    Th = R([1, 0, 0], roll, [0, y, P["Z_ROLL"]]); Tt = Th @ R([0, 1, 0], pitch, [0, y, P["Z_PITCH"]])
    Ts = Tt @ R([0, 1, 0], knee, [0, y, P["Z_KNEE"]]); Tf = Ts @ R([0, 1, 0], ankle, [0, y, P["Z_ANKLE"]])
    return {"torso": np.eye(4), f"hip_{s}": Th, f"thigh_{s}": Tt, f"shank_{s}": Ts, f"foot_{s}": Tf}


names = ["torso", "hip_{s}", "thigh_{s}", "shank_{s}", "foot_{s}"]
pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
grid = dict(roll=[-30, 0, 30], pitch=[-60, -30, 0, 30, 60], knee=[-10, 0, 30, 60, 90, 110], ankle=[-45, 0, 45])
worst = {}
for s in "lr":
    for combo in itertools.product(*grid.values()):
        T = pose(*combo, s)
        for A, B in pairs:
            A, B = A.format(s=s), B.format(s=s)
            ma = links[A].copy(); ma.apply_transform(T[A]); mb = links[B].copy(); mb.apply_transform(T[B])
            if not (np.all(ma.bounds[1] > mb.bounds[0]) and np.all(mb.bounds[1] > ma.bounds[0])):
                continue
            v = ma.intersection(mb, engine="manifold").volume
            if v > 1.0:
                worst.setdefault(f"{A}/{B}", []).append((*combo, round(float(v), 1)))
for k, v in worst.items():
    print(k, len(v), "colliding poses (roll, pitch, knee, ankle, mm3), e.g.", sorted(v, key=lambda x: -x[-1])[:4])
print("grid:", grid)
if not worst:
    print("no collisions")
json.dump(worst, open(D / "motion_check.json", "w"), indent=1)
