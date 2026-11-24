# Two-link pendulum (step 2a): model check

Hip = servo 1 (ID 6) on the table, knee = servo 2 (ID 2) in the pocket of the upper link, Nano 33 IoT on the lower link (hardware:
[cad/](../../cad/README.md)). Both 12 V, profile off, P = 32, D = 0.

## Manual check ([`manual_check.py`](manual_check.py))

Slow 20–30° moves of each joint and both together, while reading both servos and the Nano:

- The Nano's filtered tilt equals hip + knee: **0.07° mean, 0.24° max difference**. On this lower link the board is mounted so its angle
  starts near ±180° (wrap the angle) and its gyro z has the **opposite sign** to the joints.
- Load to hold 30° out: about 3% (hip) and 2.4–4% (knee).

## Model check: same goals on the real arm and in MuJoCo + BAM ([`trajectories.py`](trajectories.py), [`run_traj_real.py`](run_traj_real.py), [`compare_traj.py`](compare_traj.py))

The model ([`dp_model.py`](dp_model.py)): BAM 12 V **m5** on both joints, masses as weighed (servo 59 g, lower assembly 26 g; upper link
estimated 17 g). No fitting to these runs.

![compare](data/traj_compare.png)

| Trajectory | Hip: real tracking error | Hip: **sim vs real** | Knee: real tracking error | Knee: **sim vs real** |
|---|---:|---:|---:|---:|
| hip sine ±60° | 3.77° | **0.27°** | 0.16° | **0.17°** |
| knee sine ±70° | 0.09° | **0.09°** | 6.39° | **0.52°** |
| both sine | 2.43° | **0.18°** | 6.44° | **0.39°** |
| steps | 3.07° | **0.20°** | 6.63° | **0.18°** |
| fast knee (±50° square, 1 Hz) | 0.53° | **0.06°** | 37.65° | **0.37°** |

- **The simulation predicts both joints to 0.06–0.52°**, also with both moving at once and the knee pushing back on the hip. The 12 V m5
  model fitted on the single pendulum carries over to a two-joint chain without changes.
- The large "real tracking error" values are the servos lagging behind fast goals (the knee cannot follow a 1 Hz ±50° square wave);
  the simulation has the same lag.
- When only the hip moves, the real knee is pushed up to 0.35° (4 encoder steps) by the motion; the simulation shows less (0.01°).
