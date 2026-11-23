# C044 (ID 1) with the 450 g pendulum

This is the same pendulum as the C046 and C001 450 g sets: 450 g total, with the centre of mass at 100 mm (0.44 Nm when horizontal).

## Settings

| Item | Value |
|---|---|
| Servo | C044 unit 2 (bus ID 1), profile off in EEPROM |
| Supply | RD6006 at 7.40 V |
| Gains | P = 4 / 8 / 16 / 32, D = 0 |
| Zero | Hanging rest position, raw 1969 |
| BAM log values | `mass = 0.450`, `arm_mass = 0`, `length = 0.100` |
| Runs | 16, no bus timeouts. Servo at 29 °C afterwards |

## Manual tests (`manual-tests.json.gz`)

The angle limits were opened in RAM for these tests.

| Test | Sag | PWM |
|---|---:|---:|
| Hold at +45°, P = 32 | 1.9° | 16% |
| Hold at +90°, P = 32 | 3.1° | 27% |
| Hold at −90°, P = 32 | 3.2° | 29% |
| Hold at +90°, P = 8 | 4.1° | 9% |
| Release at 44° | Falls without oscillation and stops at 3.7° | — |

The comparison of all three types under this load is in [../../compare/types-450g.md](../../compare/types-450g.md).
