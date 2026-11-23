# C044 (1:191) BAM fit

The fit uses 52 logs from unit 1 (bus ID 3): 20 no-load replays of Rhoban's commands, 16 runs with 281 g at 92 mm and 16 runs with 450 g at 100 mm.
All were recorded with the profile off and D = 0. The 13 kp 8 logs were held out for validation. A second test uses all 52 logs of **unit 2 (ID 1)**, which
the fit never saw.

## Results

Mean |sim − real| position error in degrees. Full tables: [validation-kp8.md](validation-kp8.md) and
[prediction-other-unit-id1.md](prediction-other-unit-id1.md).

| Test | m1 | m4 | m6 | C046 m4 (other type) | Rhoban C001 m6 (other type) |
|---|---:|---:|---:|---:|---:|
| Unit 1, held-out kp 8, all runs | 1.97 | 2.03 | 1.86 | 3.02 | 5.22 |
| Unit 1, held-out kp 8, without `lift_and_drop` | 0.80 | 0.66 | **0.63** | | |
| **Unit 2 (never seen)**, all 52 runs | 1.44 | 1.53 | 1.37 | | |
| **Unit 2**, without `lift_and_drop` | 0.77 | 0.67 | **0.65** | | |

- **Apart from `lift_and_drop`, the model predicts both units to about 0.65°**, including the unit it never saw. One model per servo type is
  therefore enough, at least for this pair. m4 and m6 are about equal and both better than m1.
- **The large errors come from `lift_and_drop` with 281 g.** After the release the arm swings up to about +12–20°, where gravity is weak
  (about 0.08 Nm). Depending on very small differences, it either sticks there or falls back to about −5°. On the held-out 281 g kp 8 run the real
  arm stuck at +18°, and the simulation let it fall back, which gives a 14° error. Which of the two happens varies between units and between
  gains ([C044 ID 1 281 g](../../measurements/C044/20261123-182309-id1-pendulum-281g/README.md)). This stick-slip behaviour cannot be
  predicted exactly, so in RL it has to be covered by friction randomization.
- Type matters: the C046 model on C044 data gives 3.0°, and Rhoban's C001 model gives 5.2°.

## Parameters compared with a prediction from Rhoban's C001

Assumption: the same motor in all three types, with only the gear ratio different. Then the output-side kt scales with the ratio, R stays the same, and the
armature scales with the ratio squared.

| Parameter | C001 (Rhoban) | Predicted C044 (×191/345) | C044 fit m1 / m4 / m6 | Predicted C046 (×147/345) | C046 fit m1 / m4 / m6 |
|---|---:|---:|---|---:|---|
| kt | 1.178 | 0.652 | 0.63 / 0.62 / 0.61 | 0.502 | 0.59 / 0.61 / 0.57 |
| armature | 0.0261 | 0.0080 | 0.0077 / 0.0077 / 0.0079 | 0.0047 | 0.0058 / 0.0055 / 0.0056 |
| R (Ω) | 2.48 | 2.48 | 2.25 / 1.95 / 1.83 | 2.48 | 2.58 / 2.37 / 1.98 |
| max_velocity (rad/s) | 5.29 | — | 15.4 / 15.9 / 15.4 | — | 18.4 / 18.8 / 31.1 |

- **The C044 matches the "same motor, other gears" prediction closely:** kt within 6% and the armature within 4%. That is strong evidence that the C044 and C001
  share the motor.
- The C046 is further off (kt +15–20%, armature +20%). This could be a different gearbox efficiency, or the brackets' inertia ending up in the armature.
- R and kt are partly interchangeable in this model; kt/R is what sets torque per volt.
- `max_velocity` is the firmware's rate limit on the internal target, not the motor's speed. It is far above what these trajectories need,
  so it is poorly determined.
