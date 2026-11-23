# C044 P=4 abrupt step with metal horn only

The first 90-degree target change produced simultaneous low voltage and high current reports. The recorder stopped after 57 samples at 1.530 s. This partial run does not count toward the matrix.

| Sample | Reported voltage (V) | Current register (raw) | Command (ticks) | Encoder (ticks) |
|---|---:|---:|---:|---:|
| Previous sample | 5.0 | 0 | 2949 | 1900 |
| Stop sample | 4.6 | 162 | 2949 | 1905 |

The final readback confirmed torque off and restored P=32, D=32, I=0 and settings lock on. The step and increasing-frequency sine are both limited on this power setup, even at P=4. Before retesting, check voltage at the servo's supply connector with an independent time-resolving measurement, or use a suitable bench supply with headroom above 5 V and sufficient transient response. Keep voltage within the limits of the servo and the connected adapter board. A 5 V-domain reading from the servo alone cannot establish the electrical cause of the excursions.
