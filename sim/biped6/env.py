"""Walking environment for the rough 6-servo biped sketches (model.py), to compare leg layouts.

From docs/training-checklist.md: BAM 12 V m5 in the loop on all joints (kp_fw 32), 2 ms physics, policy 50 Hz; servo speed one step
late and quantised to 0.0767 rad/s; IMU (Nano on the torso) as projected gravity with a slow +-1 deg wander and gyro noise +-0.03;
randomized BAM friction x0.7-1.3, supply 11-12.6 V, link masses +-10 %, floor friction 0.5-1.2, extra delay 0-10 ms, pushes.
Action (6): joint goals = default pose + 0.6 rad * a. Observation (31): joint pos (6), 0.1 x joint speed (6), projected gravity (3),
0.2 x gyro (3), last action (6), gait clock sin/cos (2), command (1), 1, foot contacts (2) are NOT observed (no foot sensors), pad (3).
Reward: forward speed up to the command, alive, upright, straight heading, alternating feet on the gait clock, smooth actions, power.
"""
import os, sys
import numpy as np
import gymnasium as gym
import mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import build as build_sketch
import model_v2


def build(variant):
    if variant.startswith("v2"):              # "v2" or "v2_50" (50 g on top of the torso)
        top = float(variant.split("_")[1]) / 1000 if "_" in variant else 0.0
        return model_v2.build(top)
    return build_sketch(variant)
from bam.model import load_model
from bam.mujoco import MujocoController

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARAMS = os.path.join(REPO, "fits", "STS3215-12V", "m5.json")
QD_Q, SUB, PERIOD = 0.0767, 10, 0.6
DEFAULT = {"roll": np.zeros(6), "knee": np.array([-0.35, 0.7, -0.35, -0.35, 0.7, -0.35]),
           "knee8": np.array([0, -0.3, 0.6, -0.3, 0, -0.3, 0.6, -0.3])}


