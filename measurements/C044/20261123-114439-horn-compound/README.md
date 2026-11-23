# C044 with metal horn only

Nominal 5 V, D=32. The Rhoban reference used nominal 7.4 V and its STS3215 subtype is unspecified.
Tracking MAE covers the powered phase only, without time shifting. Reference angles are interpolated at local observation times.

| Pattern | Samples | Last sample (s) | Torque off confirmed (s) | Local MAE (°) | Rhoban MAE (°) | Local voltage (V) |
|---|---:|---:|---:|---:|---:|---:|
| p4-sin_sin-90pct | 227 | 5.982 | — | 13.64 | — | 4.9–5.2 |
| p8-sin_sin-90pct | 225 | 5.980 | — | 9.07 | — | 4.9–5.3 |
| p16-sin_sin-90pct | 228 | 5.987 | — | 5.70 | — | 4.9–5.9 |

Stop reason: none. Final readback: `{'21': 32, '22': 32, '23': 0, '40': 0, '55': 1}`.
