"""Pack the v2 biped meshes (parts + official servo models) for the 3D viewer: cad/biped_v2/viewer/biped.json.

    uv run --no-project --with trimesh --with networkx python cad/biped_v2_viewer_data.py
"""
import json, base64
from pathlib import Path
import numpy as np, trimesh
D = Path(__file__).resolve().parent / "biped_v2"; P = json.load(open(D / "biped_v2_params.json"))
items = []


def add(name, file, color, link):
    m = trimesh.load(D / f"{file}.stl")
    items.append(dict(name=name, color=color, link=link, pos=base64.b64encode(m.vertices.astype(np.float32).tobytes()).decode(),
                      idx=base64.b64encode(m.faces.astype(np.uint32).tobytes()).decode()))


add("Romp", "torso", "#dfe3e8", "torso")
for s, nl in (("l", "links"), ("r", "rechts")):
    add(f"Heupstuk {nl}", f"hip_{s}", "#d2a05a", f"hip_{s}"); add(f"Been {nl}", f"leg_{s}", "#c99a5b", f"leg_{s}")
    add(f"Voet {nl}", f"foot_{s}", "#e07a4f", f"foot_{s}")
    add(f"Servo heup-zijwaarts {nl}", f"servo_roll_{s}", "#3b3f4a", "torso")
    add(f"Servo heup {nl}", f"servo_pitch_{s}", "#3b3f4a", f"leg_{s}")       # hangs in the thigh
    add(f"Servo enkel {nl}", f"servo_ankle_{s}", "#3b3f4a", f"leg_{s}")
(D / "viewer").mkdir(exist_ok=True)
json.dump(dict(parts=items, HY=P["HY"], Z_ROLL=P["Z_ROLL"], Z_PITCH=P["Z_PITCH"], Z_ANKLE=P["Z_ANKLE"]), open(D / "viewer" / "biped.json", "w"))
print("biped.json", round((D / "viewer" / "biped.json").stat().st_size / 1e6, 1), "MB")
