"""Gravity load on each joint of biped v3 while it stands on one leg (the worst moment of a step), at several knee bends.

For each joint of the stance leg: the torque gravity puts on it = the moment, about the joint axis, of the weight of everything on the
far side of that joint from the stance foot (torso, other leg, ...). Static, so a walking gait needs extra on top of this (about
1.5-2x at the peaks). Friction in the gearbox can hold part of a static load, so this is the honest upper bound, not what the
servo has to deliver every moment.

Compared with an estimate of each servo's stall torque (from the datasheet, not measured):
  STS3215 12 V (1:345): 30 kg.cm = 2.9 Nm
  C044 (1:191): 7.4 V C001 19.5 kg.cm x 191/345 = 1.06 Nm, at 5 V x 5/7.4 = 0.72 Nm
(The BAM models give the same ratio: kt * vin / R is 6.4 vs 1.58, 4.0x.)

    uv run --project ~/projects/bam python sim/biped6/static_load.py [--top 50]
"""
import argparse, os, sys
import numpy as np
import mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_v3

STALL = {"12 V": 2.9, "C044 5 V": 0.72, "C044 7.4 V": 1.06}
C044_AT = {"v3_12v": (), "v3_knee": ("knee",), "v3_roll": ("roll",), "v3_pitch": ("pitch",)}


def kind(j):
    return "roll" if "roll" in j else "pitch" if "pitch" in j else "knee" if "knee" in j else "ankle"


def pose(knee, lift=0.8):
    g = {}
    for s in "lr":
        if s == "l":   # stance leg: torso straight above the ankle
            g.update({f"hip_roll_{s}": 0.0, f"hip_pitch_{s}": -knee / 2, f"knee_{s}": knee, f"ankle_{s}": -knee / 2})
        else:          # swing leg lifted
            g.update({f"hip_roll_{s}": 0.0, f"hip_pitch_{s}": -lift * 0.75, f"knee_{s}": lift, f"ankle_{s}": -0.2})
    return g


def gravity_load(m, d, joints, stance="l"):
    """Torque gravity puts on each stance-leg joint (Nm), for the foot fixed to the floor."""
    foot = m.body(f"foot_{stance}").id
    out = {}
    for j in joints:
        if not j.endswith(stance): continue
        jid = m.joint(j).id; child = m.jnt_bodyid[jid]
        # bodies in the subtree of `child` (towards the foot) do not load this joint; all others do
        sub = set(); stack = [child]
        while stack:
            b = stack.pop(); sub.add(b); stack += [c for c in range(m.nbody) if m.body_parentid[c] == b and c != b]
        assert foot in sub
        anchor = d.xanchor[jid]; axis = d.xaxis[jid]
        tau = 0.0
        for b in range(1, m.nbody):
            if b in sub: continue
            r = d.xipos[b] - anchor; f = np.array([0, 0, -9.81 * m.body_mass[b]])
            tau += np.dot(np.cross(r, f), axis)
        out[j] = abs(tau)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--top", type=float, default=0, help="grams on top of the torso"); a = ap.parse_args()
    rows = [f"Stance leg, top mass {a.top:.0f} g. Torque gravity puts on each joint, and that as a share of the servo's stall torque "
            "(estimate) for each place of the C044.", "",
            "| knee bend | joint | load | all 12 V | C044 at knees (5 V) | C044 at hip roll (5 V) | C044 at hip pitch (5 V) |", "|---:|---|---:|---:|---:|---:|---:|"]
    for knee_deg in (20, 35, 60, 90):
        for layout in ("v3_12v",):
            xml, joints = model_v3.build_xml(a.top / 1000, masses=None)
            m = mujoco.MjModel.from_xml_string(xml); d = mujoco.MjData(m)
            g = pose(np.radians(knee_deg))
            for j in joints: d.qpos[m.joint(j).qposadr[0]] = g[j]
            mujoco.mj_forward(m, d)
            load = gravity_load(m, d, joints)
            for j in ["hip_roll_l", "hip_pitch_l", "knee_l", "ankle_l"]:
                cells = []
                for lay in ("v3_12v", "v3_knee", "v3_roll", "v3_pitch"):
                    typ = "C044 5 V" if kind(j) in C044_AT[lay] else "12 V"
                    pct = 100 * load[j] / STALL[typ]
                    cells.append(f"**{pct:.0f}%**" if typ != "12 V" else f"{pct:.0f}%")
                rows.append(f"| {knee_deg}° | {j[:-2]} | {load[j]:.2f} Nm | " + " | ".join(cells) + " |")
    txt = "\n".join(rows); print(txt)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"static_load_top{a.top:.0f}.md"), "w").write(txt + "\n")
