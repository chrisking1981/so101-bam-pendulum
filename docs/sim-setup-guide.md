# Setting up STS3215 servos in MuJoCo for sim2real: lessons from this bench

This guide records what the measurements in this repository show about simulating Feetech STS3215 servos (C001 1:345,
C044 1:191, C046 1:147) for reinforcement learning. Each point links to the data behind it. It is a living document: points
marked *provisional* rest on a single unit, a single load or a single fit.

Status (2026-11-23): all six SO-101 leader servos measured without load; C046, C044 (both units) and C001 measured with a
450 g / 100 mm pendulum; C046 also with 281 g / 92 mm. BAM fits for the C046 and the C044 (a C044 fit also tested on a second unit).

## 1. Fix the firmware acceleration profile before anything else

- STS3215 firmware 3.10 has an acceleration profile in registers 85 (maximum acceleration) and 41 (acceleration). With it on, every
  move starts about 35–50 ms later ([C001](../measurements/C001/README.md#finding-2-the-register-85-acceleration-profile-explains-it)).
- **It was on (85 = 254) on all six servos as delivered.** LeRobot writes 254 to 85 and 41 on every connect.
- **Turn it off by storing it in EEPROM.** The sequence is: torque off, lock (55) = 0, 85 = 0, then 41 = 0, then lock = 1. Register 85 only takes effect
  after a write to 41. Once stored, it survives a power cycle ([verification](../measurements/C001/README.md#update-profile-disabled-permanently-on-this-unit-2026-11-23)).
- **Do not toggle it in RAM before each move.** That proved unreliable: 5 of 20 runs still behaved as profile-on
  ([Update 2](../measurements/C001/README.md#update-2-the-5-deviating-runs-were-the-profile-not-supply-voltage)).
- **Robot startup code:** read 85/41 back from every servo and refuse to start if they are not 0/0. Do it again after anything else (for
  example LeRobot) has talked to the bus.
- **Simulation:** Rhoban's BAM STS3215 model and all fits in this repo assume the profile is **off**. If a robot has to run with it on,
  the actuator model needs an extra acceleration-limited target, and the identification must be repeated with the profile on.

## 2. One actuator model per servo type

- The gear ratio changes the behaviour too much for one model plus randomization. Under the same 450 g load, `sin_time_square` at kp 32 lags
  **22 / 41 / 105 ms** for the C046 / C044 / C001 ([types-450g](../measurements/compare/README.md)).
- On held-out C046 runs, the C046's own fit gets **0.57°**; Rhoban's C001 model gets **7.68°** ([C046 fit](../fits/C046/README.md)).
- Units of the same type are close. Without load: 3–9% in tracking error ([C044 units](../measurements/C044/20261123-163134-unit2-id1-noload-profile-off/README.md),
  [C046 units](../measurements/C046/20261123-165146-unit3-id5-noload-profile-off/README.md)). With 450 g: 0.72° mean, about 4% in
  tracking error ([C044 under load](../measurements/C044/20261123-180605-id3-pendulum-450g/README.md)).
- **Model the type that is actually in each joint.** Leader and follower arms of the SO-101 use different types; the follower in the Pro kit uses
  12 V 1:345 servos, which are not measured here.

## 3. Use BAM's model in the loop, not a fitted PD actuator

- Use `bam.mujoco.MujocoController` (CPU) or `bam.mjlab.BamActuatorCfg` (GPU), with joints driven by `<motor>` actuators. BAM's
  `to_mujoco` export to a `position` actuator is deprecated: it flattens away the load-dependent friction.
- **Model choice:** m4 or m6, which add load-dependent and Stribeck friction to m1. C046: m4 gives 0.57° on unseen runs (m1 0.88°, m6 0.63°). C044: m6 0.63° and m4 0.66°
  on unseen runs without `lift_and_drop`, and 0.65°/0.67° on a **second unit the fit never saw** ([C044 fit](../fits/C044/README.md)). Both beat m1.
- **Stick-slip cannot be predicted exactly.** After a release with a light load, the arm sometimes sticks part-way up its swing and sometimes falls back.
  Which one happens varies between units and runs, and the models miss it (up to 14° error on that run). Static friction in simulation plus friction
  randomization is the way to cover it.
- The friction under load is real and large. The C001 holds the 450 g pendulum at 45° with torque off and does not move. With P = 8, the C046 and C001 hold
  the arm almost as well as with P = 32 while using a third of the PWM ([C046 450 g](../measurements/C046/20261123-173924-id5-pendulum-450g/README.md),
  [C001 450 g](../measurements/C001/20261123-175101-id2-pendulum-450g/README.md)).

## 4. Same gains in simulation and on the robot

- BAM's STS3215 model uses the **firmware P register** (`kp_fw`) directly. The measured holding PWM matches BAM's duty = P × 0.166 ×
  error for the C046 as well (16% measured against 17% predicted).
- Set **D = 0** on the servos. BAM's model has no D term, and the factory default is D = 32. Data recorded with D = 32 is not
  comparable.
- Train with the same `kp_fw` that the robot will use. If it is randomized, randomize it in simulation too.

## 5. What to randomize, and how much

All ranges below are proposals based on the spread measured here; they are not yet validated with a trained policy.

| Quantity | Proposed range | Evidence |
|---|---|---|
| Friction scale (`friction_scale_range`) | about 0.7–1.3 | Friction varies most between units. Under load, two C044s differ most where friction dominates (rest after release, slow moves at low P). Our C001 has more static friction than Rhoban's model predicts |
| Motor strength / supply voltage (`vin_range`) | Battery range, e.g. 6.8–8.2 V for 2S | Torque and speed scale with voltage. Tracking error differs by only 3–9% between units |
| Voltage sag (`vin_drop_resistance_range`) | Small, measure on the robot | Not measured here: a bench supply was used |
| Command delay (`delay_min_lag` / `delay_max_lag`) | 0 to one control step plus the measured loop latency | Bus round trip 0.34 ms; the servo flags *moving* 1.5 ms after a goal write. The fitted `command_delay` is 1.5–2.2 ms. The real latency is set by the robot's control loop, so measure it there |
| Backlash | about ±1° (as in Microduck) | Not measured here |

Keep the type-specific model as the centre, and do not widen ranges to cover other servo types (see section 2).

## 6. Do not trust the servo's own voltage or temperature registers

- The voltage register reads about 0.3 V low at idle and showed spikes from 4.6 V to 17.8 V during motion, while the bench supply held
  7.31–7.39 V ([C001](../measurements/C001/README.md)).
- The temperature register gives single readings up to 67 °C while the servo is at 27 °C
  ([C046 450 g](../measurements/C046/20261123-173924-id5-pendulum-450g/README.md)).
- Safety guards built on these registers will trip on glitches. Only act on several consecutive readings, and use external supply
  measurements where they matter.

## 7. Bench and identification practice

- Log at a high rate. rustypot with one 8-byte read per loop reaches about 1200 Hz on this USB adapter; BAM resamples to 5 ms.
- The load must be rigid. Bolt it with two bolts; do not hang it on a string. Weigh the complete pendulum, and find its centre of mass by
  balancing it over an edge, measured from the axis.
- Use several loads per type. The C046 fit used no load, 281 g / 92 mm and 450 g / 100 mm.
- Hold out one P value (kp 8) for validation.
- **Pipeline check:** refitting Rhoban's raw data reproduces Rhoban's published parameters (kt 1.168 vs 1.178, armature 0.0259 vs 0.0261), and
  Rhoban's C001 model predicts our C001 to about 1° ([fits](../fits/README.md), [C001 450 g](../measurements/C001/20261123-175101-id2-pendulum-450g/README.md)).
- **Known limitation:** the inertia of the wide steel brackets is not modelled (point-mass assumption), an estimated 5–10%. A swing-period
  test of the pendulum would remove this.

## Open items

- A fit for the C001 with its own data (Rhoban's model already predicts it to about 1°).
- A first MuJoCo / mjlab test of the C046 model against a held-out real trajectory, and of the full randomization setup.
- The 12 V 1:345 follower servos.
- Measuring the control-loop latency and battery sag on the actual robot.
