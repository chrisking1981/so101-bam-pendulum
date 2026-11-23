# N-way comparison of our replayed logs (several servos) with the Rhoban logs they replayed.
#   python -m bam.feetech.compare_n --rhoban data_rhoban/sts3215/raw \
#       --set C046=data_raw/c046_noload --set C044=data_raw/c044_noload --set C001=data_raw/c001_noload_final \
#       --plot out.png --md out.md
import argparse, glob, json, os
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--rhoban", required=True)
p.add_argument("--set", action="append", required=True, help="NAME=dir")
p.add_argument("--plot"); p.add_argument("--md")
a = p.parse_args()
sets = [s.split("=", 1) for s in a.set]


def A(d, k): return np.array([e[k] for e in d["entries"]], float)


def load(dirn):
    return {json.load(open(f))["replay_of"]: json.load(open(f)) for f in glob.glob(os.path.join(dirn, "*.json"))}


def metrics(d):
    t, p, g = A(d, "timestamp"), A(d, "position"), A(d, "goal_position")
    en = np.array([e["torque_enable"] for e in d["entries"]])
    err = np.degrees(np.abs(g - p)[en].mean())
    tt = np.arange(0.3, min(t[-1], 5.9), 0.001); pi = np.interp(tt, t, p); gi = np.interp(tt, t, g)
    lags = np.arange(0, 0.4, 0.001)
    lag = 1000 * lags[int(np.argmin([np.mean((np.interp(tt - l, tt, gi) - pi) ** 2) for l in lags]))]
    tg = np.arange(t[0], t[-1], 0.005)
    vmax = np.degrees(np.abs(np.gradient(np.interp(tg, t, p), tg)).max())
    return err, lag, vmax


data = [(n, load(d)) for n, d in sets]
keys = set.intersection(*[set(d) for _, d in data])
order = ["up_and_down", "lift_and_drop", "sin_sin", "brutal", "sin_time_square"]
rows = []
for k in keys:
    r = json.load(open(os.path.join(a.rhoban, k)))
    rows.append((r["trajectory"], r["kp"], [d[k] for _, d in data] + [r]))
rows.sort(key=lambda x: (order.index(x[0]), x[1]))
names = [n for n, _ in data] + ["Rhoban"]
cols = " / ".join(names)
lines = [f"| Trajectory | kp | Tracking error {cols} (°) | Lag {cols} (ms) | Peak speed {cols} (°/s) |", "|---|---:|---|---|---|"]
for t, kp, logs in rows:
    m = [metrics(x) for x in logs]
    lines.append(f"| {t} | {kp} | " + " / ".join(f"{x[0]:.2f}" for x in m) + " | " + " / ".join(f"{x[1]:.0f}" for x in m)
                 + " | " + " / ".join(f"{x[2]:.0f}" for x in m) + " |")
txt = "\n".join(lines)
print(txt)
if a.md:
    open(a.md, "w").write(txt + "\n")
if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(5, 4, figsize=(17, 13), squeeze=False)
    for ax, (t, kp, logs) in zip(axs.flat, rows):
        r = logs[-1]
        ax.plot(A(r, "timestamp"), np.degrees(A(r, "goal_position")), "k:", lw=1, label="goal")
        for n, x in zip(names[::-1], logs[::-1]):
            ax.plot(A(x, "timestamp"), np.degrees(A(x, "position")), lw=1.1, label=n)
        ax.set_title(f"{t} kp{kp}", fontsize=9); ax.grid(alpha=.3)
    axs.flat[0].legend(fontsize=7)
    fig.supylabel("angle (deg)"); fig.supxlabel("time (s)"); fig.tight_layout(); fig.savefig(a.plot, dpi=105)
    print("plot ->", a.plot)
