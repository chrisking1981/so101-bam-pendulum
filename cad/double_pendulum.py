"""Printable two-link pendulum for the step-2a test: servo 1 (on the table) -> upper link -> servo 2 -> lower link with the Nano 33 IoT.

Dimensions come from official models, not guesses:
- STS3215: cad/vendor/STS3215_03a.step from TheRobotStudio/SO-ARM100 (Apache-2.0). In that model the output shaft axis is at
  (x, y) = (12.5, 0); the case is 45.4 x 24.8 mm (x -22.7..22.7, y -12.4..12.4, z -14.4..14.4); the back rests on two pads at z = -17.7 and the
  two bus connectors stick out of the back down to z = -19.4 (x -2.6..15.5, y -8.6..8.6); the horn face is at z = 18.7 with 4 holes on a
  7 mm radius (same pattern as our measuring arms).
- Arduino Nano 33 IoT: official datasheet ABX00027 section 6: board 43.16 x 17.77 mm, header rows 15.24 mm apart (100 mil grid), 15 pins
  per row at 2.54 mm, first and last pin 3.81 mm from the short edges; 4 x 1.65 mm holes 1.26 mm from the edges.

Upper link: hub for servo 1's horn (4 x M3 x 6, 4 mm thick under the heads like BAM-kort-100), 100 mm to servo 2's axis, then a pocket that holds servo 2's case with
0.25 mm clearance, a through window for its connectors (the cable leaves underneath) and two cable-tie slots.
Lower link: hub for servo 2's horn, Nano seat at 60 mm with one 1.4 mm hole per header pin (30), so the board cannot shift or rattle\n(USB toward the joint), two cable-tie slots.

    uv run --no-project --with build123d --with trimesh --with manifold3d python cad/double_pendulum.py
Writes double_pendulum.3mf (both links, print flat), cad/double_pendulum_assembly.stl (with the official servo for checking) and
cad/double_pendulum_params.json (lengths, masses and inertias for the MuJoCo model). Fit checks against the official servo are asserted.
"""
from pathlib import Path
import json
import numpy as np
import build123d as b
import trimesh

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PLA = 1.24e-3        # g/mm^3
# --- horn interface (same as bam_meetarmen.py, printed and used on the bench)
PITCH_R, M3, CENTER = 7.0, 3.4, 6.5
# --- servo, from the official STEP (servo frame)
SHAFT = (12.5, 0.0)
CASE_X, CASE_Y = (-22.7, 22.7), (-12.4, 12.4)
CASE_Z0, BACK_Z = -14.4, -17.7          # case side walls start at CASE_Z0; the back rests on two 0.5 mm pads at z = -17.7
CONN_X, CONN_Y = (-2.6, 15.5), (-8.6, 8.6)
HORN_TOP = 18.7
CLR = 0.25
# Body screws, as on the SO-101 (found in the official SO101 Assembly.step: the small screws run parallel to the servo axis into the two
# holes at the end of the case opposite the shaft, 20.5 mm apart). On the back of the case these holes are at (x, y) = (-20.3, +-10.25)
# and the back surface there is at z = -15.9. Screws come from under the plate; 2.5 mm of plastic under the head, like the SO-101 parts.
BODY_SCREWS = [(-20.3, -10.25), (-20.3, 10.25)]
BACK_AT_SCREWS = -15.9
SCREW_D, HEAD_D, UNDER_HEAD = 2.2, 4.6, 2.5
# --- links
L1, L2, T = 100.0, 80.0, 6.0             # joint-to-joint, joint-to-tip, plate thickness
NANO_R = 60.0                             # Nano centre on the lower link
WALL, WALL_H = 3.0, 16.0                  # pocket walls and their height above the plate
PIN_HOLE = 1.6                            # Nano header pin holes (1.4 printed too tight on the P1S: the pins only went in after widening)


def hub_holes(x0=0.0):
    o = PITCH_R / np.sqrt(2)
    return [(x0, 0, CENTER)] + [(x0 + sx * o, sy * o, M3) for sx in (-1, 1) for sy in (-1, 1)]


HUB_T = 4.0                               # plate thickness under the M3 heads at the horn, as on BAM-kort-100 (M3 x 6 horn screws)


def thin_hub(solid):
    """Same profile as bam_meetarmen.py: a flat 4 mm face under the screw heads out to x = 12, rising to full thickness at x = 28."""
    prof = b.Plane.XZ * b.Polygon((-15, HUB_T), (12, HUB_T), (28, T), (28, T + 30), (-15, T + 30), align=None)
    return solid - b.extrude(prof, amount=30, both=True)


