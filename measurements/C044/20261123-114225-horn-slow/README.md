# C044 with metal horn only

Nominal 5 V, D=32. The Rhoban reference used nominal 7.4 V and its STS3215 subtype is unspecified.
Tracking MAE covers the powered phase only, without time shifting. Reference angles are interpolated at local observation times.

| Pattern | Samples | Last sample (s) | Torque off confirmed (s) | Local MAE (°) | Rhoban MAE (°) | Local voltage (V) |
|---|---:|---:|---:|---:|---:|---:|
| p32-lift_and_drop | 250 | 5.999 | 2.0053 | 2.10 | 1.55 | 5.0–5.1 |
| p32-up_and_down | 251 | 5.995 | — | 0.98 | 0.65 | 5.0–5.0 |

Stop reason: p32-up_and_down AssertionError(). Final readback: `{'21': 32, '22': 32, '23': 0, '40': 0, '55': 1}`.
