# Evaluate BAM params on processed logs: mean |sim - real| position error per log.
#   python -m bam.feetech.eval_params --params a.json b.json --logdir fit/c001/proc_load
import argparse, glob, json, os
import numpy as np
from bam.model import load_model
from bam import simulate

p = argparse.ArgumentParser()
p.add_argument("--params", nargs="+", required=True)
p.add_argument("--logdir", nargs="+", required=True)
p.add_argument("--names", nargs="*")
a = p.parse_args()
names = a.names or [os.path.basename(os.path.dirname(x)) + "/" + os.path.basename(x) for x in a.params]

logs = []
for d in a.logdir:
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        logs.append(json.load(open(f)))
order = ["up_and_down", "lift_and_drop", "sin_sin", "brutal", "sin_time_square"]
logs.sort(key=lambda l: (l["mass"], order.index(l["trajectory"]), l["kp"]))


def mae(params, log):
    model = load_model(params)
    sim = simulate.Simulator(model)
    pos = np.array(sim.rollout_log(log, simulate_control=True)[0])
    real = np.array([e["position"] for e in log["entries"]])
    return np.degrees(np.mean(np.abs(pos - real)))


res = np.array([[mae(pp, l) for pp in a.params] for l in logs])
print("| mass (kg) | trajectory | kp | " + " | ".join(f"sim−real {n} (°)" for n in names) + " |")
print("|---:|---|---:|" + "---:|" * len(names))
for l, r in zip(logs, res):
    print(f"| {l['mass']:.3f} | {l['trajectory']} | {l['kp']} | " + " | ".join(f"{x:.2f}" for x in r) + " |")
print("| **mean** | | | " + " | ".join(f"**{x:.2f}**" for x in res.mean(0)) + " |")
