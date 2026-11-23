# BAM fits

All fits were made with Rhoban's `bam.fit` (CMA-ES, 6000 trials, actuator class `sts3215`) on logs resampled to 5 ms with `bam.process`.
The kp 8 logs were held out for validation (`--validation_kp 8`).

## Pipeline check: refitting Rhoban's own data

`rhoban-refit-check/m1_refit.json` is our m1 fit on Rhoban's 100 raw logs. It reproduces Rhoban's published
`feetech_sts3215_7_4V/m1.json`:

| Parameter | Rhoban published | Our refit |
|---|---:|---:|
| kt | 1.178 | 1.168 |
| R (Ω) | 2.479 | 2.491 |
| armature | 0.02608 | 0.02590 |
| max_velocity (rad/s) | 5.288 | 5.278 |
| friction_base | 0.0515 | 0.0541 |
| friction_viscous | 0.0599 | 0.0575 |

## C046 (1:147)

See [C046/README.md](C046/README.md).
