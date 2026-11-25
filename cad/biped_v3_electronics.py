"""Electronics of biped v3: two SO-101 board mounting plates in the rack on top of the torso, two USB servo boards, the servo cables
with their plugs, through the cable clips. Writes meshes for the viewer and the extra masses for the simulation.

Layout (C044 at hip pitch, the rest 12 V):
  12 V board (left plate) -> splitter:  1 -> hip roll L -> knee L -> ankle L     2 -> hip roll R -> knee R -> ankle R
  5 V board (right plate) -> splitter:  1 -> hip pitch L (C044)                  2 -> hip pitch R (C044)
The 12 V and 5 V servos never share a cable. STS3215 sockets: two 3-pin sockets on the back face (S.z = -17.7) at S.x = -1.6,
S.y = +-5.2 (pins measured in the official STEP); the plug goes in along -S.z.

Board: Seeed bus servo driver board (XIAO socket, CH343 USB chip, 42 x 25 mm, ONE servo socket), on the Seeedstudio_Mounting_Plate_SO101
(M2 holes 16.4 x 21 mm, the same pattern as the board). A small 1 -> 2 splitter per board feeds both legs. Connector places are
approximate (from a photo).

    uv run --no-project --python 3.12 --with trimesh --with manifold3d --with scipy --with networkx python cad/biped_v3_electronics.py
"""
import json
from pathlib import Path
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent; D = HERE / "biped_v3"
P = json.load(open(D / "biped_v3_params.json"))
SHAFT_X = 12.5
C044_AT = "pitch"


def w(key, sx, sy, sz):
    sv = P["servos"][key]; ex, ez = np.array(sv["ex"]), np.array(sv["ez"]); ey = np.cross(ez, ex)
    return np.array(sv["p"]) + (sx - SHAFT_X) * ex + sy * ey + sz * ez


def plug(key, port):
    """Socket point, a point 4 mm out (end of the plug body) and 8 mm out (cable leaves the plug), all on the servo's link."""
    sy = 5.2 if port == "in" else -5.2
    return w(key, -1.6, sy, -17.7), w(key, -1.6, sy, -23.0), w(key, -1.6, sy, -28.0)


def link_of(key):
    side = key[-1]
    return {"roll": "torso", "pitch": f"thigh_{side}", "knee": f"thigh_{side}", "ankle": f"shank_{side}"}[key.split("_")[0]]


# ---------------------------------------------------------------- plates and boards
RT, PY = P["RACK_TOP"], P["PLATE_Y"]
plate_src = trimesh.load(HERE / "vendor" / "Seeedstudio_Mounting_Plate_SO101.stl")
meshes = {}   # name -> (mesh, link, color, label)


def plate_tf(side):
    """Plate STL: base z 0..4, key z 4..7.6, board on the z = 0 face. Flip (key down into the rack socket), turn 90 deg so the
    plate's long side runs along y, the board's long side outward."""
    s = 1 if side == "l" else -1
    flip = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    rot = trimesh.transformations.rotation_matrix(s * np.pi / 2 * -1, [0, 0, 1])
    T = trimesh.transformations.translation_matrix([0, s * PY, RT + 4.0]) @ rot @ flip
    return T


for side, nl in (("l", "links"), ("r", "rechts")):
    T = plate_tf(side); m = plate_src.copy(); m.apply_transform(T)
    meshes[f"plate_{side}"] = (m, "torso", "#e9e4d8", f"SO-101 bordplankje {nl} (Seeed)")

