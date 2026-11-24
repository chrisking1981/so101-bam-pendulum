"""Lay the v2 biped parts flat for printing and write biped_v2.3mf (Bambu Studio, 40 % infill, 4 walls, supports on where needed).

    uv run --no-project --with trimesh --with networkx --with lxml python cad/biped_v2_print.py
"""
from pathlib import Path
import numpy as np, trimesh, zipfile, shutil, tempfile
D = Path(__file__).resolve().parent / "biped_v2"; REPO = D.parent.parent
R = trimesh.transformations.rotation_matrix
orient = {  # rotation that puts the biggest flat face on the bed
    "torso": R(np.pi, [1, 0, 0]),                 # deck down
    "hip_l": R(-np.pi / 2, [0, 1, 0]), "hip_r": R(-np.pi / 2, [0, 1, 0]),   # front roll plate down
    "leg_l": R(np.pi / 2, [1, 0, 0]), "leg_r": R(-np.pi / 2, [1, 0, 0]),    # outer side plate down
    "foot_l": np.eye(4), "foot_r": np.eye(4),     # sole down
}
support = {"torso": 1, "hip_l": 1, "hip_r": 1, "leg_l": 1, "leg_r": 1, "foot_l": 0, "foot_r": 0}
scene = trimesh.Scene(); x = 0.0; y = 0.0; row_h = 0.0
for i, (k, T) in enumerate(orient.items()):
    m = trimesh.load(D / f"{k}.stl"); m.apply_transform(T); m.apply_translation(-m.bounds[0])
    if x + m.extents[0] > 240:
        x = 0.0; y += row_h + 8; row_h = 0.0
    m.apply_translation([x, y, 0]); x += m.extents[0] + 8; row_h = max(row_h, m.extents[1])
    scene.add_geometry(m, node_name=k, geom_name=k)
path = REPO / "biped_v2.3mf"; scene.export(path)
cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
for i, k in enumerate(orient, start=1):
    cfg += [f'  <object id="{i}">', f'    <metadata key="name" value="{k}"/>', '    <metadata key="extruder" value="1"/>',
            '    <metadata key="sparse_infill_density" value="40%"/>', '    <metadata key="wall_loops" value="4"/>',
            f'    <metadata key="enable_support" value="{support[k]}"/>',
            f'    <part id="{i}" subtype="normal_part">', f'      <metadata key="name" value="{k}"/>', '    </part>', '  </object>']
cfg.append('</config>')
tmp = Path(tempfile.mkstemp(suffix=".3mf")[1])
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename != "Metadata/model_settings.config":
            zout.writestr(item, zin.read(item.filename))
    zout.writestr("Metadata/model_settings.config", "\n".join(cfg) + "\n")
shutil.move(tmp, path)
print("wrote", path, "plate extent", np.round(scene.bounds[1] - scene.bounds[0], 0))
