# Three-way comparison: two of our servos vs the Rhoban logs they both replayed.
#   python -m bam.feetech.compare3 --a data_raw/c044_noload --b data_raw/c001_noload_final \
#       --rhoban data_rhoban/sts3215/raw --names C044 C001 --plot out.png --md out.md
import argparse, glob, json, os
import numpy as np

p = argparse.ArgumentParser()
p.add_argument("--a", required=True); p.add_argument("--b", required=True)
p.add_argument("--rhoban", required=True); p.add_argument("--names", nargs=2, default=["A", "B"])
p.add_argument("--plot"); p.add_argument("--md")
a = p.parse_args()
A_, B_ = a.names


def A(d, k): return np.array([e[k] for e in d["entries"]], float)


def load(dirn):
    out = {}
    for f in glob.glob(os.path.join(dirn, "*.json")):
        d = json.load(open(f)); out[d["replay_of"]] = d
    return out


def metrics(d):
    t, p, g = A(d, "timestamp"), A(d, "position"), A(d, "goal_position")
    en = np.array([e["torque_enable"] for e in d["entries"]])
    err = np.degrees(np.abs(g - p)[en].mean())
    tt = np.arange(0.3, min(t[-1], 5.9), 0.001); pi = np.interp(tt, t, p); gi = np.interp(tt, t, g)
    lags = np.arange(0, 0.4, 0.001)
    lag = 1000 * lags[int(np.argmin([np.mean((np.interp(tt - l, tt, gi) - pi) ** 2) for l in lags]))]
    tg = np.arange(t[0], t[-1], 0.005)  # same 5 ms grid for every log (BAM's processing dt)
    v = np.gradient(np.interp(tg, t, p), tg)
    vmax = np.degrees(np.abs(v).max())
    return err, lag, vmax


da, db = load(a.a), load(a.b)
order = ["up_and_down", "lift_and_drop", "sin_sin", "brutal", "sin_time_square"]
rows = []
for k in sorted(set(da) & set(db)):
    r = json.load(open(os.path.join(a.rhoban, k)))
    rows.append((r["trajectory"], r["kp"], metrics(da[k]), metrics(db[k]), metrics(r), da[k], db[k], r))
rows.sort(key=lambda x: (order.index(x[0]), x[1]))

lines = [f"| Trajectory | kp | Tracking error {A_} | {B_} | Rhoban (°) | Lag {A_} | {B_} | Rhoban (ms) | Peak speed {A_} | {B_} | Rhoban (°/s) |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for t, kp, ma, mb, mr, *_ in rows:
    lines.append(f"| {t} | {kp} | {ma[0]:.2f} | {mb[0]:.2f} | {mr[0]:.2f} | {ma[1]:.0f} | {mb[1]:.0f} | {mr[1]:.0f} | {ma[2]:.0f} | {mb[2]:.0f} | {mr[2]:.0f} |")
txt = "\n".join(lines)
print(txt)
if a.md:
    open(a.md, "w").write(txt + "\n")

if a.plot:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(5, 4, figsize=(17, 13), squeeze=False)
    for ax, (t, kp, ma, mb, mr, xa, xb, r) in zip(axs.flat, rows):
        ax.plot(A(r, "timestamp"), np.degrees(A(r, "goal_position")), "k:", lw=1, label="goal")
        ax.plot(A(r, "timestamp"), np.degrees(A(r, "position")), lw=1.1, label="Rhoban")
        ax.plot(A(xb, "timestamp"), np.degrees(A(xb, "position")), lw=1.1, label=B_)
        ax.plot(A(xa, "timestamp"), np.degrees(A(xa, "position")), lw=1.1, label=A_)
        ax.set_title(f"{t} kp{kp}", fontsize=9); ax.grid(alpha=.3)
    axs.flat[0].legend(fontsize=7)
    fig.supylabel("angle (deg)"); fig.supxlabel("time (s)"); fig.tight_layout(); fig.savefig(a.plot, dpi=105)
    print("plot ->", a.plot)
