# Full session for one mass/length combination: all kps x all trajectories.

import argparse
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--port", default="/dev/cu.usbmodem5B421351891")
p.add_argument("--id", type=int, default=3)
p.add_argument("--mass", type=float, required=True)
p.add_argument("--arm-mass", type=float, required=True)
p.add_argument("--length", type=float, required=True)
p.add_argument("--vin", type=float, default=7.4)
p.add_argument("--motor", default="sts3215")
p.add_argument("--logdir", required=True)
p.add_argument("--kps", default="4,8,16,32")
p.add_argument("--trajectories", default="sin_time_square,lift_and_drop,up_and_down,sin_sin")
a = p.parse_args()

for kp in a.kps.split(","):
    for tr in a.trajectories.split(","):
        print(f"== kp {kp}, {tr}")
        subprocess.run([sys.executable, "-m", "bam.feetech.record_sts", "--port", a.port,
                        "--id", str(a.id), "--mass", str(a.mass), "--arm-mass", str(a.arm_mass),
                        "--length", str(a.length), "--kp", kp, "--vin", str(a.vin),
                        "--motor", a.motor, "--trajectory", tr, "--logdir", a.logdir], check=True)
        time.sleep(2)  # let the servo cool a bit between runs
