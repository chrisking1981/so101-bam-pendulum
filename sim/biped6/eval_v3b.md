Walking (10 s episodes, command 15 cm/s, so 150 cm is the target):

| layout | C044 at | nominal: forward / fell | randomized: forward mean (min) | sideways | falls |
|---|---|---|---|---:|---:|
| v3_12v | - | +31 cm / no | 39 cm (-21) | 72 cm | 1/20 |
| v3_knee | knee | +62 cm / no | 68 cm (-10) | 77 cm | 7/20 |
| v3_roll | roll | +19 cm / no | 56 cm (-67) | 131 cm | 2/20 |
| v3_pitch | pitch | +127 cm / no | 113 cm (3) | 35 cm | 0/20 |

Load while walking (all randomized episodes):

| layout | joint | servo | torque mean | torque p95 | duty p95 | duty max |
|---|---|---|---:|---:|---:|---:|
| v3_12v | roll | 12 V | 1.13 Nm | 2.63 Nm | 0.97 | 0.97 |
| v3_12v | pitch | 12 V | 0.57 Nm | 1.99 Nm | 0.97 | 0.97 |
| v3_12v | knee | 12 V | 0.14 Nm | 0.31 Nm | 0.04 | 0.97 |
| v3_12v | ankle | 12 V | 0.26 Nm | 1.02 Nm | 0.36 | 0.97 |
| v3_knee | roll | 12 V | 0.93 Nm | 2.42 Nm | 0.97 | 0.97 |
| v3_knee | pitch | 12 V | 0.77 Nm | 2.33 Nm | 0.97 | 0.97 |
| v3_knee | **knee** | C044 5 V | 0.22 Nm | 0.63 Nm | **0.69** | 0.97 |
| v3_knee | ankle | 12 V | 0.15 Nm | 0.33 Nm | 0.05 | 0.97 |
| v3_roll | **roll** | C044 5 V | 0.46 Nm | 1.02 Nm | **0.97** | 0.97 |
| v3_roll | pitch | 12 V | 0.82 Nm | 2.10 Nm | 0.97 | 0.97 |
| v3_roll | knee | 12 V | 0.65 Nm | 2.44 Nm | 0.90 | 0.97 |
| v3_roll | ankle | 12 V | 0.15 Nm | 0.38 Nm | 0.05 | 0.97 |
| v3_pitch | roll | 12 V | 0.90 Nm | 2.34 Nm | 0.97 | 0.97 |
| v3_pitch | **pitch** | C044 5 V | 0.29 Nm | 0.90 Nm | **0.97** | 0.97 |
| v3_pitch | knee | 12 V | 1.25 Nm | 3.11 Nm | 0.97 | 0.97 |
| v3_pitch | ankle | 12 V | 0.18 Nm | 0.46 Nm | 0.06 | 0.97 |
