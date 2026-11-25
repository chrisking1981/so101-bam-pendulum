Walking (10 s episodes, command 15 cm/s, so 150 cm is the target):

| layout | C044 at | nominal: forward / fell | randomized: forward mean (min) | sideways | falls |
|---|---|---|---|---:|---:|
| v3_12v | - | +6 cm / no | 9 cm (6) | 2 cm | 7/20 |
| v3_knee | knee | +162 cm / no | 121 cm (59) | 77 cm | 2/20 |
| v3_roll | roll | +106 cm / yes | 105 cm (-51) | 80 cm | 6/20 |
| v3_pitch | pitch | +187 cm / no | 159 cm (129) | 109 cm | 0/20 |

Load while walking (all randomized episodes):

| layout | joint | servo | torque mean | torque p95 | duty p95 | duty max |
|---|---|---|---:|---:|---:|---:|
| v3_12v | roll | 12 V | 1.49 Nm | 2.90 Nm | 0.43 | 0.97 |
| v3_12v | pitch | 12 V | 0.16 Nm | 0.50 Nm | 0.21 | 0.97 |
| v3_12v | knee | 12 V | 0.19 Nm | 0.45 Nm | 0.29 | 0.97 |
| v3_12v | ankle | 12 V | 3.74 Nm | 3.98 Nm | 0.59 | 0.97 |
| v3_knee | roll | 12 V | 1.19 Nm | 2.95 Nm | 0.97 | 0.97 |
| v3_knee | pitch | 12 V | 0.86 Nm | 3.59 Nm | 0.97 | 0.97 |
| v3_knee | **knee** | C044 5 V | 0.33 Nm | 1.00 Nm | **0.97** | 0.97 |
| v3_knee | ankle | 12 V | 2.44 Nm | 3.98 Nm | 0.97 | 0.97 |
| v3_roll | **roll** | C044 5 V | 0.77 Nm | 1.54 Nm | **0.97** | 0.97 |
| v3_roll | pitch | 12 V | 0.57 Nm | 2.48 Nm | 0.97 | 0.97 |
| v3_roll | knee | 12 V | 1.64 Nm | 3.65 Nm | 0.97 | 0.97 |
| v3_roll | ankle | 12 V | 2.87 Nm | 3.98 Nm | 0.97 | 0.97 |
| v3_pitch | roll | 12 V | 1.24 Nm | 3.07 Nm | 0.97 | 0.97 |
| v3_pitch | **pitch** | C044 5 V | 0.32 Nm | 1.03 Nm | **0.97** | 0.97 |
| v3_pitch | knee | 12 V | 0.56 Nm | 2.45 Nm | 0.97 | 0.97 |
| v3_pitch | ankle | 12 V | 2.36 Nm | 3.97 Nm | 0.95 | 0.97 |
