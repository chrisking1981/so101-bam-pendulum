# C001 no-load replay, acceleration profile off (85 = 0, then 41 = 0)

Same 20 replays as [the profile-on batch](../20261123-153513-noload-profile254/). The only difference is that `record_sts.py` wrote 85 = 0 and then 41 = 0 before each run (RAM only, lock on), and wrote the previous values back after each run. There were no bus timeouts. 15 of the 20 runs match Rhoban within 0.1–0.9° mean. See `comparison.txt`, `comparison.png` and [../README.md](../README.md) for the remaining differences.
