"""Eight-servo biped, version 3: the v2 parts plus a knee (per leg hip roll, hip pitch, knee, ankle pitch), SO-101 style.
Thigh: holds the hip-pitch servo (upside down, top) and the knee servo (bottom). Shank: clevis on both knee horns, holds the ankle
servo. Torso, hip cross bracket and foot as in v2.

Every joint sits in a clevis that is screwed to BOTH horns of its servo (front metal horn and back metal horn, 4 x M3 each, 4 mm plate
under the heads like the measuring arms). The next servo stands upright in that clevis and is held at the end of its case opposite the
shaft with four small screws (two in the back holes, two in the front holes), as the SO-101 holds its servos. Because each held servo
stands with its far end away from the next joint, the next clevis cannot swing into the holder.

Sources (cad/vendor, see cad/README.md):
- STS3215 STEP (SO-ARM100): case 45.4 x 24.8 mm, shaft at S(12.5, 0); back screw holes S(-20.3, +-10.25) on the back face z = -15.9,
  front screw holes S(-16.5, +-10.25) on the front face z = +15.9; back pads to z = -17.7, front cap to z = +17.2;
  connectors on the back at S.x -2.6..-0.5 (out to z = -19.4).
- SO101 Assembly.step: the outer faces of the front and back horns of one servo are 37.48 mm apart; front horn face at S.z = 19.44,
  back horn face at S.z = -18.04 (front horn 4.7 mm, back horn 3.5 mm, case 35.7 mm).

World frame, robot standing, all joints at zero: x forward, y left, z up, ground at z = 0. Lengths in mm.

    uv run --no-project --with build123d --with trimesh --with manifold3d --with lxml --with networkx python cad/biped_v2.py
"""
from pathlib import Path
import json
import numpy as np
import build123d as b
import trimesh

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "biped_v3"; OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- servo data (S frame of the official STEP)
SHAFT_X = 12.5
FRONT_HORN, BACK_HORN = 19.44, -18.04
CASE = dict(x=(-22.7, 22.7), y=(-12.4, 12.4), zf=17.2, zb=-17.7)
BACK_HOLES, FRONT_HOLES = [(-20.3, -10.25), (-20.3, 10.25)], [(-16.5, -10.25), (-16.5, 10.25)]
BACK_AT_HOLES, FRONT_AT_HOLES = -15.9, 15.9
CLR = 0.25
# ---------------------------------------------------------------- design choices
HY = 35.0                     # half hip width (servo axes at y = +-35)
Z_ANKLE, L_SHANK, L_THIGH, H_HIP = 22.0, 60.0, 80.0, 39.0
Z_KNEE = Z_ANKLE + L_SHANK    # 82
Z_PITCH = Z_KNEE + L_THIGH    # 162
Z_ROLL = Z_PITCH + H_HIP      # 201
PLATE, WALL, HUB_R = 4.0, 3.0, 12.5
M3, M3_CENTER, PITCH_R = 3.4, 6.5, 7.0
M2_CLEAR, M2_HEAD, UNDER_HEAD = 2.2, 4.6, 2.5
HOLD_FROM = -6.0              # holders grip the case from its far end (S.x -22.7) to S.x = -6 (connectors start at -2.6)


class Servo:
    """A servo placed in the world: ez = world direction of S.z (front horn), ex = world direction of S.x, p = shaft point."""
    def __init__(self, name, p, ez, ex):
        self.name, self.p = name, np.array(p, float)
        self.ez, self.ex = np.array(ez, float), np.array(ex, float)
        self.ey = np.cross(self.ez, self.ex)

    def w(self, sx, sy, sz):
        return self.p + (sx - SHAFT_X) * self.ex + sy * self.ey + sz * self.ez

    def location(self):
        R = np.column_stack([self.ex, self.ey, self.ez])
        t = self.p - SHAFT_X * self.ex
        return b.Location(b.Plane(origin=tuple(t), x_dir=tuple(R[:, 0]), z_dir=tuple(R[:, 2])))


def box(x0, x1, y0, y1, z0, z1):
    return b.Pos(min(x0, x1), min(y0, y1), min(z0, z1)) * b.Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), align=(b.Align.MIN,) * 3)


