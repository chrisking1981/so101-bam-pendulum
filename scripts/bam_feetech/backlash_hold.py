# Hold the servo at 0 (P32) for a fixed time and log encoder + load while the operator wiggles the arm by hand.
import sys, time, json, numpy as np
from bam.feetech.sts import STS, STEP, load_zero
ID = int(sys.argv[1]); SECS = float(sys.argv[2]); OUT = sys.argv[3]
m = STS('/dev/cu.usbmodem5B421346401', ID)
zero = m.read_raw()[0]  # hold at the current hanging position (no gravity zero needed for backlash)
orig = (m.c.read_p_coefficient(ID)[0], m.c.read_d_coefficient(ID)[0])
log = []
try:
    m.open_limits(); m.set_gains(32, 0); m.goal_raw(zero); m.torque(True)
    t0 = time.time(); nxt = 0
    while (t := time.time() - t0) < SECS:
        pos, spd, load, v, temp = m.read_raw()
        log.append((t, (pos - zero) * STEP * 57.2958, load))
        if t >= nxt:
            w = [x for x in log if x[0] > t - 1]
            print(f"t={t:5.1f}s  encoder {min(x[1] for x in w):+.2f}..{max(x[1] for x in w):+.2f} deg  load {min(x[2] for x in w):+5.0f}..{max(x[2] for x in w):+5.0f}", flush=True)
            nxt += 5
finally:
    m.torque(False); m.set_gains(*orig)
a = np.array(log)
json.dump(dict(id=ID, zero=zero, t=a[:, 0].tolist(), pos_deg=a[:, 1].tolist(), load=a[:, 2].tolist()), open(OUT, 'w'))
print(f"total encoder range {a[:,1].min():+.2f}..{a[:,1].max():+.2f} deg, load range {a[:,2].min():+.0f}..{a[:,2].max():+.0f} /1000, samples {len(a)}")
