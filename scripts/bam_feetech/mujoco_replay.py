# Replay real pendulum logs in MuJoCo and compare the simulated angle with the measured one.
#
# Two actuator variants on the same MJCF pendulum:
#   bam     : <motor> actuator driven every step by bam.mujoco.MujocoController (BAM model in the loop)
#   pd      : MuJoCo <position> actuator with constant kp/damping/frictionloss/armature from bam.to_mujoco
#             (the classic "fitted PD" approach, deprecated in BAM)
#
#   python -m bam.feetech.mujoco_replay --params fits/C046/m4.json --logdir fit/c046/val_kp8 [--plot out.png]
import argparse, glob, json, os
import numpy as np
import mujoco
from bam.model import load_model
from bam.mujoco import MujocoController
from bam.to_mujoco import to_mujoco

p = argparse.ArgumentParser()
p.add_argument("--params", required=True)
p.add_argument("--logdir", nargs="+", required=True)
p.add_argument("--dt", type=float, default=0.001)
p.add_argument("--vin", type=float, default=7.4)
p.add_argument("--plot")
p.add_argument("--md")
a = p.parse_args()

XML = """
<mujoco>
  <option timestep="{dt}" gravity="0 0 -9.81" integrator="implicitfast"/>
  <worldbody>
    <body name="arm" pos="0 0 0">
      <joint name="j" type="hinge" axis="0 1 0" {joint_extra}/>
      {mass_geom}
    </body>
  </worldbody>
  <actuator>{act}</actuator>
</mujoco>
"""


def build(log, variant, pd_params=None):
    m, L = log["mass"], log["length"]
    if m > 0 and L > 0:
        # point mass hanging at -L (q = 0 is straight down)
        mass_geom = f'<geom type="sphere" size="0.005" pos="0 0 {-L}" mass="{m}" contype="0" conaffinity="0"/>'
    else:
        mass_geom = '<geom type="sphere" size="0.005" mass="1e-6" contype="0" conaffinity="0"/>'
    if variant == "bam":
        act, joint_extra = '<motor name="j" joint="j" gear="1"/>', ""
    else:
        pp = pd_params
        act = f'<position name="j" joint="j" kp="{pp["kp"]}" forcerange="{-pp["forcerange"]} {pp["forcerange"]}" forcelimited="true"/>'
        joint_extra = f'damping="{pp["damping"]}" frictionloss="{pp["frictionloss"]}" armature="{pp["armature"]}"'
    return mujoco.MjModel.from_xml_string(XML.format(dt=a.dt, joint_extra=joint_extra, mass_geom=mass_geom, act=act))


def run(log, variant):
    model = load_model(a.params)
    act = model.actuator
    act.kp = log["kp"]
    act.vin = a.vin
    pd_params = to_mujoco(act) if variant == "pd" else None
    mj = build(log, variant, pd_params)
    d = mujoco.MjData(mj)
    ent = log["entries"]
    t_log = np.array([e["timestamp"] for e in ent])
    d.qpos[0] = ent[0]["position"]
    mujoco.mj_forward(mj, d)
    ctrl = MujocoController(model, "j", mj, d) if variant == "bam" else None
    out = []
    i = 0
    T = t_log[-1]
    while d.time < T:
        while i + 1 < len(t_log) and t_log[i + 1] <= d.time:
            i += 1
        goal, on = ent[i]["goal_position"], ent[i]["torque_enable"]
        if variant == "bam":
            ctrl.set_q_target("j", goal)
            ctrl.update()
            if not on:  # torque released: BAM gives zero motor torque, its friction stays applied
                d.ctrl[0] = 0.0
        else:
            d.ctrl[0] = goal
            mj.actuator_gainprm[0, 0] = pd_params["kp"] if on else 0.0
            mj.actuator_biasprm[0, 1] = -pd_params["kp"] if on else 0.0
        mujoco.mj_step(mj, d)
        out.append((d.time, d.qpos[0]))
    out = np.array(out)
    sim = np.interp(t_log, out[:, 0], out[:, 1])
    real = np.array([e["position"] for e in ent])
    return t_log, sim, real


logs = []
for dd in a.logdir:
    for f in sorted(glob.glob(os.path.join(dd, "*.json"))):
        logs.append(json.load(open(f)))
order = ["up_and_down", "lift_and_drop", "sin_sin", "brutal", "sin_time_square"]
logs.sort(key=lambda l: (l["mass"], order.index(l["trajectory"]), l["kp"]))

rows, traces = [], []
for l in logs:
    t, sb, real = run(l, "bam")
    _, sp, _ = run(l, "pd")
    eb, ep = np.degrees(np.mean(np.abs(sb - real))), np.degrees(np.mean(np.abs(sp - real)))
    rows.append((l["mass"], l["trajectory"], l["kp"], eb, ep))
    traces.append((l, t, real, sb, sp))

lines = ["| mass (kg) | trajectory | kp | MuJoCo + BAM in the loop (°) | MuJoCo position actuator from to_mujoco (°) |", "|---:|---|---:|---:|---:|"]
for m, tr, kp, eb, ep in rows:
    lines.append(f"| {m:.3f} | {tr} | {kp} | {eb:.2f} | {ep:.2f} |")
r = np.array([[x[3], x[4]] for x in rows]); nl = np.array([x[1] != "lift_and_drop" for x in rows])
lines.append(f"| **mean** | | | **{r[:,0].mean():.2f}** | **{r[:,1].mean():.2f}** |")
lines.append(f"| **mean without lift_and_drop** | | | **{r[nl,0].mean():.2f}** | **{r[nl,1].mean():.2f}** |")
txt = "\n".join(lines); print(txt)
if a.md:
    open(a.md, "w").write(txt + "\n")
if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    n = len(traces); cols = 4; rws = int(np.ceil(n / cols))
    fig, axs = plt.subplots(rws, cols, figsize=(4.3 * cols, 2.6 * rws), squeeze=False)
    for ax, (l, t, real, sb, sp) in zip(axs.flat, traces):
        g = np.degrees([e["goal_position"] for e in l["entries"]])
        ax.plot(t, g, "k:", lw=1, label="goal")
        ax.plot(t, np.degrees(real), lw=1.6, label="real servo")
        ax.plot(t, np.degrees(sb), lw=1.1, label="MuJoCo + BAM")
        ax.plot(t, np.degrees(sp), lw=1.0, alpha=.8, label="MuJoCo position actuator")
        ax.set_title(f"{l['trajectory']} kp{l['kp']} {int(l['mass']*1000)} g", fontsize=9); ax.grid(alpha=.3)
    for ax in axs.flat[n:]:
        ax.axis("off")
    axs.flat[0].legend(fontsize=7)
    fig.supylabel("angle (deg)"); fig.supxlabel("time (s)"); fig.tight_layout(); fig.savefig(a.plot, dpi=105)
    print("plot ->", a.plot)