def drill(solid, holes, z0=-1, h=50):
    for x, y, d in holes:
        solid -= b.Pos(x, y, z0) * b.Cylinder(d / 2, h, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    return solid


def upper_link():
    # servo 2 sits with its back on the plate top (z = T); servo frame -> link frame: x_link = L1 + (x_s - 12.5), z_link = T + (z_s - BACK_Z)
    sx = lambda xs: L1 + xs - SHAFT[0]
    px0, px1 = sx(CASE_X[0]) - CLR - WALL, sx(CASE_X[1]) + CLR + WALL
    py = CASE_Y[1] + CLR + WALL
    plate = b.Pos(0, 0, 0) * b.Cylinder(12, T, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    plate += b.Box(px0, 20, T, align=(b.Align.MIN, b.Align.CENTER, b.Align.MIN))
    plate += b.Pos(px0, -py, 0) * b.Box(px1 - px0, 2 * py, T, align=(b.Align.MIN, b.Align.MIN, b.Align.MIN))
    # pocket walls: outer box minus case outline with clearance, from the plate top up WALL_H
    wall_z0 = T
    outer = b.Pos(px0, -py, wall_z0) * b.Box(px1 - px0, 2 * py, WALL_H, align=(b.Align.MIN, b.Align.MIN, b.Align.MIN))
    inner = b.Pos(sx(CASE_X[0]) - CLR, CASE_Y[0] - CLR, wall_z0 - 1) * b.Box(CASE_X[1] - CASE_X[0] + 2 * CLR, CASE_Y[1] - CASE_Y[0] + 2 * CLR, WALL_H + 2,
                                                                          align=(b.Align.MIN, b.Align.MIN, b.Align.MIN))
    part = plate + (outer - inner)
    # window for the connectors and the cable (through the plate)
    part -= b.Pos(sx(CONN_X[0]) - 1.5, CONN_Y[0] - 1.5, -1) * b.Box(CONN_X[1] - CONN_X[0] + 3, CONN_Y[1] - CONN_Y[0] + 3, T + 2,
                                                                      align=(b.Align.MIN, b.Align.MIN, b.Align.MIN))
    # cable-tie slots through the plate, either side of the window (4 x 2 mm), so ties go over the servo case
    for x in (sx(-16.0), sx(19.5)):
        for y in (-py - 2.5, py + 2.5):
            part += b.Pos(x, y, 0) * b.Box(8, 5, T, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
            part -= b.Pos(x, y, -1) * b.Box(4, 2.2, T + 2, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    # body screws: a foot under each hole bridges the gap between plate and case back, counterbored from below
    for xs, ys in BODY_SCREWS:
        foot_h = (BACK_AT_SCREWS - BACK_Z)            # 1.8 mm
        part += b.Pos(sx(xs), ys, T) * b.Cylinder(2.6, foot_h, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        part -= b.Pos(sx(xs), ys, -1) * b.Cylinder(SCREW_D / 2, T + foot_h + 2, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        top = T + foot_h
        part -= b.Pos(sx(xs), ys, -1) * b.Cylinder(HEAD_D / 2, top - UNDER_HEAD + 1, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    part = thin_hub(part)
    part = drill(part, hub_holes(0.0))
    return part


def lower_link(as_built=False):
    """as_built=True: the lower link actually on the bench (printed from commit 32bb5cd): 6 mm hub with the four horn-screw holes
    counterbored by hand (about 5 mm wide, 2 mm deep, so M3 x 6 screws grip the horn) and 1.4 mm pin holes."""
    nano_l, nano_w = 43.16, 17.77
    pad_l = nano_l + 8
    part = b.Cylinder(12, T, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    part += b.Box(L2, 16, T, align=(b.Align.MIN, b.Align.CENTER, b.Align.MIN))
    part += b.Pos(NANO_R, 0, 0) * b.Box(pad_l, nano_w + 10, T, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    part += b.Pos(L2, 0, 0) * b.Cylinder(8, T, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    if as_built:
        part = drill(part, hub_holes(0.0))
        for x, y, d in hub_holes(0.0):
            if d == M3:
                part -= b.Pos(x, y, T - 2.0) * b.Cylinder(2.5, 3.0, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    else:
        part = thin_hub(part)
        part = drill(part, hub_holes(0.0))
    # one hole per header pin: two rows 15.24 apart, 15 pins at 2.54 (first/last 3.81 mm from the board ends).
    # 0.64 mm square pins (0.9 mm diagonal); FDM holes print small. 1.4 mm was too tight in practice, so 1.6 mm.
    for y in (-15.24 / 2, 15.24 / 2):
        for k in range(15):
            x = NANO_R - 43.16 / 2 + 3.81 + 2.54 * k
            part -= b.Pos(x, y, -1) * b.Cylinder((1.4 if as_built else PIN_HOLE) / 2, T + 2, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    # cable-tie slots either side of the board, between the rows ends
    for x in (NANO_R - nano_l / 2 + 2, NANO_R + nano_l / 2 - 2):
        for y in (-(nano_w / 2 + 3), nano_w / 2 + 3):
            part -= b.Pos(x, y, -1) * b.Box(2.2, 4, T + 2, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
    return part


def mesh_of(shape):
    vs, fs = shape.tessellate(0.02)
    return trimesh.Trimesh(np.array([[v.X, v.Y, v.Z] for v in vs]), np.array(fs))


up, lo = upper_link(), lower_link()
assert up.is_valid and lo.is_valid and len(up.solids()) == 1 and len(lo.solids()) == 1

# --- fit check with the official servo placed in the pocket
servo = b.import_step(str(HERE / "vendor" / "STS3215_03a.step"))
servo_in_pocket = b.Pos(L1 - SHAFT[0], -SHAFT[1], T - BACK_Z) * servo
inter = (up & servo_in_pocket)
iv = sum(s.volume for s in inter.solids()) if inter else 0.0
print(f"overlap official servo / upper link: {iv:.3f} mm^3")
assert iv < 0.01, "servo collides with the upper link"
sv = servo_in_pocket.bounding_box()
print(f"servo 2 in pocket: x {sv.min.X:.2f}..{sv.max.X:.2f}, z {sv.min.Z:.2f}..{sv.max.Z:.2f}; its shaft at x = {L1:.1f}")
# the shaft of the placed servo must sit at x = L1
shaft_faces = [f for f in servo_in_pocket.faces() if f.geom_type == b.GeomType.CYLINDER and abs(f.radius - 10.0) < 0.01]
ax = shaft_faces[0].axis_of_rotation.position
assert abs(ax.X - L1) < 0.01 and abs(ax.Y) < 0.01
# horn holes of the placed servo line up with nothing in the plate (they are above it); lower-link hub matches the horn pattern:
horn_holes = sorted({(round(f.axis_of_rotation.position.X - L1, 2), round(f.axis_of_rotation.position.Y, 2)) for f in servo_in_pocket.faces()
                     if f.geom_type == b.GeomType.CYLINDER and abs(f.radius - 1.25) < 0.01 and f.bounding_box().min.Z > 20})
print("servo 2 horn holes relative to its axis:", horn_holes)
# the body-screw holes of the link line up with the servo's own holes (r = 0.75 on its back)
back_holes = sorted({(round(f.axis_of_rotation.position.X, 2), round(f.axis_of_rotation.position.Y, 2)) for f in servo_in_pocket.faces()
                     if f.geom_type == b.GeomType.CYLINDER and abs(f.radius - 0.75) < 0.01 and f.bounding_box().max.Z < T + 5})
want = [(round(L1 + xs - SHAFT[0], 2), ys) for xs, ys in BODY_SCREWS]
print("servo back holes:", back_holes, " link screw holes:", want)
assert all(min(abs(bx - wx) + abs(by - wy) for bx, by in back_holes) < 0.05 for wx, wy in want), "body screws miss the servo holes"
hub = sorted((round(x, 2), round(y, 2)) for x, y, d in hub_holes(0.0) if d == M3)
assert all(min(abs(hx - x) + abs(hy - y) for x, y in hub) < 0.05 for hx, hy in horn_holes), "hub pattern does not match the horn"

# hub thickness under the horn screws: 4 mm on both links (M3 x 6 screws need it, as on the measuring arms)
for name, part in (("upper", up), ("lower", lo)):
    m_ = mesh_of(part) if 'mesh_of' in globals() else None
    hub_top = max(v.Z for v in part.vertices() if (v.X ** 2 + v.Y ** 2) ** 0.5 < 11.5)
    print(f"{name} link: hub thickness at the horn screws {hub_top:.2f} mm")
    assert abs(hub_top - HUB_T) < 0.01, "hub must be 4 mm under the M3 heads"

# --- outputs
mu, ml = mesh_of(up), mesh_of(lo)
for name, m in (("upper", mu), ("lower", ml)):
    assert m.is_watertight
    print(f"{name} link: {m.extents.round(1)} mm, volume {m.volume:.0f} mm3, mass at 100% infill {m.volume * PLA:.1f} g")
scene = trimesh.Scene()
scene.add_geometry(mu, node_name="upper_link", geom_name="upper_link")
ml2 = ml.copy(); ml2.apply_translation([0, 50, 0])
scene.add_geometry(ml2, node_name="lower_link", geom_name="lower_link")
scene.export(REPO / "double_pendulum.3mf")
ms = mesh_of(servo_in_pocket)
asm = trimesh.util.concatenate([mu, ms, ml.copy().apply_translation([L1, 0, T - BACK_Z + HORN_TOP])])
asm.export(HERE / "double_pendulum_assembly.stl")


def inertia_about_axis(m, axis_xy, mass):
    """Inertia (kg m^2) about a z axis through axis_xy, for a part of given mass (g) with the mesh's shape (uniform density)."""
    mm = m.copy(); mm.apply_translation([-axis_xy[0], -axis_xy[1], 0]); mm.density = mass / mm.volume
    return float(mm.moment_inertia[2, 2]) * 1e-9, (mm.center_mass[:2] * 1e-3).tolist()


lo_built = lower_link(as_built=True); mlb = mesh_of(lo_built)
mlb.export(HERE / "lower_link_as_built.stl")
print(f"lower link as built: volume {mlb.volume:.0f} mm3, mass at 100% infill {mlb.volume * PLA:.1f} g (written to cad/lower_link_as_built.stl)")
params = dict(L1_m=L1 / 1000, L2_m=L2 / 1000, nano_r_m=NANO_R / 1000, servo_mass_g=55.0, nano_mass_g=5.5,
              upper_link_volume_mm3=float(mu.volume), lower_link_volume_mm3=float(ml.volume), lower_link_as_built_volume_mm3=float(mlb.volume),
              servo2_axis_height_above_link1_bottom_mm=T - BACK_Z + HORN_TOP,
              as_built={"lower_link": "commit 32bb5cd: 6 mm hub; 4 horn-screw holes counterbored by hand (~5 mm, 2 mm deep) so M3x6 "
                                      "screws grip; 1.4 mm pin holes widened by hand. Modelled by lower_link(as_built=True) -> cad/lower_link_as_built.stl",
                        "upper_link": "current version (4 mm hub, body screws)", "masses_g": "to be weighed"},
              note="link masses depend on infill: weigh the printed parts and put the real values here")
json.dump(params, open(HERE / "double_pendulum_params.json", "w"), indent=1)
# the 30 pin holes sit exactly on the datasheet grid
pin_x = [NANO_R - 43.16 / 2 + 3.81 + 2.54 * k for k in range(15)]
assert abs(pin_x[0] - (NANO_R - 43.16 / 2 + 3.81)) < 1e-9 and abs(pin_x[-1] - (NANO_R + 43.16 / 2 - 3.79)) < 0.05
print(f"Nano pin holes: 2 x 15, x {pin_x[0]:.2f}..{pin_x[-1]:.2f} mm, rows at y = +-7.62 mm, diameter {PIN_HOLE} mm")
print("wrote double_pendulum.3mf, cad/double_pendulum_assembly.stl, cad/double_pendulum_params.json")

# --- Bambu Studio per-object settings: sturdy, and a known infill so the printed mass is predictable (weigh the parts anyway)
import zipfile, shutil, tempfile
path = REPO / "double_pendulum.3mf"
cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
for i, name in enumerate(["upper_link", "lower_link"], start=1):
    cfg += [f'  <object id="{i}">', f'    <metadata key="name" value="{name}"/>', '    <metadata key="extruder" value="1"/>',
            '    <metadata key="sparse_infill_density" value="40%"/>', '    <metadata key="wall_loops" value="4"/>',
            f'    <part id="{i}" subtype="normal_part">', f'      <metadata key="name" value="{name}"/>', '    </part>', '  </object>']
cfg.append('</config>')
tmp = Path(tempfile.mkstemp(suffix=".3mf")[1])
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename != "Metadata/model_settings.config":
            zout.writestr(item, zin.read(item.filename))
    zout.writestr("Metadata/model_settings.config", "\n".join(cfg) + "\n")
shutil.move(tmp, path)
print("print settings: 40% infill, 4 walls, both parts flat on the plate")
