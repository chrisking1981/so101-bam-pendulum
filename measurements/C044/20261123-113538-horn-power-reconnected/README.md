# C044 horn-only replay after reconnecting the 5 V adapter

P=32, D=32, I=0. Configuration and trip sample in status.json. The slow pattern completed. The 90%-amplitude sine stopped at the first 5.6 V report, above the 5.5 V test guard. The partial error covers only the recorded interval. Torque was read back off after the stop.

| Pattern | Samples | Last sample (s) | Voltage (V) | Tracking MAE (°) |
|---|---:|---:|---:|---:|
| p32-up_and_down | 250 | 5.997 | 5.0–5.0 | 0.98 |
| p32-sin_sin-90pct | 10 | 0.216 | 5.0–5.6 | 4.87 |
