"""RL environment for the two-link pendulum: move hip and knee to commanded angles (the step-2a sim2real test).

Everything learned on the one-servo pipeline test is in from the start (docs/training-checklist.md):
- BAM 12 V m5 in the loop on both joints (kp_fw 32), 2 ms physics, policy at 50 Hz.
- Servo speed register one control step late and quantised to 0.0767 rad/s; encoder noise +-0.001 rad.
- Nano on the lower link: tilt = hip + knee with a slow +-1 deg (std) wander, gyro = hip rate + knee rate with +-0.03 rad/s noise.
- Strong penalty on action changes (3.0), so the policy holds still.
Randomized per episode: BAM friction x0.7-1.3, supply 11.0-12.6 V, masses (upper link +-25 %, servo 2 +-5 %, lower assembly +-15 %),
extra command delay 0-10 ms, small cable spring (0-0.01 N m/rad) and friction (0-0.01 N m) per joint.
Observation (13): q_hip, q_knee, 0.1 qd_hip, 0.1 qd_knee, tilt, 0.1 gyro, target_hip, target_knee, err_hip, err_knee, last action (2), 1.
Action (2): goal = 1.4 rad * a per joint, clipped to +-80 deg (cable to servo 2).
"""
import os, sys
import numpy as np
import gymnasium as gym
import mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_model import build, PARAMS
from bam.model import load_model
from bam.mujoco import MujocoController

KP_FW, ACTION_SCALE, LIM = 32, 1.4, np.radians(80)
SUB, QD_Q = 10, 0.0767


def test_targets():
    seq = [(0, 0), (40, 0), (40, 50), (-30, 50), (-30, -40), (20, -60), (0, 30), (50, -30), (0, 0)]
    return [(1.5 * i, np.radians(h), np.radians(k)) for i, (h, k) in enumerate(seq)]


class DPEnv(gym.Env):
    def __init__(self, randomize=True, episode_s=6.0, schedule=None):
        super().__init__()
        self.randomize, self.max_steps, self.schedule = randomize, int(episode_s * 50), schedule
        self.action_space = gym.spaces.Box(-1, 1, (2,), np.float32)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (13,), np.float32)
        self.model = load_model(PARAMS); self.model.actuator.kp = KP_FW

    def _targets(self):
        if self.schedule is not None:
            row = [r for r in self.schedule if r[0] <= self.t + 1e-9][-1]; return np.array(row[1:])
        if self.t >= self.next_change:
            r = self.np_random
            self.tg = np.array([r.uniform(-1.0, 1.0), r.uniform(-1.1, 1.1)]); self.next_change = self.t + r.uniform(0.8, 2.0)
        return self.tg

    def _obs(self):
        r = self.np_random; q, qd = self.d.qpos.copy(), self.d.qvel.copy()
        if self.randomize:
            self.tilt_err += -self.tilt_err * 0.01 + np.radians(1.0) * np.sqrt(0.02) * r.standard_normal()
            qn = q + r.uniform(-0.001, 0.001, 2)
            qdn = np.round((self.qd_prev + r.uniform(-0.05, 0.05, 2)) / QD_Q) * QD_Q
            tilt = q.sum() + self.tilt_err + r.uniform(-0.003, 0.003); gyro = qd.sum() + r.uniform(-0.03, 0.03)
        else:
            qn, qdn, tilt, gyro = q, np.round(self.qd_prev / QD_Q) * QD_Q, q.sum(), qd.sum()
        self.qd_prev = qd
        tg = self._targets()
        return np.concatenate([qn, 0.1 * qdn, [tilt, 0.1 * gyro], tg, qn - tg, self.last_a, [1.0]]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed); r = self.np_random
        if self.randomize:
            scale = dict(upper_link=r.uniform(0.75, 1.25), servo2=r.uniform(0.95, 1.05), lower_link=r.uniform(0.85, 1.15),
                         nano=r.uniform(0.85, 1.15), screws=r.uniform(0.85, 1.15), cable=r.uniform(0.6, 1.4))
            self.fscale, vin, self.delay = r.uniform(0.7, 1.3), r.uniform(11.0, 12.6), int(r.integers(0, 6))
            self.k_cable, self.f_cable = r.uniform(0, 0.01, 2), r.uniform(0, 0.01, 2)
        else:
            scale, self.fscale, vin, self.delay = None, 1.0, 12.0, 0
            self.k_cable, self.f_cable = np.zeros(2), np.zeros(2)
        self.m = build(scale=scale); self.d = mujoco.MjData(self.m)
        self.model.actuator.vin = vin
        self.ctrl = MujocoController(self.model, ["hip", "knee"], self.m, self.d)
        self.d.qpos[:] = r.uniform(-0.05, 0.05, 2) if self.randomize else 0.0
        mujoco.mj_forward(self.m, self.d)
        self.t, self.steps, self.last_a, self.tilt_err, self.qd_prev = 0.0, 0, np.zeros(2), 0.0, np.zeros(2)
        self.tg, self.next_change = np.zeros(2), r.uniform(0.3, 1.0)
        self.queue = [np.zeros(2)] * (self.delay + 1)
        return self._obs(), {}

    def step(self, action):
        a = np.clip(np.asarray(action, float), -1, 1)
        goal = np.clip(ACTION_SCALE * a, -LIM, LIM)
        for _ in range(SUB):
            self.queue.append(goal); g = self.queue.pop(0)
            self.ctrl.set_q_target("hip", g[0]); self.ctrl.set_q_target("knee", g[1]); self.ctrl.update()
            if self.fscale != 1.0:
                self.m.dof_frictionloss[:] = self.m.dof_frictionloss * self.fscale + self.f_cable
            else:
                self.m.dof_frictionloss[:] += self.f_cable
            self.d.qfrc_applied[:] = -self.k_cable * self.d.qpos
            mujoco.mj_step(self.m, self.d)
        self.t += 0.02; self.steps += 1
        tg = self._targets(); err = self.d.qpos - tg
        reward = -np.abs(err).sum() - 3.0 * float(np.sum((a - self.last_a) ** 2)) - 0.01 * float(np.sum(np.abs(self.d.qvel) * (np.abs(err) < 0.05)))
        self.last_a = a
        return self._obs(), float(reward), False, self.steps >= self.max_steps, {"q": self.d.qpos.copy(), "target": tg, "goal": goal}
