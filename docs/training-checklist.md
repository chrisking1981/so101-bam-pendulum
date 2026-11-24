# Sim2real checklist for training the 12 V robot

Everything measured on the bench that the RL training must include, with the numbers and where they come from.
Compared with Microduck (Pollen Robotics / Hugging Face, [`microduck_rl`](https://github.com/pollen-robotics/microduck_rl)), whose
recipe is the reference for this project. Update this page whenever a measurement changes.

Setup decided on 2026-11-24: the robot runs **tethered**. The policy runs on the MacBook at 50 Hz; servos go through the SO-101 USB adapter
at 12 V; the IMU is an Arduino Nano 33 IoT over USB ([firmware](../firmware/README.md)). Training later on a PC with an RTX 3090 (mjlab).

## Actuators

| Item | Value for the 12 V follower (1:345) | Source | Microduck (XL330) |
|---|---|---|---|
| Model | BAM **m5** in the loop (`fits/STS3215-12V/m5.json`), actuator class `sts3215`, `vin` 12 V | [fit](../fits/STS3215-12V/README.md): 0.27–0.30° on unseen units; [MuJoCo check](../fits/mujoco/README.md) | BAM m6 in the loop |
| Never use | a constant MuJoCo position actuator (`to_mujoco`) | 4–15× worse, wrong torque-off behaviour | same conclusion |
| Firmware gains | P = `kp_fw` used on the robot, **D = 0** | [guide §4](sim-setup-guide.md) | kp_fw 200 |
| Acceleration profile | off in EEPROM (reg 85 / 41 = 0) | [guide §1](sim-setup-guide.md) | — |
| Torque / current limits | full (1000 / 310 / overload 80 on ID 6) | [guide §1b](sim-setup-guide.md) | — |
| `q_offset` | do **not** use on the robot (bench nuisance parameter) | fit | — |

## Domain randomization

Non-accumulating: restore the defaults and then apply a fresh sample at every reset (a Microduck lesson). Under BAM, randomize friction
through BAM's friction budget (`friction_scale`), not MuJoCo's `dof_frictionloss`, which BAM overwrites.

| Quantity | Our range | Evidence | Microduck |
|---|---|---|---|
| BAM friction scale | **0.7–1.3** | ID 3 slips with 218 g where ID 2/6 hold; at 401 g all three stop at different angles after release ([401 g](../measurements/STS3215-12V/20261124-125045-id3-pendulum-2holesaws-387g/README.md)) | 0.9–1.1 |
| Supply voltage | 11.0–12.6 V (adapter; to be checked under load) | 12 V adapter, not yet measured under load | 6.5–8.2 V |
| Voltage sag under load | small, **measure on the robot** (needs a BAM version with `vin_drop_gain_range`) | not measured | 0–0.2 V per N·m, floor 6 V |
| Action delay on top of BAM | 0–10 ms (start), refine with the whole-loop measurement | arm moves ~15 ms after the command; BAM m5 already has 5 ms pure delay plus the motor response ([IMU latency](../measurements/IMU/20261124-nano-on-arm-id6/README.md)) | 15–30 ms |
| Backlash | **0–0.5° total** per joint (or none) | not measurable by eye, < ~0.5° on all three units ([backlash](../measurements/STS3215-12V/20261124-backlash-id3-id2-id6/README.md)) | 2° total (±1°), fixed |
| Encoder offset per joint | ±0.9° | zeros found by `find_vertical` differ 0.8–8° from mounting; after calibration about ±1° | ±0.86° |
| Link mass / inertia | ±5–10% | weigh the parts | ±5% |
| Centre of mass | ±3 mm, later ±8 mm | — | ±3 → ±8 mm |
| Armature | ±10% | fit spread m1–m6: 0.018–0.033 | ±10% |
| Floor friction | 0.5–1.2 (current biped env) | — | 0.7–1.3 |
| Pushes | every 3–6 s, ±0.3 m/s | — | same |
| **Tether cables** (Nano USB, servo bus) | the clamped piece of cable counted in the weighed link mass; per joint a small random spring (0–0.01 N·m/rad) and extra friction (0–0.01 N·m) for cable drag. Route the cables along the links, clamp them next to each joint with a loop | with the USB cable on the Nano and not modelled, the one-servo pipeline test still matched to 0.24° ([pipeline test](../sim/pendulum_policy/README.md)); check again with two joints | — (Microduck is not tethered) |

## IMU (Nano 33 IoT, LSM6DS3)

| Item | Value | Source | Microduck |
|---|---|---|---|
| Rate | 427 Hz | [firmware](../firmware/README.md) | — |
| Gyro noise | 0.002 rad/s std measured → train with **±0.03 rad/s** uniform | still test | ±0.03 rad/s |
| Gyro bias | up to −9.8 °/s, stable → **calibrated at start-up on the Nano** (2 s still, firmware v2), 0.01 °/s after | still tests | the chip estimates its own bias |
| Gravity vector noise | train with ±0.01 (unit vector) | — | ±0.01 |
| **Drivetrain vibration** | 117.5 Hz, ~1.5 m/s² while a servo moves (20°/s) → the accelerometer angle jumps ±10–25° per raw sample; in fast moves the arm's own acceleration gives up to 82° | [IMU on arm](../measurements/IMU/20261124-nano-on-arm-id6/README.md) | — |
| → solution (done) | **on-board Mahony filter on the Nano** (firmware v2): filtered tilt within 2° of the encoder (mean 0.5–0.85°), no measurable lag. A 20 ms average is not enough (59° in fast moves) | [filter test](../measurements/IMU/20261124-nano-on-arm-id6/README.md#on-board-tilt-filter-firmware-v2) | chip does the fusion (LSM6DSV16X SFLP) |
| Projected gravity in simulation | the true gravity from MuJoCo, plus a **slowly varying tilt error of ±2°** (and the ±0.01 noise); not white noise | filter test | ±0.01 noise |
| IMU latency | ~2 ms behind the servo encoder readout | IMU latency | obs delay 0–20 ms |
| IMU mounting error | randomize up to ~6° (random axis); a systematic offset is calibrated at start-up | | up to 6° |
| **Joint velocity (servo speed register)** | **one control step (20 ms) late and quantised to 0.0767 rad/s** (measured); without this in sim the policy oscillated at 8.5 Hz on the real servo. Joint pos noise ±0.001 rad | [pipeline test](../sim/pendulum_policy/README.md) | 1-step lag, vel noise ±0.25 |

## Pipeline test on one servo (done)

The complete chain (BAM sim + DR → PPO → ONNX → 50 Hz loop on the Mac with servo + Nano) was tested on the pendulum: real and sim agree to
0.24° mean, 1.4° max ([details](../sim/pendulum_policy/README.md)). Also needed: a penalty on action changes strong enough that the policy
holds still in simulation, and check in simulation for oscillation before running on hardware.

## Policy and training practice (from Microduck's playbook)

- 50 Hz policy, no action low-pass filter unless the same filter runs on the robot.
- Export to ONNX with the observation normaliser baked in.
- Smoke test first: 5 iterations with 64 envs before any long run.
- Train the zero command (standing still) explicitly.
- Every penalty term in the logs must stay ≤ 0 (sign check).

## Still to measure

- [x] Whole-loop timing on the Mac at 50 Hz, one servo: period 20.00 ms (max 20.3), 1 ms work, IMU data 0.9 ms old ([pipeline test](../sim/pendulum_policy/README.md)). Repeat with all servos on the bus.
- [ ] Supply voltage at the servos with several servos loaded at once (sag).
- [ ] Vibration on the robot body with all leg servos moving, and the filter's real-world output.
- [ ] Gyro bias drift over 10+ minutes as the board warms up.
- [ ] 15 cm arm (higher moment) as an extra check of the 12 V model.
