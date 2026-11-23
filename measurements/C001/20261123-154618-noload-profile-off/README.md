# C001 no-load replay, acceleration profile off by RAM toggle (85 = 0, then 41 = 0)

These are the same 20 replays as [the profile-on batch](../20261123-153513-noload-profile254/). The difference is that `record_sts.py` wrote 85 = 0 and then 41 = 0 before each run (RAM only, lock on), and restored the previous values after each run. There were no bus timeouts.

**5 runs are invalid:** brutal kp 8 and kp 16, sin_sin kp 4, and sin_time_square kp 16 and kp 32. Their deviation from Rhoban matches the profile-on batch almost exactly, so the profile was most likely still active in them. They were re-recorded with the profile stored off in EEPROM; see [../20261123-160744-rerun-eeprom-profile-off](../20261123-160744-rerun-eeprom-profile-off/) and [../README.md](../README.md#update-2-the-5-deviating-runs-were-the-profile-not-supply-voltage). The other 15 runs match Rhoban within 0.1–0.9° mean.
