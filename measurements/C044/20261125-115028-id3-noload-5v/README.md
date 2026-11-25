# C044 unit 1 (bus ID 3) without load at 5 V, and both C044s at 5 V compared

Same 20 no-load replays as for unit 2 ([`../20261125-114340-id1-noload-5v`](../20261125-114340-id1-noload-5v/README.md)), on the SO-101
leader's 5 V adapter. Unit 1 is the servo the C044 model was fitted on (at 7.4 V).

| Model (fitted at 7.4 V on unit 1) | Unit 1 at 5 V | Unit 1 at 7.4 V | Unit 2 at 5 V | Unit 2 at 7.4 V |
|---|---:|---:|---:|---:|
| m1 | 0.58° | 0.39° | 0.51° | 0.40° |
| **m4** | **0.34°** | **0.26°** | **0.30°** | **0.31°** |
| m6 | 0.46° | 0.33° | 0.41° | 0.37° |

- **The 7.4 V model predicts both units at 5 V to about 0.3° (m4).** Only a little worse than at 7.4 V for unit 1 (0.34° against 0.26°).
  Setting `vin = 5.0` is enough; no separate 5 V fit is needed.
- **At 5 V the servos are clearly slower:** the tracking error is about 1.4 times larger on average, and in the fastest runs
  (`sin_time_square`, kp 32) twice as large (14.7° / 13.5° against 7.3° / 6.9°). That is the expected effect of 5/7.4 of the voltage, and
  the model reproduces it.
- **The two units agree at 5 V** to 0.24° in tracking error, so a pair of them (for example as knees) behaves the same left and right.
