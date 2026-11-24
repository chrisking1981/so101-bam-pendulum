"""Rough MuJoCo sketches of two 6-servo biped layouts with STS3215 12 V servos, to choose a leg layout before drawing parts.

A "roll":  per leg hip roll (x axis, servo on the torso) -> hip pitch -> one straight leg 130 mm -> ankle pitch -> foot.
B "knee":  per leg hip pitch (servo on the torso) -> thigh 80 mm -> knee -> shank 80 mm -> ankle pitch -> foot.
Masses: STS3215 12 V 59 g each (weighed, with metal horn), printed brackets 10-20 g per link (SO-101 style: driving horn on one side,
passive horn on the other), feet 15 g, torso 70 g plus its two servos (plate, Nano 33 IoT, cable clips). Servo blocks are 45 x 25 x 35 mm.
Both stand about 0.21 m tall at the hip and weigh about 0.5 kg.
"""
import mujoco

SERVO = 0.059
FLOOR = '<geom name="floor" type="plane" size="3 3 0.1" contype="1" conaffinity="1" friction="0.9 0.02 0.001" rgba=".85 .87 .85 1"/>'
DEF = 'contype="2" conaffinity="1"'


def servo_geom(name, pos, euler="0 0 0"):
    return f'<geom name="{name}" type="box" size="0.0227 0.0124 0.0175" pos="{pos}" euler="{euler}" mass="{SERVO}" {DEF} rgba=".25 .27 .32 1"/>'


def leg_roll(s, side):
    y = 0.035 * s
    return f"""
    <body name="hiproll_{side}" pos="0 {y} -0.03">
      <joint name="hip_roll_{side}" axis="1 0 0" range="-0.6 0.6"/>
      {servo_geom(f"s_hp_{side}", "0 0 -0.03", "90 0 0")}
      <geom type="box" size="0.02 0.015 0.01" pos="0 0 -0.012" mass="0.010" {DEF} rgba=".82 .63 .35 1"/>
      <body name="leg_{side}" pos="0 0 -0.03">
        <joint name="hip_pitch_{side}" axis="0 1 0" range="-1.4 1.4"/>
        <geom type="capsule" size="0.009" fromto="0 0 -0.01 0 0 -0.12" mass="0.020" {DEF} rgba=".82 .63 .35 1"/>
        {servo_geom(f"s_an_{side}", "0 0 -0.13", "90 0 0")}
        <body name="foot_{side}" pos="0 0 -0.13">
          <joint name="ankle_{side}" axis="0 1 0" range="-1.2 1.2"/>
          <geom name="foot_{side}" type="box" size="0.045 0.025 0.004" pos="0.008 0 -0.024" mass="0.015" {DEF} rgba=".9 .5 .3 1"/>
        </body>
      </body>
    </body>"""


def leg_knee(s, side):
    y = 0.04 * s
    return f"""
    <body name="thigh_{side}" pos="0 {y} -0.03">
      <joint name="hip_pitch_{side}" axis="0 1 0" range="-1.4 1.4"/>
      <geom type="capsule" size="0.009" fromto="0 0 -0.005 0 0 -0.075" mass="0.012" {DEF} rgba=".82 .63 .35 1"/>
      {servo_geom(f"s_kn_{side}", "0 0 -0.08", "90 0 0")}
      <body name="shank_{side}" pos="0 0 -0.08">
        <joint name="knee_{side}" axis="0 1 0" range="-0.2 2.2"/>
        <geom type="capsule" size="0.009" fromto="0 0 -0.005 0 0 -0.075" mass="0.012" {DEF} rgba=".82 .63 .35 1"/>
        {servo_geom(f"s_an_{side}", "0 0 -0.08", "90 0 0")}
        <body name="foot_{side}" pos="0 0 -0.08">
          <joint name="ankle_{side}" axis="0 1 0" range="-1.2 1.2"/>
          <geom name="foot_{side}" type="box" size="0.05 0.03 0.004" pos="0.008 0 -0.024" mass="0.015" {DEF} rgba=".9 .5 .3 1"/>
        </body>
      </body>
    </body>"""


