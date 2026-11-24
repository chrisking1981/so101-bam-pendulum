# 12 V follower ID 6 (ex-gripper) with full torque limits: no-load replay, all three 12 V units

LeRobot's gripper limits on ID 6 were stored in EEPROM with the operator's approval, set to the values of the joint servos:

| Register | Before (LeRobot gripper) | After |
|---|---:|---:|
| `max_torque_limit` | 500 | **1000** |
| `torque_limit` | 500 | **1000** |
| `protection_current` | 250 | **310** (as read on ID 3) |
| `overload_torque` | 25 | **80** (factory value read on the 7.4 V C001; not yet read on ID 2/3) |

- **Verification:** all four values were read back after unplugging the 12 V adapter, together with the profile (85 = 0, 41 = 0).
- **Step test**, +90° at P = 32: 5° at **55.8 ms**. With the limits it took 64.3 ms; ID 2 and ID 3 took 55.0 and 56.5 ms.
- **Caution:** if this servo is used as a LeRobot gripper again, set the gripper limits back (or recalibrate with LeRobot), or the gripper can overheat when it grips.

## ID 3 / ID 2 / ID 6 with full limits / ID 6 with the gripper limits

| Trajectory | kp | Tracking error ID3 / ID2 / ID6 full / ID6 limited (°) | Lag ID3 / ID2 / ID6 full / ID6 limited (ms) | \|ID6 full − ID3\| (°) |
|---|---:|---|---|---:|
| up_and_down | 4 | 5.49 / 5.48 / 5.36 / 5.45 | 303 / 299 / 296 / 295 | 0.18 |
| up_and_down | 8 | 2.76 / 2.83 / 2.80 / 2.77 | 150 / 151 / 152 / 152 | 0.07 |
| up_and_down | 16 | 1.45 / 1.47 / 1.44 / 1.48 | 78 / 78 / 78 / 78 | 0.05 |
| up_and_down | 32 | 0.78 / 0.78 / 0.78 / 0.77 | 41 / 41 / 41 / 42 | 0.04 |
| lift_and_drop | 4 | 12.30 / 12.23 / 12.26 / 12.25 | 295 / 290 / 289 / 290 | 0.40 |
| lift_and_drop | 8 | 6.54 / 6.61 / 6.47 / 6.52 | 148 / 148 / 148 / 149 | 0.08 |
| lift_and_drop | 16 | 3.34 / 3.35 / 3.36 / 3.38 | 75 / 75 / 75 / 75 | 0.08 |
| lift_and_drop | 32 | 1.70 / 1.75 / 1.74 / 1.77 | 38 / 38 / 38 / 38 | 0.01 |
| sin_sin | 4 | 17.27 / 17.04 / 16.87 / 16.92 | 244 / 239 / 237 / 238 | 0.50 |
| sin_sin | 8 | 10.71 / 10.75 / 10.82 / 11.34 | 138 / 137 / 137 / 147 | 0.14 |
| sin_sin | 16 | 6.20 / 6.23 / 6.22 / 7.36 | 75 / 75 / 75 / 95 | 0.07 |
| sin_sin | 32 | 3.29 / 3.32 / 3.29 / 4.91 | 39 / 39 / 39 / 63 | 0.06 |
| brutal | 4 | 14.16 / 14.03 / 14.18 / 14.87 | 388 / 387 / 384 / 399 | 0.21 |
| brutal | 8 | 9.34 / 8.70 / 9.81 / 11.91 | 292 / 292 / 291 / 373 | 0.12 |
| brutal | 16 | 7.06 / 6.97 / 7.01 / 10.89 | 232 / 232 / 231 / 351 | 0.10 |
| brutal | 32 | 6.13 / 6.21 / 6.09 / 10.29 | 201 / 201 / 200 / 342 | 0.06 |
| sin_time_square | 4 | 30.30 / 30.01 / 30.24 / 30.55 | 221 / 219 / 217 / 220 | 0.48 |
| sin_time_square | 8 | 26.54 / 26.40 / 26.42 / 28.06 | 167 / 168 / 167 / 192 | 0.16 |
| sin_time_square | 16 | 20.61 / 20.65 / 20.52 / 26.29 | 117 / 118 / 118 / 174 | 0.32 |
| sin_time_square | 32 | 16.11 / 16.03 / 15.96 / 23.62 | 90 / 89 / 89 / 167 | 0.33 |

With full limits: mean |ID6 − ID3| 0.17° (median 0.11°), tracking error +0.0% vs ID3. With LeRobot gripper limits it was 2.21°.

**With equal limits, all three 12 V units are practically identical without load:** pairs differ by 0.14–0.17° mean, and the tracking error is the same within 0.1%.
The earlier 2.2° difference of ID 6 came entirely from the LeRobot gripper limits.
