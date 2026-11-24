# Firmware

## nano33_imu

Streams the LSM6DS3 IMU of an Arduino Nano 33 IoT over USB (416 Hz, ±4 g, ±1000 °/s, raw counts as text lines `t_us,gx,gy,gz,ax,ay,az`).
The registers are written directly, without the Arduino_LSM6DS3 library, which is limited to 104 Hz.

```
arduino-cli compile --fqbn arduino:samd:nano_33_iot firmware/nano33_imu
arduino-cli upload -p /dev/cu.usbmodem1301 --fqbn arduino:samd:nano_33_iot firmware/nano33_imu
uv run python scripts/imu/nano_imu.py --port /dev/cu.usbmodem1301 --secs 10
```

First test (2026-11-24), board lying still on the table, quiet part of a 10 s recording:

| Quantity | Value |
|---|---|
| Sample rate | 427 Hz (dt 2.34 ms, max 2.40 ms on the Arduino clock) |
| Gyro noise (std) | 0.0026 / 0.0021 / 0.0015 rad/s (x/y/z) |
| Gyro bias | +0.25 / −9.8 / −2.6 °/s, so it must be calibrated at start-up (the policy cannot learn a fixed bias away) |
| Accel noise (std) | 0.011 / 0.013 / 0.014 m/s² |
| |g| | 9.94 m/s² |

For comparison, Microduck's training uses uniform noise of ±0.03 rad/s on the gyro and ±0.01 on the gravity vector. The measured sensor
noise is well below that. The host received one gap of ~60 ms in the 10 s, at a moment when the board was being touched. The receive
timing will be checked again in a longer run.
