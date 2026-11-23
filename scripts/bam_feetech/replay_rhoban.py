# Replay every Rhoban STS3215 raw log of one load configuration on our servo.
#
#   python -m bam.feetech.replay_rhoban --rhoban <dir with raw/*.json> --mass 0 --length 0 \
#       --arm-mass 0 --id 2 --motor sts3215_c001 --vin 7.1 --logdir data_raw/c001 --zero-here
#
# --mass/--length select which Rhoban configuration to replay (0/0, 0.546/0.1, 1.084/0.1,
# 1.084/0.15, 0.546/0.15). The values written to our logs are --our-mass/--our-length if
# given (use your weighed values), else the same as Rhoban's.

import argparse
import glob
import json
import os
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--rhoban", required=True)
p.add_argument("--mass", type=float, required=True)
p.add_argument("--length", type=float, required=True)
p.add_argument("--our-mass", type=float)
p.add_argument("--our-length", type=float)
p.add_argument("--arm-mass", type=float, default=0.0)
p.add_argument("--port", default="/dev/cu.usbmodem5B421351891")
p.add_argument("--id", type=int, required=True)
p.add_argument("--motor", required=True)
p.add_argument("--vin", type=float, required=True)
p.add_argument("--logdir", required=True)
p.add_argument("--zero-here", action="store_true")
p.add_argument("--only", help="comma list of trajectories to replay")
a = p.parse_args()

runs = []
for f in sorted(glob.glob(os.path.join(a.rhoban, "**", "*.json"), recursive=True)):
    d = json.load(open(f))
    if abs(d["mass"] - a.mass) < 1e-6 and abs(d["length"] - a.length) < 1e-6:
        if not a.only or d["trajectory"] in a.only.split(","):
            runs.append((d["kp"], d["trajectory"], f))
runs.sort()
print(f"{len(runs)} Rhoban runs for mass={a.mass} length={a.length}")

done = set()
for g in glob.glob(os.path.join(a.logdir, "*.json")):
    try:
        done.add(json.load(open(g)).get("replay_of"))
    except Exception:
        pass

for kp, tr, f in runs:
    if os.path.basename(f) in done:
        print(f"-- skip kp {kp}, {tr} (already recorded)")
        continue
    print(f"== kp {kp}, {tr}  ({os.path.basename(f)})", flush=True)
    cmd = [sys.executable, "-m", "bam.feetech.record_sts", "--port", a.port, "--id", str(a.id),
           "--mass", str(a.our_mass if a.our_mass is not None else a.mass),
           "--length", str(a.our_length if a.our_length is not None else a.length),
           "--arm-mass", str(a.arm_mass), "--vin", str(a.vin), "--motor", a.motor,
           "--logdir", a.logdir, "--replay", f]
    if a.zero_here:
        cmd.append("--zero-here")
    subprocess.run(cmd, check=True)
    time.sleep(2)