BOARD = dict(L=42.0, W=25.0, T=1.6, stand=3.0)
HOLES_PLATE = [(6.4, -10.5), (6.4, 10.5), (22.8, -10.5), (22.8, 10.5)]   # M2 holes in the plate STL frame (z = 0 face)
# On the board (photo): the four holes sit at the screw-terminal end, 21 mm across and 16.8 mm apart along the board; the hole
# pattern centre is 10.1 mm from the board centre. USB-C at the far end, one 3-pin servo socket on the side near the terminal.
boards = {}
for side, volt, col in (("l", "12v", "#2c6fb5"), ("r", "5v", "#2f9a6a")):
    T = plate_tf(side)
    hc = np.mean([T @ [hx, hy, 0, 1] for hx, hy in HOLES_PLATE], axis=0)[:3]
    s = 1 if side == "l" else -1
    out_dir = np.sign(hc[1]) if abs(hc[1]) > 1 else s            # USB end away from the hole pattern
    bc = hc + np.array([0, out_dir * 10.1, 0])
    z0 = RT + 4.0 + BOARD["stand"]; top = z0 + BOARD["T"]
    pcb = trimesh.creation.box([BOARD["W"], BOARD["L"], BOARD["T"]]); pcb.apply_translation([bc[0], bc[1], z0 + BOARD["T"] / 2])
    parts = [pcb]
    for hx, hy in HOLES_PLATE:
        q = (T @ [hx, hy, 0, 1])[:3]; st = trimesh.creation.cylinder(radius=2.0, height=BOARD["stand"], sections=16)
        st.apply_translation([q[0], q[1], RT + 4.0 + BOARD["stand"] / 2]); parts.append(st)
    term_y = bc[1] - out_dir * 17.0
    comps = []
    for dx in (-6.5, 6.5):                                                       # XIAO socket rows
        h = trimesh.creation.box([2.6, 18.0, 8.5]); h.apply_translation([bc[0] + dx, bc[1] + out_dir * 4.0, top + 4.25]); comps.append(h)
    usb = trimesh.creation.box([9.0, 7.5, 3.2]); usb.apply_translation([bc[0], bc[1] + out_dir * (BOARD["L"] / 2 - 3.0), top + 1.6]); comps.append(usb)
    term = trimesh.creation.box([8.0, 7.5, 10.0]); term.apply_translation([bc[0] - 4.0, term_y, top + 5.0]); comps.append(term)
    cap = trimesh.creation.cylinder(radius=3.2, height=7.5, sections=20); cap.apply_translation([bc[0] + 6.0, term_y, top + 3.75]); comps.append(cap)
    sock = trimesh.creation.box([6.0, 8.0, 6.0]); xs = bc[0] - BOARD["W"] / 2 - 1.0
    sock.apply_translation([xs, bc[1] - out_dir * 9.0, top + 3.0])
    meshes[f"hdr_{side}"] = (sock, "torso", "#f2f2ee", None)
    # 1 -> 2 splitter on the back of the rack: the board has one servo socket, the bus goes to both legs
    sp = np.array([P["TORSO_X"][0] - 4.0, bc[1] - out_dir * 9.0, RT - 8.0])
    spl = trimesh.creation.box([6.0, 14.0, 9.0]); spl.apply_translation(sp)
    meshes[f"split_{side}"] = (spl, "torso", "#f2f2ee", f"Verdeelstukje 1 -> 2 ({volt.upper()})")
    meshes[f"board_{side}"] = (trimesh.util.concatenate(parts), "torso", col,
                               f"USB-servobordje {volt.upper()} ({'heup-rol, knie, enkel' if volt == '12v' else 'C044 heup-pitch'})")
    meshes[f"conn_{side}"] = (trimesh.util.concatenate(comps), "torso", "#3a3d42", None)
    src = np.array([xs - 3.0, bc[1] - out_dir * 9.0, top + 3.0])
    boards[volt] = dict(src=src, split=sp, p1=sp + [-3.0, 4.5, 0], p2=sp + [-3.0, -4.5, 0])

# ---------------------------------------------------------------- cables (points on links; the viewer bends them with the joints)
CL = P["clips"]
ring = lambda p, n: (np.array(p) + np.array(n) * (1.6 + P["CABLE_D"] / 2 + 0.2))
clip_t = {round(p[1]): ring(p, n) for p, n in CL["torso"]}
wires = []


def wire(name, volt, pts):
    wires.append(dict(name=name, volt=volt, pts=[dict(p=[round(float(v), 2) for v in p], link=l) for p, l in pts]))


back = P["TORSO_X"][0] - 6.0
for volt, bd in boards.items():
    wire(f"bordje {volt} -> verdeelstukje", volt, [(bd["src"], "torso"), (bd["src"] + [-5, 0, 0], "torso"), (bd["split"] + [0, 0, 6.5], "torso")])
