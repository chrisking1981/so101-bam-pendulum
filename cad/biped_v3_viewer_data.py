"""Pack the v3 (8-servo) biped meshes for the 3D viewer: cad/biped_v3/viewer/biped.json."""
import json, base64
from pathlib import Path
import numpy as np, trimesh
D = Path(__file__).resolve().parent / "biped_v3"; P = json.load(open(D / "biped_v3_params.json"))
items = []


def add(name, file, color, link):
    m = trimesh.load(D / f"{file}.stl")
    items.append(dict(name=name, color=color, link=link, pos=base64.b64encode(m.vertices.astype(np.float32).tobytes()).decode(),
                      idx=base64.b64encode(m.faces.astype(np.uint32).tobytes()).decode()))


add("Romp", "torso", "#dfe3e8", "torso")
for s, nl in (("l", "links"), ("r", "rechts")):
    add(f"Heupstuk {nl}", f"hip_{s}", "#d2a05a", f"hip_{s}"); add(f"Bovenbeen {nl}", f"thigh_{s}", "#c99a5b", f"thigh_{s}")
    add(f"Onderbeen {nl}", f"shank_{s}", "#b98a4d", f"shank_{s}"); add(f"Voet {nl}", f"foot_{s}", "#e07a4f", f"foot_{s}")
    add(f"Servo heup-zijwaarts {nl}", f"servo_roll_{s}", "#3b3f4a", "torso")
    add(f"Servo heup {nl}", f"servo_pitch_{s}", "#3b3f4a", f"thigh_{s}")
    add(f"Servo knie {nl}", f"servo_knee_{s}", "#3b3f4a", f"thigh_{s}")
    add(f"Servo enkel {nl}", f"servo_ankle_{s}", "#3b3f4a", f"shank_{s}")
json.dump(dict(parts=items, HY=P["HY"], Z_ROLL=P["Z_ROLL"], Z_PITCH=P["Z_PITCH"], Z_KNEE=P["Z_KNEE"], Z_ANKLE=P["Z_ANKLE"]),
          open(D / "viewer" / "biped.json", "w"))
print("biped.json", round((D / "viewer" / "biped.json").stat().st_size / 1e6, 1), "MB")
