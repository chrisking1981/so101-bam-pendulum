# 12 V follower ID 2 with the same hole-saw pendulum (218 g, 100 mm), and both 12 V units compared under load

This is the same pendulum as [ID 3](../20261124-110331-id3-pendulum-holesaw-218g/README.md), moved over without changes. BAM log values: `mass = 0.209`,
`arm_mass = 0.009`, `length = 0.100`. 12 V adapter, profile off, P = 4/8/16/32, D = 0. 16 runs, no bus timeouts, 29 °C afterwards.

**Zero caveat.** These 1:345 12 V servos are not back-driven by this pendulum, so the arm does not swing to the bottom when the torque is off. The "hanging" zero
(raw 2469 here, 2055 on ID 3) is the position the arm was mounted in, not necessarily vertical. BAM's `q_offset` parameter (±0.2 rad) can absorb a small error;
it was not checked against a plumb line.

## Manual tests

| Test | ID 2 sag / PWM | ID 3 sag / PWM |
|---|---|---|
| Hold at +45°, P = 32 | 0.62° / 6.4% | 0.53° / 5.6% |
| Hold at +90°, P = 32 | 0.62° / 5.6% | 0.62° / 6.4% |
| Hold at −90°, P = 32 | 0.53° / 5.6% | 0.70° / 7.2% |
| Hold at +90°, P = 8 | 0.62° / 2.6% | 0.79° / 3.0% |
| Release at 45° | does not move | does not move |

## ID 3 vs ID 2, same pendulum

| Trajectory | kp | Tracking error ID3 / ID2 (°) | Lag ID3 / ID2 (ms) | \|ID3 − ID2\| (°) |
|---|---:|---|---|---:|
| up_and_down | 4 | 5.79 / 6.18 | 337 / 348 | 0.31 |
| up_and_down | 8 | 3.10 / 3.09 | 174 / 178 | 0.15 |
| up_and_down | 16 | 1.57 / 1.60 | 89 / 92 | 0.09 |
| up_and_down | 32 | 0.86 / 0.86 | 48 / 49 | 0.06 |
| lift_and_drop | 4 | 13.53 / 13.47 | 322 / 320 | 0.77 |
| lift_and_drop | 8 | 7.28 / 7.23 | 165 / 164 | 7.40 |
| lift_and_drop | 16 | 3.80 / 3.77 | 84 / 83 | 34.08 |
| lift_and_drop | 32 | 1.97 / 1.94 | 43 / 43 | 33.46 |
| sin_sin | 4 | 16.66 / 17.40 | 235 / 235 | 0.21 |
| sin_sin | 8 | 10.70 / 10.79 | 137 / 137 | 0.13 |
| sin_sin | 16 | 6.21 / 6.23 | 75 / 75 | 0.13 |
| sin_sin | 32 | 3.31 / 3.35 | 39 / 39 | 0.08 |
| sin_time_square | 4 | 30.02 / 30.28 | 215 / 217 | 0.44 |
| sin_time_square | 8 | 26.32 / 26.44 | 167 / 167 | 0.34 |
| sin_time_square | 16 | 20.71 / 20.74 | 116 / 118 | 0.31 |
| sin_time_square | 32 | 16.20 / 16.24 | 89 / 89 | 0.35 |

Mean |ID3 − ID2| with 218 g: 4.89° (median 0.31°); ID2 tracking error vs ID3 +0.9%.
ID3 lift_and_drop kp32 after release: start -89.5°, end -35.9°, max -35.9°
ID2 lift_and_drop kp32 after release: start -89.5°, end -89.4°, max -89.4°

- **While the motor is driving, the two units are practically identical under load:** 0.06–0.44° on every run except `lift_and_drop`, and tracking error within 1%.
- **The big differences are in `lift_and_drop` after the release at −90°.** ID 3 slips back to −36°; ID 2 does not move at all (−89.5° → −89.4°). At −90° the gravity torque is
  about 0.21 Nm. That is right at the threshold where the gearbox can be back-driven, and the units sit on either side of it. This is the same stick-slip effect seen
  on the C044 units, but much larger here.
- **For RL:** with torque on, one 12 V model fits both units. Torque-off behaviour (falling limbs, compliant modes) depends on static friction that differs per unit
  and cannot be predicted precisely. Randomize it widely, or avoid switching torque off.
