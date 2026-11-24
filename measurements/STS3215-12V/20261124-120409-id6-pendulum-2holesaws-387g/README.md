# 12 V follower ID 6 with two hole saws (387 g saws, 401 g total), compared with no load and one hole saw

Both hole saws (387 g together) are nested on the 100 mm hole of the short arm, each with its own centring bushing. BAM log values: `mass = 0.392`, `arm_mass = 0.009`,
`length = 0.100`. Complete pendulum weighed at **401 g** (saws, bushings, bolt, washers and arm), so `mass` = 401 − 9 g arm.
12 V adapter, profile off, full torque limits, P = 4/8/16/32, D = 0. 16 runs, no bus timeouts, 31 °C afterwards.

**Zero measured before recording** with `find_vertical` (±90° sweep): the mounted position was **0.82°** from the gravity vertical (fit residual 1.4/1000, gravity
amplitude 53/1000 PWM). The corrected zero, raw 2158, was used for all runs.

## Manual tests

| Test | Sag | PWM |
|---|---:|---:|
| Hold at 0, P = 32 | 0.70° | 0% |
| Hold at +45°, P = 32 | 0.79° | 8.0% |
| Hold at +90°, P = 32 | 1.23° | 12.0% |
| Hold at −90°, P = 32 | 0.97° | 9.6% |
| Hold at +90°, P = 8 | 1.23° | 12.0% |
| Release at 45° | does not move | — |

The P = 8 hold shows the same sag as P = 32 because the arm came up under P = 32 and the gearbox friction keeps it there. Static holds on this servo depend on how the arm got there.

## ID 6 at 0, 218 and 387 g (same servo, same zero method)

| Trajectory | kp | RMS error 0 / 218 / 387 g (°) | Lag 0 / 218 / 387 g (ms) | Peak PWM 0 / 218 / 387 g (%) |
|---|---:|---|---|---|
| up_and_down | 4 | 6.88 / 8.10 / 9.42 | 297 / 317 / 351 | 16 / 18 / 21 |
| up_and_down | 8 | 3.59 / 4.18 / 4.85 | 152 / 168 / 186 | 17 / 19 / 22 |
| up_and_down | 16 | 1.85 / 2.14 / 2.51 | 78 / 88 / 97 | 17 / 20 / 24 |
| up_and_down | 32 | 0.99 / 1.16 / 1.33 | 41 / 47 / 52 | 18 / 20 / 23 |
| lift_and_drop | 4 | 13.56 / 14.93 / 16.07 | 281 / 304 / 325 | 23 / 25 / 26 |
| lift_and_drop | 8 | 7.12 / 7.96 / 8.94 | 148 / 163 / 180 | 24 / 26 / 29 |
| lift_and_drop | 16 | 3.69 / 4.16 / 4.59 | 75 / 84 / 92 | 25 / 27 / 30 |
| lift_and_drop | 32 | 1.90 / 2.13 / 2.37 | 38 / 43 / 48 | 26 / 28 / 30 |
| sin_sin | 4 | 20.95 / 20.98 / 20.81 | 231 / 234 / 238 | 48 / 45 / 43 |
| sin_sin | 8 | 13.21 / 13.16 / 13.22 | 135 / 136 / 138 | 63 / 60 / 58 |
| sin_sin | 16 | 7.52 / 7.55 / 7.73 | 75 / 75 / 73 | 72 / 69 / 71 |
| sin_sin | 32 | 3.97 / 4.04 / 4.01 | 39 / 39 / 39 | 76 / 72 / 69 |
| sin_time_square | 4 | 36.36 / 36.27 / 36.06 | 225 / 224 / 224 | 65 / 65 / 65 |
| sin_time_square | 8 | 33.31 / 33.16 / 33.37 | 150 / 152 / 155 | 92 / 93 / 94 |
| sin_time_square | 16 | 27.59 / 27.46 / 30.02 | 95 / 96 / 112 | 100 / 100 / 100 |
| sin_time_square | 32 | 22.97 / 23.37 / 22.84 | 68 / 68 / 68 | 100 / 100 / 100 |

Release at −90° (`lift_and_drop`), position at the release → at the end of the log:
- 0 g: no movement
- 218 g: no movement
- **387 g: the arm falls back to near vertical** (kp4 −76→+1°, kp8 −85→+5°, kp16 −88→+7°, kp32 −89→+9°)

## Findings

- **387 g back-drives the 12 V servo at 90°.** 218 g did not. Gravity torque at 90° is about 0.39 N·m with 387 g, against about 0.21 N·m with 218 g. The static gearbox
  friction of ID 6 lies between those two. At 45° (0.27 N·m) the arm still holds. The arm stops a few degrees past vertical: that is the friction band.
- **Slow trajectories (`up_and_down`, `lift_and_drop`):** error and lag grow steadily with the load, by about +15–20% per step at every kp. Example: up_and_down at
  kp 32 goes 0.99 → 1.16 → 1.33° and 41 → 47 → 52 ms.
- **Fast trajectories (`sin_sin`, `sin_time_square`):** practically no change. These runs are limited by velocity and PWM saturation (up to 100%), not by gravity.
  One exception is sin_time_square kp 16 (27.5 → 30.0°).
- This gives a third load point for the 12 V BAM fit, with a clear gravity effect. Together with the 15 cm arm, the fit can separate friction, inertia and motor torque.
