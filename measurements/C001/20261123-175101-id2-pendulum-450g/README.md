# C001 (ID 2) with the 450 g pendulum, and Rhoban's model tested on our data

This is the same pendulum as [the C046 450 g set](../../C046/20261123-173924-id5-pendulum-450g/README.md): 450 g total, with the centre of mass at
100 mm. The gravity torque is 0.44 Nm when the arm is horizontal. Rhoban's lightest configuration was 0.546 kg at 0.10 m, so this is close.

## Settings

| Item | Value |
|---|---|
| Servo | C001 (1:345), bus ID 2, profile off in EEPROM |
| Supply | RD6006 at 7.40 V |
| Gains | P = 4 / 8 / 16 / 32, D = 0 |
| Zero | Hanging rest position, raw 1755 (all samples equal) |
| BAM log values | `mass = 0.450`, `arm_mass = 0`, `length = 0.100` |
| Runs | 16, about 1200–2000 Hz, no bus timeouts. Servo at 28 °C afterwards |
| Fits running at the same time | The C046 fits were running on the same Mac during this recording. The sample rate was unaffected |

## Manual tests (`manual-tests.json.gz`)

| Test | Result |
|---|---|
| Hold at +45°, P = 32 | 0.97° sag, 9.6% PWM |
| Hold at +90°, P = 32 | 1.49° sag, 14.4% PWM. The C046 needed 30% for the same load |
| Hold at +90°, P = 8 | **Same 1.49°**, 4.6% PWM. Friction holds the arm, so the lower P makes no difference |
| Hold at −90° | **Invalid.** The goal (raw 731) was below the servo's stored angle limit (828), and this test script did not open the limits. The arm stopped at −80.3°. `record_sts.py` does open the limits, so the runs are not affected |
| Release at 44.8° (torque off) | **The arm does not move** and stays at 44.8°. The C001 gearbox is not back-driven by 0.31 Nm |

## Rhoban's bundled model on our C001

Rhoban's `feetech_sts3215_7_4V` m1 and m6 parameters, fitted on Rhoban's own servo, were run in BAM's simulator on our
logs. We did no fitting here. The values are the mean |sim − real| position error per run. The no-load runs are the 20 valid ones from
[final-noload-comparison.md](../final-noload-comparison.md). Full table: [rhoban-model-on-our-data.md](rhoban-model-on-our-data.md).

| Set | Rhoban m1 | Rhoban m6 |
|---|---:|---:|
| Mean over all 36 runs | **1.13°** | **1.11°** |
| up_and_down, 450 g, kp 4 / 8 / 16 / 32 | 2.01 / 1.24 / 0.66 / 0.34 | 1.50 / 0.72 / 0.30 / 0.12 |
| sin_sin, 450 g | 0.37–0.77 | 0.28–0.74 |
| sin_time_square, 450 g | 0.65–1.46 | 1.05–1.65 |
| lift_and_drop, 450 g, kp 4 / 8 / 16 / 32 | 9.35 / 2.58 / 2.89 / 2.97 | 8.66 / 2.70 / 2.90 / 3.03 |

- **Rhoban's model predicts our C001 to about 1° without any re-fitting**, with and without load. This confirms the bench (mass, centre of mass,
  zero, recorder) and supports the conclusion that Rhoban's unit was a C001 with the acceleration profile off.
- **The only clear miss is where the arm comes to rest after release** in `lift_and_drop`. Real and simulated arm both fall from −90° and swing to
  about +30°, but the real arm stops earlier. At kp 4 it stops at +24.3° against +4.9° in simulation. At the other gains it stops at −2 to −4° against +2°.
  So our unit has more static friction under load than Rhoban's model. The manual release test above shows the same thing.

## Not done yet

- A 281 g set on the C001.
- Our own fit for the C001, to compare with Rhoban's parameters.
