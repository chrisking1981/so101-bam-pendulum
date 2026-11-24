# 12 V follower ID 2 with two hole saws (401 g total), compared with ID 6

This is the same pendulum as in the ID 6 run of 20261124-120409: both hole saws on the 100 mm hole, 401 g weighed in total. BAM log values: `mass = 0.392`,
`arm_mass = 0.009`, `length = 0.100`. 12 V adapter, profile off, full torque limits, P = 4/8/16/32, D = 0. 16 runs, no bus timeouts, 28 °C afterwards.

**Zero measured before recording** with `find_vertical` (±90° sweep): the hanging position was **0.77°** from the gravity vertical (fit residual 1.7/1000, gravity
amplitude 61/1000 PWM, friction half-band 53/1000). The corrected zero, raw 2385, was used for all runs.

## Manual tests

| Test | Sag ID 2 | PWM ID 2 | Sag ID 6 | PWM ID 6 |
|---|---:|---:|---:|---:|
| Hold at 0, P = 32 | 0.18° | 2.4% | 0.70° | 0% |
| Hold at +45°, P = 32 | 0.97° | 9.6% | 0.79° | 8.0% |
| Hold at +90°, P = 32 | 1.32° | 12.8% | 1.23° | 12.0% |
| Hold at −90°, P = 32 | 0.97° | 9.6% | 0.97° | 9.6% |
| Hold at +90°, P = 8 | 1.32° | 4.4% | 1.23° | 12.0% |
| Release at 45° | does not move | — | does not move | — |

## ID 6 vs ID 2, same pendulum

| Trajectory | kp | RMS error ID6 / ID2 (°) | Lag ID6 / ID2 (ms) | Peak PWM ID6 / ID2 (%) |
|---|---:|---|---|---|
| up_and_down | 4 | 9.42 / 9.81 | 351 / 369 | 21 / 22 |
| up_and_down | 8 | 4.85 / 5.03 | 186 / 193 | 22 / 22 |
| up_and_down | 16 | 2.51 / 2.49 | 97 / 98 | 24 / 22 |
| up_and_down | 32 | 1.33 / 1.32 | 52 / 52 | 23 / 23 |
| lift_and_drop | 4 | 16.07 / 16.61 | 325 / 335 | 26 / 27 |
| lift_and_drop | 8 | 8.94 / 8.83 | 180 / 175 | 29 / 28 |
| lift_and_drop | 16 | 4.59 / 4.52 | 92 / 90 | 30 / 29 |
| lift_and_drop | 32 | 2.37 / 2.38 | 48 / 47 | 30 / 30 |
| sin_sin | 4 | 20.81 / 21.57 | 238 / 242 | 43 / 43 |
| sin_sin | 8 | 13.22 / 13.44 | 138 / 140 | 58 / 59 |
| sin_sin | 16 | 7.73 / 7.68 | 73 / 75 | 71 / 67 |
| sin_sin | 32 | 4.01 / 4.11 | 39 / 39 | 69 / 70 |
| sin_time_square | 4 | 36.06 / 36.49 | 224 / 229 | 65 / 65 |
| sin_time_square | 8 | 33.37 / 33.34 | 155 / 156 | 94 / 96 |
| sin_time_square | 16 | 30.02 / 27.57 | 112 / 98 | 100 / 100 |
| sin_time_square | 32 | 22.84 / 23.34 | 68 / 68 | 100 / 100 |

## Findings

- **The two units are practically identical under the heavier load.** Tracking error and lag agree within ~2–5% on every run. The one outlier is sin_time_square
  kp 16, which was also the outlier in the ID 6 load series. That run lies at the saturation edge and is sensitive to small differences.
- **Both units are back-driven by 401 g at −90°.** After the torque goes off, the arm falls back to near vertical. ID 2 stops at −1…−8°, ID 6 at +1…+9°. The
  gearbox friction band is about the same on both, but on the other side of vertical: the arm stops as soon as the gravity torque drops below the static friction.
  Both hold at 45°.
- **The first manual-test attempt stopped on the temperature guard** (5 reads above 45 °C in a row, peak 54 °C). The servo read 25–27 °C right afterwards.
  The present-temperature register has sporadic false reads: about 0.3% of all samples in every 12 V log (also the earlier 218 g runs), up to 150 °C, mostly
  under high load. The guard now needs 50 reads in a row. Temperature is not used by the BAM fit. Ignore those single values when looking at the logs.
