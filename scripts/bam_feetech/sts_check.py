# Pre-flight checks for STS3215 BAM recording (no motion unless stated).
#
#   python -m bam.feetech.sts_check              status of servo (+ RD6006)
#   python -m bam.feetech.sts_check --zero       torque off, store hanging position
#   python -m bam.feetech.sts_check --rate       measure read loop rate (3 s, torque off)

import argparse
import json
import struct
import time
import numpy as np
import serial
from bam.feetech.sts import STS, STEP, ZERO_FILE

p = argparse.ArgumentParser()
p.add_argument("--port", default="/dev/cu.usbmodem5B421351891")
p.add_argument("--id", type=int, default=3)
p.add_argument("--rd-port", default="/dev/cu.usbserial-1130")
p.add_argument("--zero", action="store_true")
p.add_argument("--rate", action="store_true")
a = p.parse_args()


def rd6006(port):
    def crc(d):
        c = 0xFFFF
        for b in d:
            c ^= b
            for _ in range(8):
                c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
        return struct.pack("<H", c)

    try:
        s = serial.Serial(port, 115200, timeout=0.3)
        q = bytes([1, 3, 0, 0, 0, 20])
        s.write(q + crc(q))
        time.sleep(0.15)
        r = s.read(64)
        s.close()
        g = struct.unpack(">20H", r[3:43])
        return dict(vset=g[8] / 100, iset=g[9] / 1000, vout=g[10] / 100, iout=g[11] / 1000, on=g[18])
    except Exception as e:
        return {"error": str(e)}


m = STS(a.port, a.id)
c = m.c
pos, spd, load, volt, temp = m.read_raw()
print(f"STS3215 id={a.id}: pos={pos} ({(pos-2048)*STEP:+.3f} rad)  V={volt:.1f}  T={temp}C")
print(f"  limits raw: {c.read_raw_min_angle_limit(a.id)[0]}..{c.read_raw_max_angle_limit(a.id)[0]}"
      f"  P/I/D={c.read_p_coefficient(a.id)[0]}/{c.read_i_coefficient(a.id)[0]}/{c.read_d_coefficient(a.id)[0]}"
      f"  lock={c.read_lock(a.id)[0]}  torque={c.read_torque_enable(a.id)[0]}")
if a.rd_port:
    rd = rd6006(a.rd_port)
    print("  RD6006:", rd)
    if "iset" in rd and rd["iset"] < 2.5:
        print("  !! RD6006 current limit < 2.5 A: stalls/fast moves will hit CC mode and drop voltage")
    if "vout" in rd and abs(rd["vout"] - volt) > 0.3:
        print(f"  !! servo sees {volt:.1f} V vs {rd['vout']:.2f} V at supply (cable/adapter drop)")

if a.zero:
    m.torque(False)
    input("Torque OFF. Let the pendulum hang still straight down, then press Enter...")
    vals = [m.read_raw()[0] for _ in range(50)]
    zero = int(round(np.median(vals)))
    spread = max(vals) - min(vals)
    json.dump({"zero": zero, "port": a.port, "id": a.id}, open(ZERO_FILE, "w"))
    print(f"zero = {zero} (spread {spread} steps) -> {ZERO_FILE}")
    # sin_sin goes to ~ +-2.07 rad = +-1350 steps around zero; must not wrap 0/4095
    if not (1400 <= zero <= 2700):
        print("!! Zero is too close to the 0/4095 wrap: trajectories (up to +-2.07 rad) would wrap.")
        print("   Re-mount the horn/arm so the hanging position reads near 2048.")
    else:
        print("OK: +-2.1 rad around zero stays inside the encoder range.")

if a.rate:
    m.torque(False)
    t0 = time.time()
    ts = []
    while time.time() - t0 < 3:
        m.read_raw()
        ts.append(time.time())
    dt = np.diff(ts) * 1000
    print(f"read rate: {len(ts)/3:.0f} Hz, dt mean {dt.mean():.2f} ms, p99 {np.percentile(dt,99):.2f} ms, max {dt.max():.2f} ms")
