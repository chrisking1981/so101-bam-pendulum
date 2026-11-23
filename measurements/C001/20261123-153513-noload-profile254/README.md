# C001 no-load replay, acceleration profile as found (85 = 254, 41 = 0)

These are 20 replays of Rhoban's no-load STS3215 logs: 5 trajectories × kp 4/8/16/32, with D = 0, I = 0, the metal horn only, and 7.40 V set on the RD6006.

- The kp 4 and kp 8 runs were recorded first. The batch then stopped on a bus timeout during `brutal` kp 16. After the stop, torque was off and P/D were restored. The shaft was re-centred to raw 1569, and the rest of the batch was recorded from that point.
- These logs have no `accel_profile_85_41` field. The registers were read before and after the batch, and both times they were 85 = 254, 41 = 0.
- Compared with Rhoban, the motion starts about 35–50 ms late. See `comparison.txt`, `comparison.png` and [../README.md](../README.md).
