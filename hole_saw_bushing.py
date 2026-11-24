"""Centring bushing for mounting hole saws as pendulum weights on the printed arm.

A hole saw's 15 mm arbor hole is centred on an M4 load hole of the arm, so the saw's centre of mass sits exactly on that hole.
- Outer diameter 14.7 mm: slip fit in the 15 mm arbor hole (0.3 mm clearance).
- Height 4.6 mm: just below the 5 mm thick saw base, so the M4 bolt clamps the saw itself (not the bushing) against the arm.
  For two nested saws use one bushing per saw.
- M4 clearance hole 4.4 mm.
Writes hole_saw_bushing.3mf with two bushings on the plate (one per saw), each set to 100% infill and 3 walls for Bambu Studio.

    uv run python hole_saw_bushing.py
"""
from pathlib import Path
import trimesh
from trimesh.creation import cylinder

OUT = Path(__file__).resolve().parent
OD, H, HOLE = 14.7, 4.6, 4.4


def bushing():
    outer = cylinder(radius=OD / 2, height=H, sections=96)
    inner = cylinder(radius=HOLE / 2, height=H + 2, sections=64)
    b = outer.difference(inner)
    b.apply_translation([0, 0, H / 2])          # sit on the plate
    return b


parts = []
for i, x in enumerate([-12.0, 12.0]):
    p = bushing(); p.apply_translation([x, 0, 0]); parts.append(p)
scene = trimesh.Scene()
for i, p in enumerate(parts):
    assert p.is_watertight and p.is_volume
    scene.add_geometry(p, node_name=f"bushing_{i + 1}", geom_name=f"bushing_{i + 1}")
path = OUT / "hole_saw_bushing.3mf"
scene.export(path)

# Per-object print settings for Bambu Studio: 100% infill for both bushings (small, loaded parts).
import zipfile, shutil, tempfile
cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
for i in range(1, len(parts) + 1):
    cfg += [f'  <object id="{i}">',
            f'    <metadata key="name" value="bushing_{i}"/>',
            '    <metadata key="extruder" value="1"/>',
            '    <metadata key="sparse_infill_density" value="100%"/>',
            '    <metadata key="sparse_infill_pattern" value="zig-zag"/>',   # Bambu's name for rectilinear (grid cannot do 100%)
            '    <metadata key="wall_loops" value="3"/>',
            f'    <part id="{i}" subtype="normal_part">',
            f'      <metadata key="name" value="bushing_{i}"/>',
            '    </part>',
            '  </object>']
cfg.append('</config>')
tmp = Path(tempfile.mkstemp(suffix=".3mf")[1])
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        zout.writestr(item, zin.read(item.filename))
    zout.writestr("Metadata/model_settings.config", "\n".join(cfg) + "\n")
shutil.move(tmp, path)
b = parts[0]
print(f"{path}: 2 bushings, OD {OD} mm, height {H} mm, M4 hole {HOLE} mm, volume {b.volume:.0f} mm3 each, extents {b.extents.round(2)}")
