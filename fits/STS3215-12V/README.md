# STS3215 12 V follower (1:345) BAM fit

The fit uses 52 logs from **ID 6**, all at 12 V with the profile off, full torque limits and D = 0:

- 20 no-load runs (horn only)
- 16 runs with one hole saw (218 g total, `mass = 0.209`, `arm_mass = 0.009`, 100 mm)
- 16 runs with two hole saws (401 g total, `mass = 0.392`)

The 13 kp 8 logs were held out (`--validation_kp 8`). The actuator class is `sts3215`. The supply voltage, 12 V, comes from each log's `vin`.
The prediction test runs all 52 logs of **ID 2 and ID 3**, two units the fit never saw (same three loads; the ID 2 218 g runs are the zero-corrected
copies; the ID 3 218 g zero was not measured).

## Results

Mean |sim − real| position error in degrees. Full tables: [validation-id6-kp8.md](validation-id6-kp8.md), [prediction-id2.md](prediction-id2.md),
[prediction-id3.md](prediction-id3.md).

| Test | m1 | m2 | m3 | m4 | m5 | m6 | Rhoban C001 7.4 V m6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ID 6, held-out kp 8 (13 runs) | 1.03 | 0.41 | 0.52 | 0.36 | 0.32 | **0.31** | 8.11 |
| **ID 2 (never seen)**, without `lift_and_drop` (40) | 0.45 | 0.39 | 0.45 | 0.37 | **0.30** | 0.39 | 3.80 |
| **ID 3 (never seen)**, without `lift_and_drop` (40) | 0.41 | 0.35 | 0.41 | 0.36 | **0.27** | 0.38 | 3.74 |
| ID 2, `lift_and_drop` only (12) | 3.59 | 3.19 | 3.23 | 3.10 | 3.17 | 3.24 | 18.42 |
| ID 3, `lift_and_drop` only (12) | 5.80 | 7.73 | 7.84 | 7.73 | 7.75 | 7.85 | 14.31 |

- **m5 is the recommended model.** It predicts both unseen units to about 0.3° on every trajectory except `lift_and_drop`, and it is
  practically tied with m6 on the held-out ID 6 runs. m5 has load-dependent friction with separate motor and external terms (plus Stribeck),
  which suits a gearbox that cannot be back-driven.
- **Rhoban's 7.4 V C001 model does not fit the 12 V servo**, even with the voltage set to 12 V: 8° on held-out runs (up to 53° on
  `lift_and_drop`). Same gear ratio, different motor.
- **The remaining errors are all in `lift_and_drop`, which is the release with the torque off.** Whether the arm sticks or falls depends on
  the static friction of each unit, right at the edge:
  - ID 3 slips with 218 g, but ID 6 holds (21–28° error on ID 3 at kp 8/16/32).
  - With 401 g all three fall back, but they stop anywhere between −8° and +9° (2–7° error).
  
  In RL, this stick-slip has to be covered by friction randomization of at least ±30%. It cannot be predicted per unit.

## Parameters compared with Rhoban's C001 (7.4 V, also 1:345)

| Parameter | C001 7.4 V (Rhoban m1) | 12 V m1 | 12 V m5 | 12 V m6 |
|---|---:|---:|---:|---:|
| kt (N·m/A) | 1.178 | 2.31 | 2.20 | 1.53 |
| R (Ω) | 2.48 | 3.35 | 4.13 | 1.90 |
| kt / R | 0.48 | 0.69 | 0.53 | 0.80 |
| armature (kg·m²) | 0.0261 | 0.0328 | 0.0243 | 0.0184 |
| max_velocity (rad/s) | 5.29 | 4.94 | 4.97 | 5.00 |
| friction_base (N·m) | 0.05 | 0.20 | 0.05 + load terms | 0.06 + load terms |

- **kt is about twice as high and R higher.** That matches a motor wound for 12 V: more turns, so more torque per amp and more resistance.
  At 12 V it delivers more torque than the C001 at 7.4 V. kt, R and `error_gain_ratio` are partly interchangeable: m4/m6 settle on lower kt
  with `error_gain_ratio` ≈ 0.7. Compare torque per volt, not kt alone.
- **The armature is about the same as the C001 (0.018–0.033).** That fits the same 1:345 gearbox.
- **The friction is much higher.** It is 0.20 N·m Coulomb in m1, against 0.05 for the C001. In m5/m6 most of it is load-dependent
  (`load_friction_external` ≈ 0.2–0.26). That is the non-back-drivable gearbox, and it agrees with the measured static holding limit (holds 0.27 N·m,
  slips at 0.39 N·m).
- `max_velocity` ≈ 5.0 rad/s is reached in the fast runs, so here it is well determined (unlike the C044/C046 fits).

## Reproduce

```
uv run python -m bam.process --raw fit/f12_id6/raw --logdir fit/f12_id6/processed --dt 0.005
uv run python -m bam.fit --logdir fit/f12_id6/processed --actuator sts3215 --model m5 --validation_kp 8 --trials 6000 --output m5.json
uv run python -m bam.feetech.eval_params --params m5.json --logdir fit/f12_id2/processed
```
Note: `bam.fit` imports wandb, which needs protobuf < 4 as pinned in BAM's `pyproject.toml`. If another install upgraded protobuf, run
`uv pip install "protobuf>=3.20,<4"`.
