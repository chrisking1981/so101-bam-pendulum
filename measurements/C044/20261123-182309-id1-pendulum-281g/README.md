# C044 unit 2 (ID 1) with the 281 g pendulum

This is the same 281 g pendulum as the other 281 g sets: two large steel brackets at the 75 mm and 100 mm holes, with the centre of mass at 92 mm.

Settings:

- Supply: RD6006 at 7.40 V.
- P = 4/8/16/32, D = 0, profile off in EEPROM.
- Zero: hanging rest position raw 2040.
- BAM log values: `mass = 0.281`, `arm_mass = 0`, `length = 0.092`.
- 16 runs, no bus timeouts. The servo read 29 °C afterwards.

Unit 2 now has no-load, 281 g and 450 g data, the same as unit 1 (ID 3). Its data is used to test whether a fit on unit 1 also predicts
unit 2: see [fits/C044](../../../fits/C044/README.md).
