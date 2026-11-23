# Simple 4-servo biped in MuJoCo

`biped.xml` is the plain biped from [docs/robot-concepts.html](../../docs/robot-concepts.html), built in MuJoCo with the fitted BAM servo models in
the loop:

- **Hips:** C044, BAM fit [fits/C044/m6.json](../../fits/C044/m6.json).
- **Ankles:** C046, BAM fit [fits/C046/m4.json](../../fits/C046/m4.json).
- All four joints pitch about the lateral axis and are driven by `<motor>` actuators. `run_biped.py` attaches a
  `bam.mujoco.MujocoController` per servo type, which runs the STS3215 firmware P-controller (`kp_fw` = 32, 7.4 V), the motor model and BAM's
  friction every 1 ms step.
- Every part is a box, so weighed masses and measured centres of mass can be entered directly. Foot contact is four rubber pads per foot. The IMU is a
  site in the middle of the pelvis, with quaternion, gyro and accelerometer sensors.
- Total mass **0.569 kg, estimated**: servo 55 g, printed holder 12 g, 2S LiPo 60 g. Replace these with weighed values once it is built.

## First test (2026-11-23)

| Test | What it does | Pelvis height | Max pitch / roll | Max joint error | Result |
|---|---|---|---|---|---|
| stand | all targets 0, 4 s | 0.160 m | 0.2° / 0.0° | 0.1° | upright |
| lean | ankles tilt the body ±0.2 rad | 0.158–0.160 m | 11.7° / 0.0° | 0.7° | upright |
| scissor | hips swing in opposite phase (±0.25 rad), ankles compensate | 0.157–0.160 m | 1.2° / 0.1° | 1.5° | upright |

![Frames from the three tests](biped_frames.png)

This only shows that the model is consistent, stands, and that the BAM servos drive it as intended. It is not yet validated against a real robot.

## Run

From a [Rhoban/bam](https://github.com/Rhoban/bam) checkout with `uv sync --extra mujoco`:

```bash
MUJOCO_GL=cgl uv run python /path/to/sim/biped/run_biped.py --render frames
```

To look at the model interactively (without the BAM servos, so the joints are limp):

```bash
uv run python -m mujoco.viewer --mjcf=/path/to/sim/biped/biped.xml
```

On macOS use `mjpython` instead of `python` for the viewer.

## Next steps towards RL

- Build the real biped and weigh each part, then update the masses in `biped.xml`.
- Train in mjlab with `BamActuatorCfg` and the randomization ranges from [docs/sim-setup-guide.md](../../docs/sim-setup-guide.md):
  friction about 0.7–1.3, battery voltage, delay, and backlash once it is measured.
- Store the acceleration profile off (85 = 0, 41 = 0) in all four servos' EEPROM, and check it at startup.
