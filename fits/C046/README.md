# C046 (1:147) BAM fit

The fit uses 52 logs from unit 3 (bus ID 5), recorded with the acceleration profile off and with D = 0:

- 20 no-load replays of Rhoban's commands
- 16 runs with 281 g at 92 mm
- 16 runs with 450 g at 100 mm

The 13 kp 8 logs were held out.

## Validation on the held-out kp 8 logs

Mean |sim − real| position error, in degrees. Full table: [validation-kp8.md](validation-kp8.md).

| Model | Mean on unseen runs |
|---|---:|
| C046 m1 | 0.88° |
| **C046 m4** | **0.57°** |
| C046 m6 | 0.63° |
| Rhoban's C001 m6 (wrong servo type) | 7.68° |

**m4 is the best**, ahead of m6. m4 adds load-dependent friction and Stribeck friction to m1; m6 adds more load-friction terms, which do not
generalise better on this data. Using the C001 model for a C046 is about 13× worse.

## Parameters compared with a prediction from Rhoban's C001

If the C046 uses the same motor as the C001 with a different gear ratio (147 instead of 345), the output-side kt should scale with
the ratio (× 0.426), R should stay the same, and the armature should scale with the ratio squared (× 0.18).

| Parameter | Predicted from C001 | C046 m1 | C046 m4 | C046 m6 |
|---|---:|---:|---:|---:|
| kt | 0.50 | 0.59 | 0.61 | 0.57 |
| R (Ω) | 2.48 | 2.58 | 2.37 | 1.98 |
| armature | 0.0047 | 0.0058 | 0.0055 | 0.0056 |

- The fitted values are in the predicted range: kt about 15–20% higher and the armature about 20% higher. That is consistent with "same motor, other gears" plus
  different gearbox losses. kt and R are partly interchangeable in this model (it is the torque per volt, kt/R, that matters), which explains the spread in R.
- Remaining limitation: the pendulum's moment of inertia is underestimated by an estimated 5–10%, because the steel angle brackets are
  wide. The fit may have absorbed part of that into the armature.
