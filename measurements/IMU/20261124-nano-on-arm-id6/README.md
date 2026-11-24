# Nano 33 IoT IMU on the pendulum arm (ID 6, arm only, no hole saws)

The Nano is taped flat on the arm, with its z axis along the servo shaft. The servo swept slowly at 20°/s, P = 32: 0 → +90° → −90° → 0,
holding 1 s at each end. Encoder and IMU were recorded together ([`scripts/imu/servo_imu_sweep.py`](../../../scripts/imu/servo_imu_sweep.py),
analysis in [`scripts/imu/analyse_sweep.py`](../../../scripts/imu/analyse_sweep.py)).

![sweep](sweep_20dps.png)

| Quantity | Result |
|---|---|
| Gyro (z), integrated, against the encoder | max difference **0.32°** over the whole 22 s sweep, drift 0.06° (after subtracting the bias measured in the first second) |
| Gravity angle (accelerometer) against the encoder, arm standing still | within about ±1.3° over ±90° (small mounting tilt and accelerometer scale error) |
| Gravity angle **while moving** | up to ±10–25° noise: a **117.5 Hz vibration** from the servo drivetrain at this speed (tangential acceleration ~1.5 m/s² std) |

- **The gyro agrees with the servo encoder to a few tenths of a degree.** The IMU readout, the axes and the time base all work.
- **When a servo moves, the accelerometer sees strong high-frequency vibration**, here 117.5 Hz at 20°/s. The policy runs at 50 Hz, so
  sampling the accelerometer once per step would alias that vibration into large random tilt errors. Average all IMU samples within each
  20 ms step (a 20 ms box filter attenuates 117 Hz to about 12%), and/or combine gyro and accelerometer (a complementary filter) for the
  gravity vector. The gyro itself is hardly affected (1.8°/s std at 117 Hz).
- Next: fast steps to measure the latency between the servo encoder and the IMU.

## Latency: ±30° steps at P = 32

![steps](steps_30deg.png)

Eight steps of ±30° ([`scripts/imu/analyse_steps.py`](../../../scripts/imu/analyse_steps.py)). All times are on the Mac's clock, from the
moment the goal-position write returns.

| Quantity | Median (range) |
|---|---|
| Command → gyro sees > 20°/s, measured when the sample **arrives on the Mac** | **17.5 ms** (15.5–25.4) |
| Same, at the time the IMU took the sample | 15.7 ms |
| Command → encoder has moved > 0.5° | 25.8 ms (23.1–28.6) |
| IMU arrival delay relative to the servo encoder readout (cross-correlation of the velocities, r = 0.95) | **2 ms** |
| USB batches from the Nano | every 2.3 ms (p99 4.6 ms, max 13.6 ms) |

- **The arm starts moving ~15 ms after the command is sent.** That includes the servo's own reaction time and the first part of the
  acceleration (20°/s is reached quickly; the 0.5° threshold on the encoder comes later, at ~26 ms). The peak speed of a 30° step is about 270°/s.
- **The IMU path adds only about 2 ms** compared with reading the servo's encoder: the Nano over USB is fast.
- The gyro rate and the encoder velocity agree closely (right plot). The encoder velocity is noisier because it is differentiated from 0.088° steps.
- For the simulation: the BAM m5 fit has a 5 ms pure command delay. The rest of the ~15 ms is the motor and firmware response, which BAM
  already models. The RL action delay should therefore be randomized around a few milliseconds on top of BAM. Microduck uses 15–30 ms,
  but without our own measurement. A whole-loop measurement on the robot (sensor read + policy + write at 50 Hz) is still to do.

## On-board tilt filter (firmware v2)

The Nano now calibrates its gyro bias at start-up (2 s still) and runs a Mahony filter (gyro + accelerometer, KP = 0.5 /s) at every
sample. It sends the filtered "up" vector together with the raw data ([firmware](../../../firmware/README.md)). The same sweep and steps
were repeated, and the filtered angle was compared with the servo encoder
([`scripts/imu/analyse_filter.py`](../../../scripts/imu/analyse_filter.py)).

![filter](filter_vs_encoder.png)

| Angle source | Slow sweep: mean / max error | ±30° steps: mean / max error | Error while moving (steps) |
|---|---|---|---|
| **Filtered on the Nano** | **0.85° / 1.8°** | **0.54° / 2.0°** | **0.8°** |
| Raw accelerometer | 3.3° / 26° | 3.2° / 82° | 22° |
| Accelerometer averaged over 20 ms | 0.9° / 5.3° | 2.4° / 59° | 17° |

- Still, after calibration, the gyro bias is 0.01°/s (was −9.8°/s) and the filtered up vector agrees with the accelerometer to 0.12°.
- **The filter is needed.** In fast moves the accelerometer measures the arm's own acceleration, not gravity: up to 82° wrong, and a 20 ms
  average does not help (59°). The filtered angle stays within 2° of the encoder.
- **No measurable lag** of the filtered angle (within a few ms of the encoder).
- The remaining error is a slow ±1–2° wander: after fast moves the accelerometer correction (time constant ~2 s) pulls it back. Plus about
  1° from accelerometer scale and mounting. In simulation, model it as a slowly varying tilt error of about ±2° on the projected gravity,
  not as white noise.
