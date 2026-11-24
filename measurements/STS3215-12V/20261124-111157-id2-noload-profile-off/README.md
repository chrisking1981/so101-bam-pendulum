# Second STS3215 12 V follower servo (ID 2): no-load replay and unit comparison

This is the second follower servo from the same Pro kit: bus ID 2 (shoulder lift), model 777, firmware 3.10, max voltage limit 14.0 V. Supply: 12 V adapter through
the follower board; the servo reads 11.9 V.

- **As found:** P = 16, D = 32, profile on (85 = 254, 41 = 0, 86 = 1).
- **Profile:** stored off in EEPROM. Verified after unplugging the adapter for about 3 s: 85 = 0, 41 = 0.
- **Step test**, +90° at P = 32: load > 0 at 1.6 ms, first tick at 16.2 ms, 5° at **55.0 ms**. Unit ID 3 took 56.5 ms.
- All 20 Rhoban no-load logs replayed, P = Rhoban kp, D = 0, `--zero-here` after centring at raw 2045.

## ID 3 vs ID 2, identical commands

| Trajectory | kp | Tracking error ID3 / ID2 (°) | Lag ID3 / ID2 (ms) | \|ID3 − ID2\| (°) |
|---|---:|---|---|---:|
| up_and_down | 4 | 5.49 / 5.48 | 303 / 299 | 0.10 |
| up_and_down | 8 | 2.76 / 2.83 | 150 / 151 | 0.08 |
| up_and_down | 16 | 1.45 / 1.47 | 78 / 78 | 0.04 |
| up_and_down | 32 | 0.78 / 0.78 | 41 / 41 | 0.04 |
| lift_and_drop | 4 | 12.30 / 12.23 | 295 / 290 | 0.31 |
| lift_and_drop | 8 | 6.54 / 6.61 | 148 / 148 | 0.08 |
| lift_and_drop | 16 | 3.34 / 3.35 | 75 / 75 | 0.01 |
| lift_and_drop | 32 | 1.70 / 1.75 | 38 / 38 | 0.01 |
| sin_sin | 4 | 17.27 / 17.04 | 244 / 239 | 0.38 |
| sin_sin | 8 | 10.71 / 10.75 | 138 / 137 | 0.11 |
| sin_sin | 16 | 6.20 / 6.23 | 75 / 75 | 0.07 |
| sin_sin | 32 | 3.29 / 3.32 | 39 / 39 | 0.06 |
| brutal | 4 | 14.16 / 14.03 | 388 / 387 | 0.13 |
| brutal | 8 | 9.34 / 8.70 | 292 / 292 | 0.10 |
| brutal | 16 | 7.06 / 6.97 | 232 / 232 | 0.11 |
| brutal | 32 | 6.13 / 6.21 | 201 / 201 | 0.03 |
| sin_time_square | 4 | 30.30 / 30.01 | 221 / 219 | 0.39 |
| sin_time_square | 8 | 26.54 / 26.40 | 167 / 168 | 0.24 |
| sin_time_square | 16 | 20.61 / 20.65 | 117 / 118 | 0.21 |
| sin_time_square | 32 | 16.11 / 16.03 | 90 / 89 | 0.26 |

Mean |ID3 − ID2| 0.14° (median 0.10°); ID2 tracking error vs ID3 -0.1%.

**These two 12 V units are almost identical without load: 0.14° mean difference, tracking error within 0.1%.** The pairs of 7.4 V leader servos differed
by 0.27° (two C044) and 0.26–0.48° (three C046). Both 12 V units differ from Rhoban's 7.4 V unit by about 1.3° (ID 2: 1.29°, ID 3: 1.33°), so that is a
difference between servo types, not between units.
