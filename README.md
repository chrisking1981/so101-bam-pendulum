# SO-101 leader servo pendulum
A printable bench arm for measuring Feetech STS3215-C044 (1:191) and C046 (1:147) position tracking under known loads. The goal is a MuJoCo actuator model whose predictions match held-out physical trajectories. No validated actuator fit is available yet.

## Prints
Open BAM-kort-100.3mf (load holes at 50, 75 and 100 mm) or BAM-lang-150.3mf (150 mm) in your slicer, flat, at 100%. Mounting face: 4 mm, four M3 clearance holes on a 14 mm pitch circle. The mounting coupon fit one C044 horn. Check clearance and thread engagement on your own hardware. Print strength under dynamic load has not been established. Parametric source: bam_meetarmen.py (Python, build123d and trimesh).

## Measurements
Use measurements/<variant>/<date>-<unique-run>/ for each run. Keep raw recordings unchanged. Store hardware setup, firmware settings, zero convention, actual supply voltage, weighed masses, payload centre radius and arm balance point with each recording. Label estimates explicitly. Record time, commanded and measured angle with units, and torque-enable state. Include voltage, speed, current or load when available. Keep data from a separate trajectory for validation. Commit and push each finished run to preserve it off-device.

Separate the printed arm from hardware around the rotation axis and from the tip payload. The standard BAM pendulum approximation assumes a uniform rod to the load radius. With a fixed arm and multiple holes, its own centre of mass and inertia stay fixed as the load moves.

Reference: https://bam.readthedocs.io/en/latest/identification/index.html

[Short pendulum and fastener mass estimates before weighing](measurements/short-arm-mass-estimates.md)

### First C044 baseline (planned)
With the servo body fixed, pendulum removed and no tip load, document whether the metal horn and centre screw are installed. Read the current encoder position, firmware settings, supply voltage and permitted range before movement. Use the starting position as the reference and run three identical small position steps: reference → +15° → reference, holding each target for one second. Timestamp commands and encoder samples separately, including the settling intervals; log supply voltage and current where available. Compare onset delay, rise time, overshoot, final error and repeatability. This baseline should precede replay with the weighed arm; the earlier 90° check only verified travel.
