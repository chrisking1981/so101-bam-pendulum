"""MuJoCo model built from the v3 CAD (cad/biped_v3, 8 servos with knees): joint positions from biped_v3_params.json, masses and inertias from the
printed part meshes (40 % infill, 4 walls: about 60 % of solid PLA), STS3215 12 V servos 59 g (weighed) as boxes at their real
place, Nano 5.5 g on the deck, and an optional extra mass on top of the torso (a "head" on the four M3 holes).

Bodies: torso (both hip-roll servos), hip_{l,r} (cross bracket), thigh_{l,r} (thigh + hip-pitch servo + knee servo),
shank_{l,r} (shank + ankle servo), foot_{l,r}. The servo mass can be set per joint (12 V 59 g, C044 57 g).
"""
import json, os
import numpy as np
import mujoco
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
CAD = os.path.join(REPO, "cad", "biped_v3")
P = json.load(open(os.path.join(CAD, "biped_v3_params.json")))
FILL, PLA, SERVO = 0.6, 1.24e-3, 0.059
SERVO_BOX = np.array([45.4, 24.8, 35.0])   # along S.x, S.y, S.z (mm)


def part_inertial(name):
    m = trimesh.load(os.path.join(CAD, f"{name}.stl"))
    mass = m.volume * PLA * FILL / 1000.0                     # kg
    mm = m.copy(); mm.density = mass / m.volume               # kg/mm^3
    I = np.array(mm.moment_inertia) * 1e-6                    # kg mm^2 -> kg m^2
    return mass, np.array(m.center_mass) / 1000.0, I


def servo_inertial(key, mass=SERVO):
    sv = P["servos"][key]; ex, ez = np.array(sv["ex"]), np.array(sv["ez"]); ey = np.cross(ez, ex)
    c = (np.array(sv["p"]) - 12.5 * ex) / 1000.0              # case centre (S origin)
    a, b_, d = SERVO_BOX / 1000.0
    Il = mass / 12.0 * np.diag([b_ ** 2 + d ** 2, a ** 2 + d ** 2, a ** 2 + b_ ** 2])
    R = np.column_stack([ex, ey, ez]); return mass, c, R @ Il @ R.T


def combine(items, origin):
    M = sum(m for m, _, _ in items); com = sum(m * c for m, c, _ in items) / M
    I = np.zeros((3, 3))
    for m, c, Ic in items:
        d = c - com; I += Ic + m * (d @ d * np.eye(3) - np.outer(d, d))
    return M, com - origin, I


def inertial_xml(M, com, I):
    return (f'<inertial pos="{com[0]:.5f} {com[1]:.5f} {com[2]:.5f}" mass="{M:.5f}" '
            f'fullinertia="{I[0,0]:.3e} {I[1,1]:.3e} {I[2,2]:.3e} {I[0,1]:.3e} {I[0,2]:.3e} {I[1,2]:.3e}"/>')


JOINTS = ["hip_roll_l", "hip_pitch_l", "knee_l", "ankle_l", "hip_roll_r", "hip_pitch_r", "knee_r", "ankle_r"]


ELEC_G = dict(boards=2 * 10.0, splitters=2 * 3.0, cables=10.0)   # estimates (g); rack and plates from their meshes


def electronics_items():
    """Board rack, two SO-101 plates, two boards, splitters and cables (cad/biped_v3_electronics.py), all on the torso."""
    items = [part_inertial("rack")]
    for s in "lr":
        items.append(part_inertial(f"elec_plate_{s}"))
    E = json.load(open(os.path.join(CAD, "electronics.json")))
    bz = (P["RACK_TOP"] + 10) / 1000
    for k, g in ELEC_G.items():
        z = bz if k == "boards" else (P["RACK_TOP"] - 10) / 1000
        items.append((g / 1000, np.array([-0.005, 0, z]), np.eye(3) * 2e-7))
    return items


