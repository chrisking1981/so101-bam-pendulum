"""MuJoCo model of the two-link pendulum (step 2a) with the BAM 12 V m5 actuator on both joints.

Geometry and masses from cad/double_pendulum.py and weighing (cad/double_pendulum_params.json):
- hip (servo 1, ID 6) at the origin, axis y, q = 0 hanging straight down; knee (servo 2, ID 2) 100 mm further down the upper link.
- upper body: printed upper link (22 g from the Bambu Studio slice, centroid 68 mm) + servo 2 (59 g weighed, centre 87.5 mm).
- lower body: 26 g weighed = as-built lower link (12.3 g from the slice, centroid 43 mm) + Nano (5.5 g at 60 mm) + 4 M3 screws (~2.4 g at the hub)
  + the clamped USB cable (~5.8 g, the rest of the 26 g, taken as spread 0..70 mm).
"""
import os
import numpy as np
import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PARAMS = os.path.join(REPO, "fits", "STS3215-12V", "m5.json")
L1 = 0.100

# Bambu Studio slice of both links: 35.6 g, split by volume -> upper link 22.0 g, as-built lower link 12.3 g;
# lower assembly weighed 26 g -> cable piece 26 - 12.3 - 5.5 - 2.4 = 5.8 g
NOMINAL = dict(upper_link=0.0220, servo2=0.059, lower_link=0.0123, nano=0.0055, screws=0.0024, cable=0.0058)

XML = """
<mujoco>
  <option timestep="{dt}" gravity="0 0 -9.81" integrator="implicitfast"/>
  <worldbody>
    <body name="upper">
      <joint name="hip" type="hinge" axis="0 1 0"/>
      <geom name="ul" type="box" size="0.058 0.010 0.003" pos="0 0 -0.068" euler="0 90 0" mass="{upper_link}" contype="0" conaffinity="0"/>
      <geom name="s2" type="box" size="0.0227 0.0124 0.0175" pos="0 0 -0.0875" euler="0 90 0" mass="{servo2}" contype="0" conaffinity="0"/>
      <body name="lower" pos="0 0 -{L1}">
        <joint name="knee" type="hinge" axis="0 1 0"/>
        <geom name="ll" type="box" size="0.043 0.008 0.003" pos="0 0 -0.043" euler="0 90 0" mass="{lower_link}" contype="0" conaffinity="0"/>
        <geom name="nano" type="box" size="0.0216 0.0089 0.003" pos="0 0 -0.060" euler="0 90 0" mass="{nano}" contype="0" conaffinity="0"/>
        <geom name="screws" type="sphere" size="0.006" pos="0 0 0" mass="{screws}" contype="0" conaffinity="0"/>
        <geom name="cable" type="capsule" size="0.002" fromto="0 0 0 0 0 -0.070" mass="{cable}" contype="0" conaffinity="0"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="hip" joint="hip" gear="1"/>
    <motor name="knee" joint="knee" gear="1"/>
  </actuator>
</mujoco>
"""


def build(dt=0.002, scale=None, servo2=None):
    m = dict(NOMINAL)
    if servo2 is not None:
        m["servo2"] = servo2
    if scale:
        m = {k: v * scale.get(k, 1.0) for k, v in m.items()}
    return mujoco.MjModel.from_xml_string(XML.format(dt=dt, L1=L1, **m))


if __name__ == "__main__":
    mm = build(); d = mujoco.MjData(mm); mujoco.mj_forward(mm, d)
    print("body masses (g):", {mm.body(i).name: round(mm.body_mass[i] * 1000, 1) for i in range(1, mm.nbody)})
    print("total %.1f g" % (mm.body_mass[1:].sum() * 1000))
