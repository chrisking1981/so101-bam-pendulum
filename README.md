# SO-101 leader servo pendulum
A printable bench arm for measuring Feetech STS3215-C001 (1:345), C044 (1:191) and C046 (1:147) position tracking under known loads. The goal is a MuJoCo actuator model whose predictions match held-out physical trajectories. No validated actuator fit is available yet.

**Robot concepts that use all six leader servos (3D, open the HTML in a browser): [docs/robot-concepts.html](docs/robot-concepts.html).**

**Simple 4-servo biped in MuJoCo with the fitted BAM servo models: [sim/biped](sim/biped/README.md).**

**How to set up the simulation, based on these measurements: [docs/sim-setup-guide.md](docs/sim-setup-guide.md).**

## Findings so far (no load, 2026-11-23)

Six leader-arm servos were measured (C001, two C044 units and three C046 units), each with only the metal horn attached and at 7.40 V. Each one replayed the exact
command sequences of [Rhoban's public BAM STS3215 data](https://huggingface.co/buckets/Gregwar/bam_data) (20 no-load logs).

| Finding | Result | Details |
|---|---|---|
| Hidden firmware acceleration profile (register 85) | Adds about 35–50 ms of start-up delay to every move. It was on (85 = 254) on all six servos as received. Disabling it (85 = 0, then 41 = 0) works, and once stored in EEPROM it survives a power cycle. Toggling it in RAM before each run proved unreliable | [C001](measurements/C001/README.md) |
| C001 (1:345) vs Rhoban's STS3215 | With the profile off, mean trace difference 0.74° over 20 runs. Our unit tracks about 5% worse. Rhoban's unit was most likely a C001 with the profile off | [Table](measurements/C001/final-noload-comparison.md) |
| C044 (1:191) vs C001 (1:345) | Without load the C044 has about 35–40% less lag, peaks about 1.6× faster in a step (about 520 vs 320 °/s) and overshoots more. Rhoban's 1:345 model does not fit a C044 | [C044](measurements/C044/20261123-161907-noload-profile-off/README.md) |
| C046 (1:147) vs C044 and C001 | The order holds in every run: lower gearing gives less lag, a faster step (C046 about 660 °/s) and more overshoot (8° at kp 32). The C046 has about 15–20% less lag than the C044 and about half that of the C001 | [C046](measurements/C046/20261123-163853-noload-profile-off/README.md) |
| STS3215 12 V follower (1:345) without load | Behaves almost like the 7.4 V C001: 5° step in 56.5 ms (C001 59 ms), similar lag and peak speed; somewhat more lag at kp 4. Profile was on as well and is stored off | [12 V no load](measurements/STS3215-12V/20261124-105321-id3-noload-profile-off/README.md), [12 V with 218 g](measurements/STS3215-12V/20261124-110331-id3-pendulum-holesaw-218g/README.md): under load very stiff (0.6° sag at 0.21 Nm); Rhoban's 7.4 V model misses it by 4–7° |
| Three 12 V follower units without load | Pairs differ by only 0.14–0.17°, once the LeRobot gripper limits on ID 6 (50% torque) were set equal to the others | [3 units](measurements/STS3215-12V/) |
| Unit-to-unit spread, same kit | Two C044 units: 0.27° mean trace difference, about 3% in tracking error. Three C046 units: 0.26–0.48° between pairs, up to about 9%; the gripper servo is the slowest | [C044 units](measurements/C044/20261123-163134-unit2-id1-noload-profile-off/README.md), [C046 units](measurements/C046/20261123-165146-unit3-id5-noload-profile-off/README.md) |
| USB hub, bus latency | Not a factor. Round trip 0.34 ms, and the servo flags *moving* 1.5 ms after a goal write | [C001](measurements/C001/README.md#finding-1-the-extra-delay-comes-from-the-servo-firmware-not-from-usb) |
| Servo voltage register | Unreliable: it reads about 0.3 V low at idle and spikes to 17.8 V during motion. Do not use it as a guard | [C001](measurements/C001/README.md) |

All six servos of one SO-101 leader arm (Seeed kit SKU 114993667), each with the acceleration profile stored off in EEPROM:

| Joint | Bus ID | Type | 5° step time (P = 32) | Data |
|---|---:|---|---:|---|
| 1 | 1 | C044 1:191 | 36.4 ms | [C044 unit 2](measurements/C044/20261123-163134-unit2-id1-noload-profile-off/README.md) |
| 2 | 2 | C001 1:345 | 59.0 ms | [C001](measurements/C001/README.md) |
| 3 | 3 | C044 1:191 | 35.7 ms | [C044 unit 1](measurements/C044/20261123-161907-noload-profile-off/README.md) |
| 4 | 4 | C046 1:147 | 31.5 ms | [C046 unit 1](measurements/C046/20261123-163853-noload-profile-off/README.md) |
| 5 | 5 | C046 1:147 | 32.6 ms | [C046 unit 3](measurements/C046/20261123-165146-unit3-id5-noload-profile-off/README.md) |
| 6 (gripper) | 6 | C046 1:147 | 32.6 ms | [C046 unit 2](measurements/C046/20261123-164605-unit2-id6-noload-profile-off/README.md) |

Loaded runs on the C046 (ID 5): [281 g at 92 mm](measurements/C046/20261123-171452-id5-pendulum-281g/README.md) and [450 g at 100 mm](measurements/C046/20261123-173924-id5-pendulum-450g/README.md), each with 16 runs plus manual hold and release tests. Same 450 g load on all three types: [types-450g](measurements/compare/README.md). BAM fits: [C046](fits/C046/README.md) and [C044](fits/C044/README.md). The C044 fit also predicts a second C044 unit it never saw to 0.65° (without the stick-slip release runs). [In MuJoCo](fits/mujoco/README.md), the models with BAM in the loop reproduce real runs to about 0.6°; a constant position actuator is 1.5–3.6× worse. Its m4 model predicts held-out runs to 0.57°; Rhoban's C001 model gives 7.7° on the same runs. Refitting Rhoban's data reproduces their published parameters ([fits](fits/README.md)). The earlier C044 runs in `measurements/C044/2026112*-horn-*` were made with a 5 V
adapter, D = 32, the profile on and about 40 Hz logging, so they are not comparable with the runs above.

## Prints
Open BAM-kort-100.3mf (load holes at 50, 75 and 100 mm) or BAM-lang-150.3mf (150 mm) in your slicer, flat, at 100%. Mounting face: 4 mm, four M3 clearance holes on a 14 mm pitch circle. The mounting coupon fit one C044 horn. Check clearance and thread engagement on your own hardware. Print strength under dynamic load has not been established. Parametric source: bam_meetarmen.py (Python, build123d and trimesh).

**Hole saws as weights:** a hole saw is round and symmetric, so when its arbor hole is centred on a load hole of the arm, its centre of mass is
exactly on that hole. Print [hole_saw_bushing.3mf](hole_saw_bushing.3mf) (source: [hole_saw_bushing.py](hole_saw_bushing.py)): a Ø14.7 × 4.6 mm
bushing with an M4 hole, which centres the saw's 15 mm hole on the arm's M4 bolt. It is slightly lower than the 5 mm saw base, so the bolt clamps the
saw itself. Use one bushing per stacked saw and a large washer under the nut. Tape over the teeth before running fast trajectories.

## Measurements
Use measurements/<variant>/<date>-<unique-run>/ for each run. Keep raw recordings unchanged. Store hardware setup, firmware settings, zero convention, actual supply voltage, weighed masses, payload centre radius and arm balance point with each recording. Label estimates explicitly. Record time, commanded and measured angle with units, and torque-enable state. Include voltage, speed, current or load when available. Keep data from a separate trajectory for validation. Commit and push each finished run to preserve it off-device.

Separate the printed arm from hardware around the rotation axis and from the tip payload. The standard BAM pendulum approximation assumes a uniform rod to the load radius. With a fixed arm and multiple holes, its own centre of mass and inertia stay fixed as the load moves.

Reference: https://bam.readthedocs.io/en/latest/identification/index.html

[Short pendulum and fastener mass estimates before weighing](measurements/short-arm-mass-estimates.md)

### Firmware acceleration profile: check it first
The STS3215 has an acceleration profile in registers 85 (maximum acceleration) and 41 (acceleration). It adds about 35–50 ms of start-up delay to every move. LeRobot turns it on, and so do other tools. Rhoban's BAM STS3215 data matches a servo with the profile off (85 = 0, then 41 = 0). Record and simulate with the same 85/41 values the robot will run with, store those values with every log, and read them back at startup. See [C001 no-load replay of Rhoban's data](measurements/C001/README.md), [C044 vs C001 vs Rhoban, no load](measurements/C044/20261123-161907-noload-profile-off/README.md) and [two C044 units compared](measurements/C044/20261123-163134-unit2-id1-noload-profile-off/README.md).

The recorder used here (rustypot, about 1.2 kHz, `--replay` of Rhoban logs) is in [scripts/bam_feetech](scripts/bam_feetech/).

### First C044 baseline (planned)
With the servo body fixed, pendulum removed and no tip load, document whether the metal horn and centre screw are installed. Read the current encoder position, firmware settings, supply voltage and permitted range before movement. Use the starting position as the reference and run three identical small position steps: reference → +15° → reference, holding each target for one second. Timestamp commands and encoder samples separately, including the settling intervals; log supply voltage and current where available. Compare onset delay, rise time, overshoot, final error and repeatability. This baseline should precede replay with the weighed arm; the earlier 90° check only verified travel.