def cyl(center, axis, r, a0, a1):
    """Cylinder of radius r along unit axis from center + a0*axis to center + a1*axis."""
    axis = np.array(axis, float); c = np.array(center, float) + a0 * axis
    return b.Solid.make_cylinder(r, a1 - a0, b.Plane(origin=tuple(c), z_dir=tuple(axis)))


def horn_plate(sv, face, outward, thick, extra):
    """Disc plate on one horn of servo sv (face = S.z of the horn face, outward = +1/-1 along ez), union with `extra` (arm),
    with the 4 x M3 horn pattern and centre hole."""
    n = sv.ez * outward
    c = sv.w(SHAFT_X, 0, face)
    disc = cyl(c, n, HUB_R, 0, thick)
    part = disc + extra
    return part


def horn_holes(sv, face, outward):
    n = sv.ez * outward; c = sv.w(SHAFT_X, 0, face)
    o = PITCH_R / np.sqrt(2)
    cut = cyl(c, n, M3_CENTER / 2, -1, 30)
    for a in (-1, 1):
        for bb in (-1, 1):
            p = sv.w(SHAFT_X + a * o, bb * o, face)
            cut += cyl(p, n, M3 / 2, -1, 30)
    return cut


def holder(sv, x_lo=HOLD_FROM):
    """SO-101-style holder around the far end of servo sv's case: back plate, front plate, end wall, two side walls,
    with 4 screw feet. Returns (solid, cut) in world coordinates."""
    xs0, xs1 = CASE["x"][0] - CLR - WALL, x_lo                     # along S.x
    ys0, ys1 = CASE["y"][0] - CLR - WALL, CASE["y"][1] + CLR + WALL
    zb_in, zf_in = CASE["zb"] - CLR, CASE["zf"] + CLR               # inner faces of the back / front plates
    loc = sv.location()
    back = loc * box(xs0, xs1, ys0, ys1, zb_in - WALL, zb_in)
    front = loc * box(xs0, xs1, ys0, ys1, zf_in, zf_in + WALL)
    end = loc * box(xs0, CASE["x"][0] - CLR, ys0, ys1, zb_in - WALL, zf_in + WALL)
    side = loc * box(xs0, xs1, ys0, CASE["y"][0] - CLR, zb_in - WALL, zf_in + WALL) + loc * box(xs0, xs1, CASE["y"][1] + CLR, ys1, zb_in - WALL, zf_in + WALL)
    solid = back + front + end + side
    cut = None
    for (hx, hy), z_case, z_in, sgn in [(h, BACK_AT_HOLES, zb_in, -1) for h in BACK_HOLES] + [(h, FRONT_AT_HOLES, zf_in, +1) for h in FRONT_HOLES]:
        # foot from the plate to the case surface at the hole
        foot = loc * b.Pos(hx, hy, min(z_case, z_in)) * b.Cylinder(2.6, abs(z_in - z_case), align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        solid += foot
        outer = z_in + sgn * WALL
        hole = loc * b.Pos(hx, hy, min(z_case, outer) - 1) * b.Cylinder(M2_CLEAR / 2, abs(outer - z_case) + 2, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        cb_len = abs(outer - z_case) - UNDER_HEAD
        cb_z0 = outer - sgn * cb_len if sgn > 0 else outer - 1
        cbore = loc * b.Pos(hx, hy, min(outer, outer - sgn * cb_len) - (1 if sgn < 0 else 0)) * b.Cylinder(M2_HEAD / 2, cb_len + 1, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        cut = hole + cbore if cut is None else cut + hole + cbore
    return solid, cut


# ---------------------------------------------------------------- servo placement
servos = {}
for side, s in (("l", 1), ("r", -1)):
    servos[f"roll_{side}"] = Servo(f"roll_{side}", (0, s * HY, Z_ROLL), ez=(1, 0, 0), ex=(0, 0, -1))      # body up, horns front/back
    servos[f"pitch_{side}"] = Servo(f"pitch_{side}", (0, s * HY, Z_PITCH), ez=(0, s, 0), ex=(0, 0, 1))   # body DOWN in the thigh, front horn outward
    servos[f"knee_{side}"] = Servo(f"knee_{side}", (0, s * HY, Z_KNEE), ez=(0, s, 0), ex=(0, 0, -1))      # body UP in the thigh
    servos[f"ankle_{side}"] = Servo(f"ankle_{side}", (0, s * HY, Z_ANKLE), ez=(0, s, 0), ex=(0, 0, -1))


def clevis(sv, down_to, joiner):
    """Two horn plates on servo sv (front and back horn), each extended down (along world -z) to z = down_to, joined by `joiner`."""
    parts = None
    for face, out in ((FRONT_HORN, 1), (BACK_HORN, -1)):
        n = sv.ez * out; c = sv.w(SHAFT_X, 0, face)
        disc = cyl(c, n, HUB_R, 0, PLATE)
        # arm from the hub down to down_to, width 2*HUB_R across
        p0 = c + n * 0; lat = np.cross(n, [0, 0, 1]); lat /= np.linalg.norm(lat)
        corners = [p0 + lat * HUB_R, p0 - lat * HUB_R]
        xs = [q[0] for q in corners] + [q[0] + n[0] * PLATE for q in corners]
        ys = [q[1] for q in corners] + [q[1] + n[1] * PLATE for q in corners]
        arm = box(min(xs), max(xs), min(ys), max(ys), down_to, c[2])
        plate = disc + arm
        parts = plate if parts is None else parts + plate
    return parts + joiner


def finish(solid, cuts):
    for c in cuts:
        if c is not None:
            solid -= c
    return solid


# ---------------------------------------------------------------- electronics on top, cable clips
TORSO_X = (CASE["zb"] - CLR - WALL, CASE["zf"] + CLR + WALL)          # torso box front-back (x)
TORSO_YW = HY + CASE["y"][1] + CLR + WALL                              # torso half width
TORSO_TOP = Z_ROLL + (SHAFT_X - CASE["x"][0]) + CLR + WALL             # top of the deck
RACK_H, RACK_T = 12.0, 6.0          # rack: 12 mm pillars over the Nano, 6 mm top with the two dovetail sockets
RACK_TOP = TORSO_TOP + RACK_H + RACK_T
PLATE_Y = 25.8                      # the two SO-101 board plates (51 x 42) side by side, centres at y = +-25.8
KEY = dict(narrow=16.0, wide=18.2, depth=3.6)   # square dovetail key under the SO-101 mounting plate (measured from the STL)
DECK_M3 = [(xx, yy) for xx in (TORSO_X[0] + 5, TORSO_X[1] - 5) for yy in (-TORSO_YW + 6, TORSO_YW - 6)]
CABLE_D = 3.5                       # bore of the cable clips (servo cable about 3 mm)


def make_rack():
    """Board rack: screwed on the four M3 holes of the torso deck on 12 mm pillars (the Nano stays underneath), with two dovetail
    sockets that take the SO-101 board mounting plate (Seeed or WaveShare version) sliding in from the back, as on the SO-101 base."""
    x0, x1 = TORSO_X
    sol = box(x0, x1, -TORSO_YW, TORSO_YW, TORSO_TOP + RACK_H, RACK_TOP)
    cuts = [box(-9, 9, -TORSO_YW + 14, TORSO_YW - 14, TORSO_TOP + RACK_H - 1, RACK_TOP - KEY["depth"] - 1.2)]   # lighten the middle
    for (xx, yy) in DECK_M3:
        sol += cyl((xx, yy, TORSO_TOP), (0, 0, 1), 4.0, 0, RACK_H + 0.5)
        cuts.append(cyl((xx, yy, TORSO_TOP - 1), (0, 0, 1), M3 / 2, 0, RACK_H + RACK_T + 2))
        cuts.append(cyl((xx, yy, RACK_TOP - 2.5), (0, 0, 1), 3.2, 0, 3))                 # head counterbore
    c = 0.2
    for yc in (-PLATE_Y, PLATE_Y):
        # dovetail channel along x, open at the back (-x), stop at the front edge of the key
        prof = b.Polygon((yc - KEY["narrow"] / 2 - c, RACK_TOP + 0.01), (yc + KEY["narrow"] / 2 + c, RACK_TOP + 0.01),
                         (yc + KEY["wide"] / 2 + c, RACK_TOP - KEY["depth"] - c), (yc - KEY["wide"] / 2 - c, RACK_TOP - KEY["depth"] - c), align=None)
        length = (KEY["wide"] / 2 + c) - (x0 - 1)
        ch = b.extrude(b.Plane.YZ.offset(x0 - 1) * prof, amount=length)
        cuts.append(ch)
    return finish(sol, cuts)


def clip(p, n, z_len=7.0):
    """Cable clip on a flat face: p = point on the face, n = outward normal (+-x or +-y). A ring around a vertical cable with a 2.6 mm
    mouth so the cable clicks in, on a 1.6 mm pad, like the cable clips moulded on the SO-101 arm parts."""
    p, n = np.array(p, float), np.array(n, float); t = np.array([-n[1], n[0], 0.0])        # t: along the face, horizontal
    r_in, r_out, pad = CABLE_D / 2, CABLE_D / 2 + 1.3, 1.6
    cen = p + n * (pad + r_in + 0.2)
    corners = [p - t * 4, p + t * 4, p - t * 4 + n * pad, p + t * 4 + n * pad]
    xs, ys = [q[0] for q in corners], [q[1] for q in corners]
    body = box(min(xs), max(xs), min(ys), max(ys), p[2] - z_len / 2, p[2] + z_len / 2) + cyl(cen, (0, 0, 1), r_out, -z_len / 2, z_len / 2)
    body -= cyl(cen, (0, 0, 1), r_in, -z_len, z_len)
    m0, m1 = cen + n * 0.5 - t * 1.3, cen + n * (r_out + 1) + t * 1.3
    body -= box(min(m0[0], m1[0]), max(m0[0], m1[0]), min(m0[1], m1[1]), max(m0[1], m1[1]), p[2] - z_len, p[2] + z_len)
    return body


def clip_spots(side):
    """Where the clips sit (point on the face, outward normal), per link."""
    s = 1 if side == "l" else -1
    thigh_in = s * (HY + CASE["zb"] - CLR - WALL)            # inner face of the thigh's back plate
    shank_in = s * (HY + BACK_HORN - PLATE)                  # inner face of the shank's back clevis plate
    return {"thigh": [((-7.0, thigh_in, 122.0), (0, -s, 0))],
            "shank": [((-7.0, shank_in, 64.0), (0, -s, 0))]}


TORSO_CLIPS = [((TORSO_X[0], yy, TORSO_TOP - 9.0), (-1, 0, 0)) for yy in (-30.0, -13.0, 13.0, 30.0)]


# ---------------------------------------------------------------- parts
def make_torso():
    """A closed box around the far ends of both hip-roll servos: front and back plates over the full width, deck on top with the
    Nano seat and four M3 holes for a head or extra weight, a bottom between the servos with two cable holes."""
    sol, cuts = None, []
    for side in "lr":
        h, c = holder(servos[f"roll_{side}"]); sol = h if sol is None else sol + h; cuts.append(c)
    xf0, xf1 = CASE["zf"] + CLR, CASE["zf"] + CLR + WALL            # front plate (roll servo front face looks along +x)
    xb0, xb1 = CASE["zb"] - CLR - WALL, CASE["zb"] - CLR             # back plate
    yw = HY + CASE["y"][1] + CLR + WALL
    z_lo = Z_ROLL + (SHAFT_X - (HOLD_FROM)) - 0.0                    # holders start 18.5 above the roll axis
    z_hi = Z_ROLL + (SHAFT_X - CASE["x"][0]) + CLR + WALL            # top of the holder end walls
    sol += box(xf0, xf1, -yw, yw, z_lo, z_hi) + box(xb0, xb1, -yw, yw, z_lo, z_hi)
    sol += box(xb0, xf1, -yw, yw, z_hi - WALL, z_hi)                                      # deck
    yin = HY - CASE["y"][1] - CLR - WALL
    sol += box(xb0, xf1, -yin, yin, z_lo, z_lo + WALL)                                     # bottom between the servos
    for yy in (-9.0, 9.0):                                                                  # cable holes in the bottom
        cuts.append(cyl((0, yy, z_lo - 1), (0, 0, 1), 5.0, 0, WALL + 2))
    for yy in (-7.62, 7.62):                                                                # Nano: one hole per header pin
        for k in range(15):
            xx = -43.16 / 2 + 3.81 + 2.54 * k
            cuts.append(box(xx - 0.8, xx + 0.8, yy - 0.8, yy + 0.8, z_hi - WALL - 1, z_hi + 1))
    for xx in (xb0 + 5, xf1 - 5):                                                           # M3 holes for a head / extra weight
        for yy in (-yw + 6, yw - 6):
            cuts.append(cyl((xx, yy, z_hi - WALL - 1), (0, 0, 1), M3 / 2, 0, WALL + 2))
    sol = finish(sol, cuts)
    for p, n in TORSO_CLIPS:
        sol += clip(p, n)
    return sol


def make_hip(side):
    """Cross bracket: one clevis on the hip-roll horns (plates across x), one on the hip-pitch horns (plates across y), joined by a
    frame plate between the two axes. The hip-pitch servo body hangs down in the leg, so no holder can swing into anything here."""
    roll, pitch = servos[f"roll_{side}"], servos[f"pitch_{side}"]
    s = 1 if side == "l" else -1
    z_frame0, z_frame1 = Z_ROLL - 21.0, Z_ROLL - 17.0          # below the roll servo case sweep, above the pitch servo case sweep
    ys = [s * HY + s * (BACK_HORN - PLATE), s * HY + s * (FRONT_HORN + PLATE)]
    frame = box(BACK_HORN - PLATE, FRONT_HORN + PLATE, min(ys), max(ys), z_frame0, z_frame1)
    body = clevis(roll, z_frame0, frame) + clevis(pitch, z_frame1, frame)
    return finish(body, [horn_holes(roll, FRONT_HORN, 1), horn_holes(roll, BACK_HORN, -1),
                         horn_holes(pitch, FRONT_HORN, 1), horn_holes(pitch, BACK_HORN, -1)])


def make_thigh(side):
    """Holds the hip-pitch servo (far end down) at the top and the knee servo (far end up) at the bottom."""
    pitch, knee = servos[f"pitch_{side}"], servos[f"knee_{side}"]
    hp, cp = holder(pitch); hk, ck = holder(knee)
    s = 1 if side == "l" else -1
    xw = CASE["y"][1] + CLR + WALL
    z0, z1 = Z_KNEE + (SHAFT_X - CASE["x"][0]) - 17.0, Z_PITCH - (SHAFT_X - CASE["x"][0]) + 17.0
    body = hp + hk
    for face, sgn in ((CASE["zf"] + CLR, 1), (CASE["zb"] - CLR, -1)):
        yy = [s * HY + s * face, s * HY + s * (face + sgn * WALL)]
        body += box(-xw, xw, min(yy), max(yy), z0, z1)
    body = finish(body, [cp, ck])
    for p, n in clip_spots(side)["thigh"]:
        body += clip(p, n)
    return body


def make_shank(side):
    """Clevis on both knee horns, down to a holder for the ankle servo (far end up)."""
    knee, ankle = servos[f"knee_{side}"], servos[f"ankle_{side}"]
    h, hc = holder(ankle)
    z_top_ankle = Z_ANKLE + (SHAFT_X - CASE["x"][0]) + CLR + WALL
    s = 1 if side == "l" else -1
    yo = [s * HY + s * FRONT_HORN, s * HY + s * (FRONT_HORN + PLATE)]
    yi = [s * HY + s * BACK_HORN, s * HY + s * (BACK_HORN - PLATE)]
    body = clevis(knee, Z_ANKLE + 18.5, h)
    for ys, face in ((yo, CASE["zf"] + CLR), (yi, CASE["zb"] - CLR)):
        yy = ys + [s * HY + s * face]
        body += box(-HUB_R, HUB_R, min(yy), max(yy), Z_ANKLE + 18.5, z_top_ankle)
    body = finish(body, [hc, horn_holes(knee, FRONT_HORN, 1), horn_holes(knee, BACK_HORN, -1),
                         ankle.location() * box(CASE["x"][0] - CLR, HOLD_FROM + 2, CASE["y"][0] - CLR, CASE["y"][1] + CLR, CASE["zb"] - CLR, CASE["zf"] + CLR)])
    for p, n in clip_spots(side)["shank"]:
        body += clip(p, n)
    return body


def make_foot(side):
    ankle = servos[f"ankle_{side}"]
    s = 1 if side == "l" else -1
    sole = box(-45, 60, s * HY - 26, s * HY + 26, 0, 4)
    foot = clevis(ankle, 2, sole)
    return finish(foot, [horn_holes(ankle, FRONT_HORN, 1), horn_holes(ankle, BACK_HORN, -1)])


parts = {"torso": make_torso(), "rack": make_rack()}
for side in "lr":
    parts[f"hip_{side}"] = make_hip(side); parts[f"thigh_{side}"] = make_thigh(side)
    parts[f"shank_{side}"] = make_shank(side); parts[f"foot_{side}"] = make_foot(side)
for k, v in parts.items():
    assert v.is_valid, k
    print(f"{k:8s} solids {len(v.solids())}  volume {v.volume:7.0f} mm3  bbox {np.round([v.bounding_box().size.X, v.bounding_box().size.Y, v.bounding_box().size.Z], 1)}")

# ---------------------------------------------------------------- fit checks against the official servo model
step = b.import_step(str(HERE / "vendor" / "STS3215_03a.step"))
# the STEP has a simplified front horn (2.5 mm) and no back horn; the real horns are thicker, so remove the STEP horn for the check
horn_cut = b.Pos(SHAFT_X, 0, 16.2) * b.Cylinder(10.5, 5, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
step_case = step - horn_cut
placed = {k: sv.location() * step_case for k, sv in servos.items()}
report = {}
for pk, part in parts.items():
    for sk, sv in placed.items():
        inter = part & sv
        v = sum(s.volume for s in inter.solids()) if inter else 0.0
        if v > 0.05:
            report[f"{pk} x {sk}"] = round(v, 2)
print("overlaps > 0.05 mm3:", report if report else "none")
json.dump(report, open(OUT / "fit_report.json", "w"), indent=1)

# ---------------------------------------------------------------- outputs
def mesh_of(shape, tol=0.05):
    vs, fs = shape.tessellate(tol)
    m = trimesh.Trimesh(np.array([[v.X, v.Y, v.Z] for v in vs]), np.array(fs))
    m.merge_vertices(digits_vertex=4)
    if not m.is_watertight:
        trimesh.repair.fill_holes(m); trimesh.repair.fix_normals(m)
    if not m.is_watertight:                     # last resort: let build123d write the STL from the solid itself
        import tempfile; f = tempfile.mktemp(suffix=".stl"); b.export_stl(shape, f, tolerance=tol); m = trimesh.load(f); m.merge_vertices(digits_vertex=4)
    return m


meshes = {k: mesh_of(v) for k, v in parts.items()}
for k, m in meshes.items():
    m.export(OUT / f"{k}.stl")
servo_meshes = {k: mesh_of(v, 0.15) for k, v in placed.items()}
for k, m in servo_meshes.items():
    m.export(OUT / f"servo_{k}.stl")
bad = [k for k, m in list(meshes.items()) + list(servo_meshes.items()) if not m.is_watertight]
print("meshes not watertight:", bad if bad else "none")
json.dump(dict(TORSO_TOP=TORSO_TOP, RACK_TOP=RACK_TOP, PLATE_Y=PLATE_Y, TORSO_X=TORSO_X, TORSO_YW=TORSO_YW, CABLE_D=CABLE_D,
               clips=dict(torso=[[list(p), list(n)] for p, n in TORSO_CLIPS], **{f"{k}_{sd}": [[list(p), list(n)] for p, n in v]
                                                                            for sd in "lr" for k, v in clip_spots(sd).items()}),
               HY=HY, Z_ANKLE=Z_ANKLE, Z_KNEE=Z_KNEE, Z_PITCH=Z_PITCH, Z_ROLL=Z_ROLL, L_THIGH=L_THIGH, L_SHANK=L_SHANK, H_HIP=H_HIP,
               volumes_mm3={k: float(m.volume) for k, m in meshes.items()},
               servos={k: dict(p=sv.p.tolist(), ez=sv.ez.tolist(), ex=sv.ex.tolist()) for k, sv in servos.items()}),
          open(OUT / "biped_v3_params.json", "w"), indent=1)
trimesh.util.concatenate(list(meshes.values()) + list(servo_meshes.values())).export(OUT / "assembly.stl")
print("wrote", OUT)