class Biped6Env(gym.Env):
    def __init__(self, variant="knee", randomize=True, episode_s=10.0, v_cmd=0.15, render=False):
        super().__init__()
        self.variant, self.randomize, self.max_steps, self.v_cmd = variant, randomize, int(episode_s * 50), v_cmd
        self.m, self.joints = build(variant); self.d = mujoco.MjData(self.m)
        self.model = load_model(PARAMS); self.model.actuator.kp = 32
        self.ctrl = MujocoController(self.model, self.joints, self.m, self.d)
        self.jq = np.array([self.m.joint(j).qposadr[0] for j in self.joints]); self.jv = np.array([self.m.joint(j).dofadr[0] for j in self.joints])
        self.nj = len(self.joints)
        self.default = DEFAULT.get(variant, np.zeros(self.nj))
        self.floor = self.m.geom("floor").id; self.feet = [self.m.geom("foot_l").id, self.m.geom("foot_r").id]
        self.base_mass = self.m.body_mass.copy(); self.base_fric = self.m.geom_friction[self.floor].copy()
        self.action_space = gym.spaces.Box(-1, 1, (self.nj,), np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (3 * self.nj + 10,), np.float32)
        self._renderer = None

    # helpers
    def _contacts(self):
        c = [False, False]
        for i in range(self.d.ncon):
            g = {self.d.contact[i].geom1, self.d.contact[i].geom2}
            if self.floor in g:
                for k, f in enumerate(self.feet):
                    if f in g: c[k] = True
        return c

    def _grav(self):
        R = np.zeros(9); mujoco.mju_quat2Mat(R, self.d.qpos[3:7]); return R.reshape(3, 3).T @ np.array([0, 0, -1.0])

    def _obs(self):
        r = self.np_random; q = self.d.qpos[self.jq].copy(); qd = self.d.qvel[self.jv].copy()
        g = self._grav(); gyro = self.d.qvel[3:6].copy()
        if self.randomize:
            self.tilt_err = self.tilt_err * 0.99 + np.radians(1.0) * np.sqrt(0.02) * r.standard_normal(2)
            g = g + np.array([self.tilt_err[0], self.tilt_err[1], 0]) + r.uniform(-0.01, 0.01, 3); g /= np.linalg.norm(g)
            q = q + r.uniform(-0.001, 0.001, self.nj); gyro = gyro + r.uniform(-0.03, 0.03, 3)
        qdn = np.round(self.qd_prev / QD_Q) * QD_Q; self.qd_prev = qd
        ph = 2 * np.pi * self.t / PERIOD
        return np.concatenate([q - self.default, 0.1 * qdn, g, 0.2 * gyro, self.last_a, [np.sin(ph), np.cos(ph), self.v_cmd * 5, 1.0]]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed); r = self.np_random
        mujoco.mj_resetData(self.m, self.d)
        if self.randomize:
            self.m.body_mass[:] = self.base_mass * r.uniform(0.9, 1.1, self.base_mass.shape)
            self.m.geom_friction[self.floor] = self.base_fric * [r.uniform(0.5, 1.2), 1, 1]
            self.fscale, vin, self.delay = r.uniform(0.7, 1.3), r.uniform(11.0, 12.6), int(r.integers(0, 6))
        else:
            self.m.body_mass[:] = self.base_mass; self.m.geom_friction[self.floor] = self.base_fric
            self.fscale, vin, self.delay = 1.0, 12.0, 0
        self.model.actuator.vin = vin
        self.d.qpos[self.jq] = self.default
        mujoco.mj_forward(self.m, self.d)
        low = min(self.d.geom_xpos[f][2] - 0.004 for f in self.feet)
        self.d.qpos[2] += 0.001 - low; mujoco.mj_forward(self.m, self.d)
        self.h0 = self.d.qpos[2]
        self.ctrl.reset()
        self.t, self.steps = 0.0, 0
        self.last_a, self.qd_prev, self.tilt_err = np.zeros(self.nj), np.zeros(self.nj), np.zeros(2)
        self.queue = [self.default.copy()] * (self.delay + 1)
        self.next_push = r.uniform(2, 5)
        return self._obs(), {}

    def step(self, action):
        a = np.clip(np.asarray(action, float), -1, 1)
        goal = self.default + 0.6 * a
        x0, y0 = self.d.qpos[0], self.d.qpos[1]; power = 0.0
        if self.randomize and self.t >= self.next_push:
            self.d.qvel[0:2] += self.np_random.uniform(-0.2, 0.2, 2); self.next_push = self.t + self.np_random.uniform(3, 6)
        for _ in range(SUB):
            self.queue.append(goal); g = self.queue.pop(0)
            for j, gi in zip(self.joints, g): self.ctrl.set_q_target(j, gi)
            self.ctrl.update()
            if self.fscale != 1.0: self.m.dof_frictionloss[self.jv] *= self.fscale
            mujoco.mj_step(self.m, self.d)
            power += float(np.sum(np.abs(self.d.qfrc_actuator[self.jv] * self.d.qvel[self.jv])))
        power /= SUB; self.t += 0.02; self.steps += 1
        vx = (self.d.qpos[0] - x0) / 0.02; vy = (self.d.qpos[1] - y0) / 0.02
        g = self._grav(); tilt = np.arccos(np.clip(-g[2], -1, 1))
        w, x, y, z = self.d.qpos[3:7]; yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        cl, cr = self._contacts(); phase = (self.t / PERIOD) % 1.0
        gait = 0.3 * ((phase < 0.5 and cl and not cr) or (phase >= 0.5 and cr and not cl))
        fell = self.d.qpos[2] < 0.6 * self.h0 or tilt > 0.8
        reward = (3.0 * min(vx, self.v_cmd) + 0.3 - 1.0 * abs(vy) - 0.5 * yaw ** 2 - 1.0 * tilt ** 2 + gait
                  - 0.3 * float(np.sum((a - self.last_a) ** 2)) - 0.02 * float(np.sum(a ** 2)) - 0.003 * power)
        if fell: reward -= 10.0
        self.last_a = a
        return self._obs(), float(reward), bool(fell), self.steps >= self.max_steps, {"x": self.d.qpos[0], "y": self.d.qpos[1], "power": power}

    def render(self):
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.m, 540, 960); self._cam = mujoco.MjvCamera()
            self._cam.distance, self._cam.azimuth, self._cam.elevation = 0.9, 120, -14
        self._cam.lookat[:] = [self.d.qpos[0], self.d.qpos[1], 0.12]
        self._renderer.update_scene(self.d, camera=self._cam); return self._renderer.render()