def leg_knee8(s, side):
    """Hip roll -> hip pitch -> thigh 80 mm -> knee -> shank 80 mm -> ankle pitch -> foot (4 servos per leg)."""
    y = 0.035 * s
    return f"""
    <body name="hiproll_{side}" pos="0 {y} -0.03">
      <joint name="hip_roll_{side}" axis="1 0 0" range="-0.5 0.5"/>
      {servo_geom(f"s_hp_{side}", "0 0 -0.03", "90 0 0")}
      <geom type="box" size="0.02 0.015 0.01" pos="0 0 -0.012" mass="0.010" {DEF} rgba=".82 .63 .35 1"/>
      <body name="thigh_{side}" pos="0 0 -0.03">
        <joint name="hip_pitch_{side}" axis="0 1 0" range="-1.4 1.4"/>
        <geom type="capsule" size="0.009" fromto="0 0 -0.005 0 0 -0.075" mass="0.012" {DEF} rgba=".82 .63 .35 1"/>
        {servo_geom(f"s_kn_{side}", "0 0 -0.08", "90 0 0")}
        <body name="shank_{side}" pos="0 0 -0.08">
          <joint name="knee_{side}" axis="0 1 0" range="-0.2 2.2"/>
          <geom type="capsule" size="0.009" fromto="0 0 -0.005 0 0 -0.075" mass="0.012" {DEF} rgba=".82 .63 .35 1"/>
          {servo_geom(f"s_an_{side}", "0 0 -0.08", "90 0 0")}
          <body name="foot_{side}" pos="0 0 -0.08">
            <joint name="ankle_{side}" axis="0 1 0" range="-1.2 1.2"/>
            <geom name="foot_{side}" type="box" size="0.05 0.028 0.004" pos="0.008 0 -0.024" mass="0.015" {DEF} rgba=".9 .5 .3 1"/>
          </body>
        </body>
      </body>
    </body>"""


def build_xml(variant, dt=0.002):
    if variant == "knee8":
        hips = servo_geom("s_hr_l", "0 0.035 -0.01", "0 0 90") + servo_geom("s_hr_r", "0 -0.035 -0.01", "0 0 90")
        legs = leg_knee8(1, "l") + leg_knee8(-1, "r"); z0 = 0.03 + 0.03 + 0.08 + 0.08 + 0.028 + 0.002
        joints = ["hip_roll_l", "hip_pitch_l", "knee_l", "ankle_l", "hip_roll_r", "hip_pitch_r", "knee_r", "ankle_r"]
    elif variant == "roll":
        hips = servo_geom("s_hr_l", "0 0.035 -0.01", "0 0 90") + servo_geom("s_hr_r", "0 -0.035 -0.01", "0 0 90")
        legs = leg_roll(1, "l") + leg_roll(-1, "r"); z0 = 0.03 + 0.03 + 0.13 + 0.028 + 0.002
        joints = ["hip_roll_l", "hip_pitch_l", "ankle_l", "hip_roll_r", "hip_pitch_r", "ankle_r"]
    else:
        hips = servo_geom("s_hp_l", "0 0.04 -0.01", "90 0 0") + servo_geom("s_hp_r", "0 -0.04 -0.01", "90 0 0")
        legs = leg_knee(1, "l") + leg_knee(-1, "r"); z0 = 0.03 + 0.08 + 0.08 + 0.028 + 0.002
        joints = ["hip_pitch_l", "knee_l", "ankle_l", "hip_pitch_r", "knee_r", "ankle_r"]
    xml = f"""
<mujoco>
  <option timestep="{dt}" integrator="implicitfast"/>
  <visual><global offwidth="960" offheight="540"/></visual>
  <worldbody>
    <light pos="0 0 2" dir="0 0 -1"/>
    {FLOOR}
    <body name="torso" pos="0 0 {z0:.3f}">
      <freejoint name="root"/>
      <geom name="torso" type="box" size="0.03 0.065 0.02" pos="0 0 0.02" mass="0.070" {DEF} rgba=".9 .9 .95 1"/>
      <site name="imu" pos="0 0 0.04"/>
      {hips}
      {legs}
    </body>
  </worldbody>
  <actuator>{"".join(f'<motor name="{j}" joint="{j}" gear="1"/>' for j in joints)}</actuator>
</mujoco>"""
    return xml, joints


def build(variant, dt=0.002):
    xml, joints = build_xml(variant, dt)
    return mujoco.MjModel.from_xml_string(xml), joints


if __name__ == "__main__":
    for v in ("roll", "knee", "knee8"):
        m, j = build(v); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
        print(v, "mass %.0f g" % (m.body_mass.sum() * 1000), "torso height %.3f" % d.qpos[2], "joints", j)
