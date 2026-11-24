# Third STS3215 12 V follower servo (ID 6, gripper): no-load replay with LeRobot's gripper torque limit

This is follower servo ID 6, the **gripper** of the Pro kit: model 777, firmware 3.10, max voltage limit 14.0 V, 12 V adapter.

- **Profile:** stored off in EEPROM (85 = 0, 41 = 0) and verified after unplugging the adapter.
- **Step test**, +90° at P = 32: 5° at 64.3 ms. ID 2 and ID 3 took 55.0 and 56.5 ms.

**LeRobot limits the gripper servo** (EEPROM, unchanged here), so that it cannot crush objects or overheat:

| Register | ID 6 (gripper) | ID 2 / ID 3 |
|---|---:|---:|
| `max_torque_limit` / `torque_limit` | **500** (50% PWM cap) | 1000 |
| `protection_current` | **250** | 310 |
| `overload_torque` | **25** | not read; higher |
| `protective_torque` | 20 | not read |

## Three 12 V units without load

| Trajectory | kp | Tracking error ID3 / ID2 / ID6 (°) | Lag ID3 / ID2 / ID6 (ms) | \|ID6 − ID3\| (°) | \|ID6 − ID2\| (°) |
|---|---:|---|---|---:|---:|
| up_and_down | 4 | 5.49 / 5.48 / 5.45 | 303 / 299 / 295 | 0.17 | 0.11 |
| up_and_down | 8 | 2.76 / 2.83 / 2.77 | 150 / 151 / 152 | 0.07 | 0.08 |
| up_and_down | 16 | 1.45 / 1.47 / 1.48 | 78 / 78 / 78 | 0.04 | 0.04 |
| up_and_down | 32 | 0.78 / 0.78 / 0.77 | 41 / 41 / 42 | 0.04 | 0.04 |
| lift_and_drop | 4 | 12.30 / 12.23 / 12.25 | 295 / 290 / 290 | 0.26 | 0.09 |
| lift_and_drop | 8 | 6.54 / 6.61 / 6.52 | 148 / 148 / 149 | 0.01 | 0.08 |
| lift_and_drop | 16 | 3.34 / 3.35 / 3.38 | 75 / 75 / 75 | 0.08 | 0.08 |
| lift_and_drop | 32 | 1.70 / 1.75 / 1.77 | 38 / 38 / 38 | 0.01 | 0.01 |
| sin_sin | 4 | 17.27 / 17.04 / 16.92 | 244 / 239 / 238 | 0.43 | 0.12 |
| sin_sin | 8 | 10.71 / 10.75 / 11.34 | 138 / 137 / 147 | 0.69 | 0.65 |
| sin_sin | 16 | 6.20 / 6.23 / 7.36 | 75 / 75 / 95 | 1.29 | 1.29 |
| sin_sin | 32 | 3.29 / 3.32 / 4.91 | 39 / 39 / 63 | 1.65 | 1.64 |
| brutal | 4 | 14.16 / 14.03 / 14.87 | 388 / 387 / 399 | 0.78 | 0.68 |
| brutal | 8 | 9.34 / 8.70 / 11.91 | 292 / 292 / 373 | 2.50 | 2.50 |
| brutal | 16 | 7.06 / 6.97 / 10.89 | 232 / 232 / 351 | 4.00 | 3.90 |
| brutal | 32 | 6.13 / 6.21 / 10.29 | 201 / 201 / 342 | 4.29 | 4.31 |
| sin_time_square | 4 | 30.30 / 30.01 / 30.55 | 221 / 219 / 220 | 0.84 | 0.65 |
| sin_time_square | 8 | 26.54 / 26.40 / 28.06 | 167 / 168 / 192 | 5.31 | 5.13 |
| sin_time_square | 16 | 20.61 / 20.65 / 26.29 | 117 / 118 / 174 | 9.95 | 9.79 |
| sin_time_square | 32 | 16.11 / 16.03 / 23.62 | 90 / 89 / 167 | 11.76 | 11.74 |

Mean trace difference: ID6−ID3 2.21°, ID6−ID2 2.15°, ID2−ID3 0.14°. ID6 tracking error vs ID3 +15.6%.

- **On slow trajectories all three are identical**: up_and_down and lift_and_drop within 0.01–0.26°.
- **On fast ones (brutal, sin_time_square, sin_sin at high P) ID 6 is much slower**, for example brutal kp 32 lag 342 ms vs 201 ms, because its PWM is capped at 50%. This is a
  configuration difference, not a different servo.
- **For a robot built from follower servos, check and equalise these registers on every servo.** A gripper servo left at LeRobot's limits has half the
  torque and an overload cut-out at 25% of the rated torque.