def visual_parts(c044=()):
    """CAD meshes (cad/biped_v3/*.stl, world rest coordinates in mm) per body, with colours as in the 3D viewer. Only for videos."""
    E = json.load(open(os.path.join(CAD, "electronics.json")))["parts"]
    out = [("torso", "torso", "#dfe3e8"), ("rack", "torso", "#cfd5db")]
    out += [(f"elec_{k}", v["link"], v["color"]) for k, v in E.items()]
    dark, blue = "#3b3f4a", "#3d6f9e"
    for s in "lr":
        out += [(f"hip_{s}", f"hip_{s}", "#d2a05a"), (f"thigh_{s}", f"thigh_{s}", "#c99a5b"), (f"shank_{s}", f"shank_{s}", "#b98a4d"),
                (f"foot_{s}", f"foot_{s}", "#e07a4f")]
        for k, link in (("roll", "torso"), ("pitch", f"thigh_{s}"), ("knee", f"thigh_{s}"), ("ankle", f"shank_{s}")):
            out.append((f"servo_{k}_{s}", link, blue if k in c044 else dark))
    return out


def add_visuals(xml, origins, c044=()):
    """Add the CAD meshes as visual-only geoms (no collision, no mass) and move the collision boxes to hidden group 3.
    The physics stays exactly the same as without visuals."""
    assets, geoms = [], {}
    for name, link, col in visual_parts(c044):
        rgb = " ".join(f"{int(col[i:i+2], 16)/255:.3f}" for i in (1, 3, 5))
        assets.append(f'<mesh name="v_{name}" file="{os.path.join(CAD, name + ".stl")}" scale="0.001 0.001 0.001"/>')
        o = origins[link]
        geoms.setdefault(link, []).append(f'<geom type="mesh" mesh="v_{name}" pos="{-o[0]:.5f} {-o[1]:.5f} {-o[2]:.5f}" contype="0" '
                                          f'conaffinity="0" group="1" rgba="{rgb} 1"/>')
    xml = xml.replace('contype="2"', 'contype="2" group="3"')
    xml = xml.replace('<compiler angle="radian"/>', '<compiler angle="radian" inertiafromgeom="false"/>')
    assets += ['<texture name="grid" type="2d" builtin="checker" rgb1=".86 .87 .86" rgb2=".76 .78 .77" width="300" height="300"/>',
               '<material name="grid" texture="grid" texrepeat="30 30"/>',
               '<texture name="sky" type="skybox" builtin="gradient" rgb1=".55 .65 .75" rgb2=".95 .96 .97" width="256" height="256"/>']
    xml = xml.replace('rgba=".85 .87 .85 1"', 'material="grid"')
    xml = xml.replace('<global offwidth="960" offheight="540"/>', '<global offwidth="1280" offheight="720"/><headlight ambient=".35 .35 .35" diffuse=".5 .5 .5"/>')
    xml = xml.replace("<worldbody>", "<asset>" + "".join(assets) + "</asset>\n  <worldbody>", 1)
    for link, gs in geoms.items():
        i = xml.index(f'<body name="{link}"'); j = xml.index(">", i) + 1
        xml = xml[:j] + "\n" + "\n".join(gs) + xml[j:]
    return xml


