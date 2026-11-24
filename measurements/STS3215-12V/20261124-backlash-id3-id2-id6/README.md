# Backlash check on the three 12 V followers (ID 3, ID 2, ID 6)

Each servo held the 401 g pendulum (100 mm hole) at its hanging position with P = 32, D = 0, torque on, for 2 minutes.
The operator pushed the arm end gently left and right until resistance was felt, several times, and estimated the travel at the arm end with a ruler.
The encoder and load were logged at ~2.3 kHz ([`scripts/bam_feetech/backlash_hold.py`](../../../scripts/bam_feetech/backlash_hold.py)).

| Servo | Arm-end travel (operator, by eye) | ≈ angle | Encoder travel during the pushes | Load during the pushes |
|---|---:|---:|---:|---:|
| ID 3 | ~1 mm | ~0.57° | 1.06° | ±5.6% |
| ID 2 | ~1 mm | ~0.57° | 1.32° | −6.4…+7.2% |
| ID 6 | ~1 mm | ~0.57° | 1.93° | −8.8…+9.6% |

## Result

- **No measurable backlash.** The backlash would be the arm travel *beyond* what the encoder sees (the magnetic encoder is on the output
  side). Here the encoder itself moved as much as, or more than, the arm-end travel read by eye. All the movement is the servo yielding
  under its P loop, which the BAM model already contains.
- The by-eye reading resolves about ±0.5 mm (±0.3°), so the backlash is **below about 0.5° total** on all three units.
- For comparison, Microduck (Dynamixel XL330, plastic gears) trains with 2° total (±1°). That value should **not** be copied for this servo.
  For RL, 0–0.5° total randomized per joint is enough, if any.
- A more precise number would need a dial gauge at the arm end, or an external angle sensor (IMU) on the arm.
