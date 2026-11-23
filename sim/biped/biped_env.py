"""Gymnasium environment for the simple biped with BAM servo models (C044 hips, C046 ankles).

- Physics: MuJoCo CPU, 2 ms step. The policy runs at 50 Hz (10 physics steps per action).
- Actuation: every physics step, bam.mujoco.MujocoController turns the joint targets into torque using the fitted STS3215
  firmware/motor/friction model (kp_fw = 32), exactly as on the real servo.
- Action: 4 joint targets in [-1, 1], scaled to +-0.6 rad.
- Observation (22): joint angles (4), joint velocities (4), gravity in the pelvis frame (3), gyro (3), last action (4),
  gait clock sin/cos (2), commanded forward speed (1), previous pelvis height offset (1).
- Reward: forward speed up to the command, alive bonus, penalties for tilt, sideways drift, turning and jerky actions.
- Domain randomization per episode: floor friction, BAM friction scale, supply voltage, link masses, one-step action delay.
"""
import os
import numpy as np
import gymnasium as gym
import mujoco
from bam.model import load_model
from bam.mujoco import MujocoController

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NAMES = ["hip_L", "hip_R", "ankle_L", "ankle_R"]


class BipedEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array"], "render_fps": 50}

    def __init__(self, dt=0.002, substeps=10, episode_s=10.0, randomize=True, v_cmd=0.12, render_mode=None, seed=None):
        super().__init__()
        xml = open(os.path.join(HERE, "biped.xml")).read().replace('timestep="0.001"', f'timestep="{dt}"')
        self.m = mujoco.MjModel.from_xml_string(xml)
        self.d = mujoco.MjData(self.m)
        self.hips = load_model(os.path.join(REPO, "fits", "C044", "m6.json"))
        self.ankles = load_model(os.path.join(REPO, "fits", "C046", "m4.json"))
        for mod in (self.hips, self.ankles):
            mod.actuator.kp = 32
        self.ctrl = [MujocoController(self.hips, ["hip_L", "hip_R"], self.m, self.d),
                     MujocoController(self.ankles, ["ankle_L", "ankle_R"], self.m, self.d)]
        self.substeps, self.max_steps, self.randomize, self.v_cmd = substeps, int(episode_s * 50), randomize, v_cmd
        self.jq = [self.m.joint(n).qposadr[0] for n in NAMES]
        self.jv = [self.m.joint(n).dofadr[0] for n in NAMES]
        self.floor = self.m.geom("floor").id
        self.base_friction = self.m.geom_friction[self.floor].copy()
        self.base_mass = self.m.body_mass.copy()
        self.dofs = np.array(self.jv)
        self.action_space = gym.spaces.Box(-1, 1, (4,), np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (22,), np.float32)
        self.render_mode = render_mode
        self._renderer = None

    # --- helpers
    def _quat_tilt(self):
        w, x, y, z = self.d.qpos[3:7]
        roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
        return roll, pitch

    def _gravity_body(self):
        R = np.zeros(9); mujoco.mju_quat2Mat(R, self.d.qpos[3:7]); R = R.reshape(3, 3)
        return R.T @ np.array([0, 0, -1.0])

    def _obs(self):
        ph = 2 * np.pi * self.t / 0.8
        return np.concatenate([
            self.d.qpos[self.jq], 0.1 * self.d.qvel[self.jv], self._gravity_body(),
            0.2 * self.d.qvel[3:6], self.last_a, [np.sin(ph), np.cos(ph)], [self.v_cmd * 5], [(self.d.qpos[2] - 0.16) * 10],
        ]).astype(np.float32)

    def _physics(self, targets):
        for _ in range(self.substeps):
            for c, idx in ((self.ctrl[0], (0, 1)), (self.ctrl[1], (2, 3))):
                for i in idx:
                    c.set_q_target(NAMES[i], targets[i])
                c.update()
            if self.fscale != 1.0:
                self.m.dof_frictionloss[self.dofs] *= self.fscale
            mujoco.mj_step(self.m, self.d)

    # --- gym API
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        rng = self.np_random
        mujoco.mj_resetData(self.m, self.d)
        if self.randomize:
            self.m.geom_friction[self.floor] = self.base_friction * [rng.uniform(0.5, 1.2), 1, 1]
            self.m.body_mass[:] = self.base_mass * rng.uniform(0.9, 1.1, size=self.base_mass.shape)
            self.fscale = rng.uniform(0.7, 1.3)
            vin = rng.uniform(7.0, 7.8)
            self.delay = int(rng.integers(0, 2))
        else:
            self.m.geom_friction[self.floor] = self.base_friction; self.m.body_mass[:] = self.base_mass
            self.fscale, vin, self.delay = 1.0, 7.4, 0
        for mod in (self.hips, self.ankles):
            mod.actuator.vin = vin
        for c in self.ctrl:
            c.reset()
        mujoco.mj_forward(self.m, self.d)
        self.t, self.steps = 0.0, 0
        self.last_a = np.zeros(4); self.pending = np.zeros(4)
        return self._obs(), {}

    def step(self, action):
        a = np.clip(np.asarray(action, dtype=np.float64), -1, 1)
        applied = self.pending if self.delay else a
        self.pending = a
        x0, y0 = self.d.qpos[0], self.d.qpos[1]
        self._physics(0.6 * applied)
        self.t += 0.02; self.steps += 1
        vx = (self.d.qpos[0] - x0) / 0.02
        vy = (self.d.qpos[1] - y0) / 0.02
        roll, pitch = self._quat_tilt()
        yaw_rate = self.d.qvel[5]
        fell = self.d.qpos[2] < 0.10 or abs(roll) > 0.7 or abs(pitch) > 0.7
        reward = (3.0 * min(vx, self.v_cmd) + 0.3
                  - 0.5 * abs(vy) - 0.15 * abs(yaw_rate) - 1.0 * (roll ** 2 + pitch ** 2)
                  - 0.02 * float(np.sum((a - self.last_a) ** 2)))
        if fell:
            reward -= 10.0
        self.last_a = a
        truncated = self.steps >= self.max_steps
        info = {"vx": vx, "x": self.d.qpos[0]}
        return self._obs(), float(reward), bool(fell), bool(truncated), info

    def render(self):
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.m, 540, 960)
            self._cam = mujoco.MjvCamera(); self._cam.distance = 0.75; self._cam.azimuth = 120; self._cam.elevation = -14
        self._cam.lookat[:] = [self.d.qpos[0], self.d.qpos[1], 0.10]
        self._renderer.update_scene(self.d, camera=self._cam)
        return self._renderer.render()


