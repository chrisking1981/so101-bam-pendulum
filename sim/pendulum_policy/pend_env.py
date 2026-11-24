"""Sim2real pipeline test on one servo: a policy moves the pendulum arm (with the Nano 33 IoT IMU on it) to commanded angles.

The whole chain is the one the robot will use, on a single joint:
BAM 12 V m5 actuator in MuJoCo + domain randomization -> PPO -> ONNX -> 50 Hz loop on the Mac (servo + IMU over USB).

Physics: 2 ms step, policy at 50 Hz (10 substeps). Joint q = 0 hanging, same sign as the servo encoder.
Observation (7), identical on the robot (see run_real.py):
  q (encoder), 0.1 * qdot (servo speed register), tilt (Nano filter), 0.1 * gyro_z (Nano), target, q - target, last action
Action (1): goal position = 1.5 rad * a, a in [-1, 1].
Randomized per episode: BAM friction x0.7-1.3, supply 11.0-12.6 V, Nano mass 4-8 g at 7-9 cm, arm mass +-10%, extra command delay 0-10 ms;
sensor noise as measured (docs/training-checklist.md), IMU tilt with a slow +-2 deg wander (filter behaviour),
servo speed one control step late and quantised to 0.0767 rad/s (measured on the real loop; without it the policy oscillated at 8.5 Hz).
"""
import os
import numpy as np
import gymnasium as gym
import mujoco
from bam.model import load_model
from bam.mujoco import MujocoController

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PARAMS = os.path.join(REPO, "fits", "STS3215-12V", "m5.json")
KP_FW = 32
ACTION_SCALE = 1.5
DT, SUB = 0.002, 10

XML = """
<mujoco>
  <option timestep="{dt}" gravity="0 0 -9.81" integrator="implicitfast"/>
  <worldbody>
    <body name="arm">
      <joint name="j" type="hinge" axis="0 1 0"/>
      <geom name="rod" type="capsule" size="0.002" fromto="0 0 0 0 0 -0.1" mass="{arm}" contype="0" conaffinity="0"/>
      <geom name="nano" type="box" size="0.009 0.002 0.022" pos="0 0 {nano_r}" mass="{nano}" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
  <actuator><motor name="j" joint="j" gear="1"/></actuator>
</mujoco>
"""


def test_targets():
    """Fixed target schedule used for the sim vs real comparison: (time s, target rad)."""
    seq = [0.0, 0.6, -0.6, 1.2, -1.2, 0.3, -0.3, 0.9, 0.0]
    return [(1.5 * i, x) for i, x in enumerate(seq)]


class PendEnv(gym.Env):
    def __init__(self, randomize=True, episode_s=6.0, schedule=None):
        super().__init__()
        self.randomize, self.max_steps, self.schedule = randomize, int(episode_s * 50), schedule
        self.action_space = gym.spaces.Box(-1, 1, (1,), np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (7,), np.float32)
        self.model = load_model(PARAMS); self.model.actuator.kp = KP_FW
        self.m = None

    def _build(self, arm, nano, nano_r):
        self.m = mujoco.MjModel.from_xml_string(XML.format(dt=DT, arm=arm, nano=nano, nano_r=-nano_r))
        self.d = mujoco.MjData(self.m)
        self.ctrl = MujocoController(self.model, ["j"], self.m, self.d)

    def _target(self):
        if self.schedule is not None:
            return [x for t, x in self.schedule if t <= self.t + 1e-9][-1]
        if self.t >= self.next_change:
            self.tgt = float(self.np_random.uniform(-1.2, 1.2)); self.next_change = self.t + self.np_random.uniform(0.8, 2.0)
        return self.tgt

    def _obs(self):
        r = self.np_random; q, qd = self.d.qpos[0], self.d.qvel[0]
        if self.randomize:
            # slow tilt error of the on-board filter: Ornstein-Uhlenbeck, ~1 deg std, ~2 s time constant
            self.tilt_err += -self.tilt_err * 0.02 / 2.0 + np.radians(1.0) * np.sqrt(2 * 0.02 / 2.0) * r.standard_normal()
            qn = q + r.uniform(-0.001, 0.001)
            # servo speed register: one control step old (firmware averaging) and quantised to 0.0767 rad/s (measured)
            qdn = np.round((self.qd_prev + r.uniform(-0.05, 0.05)) / 0.0767) * 0.0767
            tilt, gyro = q + self.tilt_err + r.uniform(-0.003, 0.003), qd + r.uniform(-0.03, 0.03)
        else:
            qn, qdn, tilt, gyro = q, np.round(self.qd_prev / 0.0767) * 0.0767, q, qd
        self.qd_prev = qd
        tg = self._target()
        return np.array([qn, 0.1 * qdn, tilt, 0.1 * gyro, tg, qn - tg, self.last_a], np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        r = self.np_random
        if self.randomize:
            arm, nano, nano_r = 0.009 * r.uniform(0.9, 1.1), r.uniform(0.004, 0.008), r.uniform(0.07, 0.09)
            self.fscale, vin, self.delay = r.uniform(0.7, 1.3), r.uniform(11.0, 12.6), int(r.integers(0, 6))
        else:
            arm, nano, nano_r, self.fscale, vin, self.delay = 0.009, 0.006, 0.082, 1.0, 12.0, 0
        self._build(arm, nano, nano_r)
        self.model.actuator.vin = vin
        self.ctrl.reset()
        self.d.qpos[0] = r.uniform(-0.05, 0.05) if self.randomize else 0.0
        mujoco.mj_forward(self.m, self.d)
        self.t, self.steps, self.last_a, self.tilt_err, self.qd_prev = 0.0, 0, 0.0, 0.0, 0.0
        self.tgt, self.next_change = 0.0, r.uniform(0.3, 1.0)
        self.queue = [0.0] * (self.delay + 1)
        return self._obs(), {}

    def step(self, action):
        a = float(np.clip(action[0], -1, 1))
        for _ in range(SUB):
            self.queue.append(ACTION_SCALE * a); cmd = self.queue.pop(0)
            self.ctrl.set_q_target("j", cmd); self.ctrl.update()
            if self.fscale != 1.0:
                self.m.dof_frictionloss[0] *= self.fscale
            mujoco.mj_step(self.m, self.d)
        self.t += 0.02; self.steps += 1
        tg = self._target(); err = self.d.qpos[0] - tg
        reward = -abs(err) - 3.0 * (a - self.last_a) ** 2 - 0.01 * abs(self.d.qvel[0]) * (abs(err) < 0.05)
        self.last_a = a
        return self._obs(), float(reward), False, self.steps >= self.max_steps, {"q": self.d.qpos[0], "target": tg}
