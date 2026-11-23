# Compare our replayed logs with the Rhoban logs they replayed.
#   python -m bam.feetech.compare_rhoban --ours data_raw/c001 --rhoban data_rhoban/sts3215/raw [--plot out.png]

import argparse
import glob
import json
import os
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--ours", required=True)
p.add_argument("--rhoban", required=True)
p.add_argument("--plot")
a = p.parse_args()


def arr(d, k):
    return np.array([e[k] for e in d["entries"]], dtype=float)


rows = []
pairs = []
for f in sorted(glob.glob(os.path.join(a.ours, "*.json"))):
    o = json.load(open(f))
    if not o.get("replay_of"):
        continue
    r = json.load(open(os.path.join(a.rhoban, o["replay_of"])))
    to, tr = arr(o, "timestamp"), arr(r, "timestamp")
    po = arr(o, "position")
    pr = np.interp(to, tr, arr(r, "position"))
    go = arr(o, "goal_position")
    en = np.array([e["torque_enable"] for e in o["entries"]])
    m = to <= tr[-1]
    diff = np.degrees(np.abs(po - pr)[m])
    rows.append((o["trajectory"], o["kp"],
                 np.degrees(np.abs(go - po)[en & m].mean()) if (en & m).any() else np.nan,
                 np.degrees(np.abs(np.interp(to, tr, arr(r, "goal_position")) - pr)[en & m].mean()) if (en & m).any() else np.nan,
                 diff.mean(), diff.max()))
    pairs.append((o, r))

print(f"{'trajectory':16} {'kp':>3} {'ours err':>9} {'rhob err':>9} {'|ours-rhob| mean':>17} {'max':>7}   (degrees)")
for t, kp, eo, er, dm, dx in sorted(rows):
    print(f"{t:16} {kp:3d} {eo:9.2f} {er:9.2f} {dm:17.2f} {dx:7.2f}")

if a.plot and pairs:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pairs.sort(key=lambda x: (x[0]["trajectory"], x[0]["kp"]))
    n = len(pairs)
    cols = 4 if n > 4 else n
    rws = int(np.ceil(n / cols))
    fig, axs = plt.subplots(rws, cols, figsize=(4.2 * cols, 2.6 * rws), squeeze=False)
    for ax, (o, r) in zip(axs.flat, pairs):
        ax.plot(arr(r, "timestamp"), np.degrees(arr(r, "goal_position")), "k:", lw=1, label="goal")
        ax.plot(arr(r, "timestamp"), np.degrees(arr(r, "position")), lw=1.2, label="Rhoban")
        ax.plot(arr(o, "timestamp"), np.degrees(arr(o, "position")), lw=1.2, label="ours")
        ax.set_title(f"{o['trajectory']} kp{o['kp']}", fontsize=9)
        ax.grid(alpha=.3)
    for ax in axs.flat[n:]:
        ax.axis("off")
    axs.flat[0].legend(fontsize=7)
    fig.supylabel("angle (deg)")
    fig.supxlabel("time (s)")
    fig.tight_layout()
    fig.savefig(a.plot, dpi=110)
    print("plot ->", a.plot)
