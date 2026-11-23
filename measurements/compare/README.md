# Servo types compared under the same load

[types-450g.md](types-450g.md) compares the C046 (ID 5), C044 (ID 1) and C001 (ID 2), each running the same 16 BAM runs with the same
450 g / 100 mm pendulum at 7.40 V, P = 4/8/16/32, D = 0. The plot is [types-450g.png](types-450g.png).

- **Slow, gravity-dominated moves** (`up_and_down`, `lift_and_drop`): the types are close. Here the C001 has the lowest error in
  `up_and_down` (more torque per PWM), and `lift_and_drop` is nearly identical for all three.
- **Fast moves** (`sin_sin`, `sin_time_square`): the types are far apart. In `sin_time_square` at kp 32 the lag is 22 / 41 / 105 ms and the
  tracking error is 5.4 / 9.0 / 18.0° (C046 / C044 / C001).
- **For simulation:** Rhoban's C001 model predicts our C001 to about 1°, but the C046 only to 7.7° on held-out runs. The C046's own fit gets 0.6°
  ([../../fits/C046](../../fits/C046/README.md)). One model per servo type is needed. A randomization range wide enough to cover all three
  types would make the simulated servo several times faster or slower than the real one.