class BipedEnvV2(BipedEnv):
    """Residual policy on top of the hand-made scissor gait, with a reward that asks for straight, smooth walking.

    targets = gait(t) + 0.15 rad * action, where gait(t) is the best open-loop rhythm from gait.py
    (1.5 Hz, hips +-0.25 rad in counter-phase, ankles +-0.25 rad in counter-phase to the hips).
    Extra penalties: heading error (yaw angle, not the per-step wiggle), averaged sideways drift, targets near the joint limits, jerky and large residuals, mechanical power.
    """
    F, A, B, PHI, RES = 1.5, 0.25, 0.25, np.pi, 0.15

    def gait(self, t):
        ramp = min(1.0, t / 1.0)
        s = np.sin(2 * np.pi * self.F * t); c = np.sin(2 * np.pi * self.F * t + self.PHI)
        return ramp * np.array([self.A * s, -self.A * s, self.B * c, -self.B * c])

    def _obs(self):
        o = super()._obs()
        ph = 2 * np.pi * self.F * self.t
        o[18:20] = [np.sin(ph), np.cos(ph)]        # clock in sync with the base gait
        return o

    def step(self, action):
        a = np.clip(np.asarray(action, dtype=np.float64), -1, 1)
        applied = self.pending if self.delay else a
        self.pending = a
        x0, y0 = self.d.qpos[0], self.d.qpos[1]
        tg = self.gait(self.t) + self.RES * applied
        power = 0.0
        for _ in range(self.substeps):
            for cc, idx in ((self.ctrl[0], (0, 1)), (self.ctrl[1], (2, 3))):
                for i in idx:
                    cc.set_q_target(NAMES[i], tg[i])
                cc.update()
            if self.fscale != 1.0:
                self.m.dof_frictionloss[self.dofs] *= self.fscale
            mujoco.mj_step(self.m, self.d)
            power += float(np.sum(np.abs(self.d.qfrc_actuator[self.jv] * self.d.qvel[self.jv])))
        power /= self.substeps
        self.t += 0.02; self.steps += 1
        vx = (self.d.qpos[0] - x0) / 0.02
        vy = (self.d.qpos[1] - y0) / 0.02
        roll, pitch = self._quat_tilt()
        w, x, y, z = self.d.qpos[3:7]
        yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        fell = self.d.qpos[2] < 0.10 or abs(roll) > 0.7 or abs(pitch) > 0.7
        near_limit = float(np.sum(np.clip(np.abs(tg) - 0.45, 0, None)))
        self.vy_avg = 0.92 * getattr(self, 'vy_avg', 0.0) + 0.08 * vy        # ~0.25 s average: drift, not the per-step wiggle
        reward = (3.0 * min(vx, self.v_cmd) + 0.3
                  - 4.0 * abs(self.vy_avg) - 2.0 * yaw ** 2
                  - 1.0 * (roll ** 2 + pitch ** 2)
                  - 0.05 * float(np.sum((a - self.last_a) ** 2)) - 0.02 * float(np.sum(a ** 2))
                  - 2.0 * near_limit - 0.002 * power)
        if fell:
            reward -= 10.0
        self.last_a = a
        return self._obs(), float(reward), bool(fell), bool(self.steps >= self.max_steps), {"vx": vx, "x": self.d.qpos[0]}

    def reset(self, seed=None, options=None):
        self.vy_avg = 0.0
        return super().reset(seed=seed, options=options)
