"""MuJoCo model built from the v2 CAD (cad/biped_v2): joint positions from biped_v2_params.json, masses and inertias from the
printed part meshes (40 % infill, 4 walls: about 60 % of solid PLA), STS3215 12 V servos 59 g (weighed) as boxes at their real
place, Nano 5.5 g on the deck, and an optional extra mass on top of the torso (a "head" on the four M3 holes).

Bodies: torso (both hip-roll servos), hip_{l,r} (cross bracket), leg_{l,r} (leg part + hip-pitch servo + ankle servo), foot_{l,r}.
"""
import json, os
import numpy as np
import mujoco
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
CAD = os.path.join(REPO, "cad", "biped_v2")
P = json.load(open(os.path.join(CAD, "biped_v2_params.json")))
FILL, PLA, SERVO = 0.6, 1.24e-3, 0.059
SERVO_BOX = np.array([45.4, 24.8, 35.0])   # along S.x, S.y, S.z (mm)


def part_inertial(name):
    m = trimesh.load(os.path.join(CAD, f"{name}.stl"))
    mass = m.volume * PLA * FILL / 1000.0                     # kg
    mm = m.copy(); mm.density = mass / m.volume               # kg/mm^3
    I = np.array(mm.moment_inertia) * 1e-6                    # kg mm^2 -> kg m^2
    return mass, np.array(m.center_mass) / 1000.0, I


def servo_inertial(key):
    sv = P["servos"][key]; ex, ez = np.array(sv["ex"]), np.array(sv["ez"]); ey = np.cross(ez, ex)
    c = (np.array(sv["p"]) - 12.5 * ex) / 1000.0              # case centre (S origin)
    a, b_, d = SERVO_BOX / 1000.0
    Il = SERVO / 12.0 * np.diag([b_ ** 2 + d ** 2, a ** 2 + d ** 2, a ** 2 + b_ ** 2])
    R = np.column_stack([ex, ey, ez]); return SERVO, c, R @ Il @ R.T


def combine(items, origin):
    M = sum(m for m, _, _ in items); com = sum(m * c for m, c, _ in items) / M
    I = np.zeros((3, 3))
    for m, c, Ic in items:
        d = c - com; I += Ic + m * (d @ d * np.eye(3) - np.outer(d, d))
    return M, com - origin, I


def inertial_xml(M, com, I):
    return (f'<inertial pos="{com[0]:.5f} {com[1]:.5f} {com[2]:.5f}" mass="{M:.5f}" '
            f'fullinertia="{I[0,0]:.3e} {I[1,1]:.3e} {I[2,2]:.3e} {I[0,1]:.3e} {I[0,2]:.3e} {I[1,2]:.3e}"/>')


def build_xml(top_mass=0.0, dt=0.002):
    zr, zp, za, hy = P["Z_ROLL"] / 1000, P["Z_PITCH"] / 1000, P["Z_ANKLE"] / 1000, P["HY"] / 1000
    t_items = [part_inertial("torso"), servo_inertial("roll_l"), servo_inertial("roll_r")]
    z_deck = (P["Z_ROLL"] + 12.5 + 22.7 + 0.25 + 3.0) / 1000
    t_items.append((0.0055, np.array([0, 0, z_deck + 0.004]), np.eye(3) * 1e-8))
    if top_mass > 0:
        r = 0.025; t_items.append((top_mass, np.array([0, 0, z_deck + 0.02]), np.eye(3) * 0.4 * top_mass * r * r))
    torso_origin = np.array([0, 0, zr])
    body = {"torso": combine(t_items, torso_origin)}
    legs = ""
    for s, sg in (("l", 1), ("r", -1)):
        hip = combine([part_inertial(f"hip_{s}")], np.array([0, sg * hy, zr]))
        leg = combine([part_inertial(f"leg_{s}"), servo_inertial(f"pitch_{s}"), servo_inertial(f"ankle_{s}")], np.array([0, sg * hy, zp]))
        foot = combine([part_inertial(f"foot_{s}")], np.array([0, sg * hy, za]))
        legs += f"""
      <body name="hip_{s}" pos="0 {sg*hy:.4f} 0">
        <joint name="hip_roll_{s}" axis="1 0 0" range="-0.52 0.52"/>
        {inertial_xml(*hip)}
        <body name="leg_{s}" pos="0 0 {zp-zr:.4f}">
          <joint name="hip_pitch_{s}" axis="0 1 0" range="-1.05 1.05"/>
          {inertial_xml(*leg)}
          <geom type="box" size="0.016 0.021 0.045" pos="0 0 -0.045" contype="2" conaffinity="1" mass="0" rgba=".8 .62 .36 1"/>
          <body name="foot_{s}" pos="0 0 {za-zp:.4f}">
            <joint name="ankle_{s}" axis="0 1 0" range="-0.79 0.79"/>
            {inertial_xml(*foot)}
            <geom name="foot_{s}" type="box" size="0.0525 0.026 0.002" pos="0.0075 0 {0.002-za:.4f}" contype="2" conaffinity="1" mass="0" rgba=".9 .5 .3 1"/>
          </body>
        </body>
      </body>"""
    M, com, I = body["torso"]
    xml = f"""
<mujoco>
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
  <actuator>{"".join(f'<motor name="{j}" joint="{j}" gear="1"/>' for j in ["hip_roll_l","hip_pitch_l","ankle_l","hip_roll_r","hip_pitch_r","ankle_r"])}</actuator>
</mujoco>"""
    return xml, ["hip_roll_l", "hip_pitch_l", "ankle_l", "hip_roll_r", "hip_pitch_r", "ankle_r"]


def build(top_mass=0.0, dt=0.002):
    xml, j = build_xml(top_mass, dt); return mujoco.MjModel.from_xml_string(xml), j


if __name__ == "__main__":
    for tm in (0.0, 0.05, 0.1):
        m, j = build(tm); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
        com = d.subtree_com[1]
        print(f"top {tm*1000:.0f} g: total {m.body_mass.sum()*1000:.0f} g, centre of mass height {com[2]*1000:.0f} mm, body masses",
              {m.body(i).name: round(m.body_mass[i] * 1000) for i in range(1, m.nbody)})
