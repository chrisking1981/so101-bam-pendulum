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

## Policy on both joints: trained in simulation, run on the real arm ([`dp_env.py`](dp_env.py), [`train.py`](train.py), [`run_real.py`](run_real.py), [`run_sim.py`](run_sim.py))

PPO, 1.5 M steps on the MacBook CPU (6.6 min), with everything from the one-servo test in from the start (speed-register lag and
quantisation, Nano tilt wander, smoothness penalty 3.0) plus randomized masses and a small cable spring/friction per joint.
Observation: both encoders, both servo speeds, Nano tilt and gyro, both targets and errors, last action. Goals clamped to ±80°.
Masses: upper link 22 g and as-built lower link 12.3 g from the Bambu Studio slice (35.6 g for both, split by volume); this changed
the model check above by less than 0.01°.

![policy](data/d1_real_vs_sim.png)

| | Hip | Knee |
|---|---:|---:|
| Tracking error, real (sim) | 4.08° (3.99°) | 5.59° (5.47°) |
| **Real vs sim**, mean / max | **0.22° / 1.96°** | **0.23° / 2.47°** |
| Real inside the randomized sim band | 100% | 100% |
| Oscillation while holding (action std), real | 0.01° | 0.01° |

- **It worked the first time on the real arm**, with no changes after the simulation: same response as in simulation, no oscillation.
  The lessons from the one-servo test (speed lag, smoothness) were already in the training.
- Loop on the Mac with two servos and the Nano: 20.00 ms period (max 20.00), 1.8 ms work per tick (max 4.4), fresh IMU data every tick.
- Nano tilt against hip + knee during the run: 0.69° mean (includes fast moves).

**Second real run** (same policy): real vs sim 0.20° / 0.27° mean (hip / knee), 100% inside the randomized band, no oscillation.
Run 1 vs run 2 differ by only 0.09° / 0.10° mean, so the real arm is very repeatable.

## Two C044 servos at 5 V (2026-11-25, rig `c044both`)

Hip = C044 ID 3, knee = C044 ID 1, both on the leader-arm board with its 5 V adapter; the 12 V board is not used. Every script takes
`--rig` (setups in [`rig.py`](rig.py)). Models: the C044 **m4** fit (made at 7.4 V) at 5 V, servo mass 57 g. Overview with explanation:
[showcase/01-double-pendulum-c044](../../showcase/01-double-pendulum-c044/README.md).

**Model check** ([table](data/traj_compare_c044.md), [plot](data/traj_compare_c044.png)): sim vs real 0.15–0.61° on all trajectories
except the fast knee square wave (3.26°): at full speed the real servo is slightly faster than the model at 5.0 V (0.92° with 5.2 V in the
model). Training therefore randomizes the supply between 4.8 and 5.4 V.

**Policy** (`runs/c044_1`, 1.5 M steps, 10.5 min): sim 3.82° / 5.23° tracking (hip / knee), randomized 3.95° / 5.35°, no oscillation while holding.

![c044 policy](data/c044_real_vs_sim.png)

| | Hip | Knee |
|---|---:|---:|
| Tracking error, real (sim) | 3.84° (3.82°) | 5.15° (5.23°) |
| **Real vs sim**, mean / max | **0.33° / 2.95°** | **0.34° / 3.17°** |
| Real inside the randomized sim band | 96% | 99% |
| Action std while holding, real | 0.07° | 0.07° |

First run on the real arm, no changes after training. Loop: 20.00 ms period (max 21.1), 1.7 ms work, IMU data every tick; Nano tilt vs
hip + knee 0.62° mean.

## 12 V hip + C044 knee (2026-11-25, rig `c044knee`)

Hip = 12 V follower ID 3 on the 12 V board, knee = C044 ID 1 on the leader board (5 V), each with its own cable to its own board.
Manual check: Nano tilt vs hip + knee 0.11° mean, 0.40° max. Model check: [table](data/traj_compare_c044knee.md) (sim vs real 0.06–0.52°,
fast knee 3.33°). Policy `runs/c044knee_1` (1.5 M steps, 10 min): sim 3.91° / 5.21°.

| | Hip | Knee |
|---|---:|---:|
| Tracking error, real (sim) | 4.06° (3.91°) | 5.08° (5.21°) |
| **Real vs sim**, mean / max | **0.24° / 2.19°** | **0.44° / 5.59°** |
| Inside randomized band | 99% | 98% |
| Action std while holding, real | 0.33° | 0.42° |

![c044knee](data/c044knee_real_vs_sim.png)

Loop 20.00 ms (max 20.00), 1.8 ms work; Nano tilt vs hip + knee 0.41°. The real action jitters slightly while holding (0.3–0.4°, sim 0.00°).
