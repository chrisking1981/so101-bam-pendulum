# C044 with metal horn only

Nominal 5 V, D=32. The Rhoban reference used nominal 7.4 V and its STS3215 subtype is unspecified.
Tracking MAE covers the powered phase only, without time shifting. Reference angles are interpolated at local observation times.

| Pattern | Samples | Last sample (s) | Torque off confirmed (s) | Local MAE (°) | Rhoban MAE (°) | Local voltage (V) |
|---|---:|---:|---:|---:|---:|---:|
| p4-up_and_down | 251 | 5.985 | — | 5.24 | 4.41 | 5.0–5.0 |
| p4-lift_and_drop | 250 | 5.999 | 2.0221 | 11.43 | 10.60 | 4.9–5.0 |
| p8-up_and_down | 250 | 5.977 | — | 2.96 | 2.27 | 4.9–5.0 |
| p8-lift_and_drop | 249 | 5.988 | 2.0171 | 6.22 | 5.64 | 5.0–5.0 |
| p16-up_and_down | 249 | 5.992 | — | 1.64 | 1.17 | 5.0–5.0 |
| p16-lift_and_drop | 249 | 5.978 | 2.0124 | 3.48 | 2.90 | 5.0–5.0 |

Stop reason: none. Final readback: `{'21': 32, '22': 32, '23': 0, '40': 0, '55': 1}`.
