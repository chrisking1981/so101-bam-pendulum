"""Read the Arduino Nano 33 IoT IMU stream (firmware/nano33_imu) on the Mac.

Firmware v2 lines: t_us,gx,gy,gz,ax,ay,az,ux,uy,uz (gyro bias-corrected on the board; u = filtered up vector x 1e4).
Older v1 lines without the up vector are still accepted (up = None).

    uv run python scripts/imu/nano_imu.py --port /dev/cu.usbmodem1301 --secs 10 --out imu_still.npz
Prints the sample rate, timing jitter, gyro bias and noise, and the gravity vector.
Units: gyro rad/s, accel m/s^2, t seconds (Arduino clock) and host receive time.
"""
import argparse, time
import numpy as np
import serial

GYRO = 0.035 * np.pi / 180      # rad/s per LSB (1000 dps range)
ACC = 0.122e-3 * 9.80665        # m/s^2 per LSB (+-4 g range)


class NanoIMU:
    def __init__(self, port):
        self.s = serial.Serial(port, 1_000_000, timeout=0.1)
        self.s.reset_input_buffer(); self.buf = b""; self.info = []

    def read_all(self):
        """Return all complete samples received so far: list of (t_arduino_s, t_host_s, gyro[3], acc[3], up[3] or None)."""
        self.buf += self.s.read(self.s.in_waiting or 1)
        *lines, self.buf = self.buf.split(b"\n")
        th = time.time(); out = []
        for l in lines:
            p = l.strip().split(b",")
            if l.startswith(b"#"):
                self.info.append(l.decode(errors="replace").strip()); continue
            if len(p) not in (7, 10):
                continue
            try:
                v = [int(x) for x in p]
            except ValueError:
                continue
            up = np.array(v[7:10]) * 1e-4 if len(v) == 10 else None
            out.append((v[0] * 1e-6, th, np.array(v[1:4]) * GYRO, np.array(v[4:7]) * ACC, up))
        return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/cu.usbmodem1301")
    ap.add_argument("--secs", type=float, default=10)
    ap.add_argument("--out")
    a = ap.parse_args()
    imu = NanoIMU(a.port); time.sleep(0.3); imu.read_all()
    S = []; t0 = time.time()
    while time.time() - t0 < a.secs:
        S += imu.read_all()
    t = np.array([x[0] for x in S]); th = np.array([x[1] for x in S])
    g = np.array([x[2] for x in S]); acc = np.array([x[3] for x in S])
    dt = np.diff(t)
    print(f"samples {len(S)} in {t[-1]-t[0]:.2f} s  ->  {1/np.median(dt):.1f} Hz (dt median {np.median(dt)*1e3:.2f} ms, max {dt.max()*1e3:.2f} ms)")
    print("gyro bias  (deg/s):", np.round(np.degrees(g.mean(0)), 3), "  noise std (deg/s):", np.round(np.degrees(g.std(0)), 3), "  (rad/s):", np.round(g.std(0), 4))
    print("accel mean (m/s^2):", np.round(acc.mean(0), 3), " |a| =", round(float(np.linalg.norm(acc.mean(0))), 3), "  noise std:", np.round(acc.std(0), 4))
    gv = acc.mean(0) / np.linalg.norm(acc.mean(0))
    print("tilt from flat (deg): roll %.2f  pitch %.2f" % (np.degrees(np.arctan2(gv[1], gv[2])), np.degrees(np.arctan2(-gv[0], np.hypot(gv[1], gv[2])))))
    hd = np.diff(th); print(f"host receive: batches every {np.median(hd[hd>0])*1e3:.2f} ms (max gap {hd.max()*1e3:.1f} ms)")
    if S[0][4] is not None:
        up = np.array([x[4] for x in S]); an = acc / np.linalg.norm(acc, axis=1, keepdims=True)
        dang = np.degrees(np.arccos(np.clip(np.sum(up * an, 1), -1, 1)))
        print(f"filtered up vector: mean {np.round(up.mean(0),4)}, std {np.round(up.std(0),5)}; angle to raw accel direction: mean {dang.mean():.2f} deg")
    for l in imu.info:
        print(l)
    if a.out:
        np.savez(a.out, t=t, t_host=th, gyro=g, acc=acc, **({"up": np.array([x[4] for x in S])} if S[0][4] is not None else {}))