def build_xml(top_mass=0.0, dt=0.002, masses=None, electronics=True, visual=False):
    """masses: {"roll"/"pitch"/"knee"/"ankle": kg} servo mass per joint type (default 59 g). electronics: rack, plates, boards, cables.
    visual: also draw the real CAD parts (servos with a C044 mass are drawn blue)."""
    sm = {"roll": SERVO, "pitch": SERVO, "knee": SERVO, "ankle": SERVO, **(masses or {})}
    zr, zp, zk, za, hy = P["Z_ROLL"] / 1000, P["Z_PITCH"] / 1000, P["Z_KNEE"] / 1000, P["Z_ANKLE"] / 1000, P["HY"] / 1000
    t_items = [part_inertial("torso"), servo_inertial("roll_l", sm["roll"]), servo_inertial("roll_r", sm["roll"])]
    z_deck = (P["Z_ROLL"] + 12.5 + 22.7 + 0.25 + 3.0) / 1000
    t_items.append((0.0055, np.array([0, 0, z_deck + 0.004]), np.eye(3) * 1e-8))
    if top_mass > 0:
        r = 0.025; t_items.append((top_mass, np.array([0, 0, z_deck + 0.02]), np.eye(3) * 0.4 * top_mass * r * r))
    if electronics:
        t_items += electronics_items()
    torso_origin = np.array([0, 0, zr])
    body = {"torso": combine(t_items, torso_origin)}
    legs = ""
    for s, sg in (("l", 1), ("r", -1)):
        hip = combine([part_inertial(f"hip_{s}")], np.array([0, sg * hy, zr]))
        thigh = combine([part_inertial(f"thigh_{s}"), servo_inertial(f"pitch_{s}", sm["pitch"]), servo_inertial(f"knee_{s}", sm["knee"])], np.array([0, sg * hy, zp]))
        shank = combine([part_inertial(f"shank_{s}"), servo_inertial(f"ankle_{s}", sm["ankle"])], np.array([0, sg * hy, zk]))
        foot = combine([part_inertial(f"foot_{s}")], np.array([0, sg * hy, za]))
        legs += f"""
      <body name="hip_{s}" pos="0 {sg*hy:.4f} 0">
        <joint name="hip_roll_{s}" axis="1 0 0" range="-0.52 0.52"/>
        {inertial_xml(*hip)}
        <body name="thigh_{s}" pos="0 0 {zp-zr:.4f}">
          <joint name="hip_pitch_{s}" axis="0 1 0" range="-1.05 1.05"/>
          {inertial_xml(*thigh)}
          <geom type="box" size="0.016 0.021 0.035" pos="0 0 -0.04" contype="2" conaffinity="1" mass="0" rgba=".8 .62 .36 1"/>
          <body name="shank_{s}" pos="0 0 {zk-zp:.4f}">
            <joint name="knee_{s}" axis="0 1 0" range="-0.17 1.92"/>
            {inertial_xml(*shank)}
            <geom type="box" size="0.016 0.021 0.025" pos="0 0 -0.03" contype="2" conaffinity="1" mass="0" rgba=".7 .55 .35 1"/>
            <body name="foot_{s}" pos="0 0 {za-zk:.4f}">
              <joint name="ankle_{s}" axis="0 1 0" range="-0.79 0.79"/>
              {inertial_xml(*foot)}
              <geom name="foot_{s}" type="box" size="0.0525 0.026 0.002" pos="0.0075 0 {0.002-za:.4f}" contype="2" conaffinity="1" mass="0" rgba=".9 .5 .3 1"/>
            </body>
          </body>
        </body>
      </body>"""
    M, com, I = body["torso"]
    xml = f"""
<mujoco>
  <compiler angle="radian"/>
  <option timestep="{dt}" integrator="implicitfast"/>
  <visual><global offwidth="960" offheight="540"/></visual>
  <worldbody>
    <light pos="0 0 2" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="3 3 0.1" contype="1" conaffinity="1" friction="0.9 0.02 0.001" rgba=".85 .87 .85 1"/>
    <body name="torso" pos="0 0 {zr:.4f}">
      <freejoint name="root"/>
      {inertial_xml(M, com, I)}
      <geom name="torso" type="box" size="0.02 0.05 0.02" pos="0 0 0.028" contype="2" conaffinity="1" mass="0" rgba=".9 .9 .95 1"/>
      <site name="imu" pos="0 0 0.04"/>
      {legs}
    </body>
  </worldbody>
  <actuator>{"".join(f'<motor name="{j}" joint="{j}" gear="1"/>' for j in JOINTS)}</actuator>
</mujoco>"""
    if visual:
        origins = {"torso": np.array([0, 0, zr])}
        for s, sg in (("l", 1), ("r", -1)):
            origins.update({f"hip_{s}": np.array([0, sg * hy, zr]), f"thigh_{s}": np.array([0, sg * hy, zp]),
                            f"shank_{s}": np.array([0, sg * hy, zk]), f"foot_{s}": np.array([0, sg * hy, za])})
        xml = add_visuals(xml, origins, tuple(k for k, v in (masses or {}).items() if abs(v - 0.057) < 1e-6))
    return xml, list(JOINTS)


def build(top_mass=0.0, dt=0.002, masses=None, electronics=True, visual=False):
    xml, j = build_xml(top_mass, dt, masses, electronics, visual); return mujoco.MjModel.from_xml_string(xml), j


if __name__ == "__main__":
    for tm in (0.0, 0.05, 0.1):
        m, j = build(tm); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
        com = d.subtree_com[1]
        print(f"top {tm*1000:.0f} g: total {m.body_mass.sum()*1000:.0f} g, centre of mass height {com[2]*1000:.0f} mm, body masses",
              {m.body(i).name: round(m.body_mass[i] * 1000) for i in range(1, m.nbody)})