for side, s in (("l", 1), ("r", -1)):
    # 12 V: board -> hip roll
    port = boards["12v"]["p1" if side == "l" else "p2"]
    sock, pe, pc = plug(f"roll_{side}", "in")
    wire(f"12V -> heup-rol {side}", "12v", [(port, "torso"), (port + [-3, 0, -3], "torso"), ([back, port[1] * 0.5 + s * 14, RT - 12], "torso"),
                                            (clip_t[s * 30], "torso"), ([back, s * 36, 222], "torso"), (pc, "torso"), (pe, "torso")])
    # hip roll -> knee (12 V daisy chain, down the inner side of the thigh, through the thigh clip)
    r_sock, r_pe, r_pc = plug(f"roll_{side}", "out"); k_sock, k_pe, k_pc = plug(f"knee_{side}", "in")
    tclip = ring(*CL[f"thigh_{side}"][0])
    wire(f"heup-rol -> knie {side}", "12v", [(r_pe, "torso"), (r_pc, "torso"), ([back + 2, s * 26, 205], "torso"),
                                             ([-20, s * 20, 192], f"hip_{side}"), ([-10, s * 11, 168], f"hip_{side}"),
                                             ([-8, s * 10.5, 156], f"thigh_{side}"), (tclip, f"thigh_{side}"),
                                             ([k_pc[0], s * 9.5, 104], f"thigh_{side}"), (k_pc, f"thigh_{side}"), (k_pe, f"thigh_{side}")])
    # knee -> ankle (through the shank clip)
    ko_sock, ko_pe, ko_pc = plug(f"knee_{side}", "out"); a_sock, a_pe, a_pc = plug(f"ankle_{side}", "in")
    sclip = ring(*CL[f"shank_{side}"][0])
    wire(f"knie -> enkel {side}", "12v", [(ko_pe, f"thigh_{side}"), (ko_pc, f"thigh_{side}"), ([ko_pc[0], s * 9.5, 86], f"thigh_{side}"),
                                          ([ko_pc[0] * 0.5, s * 9.5, 76], f"shank_{side}"), (sclip, f"shank_{side}"),
                                          ([a_pc[0], s * 9.5, 46], f"shank_{side}"), (a_pc, f"shank_{side}"), (a_pe, f"shank_{side}")])
    # 5 V: board -> C044 hip pitch (short, near the torso)
    port5 = boards["5v"]["p1" if side == "l" else "p2"]
    p_sock, p_pe, p_pc = plug(f"pitch_{side}", "in")
    wire(f"5V -> heup-pitch (C044) {side}", "5v", [(port5, "torso"), (port5 + [-3, 0, -3], "torso"), ([back, port5[1] * 0.5 + s * 7, RT - 12], "torso"),
                                                   (clip_t[s * 13], "torso"), ([back + 2, s * 12, 208], "torso"),
                                                   ([-14, s * 10, 188], f"hip_{side}"), ([-4, s * 9.5, 168], f"hip_{side}"),
                                                   ([p_pc[0], s * 9.5, 156], f"thigh_{side}"), (p_pc, f"thigh_{side}"), (p_pe, f"thigh_{side}")])

# plug bodies on the servos
plugs = []
for key in P["servos"]:
    for port in ("in", "out"):
        if key.startswith("pitch") and port == "out": continue
        if key.startswith("ankle") and port == "out": continue
        sock, pe, _ = plug(key, port); c = (sock + pe) / 2
        sv = P["servos"][key]; ez = np.array(sv["ez"]); ex = np.array(sv["ex"]); ey = np.cross(ez, ex)
        bx = trimesh.creation.box([3.5, 7.5, np.linalg.norm(pe - sock)])
        R = np.eye(4); R[:3, :3] = np.column_stack([ex, ey, ez]); R[:3, 3] = c; bx.apply_transform(R)
        plugs.append((bx, link_of(key)))

# ---------------------------------------------------------------- outputs
out = {}
for k, (m, link, col, lab) in meshes.items():
    m.export(D / f"elec_{k}.stl"); out[k] = dict(link=link, color=col, label=lab)
pm = {}
for m, l in plugs: pm.setdefault(l, []).append(m)
for l, ms in pm.items():
    trimesh.util.concatenate(ms).export(D / f"elec_plugs_{l}.stl"); out[f"plugs_{l}"] = dict(link=l, color="#f2f2ee", label=None)
L = {w_["name"]: sum(np.linalg.norm(np.subtract(a["p"], b["p"])) for a, b in zip(w_["pts"], w_["pts"][1:])) for w_ in wires}
json.dump(dict(parts=out, wires=wires, cable_mm=L), open(D / "electronics.json", "w"), indent=1)
# masses for the simulation: plates printed (60 % of PLA), boards about 8 g each (estimate), cable about 0.12 g/mm... per 100 mm
m_plates = sum(meshes[f"plate_{s}"][0].volume for s in "lr") * 1.24e-3 * 0.6
print("plates %.1f g (2), boards 2 x 8 g (estimate)" % m_plates)
print("cable lengths (mm, along the path):", {k: round(v) for k, v in L.items()})
print("board/splitter:", {k: {p: np.round(v, 1).tolist() for p, v in d.items()} for k, d in boards.items()})
print("plate bounds", [np.round(meshes[f"plate_{s}"][0].bounds, 1).tolist() for s in "lr"], "board bounds", [np.round(meshes[f"board_{s}"][0].bounds, 1).tolist() for s in "lr"])
