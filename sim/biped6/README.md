# Choosing the leg layout for a 6-servo biped (rough sketches)

> **Correction (2026-11-25): the results below are not valid.** The MJCF models had no `<compiler angle="radian"/>`, so MuJoCo read
> the joint ranges (written in radians) as degrees and every joint could move only about +-1-2 deg. The robots "shuffled" because their
> joints were almost locked. Fixed in `model.py`, `model_v2.py` and `model_v3.py`; the double-pendulum and one-servo tests had no joint
> ranges and are not affected. New comparison with biped v3 (8 servos) and where the C044s go: see the section at the end.


Two rough MuJoCo sketches with six STS3215 12 V servos ([`model.py`](model.py)): servo blocks of the real size and weighed mass (59 g),
SO-101-style brackets, a torso with the Nano; both about 0.5 kg and 0.22 m to the hip. Detailed parts are drawn only for the layout that wins.

- **roll:** per leg hip roll (sideways) → hip pitch → straight leg → ankle pitch.
- **knee:** per leg hip pitch → thigh → knee → shank → ankle pitch (no sideways joint).

Both were trained the same way ([`env.py`](env.py), [`train.py`](train.py)): PPO on the MacBook CPU, 5 M steps each (~50 min, both in
parallel), with everything from the [training checklist](../../docs/training-checklist.md) (BAM 12 V m5 on all joints, 1-step speed lag,
IMU tilt wander and noise, friction / voltage / mass / floor randomization, delay, pushes). Command: walk forward at 0.15 m/s.

| Layout | Nominal: forward / sideways / fell | Randomized ×20: forward mean (min) | Sideways drift | Falls | Mean power |
|---|---|---|---:|---:|---:|
| roll | +51 cm / −10 cm / no | 48 cm (40) | **9 cm** | 0/20 | **2.9 W** |
| knee | +55 cm / +14 cm / no | 48 cm (37) | 21 cm | 0/20 | 5.0 W |

![frames](compare_frames.png)  Videos: [walk_roll.mp4](walk_roll.mp4), [walk_knee.mp4](walk_knee.mp4).

- **Both walk 10 s without falling, also under randomization and pushes, and cover the same distance** (about 5 cm/s, slower than the
  15 cm/s command; both shuffle more than they step after this short training).
- **The roll layout drifts sideways half as much and uses about 40% less power.** With a sideways hip joint it can shift its weight over
  the standing foot; the knee layout has no sideways joint and holds its knees bent under load all the time.
- **Choice: the roll layout** (hip roll, hip pitch, ankle pitch per leg). These are rough sketches with a short CPU training; the gait
  itself (stepping instead of shuffling, speed) is a job for the longer training on the RTX 3090 and the reward recipe from Microduck.


## Biped v3 (8 servos): where do the two C044s go? (2026-11-25, in progress)

Model from the v3 CAD ([`model_v3.py`](model_v3.py)) with the board rack, two SO-101 plates, two USB boards and the cables on top
(694 g, centre of mass 134 mm). Each joint gets its own BAM model: 12 V **m5**, or C044 **m4** at 5 V (randomized 4.8-5.4 V).

**Gravity load on one leg** ([`static_load.py`](static_load.py), [table](static_load_top0.md)), as a share of the servo's stall torque
(datasheet estimate: 12 V 2.9 Nm, C044 at 5 V 0.72 Nm):

| Joint (stance leg) | Load | C044 there |
|---|---:|---:|
| hip roll (top) | 0.24 Nm, every step | 33% |
| **hip pitch** | 0.06 Nm | **9%** |
| knee, 35 deg / 60 deg bent | 0.07 / 0.15 Nm | 9% / 21% |
| ankle | 0.03-0.05 Nm | 7% |

The hip roll carries the torso and the other leg sideways whenever the robot stands on one leg, so it is the heaviest; the hip pitch
is the lightest. Chosen layout: **C044 at the hip pitch** (also short cables: the 5 V board sits on the torso right above them).
Walking trainings for all-12 V, C044 at the knee, at the hip roll and at the hip pitch (`--variant v3_12v / v3_knee / v3_roll / v3_pitch`)
are running; they show the dynamic loads while walking.
