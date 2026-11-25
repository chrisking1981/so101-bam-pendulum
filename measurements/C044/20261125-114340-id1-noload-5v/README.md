# C044 unit 2 (bus ID 1) without load at 5 V

The same 20 no-load replays of Rhoban's commands as at 7.4 V ([`../20261123-163134-id1-noload`](../) series, `data_raw/c044b_noload`),
now on the SO-101 leader's own **5 V adapter** and USB board. Profile off (85/41 = 0), D = 0, P = 4/8/16/32, horn only. No bus timeouts.

**Is the C044 model (fitted at 7.4 V) also right at 5 V?** Mean |sim − real| over the 20 runs, BAM's simulator with `vin` = 5.0 from the logs:

| Model (fitted at 7.4 V on unit 1) | at 5 V (these runs) | at 7.4 V (same servo, earlier runs) |
|---|---:|---:|
| m1 | 0.51° | 0.40° |
| **m4** | **0.30°** | **0.31°** |
| m6 | 0.41° | 0.37° |

**Yes.** BAM's model is voltage-driven, and the 7.4 V fit predicts this servo at 5 V as well as at 7.4 V (m4: 0.30° against 0.31°).
So the leader's C044s can be used at 5 V (as knees, for example) with the existing model and `vin = 5.0`. The largest errors are in
the fast `sin_time_square` runs (up to about 1°), as at 7.4 V. Full table: [model_check_5v.md](model_check_5v.md).
