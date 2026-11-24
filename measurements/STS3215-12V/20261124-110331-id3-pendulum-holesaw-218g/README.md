# STS3215 12 V follower (ID 3) with a hole-saw pendulum: 218 g on the short arm

## Load

- **Weight:** a bi-metal hole saw, 205 g and about 62 mm in diameter, lies flat on the short arm. It is centred on the 100 mm hole with a printed
  [bushing](../../../hole_saw_bushing.3mf), and fixed with an M4 bolt, nut, two washers and a lock washer. Its teeth are taped.
- **Total pendulum weighed as one piece: 218 g** (arm, saw, bushing and fasteners; no servo or horn).
- The saw is round, so its centre of mass is on the 100 mm hole. With the bare arm at about 9 g, the whole pendulum's centre of mass is at about 98 mm, and the
  gravity torque when horizontal is about 0.21 Nm.
- **BAM log values:** `mass = 0.209`, `arm_mass = 0.009`, `length = 0.100`. This gives the same gravity torque as the real pendulum.
- The saw's own inertia about its axis (cup of about 31 mm radius) adds roughly 8% to m·L². It is not in the log values yet.

## Settings

12 V adapter from the follower kit through the follower board; the servo reads 12.0 V. Profile off in EEPROM. P = 4/8/16/32, D = 0; P/D were restored to
the LeRobot follower values 16/32 afterwards. Zero: hanging rest position raw 2055. 16 runs, no bus timeouts, 29 °C afterwards.

## Manual tests

| Test | Sag | PWM |
|---|---:|---:|
| Hold at +45°, P = 32 | 0.53° | 5.6% |
| Hold at +90°, P = 32 | 0.62° | 6.4% |
| Hold at −90°, P = 32 | 0.70° | 7.2% |
| Hold at +90°, P = 8 | 0.79° | 3.0% |
| Release at 45° (torque off) | **does not move** (45.2° → 45.2°) | — |

Very stiff: with 0.21 Nm it sags less than 1°. For comparison, the C001 with 0.44 Nm sagged 1.5° at 14% PWM. Like the C001, the 1:345 gearbox is not back-driven.

## No load vs 218 g (same servo)

| Trajectory | kp | Tracking error no load / 218 g (°) | Lag no load / 218 g (ms) | Max PWM 218 g | for scale: C046 with 281 g, tracking error (°) |
|---|---:|---|---|---:|---:|
| up_and_down | 4 | 5.49 / 5.79 | 303 / 337 | 18% | 9.51 |
| up_and_down | 8 | 2.76 / 3.10 | 150 / 174 | 19% | 4.70 |
| up_and_down | 16 | 1.45 / 1.57 | 78 / 89 | 20% | 2.39 |
| up_and_down | 32 | 0.78 / 0.86 | 41 / 48 | 20% | 1.28 |
| lift_and_drop | 4 | 12.30 / 13.53 | 295 / 322 | 24% | 12.41 |
| lift_and_drop | 8 | 6.54 / 7.28 | 148 / 165 | 26% | 6.89 |
| lift_and_drop | 16 | 3.34 / 3.80 | 75 / 84 | 27% | 3.71 |
| lift_and_drop | 32 | 1.70 / 1.97 | 38 / 43 | 27% | 1.99 |
| sin_sin | 4 | 17.27 / 16.66 | 244 / 235 | 45% | 12.53 |
| sin_sin | 8 | 10.71 / 10.70 | 138 / 137 | 60% | 7.07 |
| sin_sin | 16 | 6.20 / 6.21 | 75 / 75 | 68% | 3.72 |
| sin_sin | 32 | 3.29 / 3.31 | 39 / 39 | 72% | 1.97 |
| sin_time_square | 4 | 30.30 / 30.02 | 221 / 215 | 65% | 23.16 |
| sin_time_square | 8 | 26.54 / 26.32 | 167 / 167 | 94% | 15.62 |
| sin_time_square | 16 | 20.61 / 20.71 | 117 / 116 | 100% | 8.99 |
| sin_time_square | 32 | 16.11 / 16.20 | 90 / 89 | 100% | 4.69 |

- **The 218 g load changes this servo very little:** the lag grows 10–15% on slow moves, and fast moves are unchanged. The C046 with a similar load more than doubled
  its error on slow moves. The extra torque of the 12 V servo shows.
- sin_time_square reaches the PWM limit from kp 8, as on the other servos.

## Rhoban's 7.4 V model on this 12 V servo

Mean |sim − real| over the 20 no-load and 16 loaded runs (tables: [rhoban-model-vin12.md](rhoban-model-vin12.md),
[rhoban-model-vin7.4.md](rhoban-model-vin7.4.md)):

| Model | Mean error |
|---|---:|
| Rhoban 7.4 V m1 / m6, simulated at the real 12 V | 6.49° / 6.76° |
| Same models, simulated as if supplied with 7.4 V | 4.14° / 4.54° |
| For comparison: Rhoban's model on our 7.4 V C001 | 1.13° / 1.11° |

**The 12 V servo needs its own model.** Rhoban's 7.4 V parameters at 12 V make the simulated servo far too strong and fast. Even at 7.4 V they miss by
4°, because the 12 V servo has more friction at low drive and more torque under load. A fit needs at least one or two more loads, for example both saws
(387 g) and the 150 mm arm.
