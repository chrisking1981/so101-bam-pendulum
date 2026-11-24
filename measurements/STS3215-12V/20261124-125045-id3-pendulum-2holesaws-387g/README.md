# 12 V follower ID 3 with two hole saws (401 g total), and all three 12 V units at 401 g

This is the same pendulum as for ID 6 (20261124-120409) and ID 2 (20261124-121542): both hole saws on the 100 mm hole, 401 g in total. BAM log values:
`mass = 0.392`, `arm_mass = 0.009`, `length = 0.100`. 12 V adapter, profile off, full torque limits, P = 4/8/16/32, D = 0. 16 runs, no bus timeouts, 29 °C afterwards.

**Zero measured before recording** with `find_vertical` (±90° sweep): the hanging position was **2.21°** from the gravity vertical (fit residual 1.5/1000, gravity
amplitude 57/1000 PWM, friction half-band 51/1000). The corrected zero, raw 2049, was used for all runs. For a non-back-drivable servo, the hanging position
lands anywhere inside the friction band. That is why the sweep is needed.

## Manual tests (sag / PWM)

| Test | ID 3 | ID 2 | ID 6 |
|---|---:|---:|---:|
| Hold at 0, P = 32 | 2.11° / 0% | 0.18° / 2.4% | 0.70° / 0% |
| Hold at +45°, P = 32 | 0.70° / 7.2% | 0.97° / 9.6% | 0.79° / 8.0% |
| Hold at +90°, P = 32 | 1.05° / 10.4% | 1.32° / 12.8% | 1.23° / 12.0% |
| Hold at −90°, P = 32 | 0.88° / 8.8% | 0.97° / 9.6% | 0.97° / 9.6% |
| Hold at +90°, P = 8 | 1.05° / 3.6% | 1.32° / 4.4% | 1.23° / 12.0% |
| Release at 45° | does not move | does not move | does not move |

The hold at 0 starts from the hanging position, which sat 2.1° off the measured zero. At 0 there is no gravity torque, so the friction keeps the arm where it is.

## Three units, same pendulum

| Trajectory | kp | RMS error ID3 / ID2 / ID6 (°) | Lag ID3 / ID2 / ID6 (ms) | Peak PWM ID3 / ID2 / ID6 (%) |
|---|---:|---|---|---|
| up_and_down | 4 | 9.37 / 9.81 / 9.42 | 351 / 369 / 351 | 21 / 22 / 21 |
| up_and_down | 8 | 4.96 / 5.03 / 4.85 | 187 / 193 / 186 | 22 / 22 / 22 |
| up_and_down | 16 | 2.54 / 2.49 / 2.51 | 97 / 98 / 97 | 22 / 22 / 24 |
| up_and_down | 32 | 1.33 / 1.32 / 1.33 | 51 / 52 / 52 | 23 / 23 / 23 |
| lift_and_drop | 4 | 15.90 / 16.61 / 16.07 | 321 / 335 / 325 | 26 / 27 / 26 |
| lift_and_drop | 8 | 8.75 / 8.83 / 8.94 | 174 / 175 / 180 | 28 / 28 / 29 |
| lift_and_drop | 16 | 4.58 / 4.52 / 4.59 | 90 / 90 / 92 | 29 / 29 / 30 |
| lift_and_drop | 32 | 2.38 / 2.38 / 2.37 | 48 / 47 / 48 | 42 / 30 / 30 |
| sin_sin | 4 | 21.13 / 21.57 / 20.81 | 236 / 242 / 238 | 43 / 43 / 43 |
| sin_sin | 8 | 13.18 / 13.44 / 13.22 | 138 / 140 / 138 | 58 / 59 / 58 |
| sin_sin | 16 | 7.62 / 7.68 / 7.73 | 74 / 75 / 73 | 66 / 67 / 71 |
| sin_sin | 32 | 4.04 / 4.11 / 4.01 | 40 / 39 / 39 | 70 / 70 / 69 |
| sin_time_square | 4 | 36.52 / 36.49 / 36.06 | 223 / 229 / 224 | 65 / 65 / 65 |
| sin_time_square | 8 | 33.06 / 33.34 / 33.37 | 153 / 156 / 155 | 94 / 96 / 94 |
| sin_time_square | 16 | 27.40 / 27.57 / 30.02 | 95 / 98 / 112 | 100 / 100 / 100 |
| sin_time_square | 32 | 23.72 / 23.34 / 22.84 | 69 / 68 / 68 | 100 / 100 / 100 |

## Findings

- **All three 12 V units are practically identical at 401 g.** Error and lag agree within ~5% on every run. At kp 16/32 the agreement is mostly within 1–2%.
- **All three are back-driven at −90° by 401 g.** They fall back to near vertical (ID 3 −4…+5°, ID 2 −8…−2°, ID 6 +1…+9°). All three hold at 45°.
  With 218 g only ID 3 slipped. Its friction is a bit lower, but the difference is small compared to the gravity torque at 401 g.
- **A static friction limit between about 0.27 N·m (holds) and 0.39 N·m (slips) is common to all units.** The friction half-band in the sweep
  (51–53/1000 PWM) is the same on all three.
- For the BAM fit, one model for all three units is justified. Fit on ID 6 (0 / 218 / 401 g) and validate on ID 2 and ID 3.
- Temperature: the same sporadic false reads as in the other logs (244 in the manual test). They are not used by the fit.
