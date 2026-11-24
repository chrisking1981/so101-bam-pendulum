# 12 V follower ID 6 (full limits) with the hole-saw pendulum, and all three 12 V units under load

This is the same 218 g pendulum (hole saw 205 g on the 100 mm hole), mounted on ID 6 by the operator "straight down by eye". BAM log values: `mass = 0.209`,
`arm_mass = 0.009`, `length = 0.100`. 12 V adapter, profile off, full torque limits, P = 4/8/16/32, D = 0. 16 runs, no bus timeouts, 31 °C afterwards.

**Zero measured before recording** with `find_vertical` (±90° sweep): the mounted position was only **0.86°** from the gravity vertical (fit residual 1.1/1000).
The corrected zero, raw 2150, was used for all runs.

## Manual tests

| Test | Sag | PWM |
|---|---:|---:|
| Hold at 0, P = 32 | 0.26° | 3.2% |
| Hold at +45°, P = 32 | 0.44° | 4.0% |
| Hold at +90°, P = 32 | 0.62° | 6.4% |
| Hold at −90°, P = 32 | 0.53° | 5.6% |
| Hold at +90°, P = 8 | 0.79° | 3.0% |
| Release at 45° | does not move | — |

## Three 12 V units, same pendulum

The ID 2 runs are the zero-corrected copies (its arm was mounted 8.26° off vertical). The ID 3 zero was not measured.

| Trajectory | kp | Tracking error ID3 / ID2 / ID6 (°) | Lag ID3 / ID2 / ID6 (ms) | \|ID6 − ID2\| (°) | \|ID6 − ID3\| (°) |
|---|---:|---|---|---:|---:|
| up_and_down | 4 | 5.79 / 6.18 / 6.03 | 337 / 348 / 336 | 8.10 | 0.16 |
| up_and_down | 8 | 3.10 / 3.09 / 3.03 | 174 / 178 / 174 | 8.21 | 0.07 |
| up_and_down | 16 | 1.57 / 1.60 / 1.53 | 89 / 92 / 90 | 8.23 | 0.07 |
| up_and_down | 32 | 0.86 / 0.86 / 0.86 | 48 / 49 / 48 | 8.24 | 0.07 |
| lift_and_drop | 4 | 13.53 / 13.47 / 13.62 | 322 / 320 / 326 | 8.00 | 0.17 |
| lift_and_drop | 8 | 7.28 / 7.23 / 7.33 | 165 / 164 / 167 | 8.03 | 0.15 |
| lift_and_drop | 16 | 3.80 / 3.77 / 3.84 | 84 / 83 / 85 | 8.15 | 0.11 |
| lift_and_drop | 32 | 1.97 / 1.94 / 1.97 | 43 / 43 / 44 | 8.19 | 0.10 |
| sin_sin | 4 | 16.66 / 17.40 / 17.49 | 235 / 235 / 236 | 7.97 | 0.19 |
| sin_sin | 8 | 10.70 / 10.79 / 10.83 | 137 / 137 / 137 | 8.09 | 0.12 |
| sin_sin | 16 | 6.21 / 6.23 / 6.26 | 75 / 75 / 75 | 8.15 | 0.09 |
| sin_sin | 32 | 3.31 / 3.35 / 3.37 | 39 / 39 / 39 | 8.23 | 0.09 |
| sin_time_square | 4 | 30.02 / 30.28 / 30.22 | 215 / 217 / 216 | 7.48 | 0.39 |
| sin_time_square | 8 | 26.32 / 26.44 / 26.31 | 167 / 167 / 167 | 7.78 | 0.36 |
| sin_time_square | 16 | 20.71 / 20.74 / 20.56 | 116 / 118 / 117 | 8.06 | 0.27 |
| sin_time_square | 32 | 16.20 / 16.24 / 16.32 | 89 / 89 / 91 | 7.40 | 0.63 |

Mean trace difference (lift_and_drop only before the release): ID6−ID2 (both with measured zero) 8.02°, ID6−ID3 (ID3 zero unknown) 0.19°.
ID3 after release at -90°: kp4 -79→-80°, kp8 -86→-43°, kp16 -89→-35°, kp32 -89→-36°
ID2 after release at -90°: kp4 -71→-70°, kp8 -78→-49°, kp16 -80→-80°, kp32 -81→-81°
ID6 after release at -90°: kp4 -79→-79°, kp8 -86→-86°, kp16 -89→-88°, kp32 -89→-89°

- **The tracking error and lag of all three units are practically identical under load:** within about 2% on every run.
- **ID 6 vs ID 3: 0.19° mean trace difference.** ID 3's unmeasured zero was therefore probably close to vertical as well.
- **ID 6 vs ID 2: a constant ~8°.** That is not a servo difference. ID 2 executed the same commands relative to an arm mounted 8.26° off vertical, so after the zero correction its
  whole trajectory is shifted by that amount relative to gravity. Its tracking error matches the others.
- **Release at −90° (`lift_and_drop`):** ID 6 and ID 2 do not move. ID 3 slips back to −35…−43° at kp 8/16/32. So ID 3 has lower static gearbox friction than the other two;
  2 of 3 units hold this load with the torque off.
