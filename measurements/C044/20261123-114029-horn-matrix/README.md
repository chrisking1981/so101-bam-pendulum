# C044 horn-only BAM sweep

P=32, D=32, I=0 with the nominal 5 V adapter. Commands were resampled at the local recording rate. The 90% sine is a distinct variant. Tracking error is measured against the commanded angle. Reference error uses linear interpolation at local timestamps for full-amplitude commands only.

| Pattern | Status | Samples | Elapsed (s) | Local tracking MAE (°) | Rhoban tracking MAE (°) | Reported V |
|---|---|---:|---:|---:|---:|---:|
| p32-up_and_down | Complete | 249 | 5.977 | 0.98 | 0.66 | 5.0–5.0 |
| p32-sin_sin-90pct | Complete | 250 | 5.994 | 3.51 | — | 4.9–6.4 |
| p32-sin_time_square | Partial | 130 | 3.101 | 5.32 | 4.08 | 4.8–8.1 |

The first torque-off write after the 4.8 V stop still read back enabled. A second write over a freshly opened connection produced a verified disabled state. The recorder now retries and checks torque-off readback. This change has only been syntax-checked.

Reference archive: https://huggingface.co/buckets/Gregwar/bam_data/resolve/feetech_sts3215_raw.zip?download=true
