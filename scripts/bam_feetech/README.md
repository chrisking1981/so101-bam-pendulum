# STS3215 recorder for BAM (rustypot)

The upstream `bam/feetech/record.py` imports pypot and hardcodes `/dev/ttyACM0` and servo ID 1. These scripts replace it. Copy them into `bam/feetech/` of a [Rhoban/bam](https://github.com/Rhoban/bam) checkout and run them with `uv run python -m bam.feetech.<name>`.

| Script | Purpose |
|---|---|
| `sts.py` | Small rustypot wrapper: raw reads, retry on bus timeout, gains, angle limits, acceleration profile (registers 85/41) |
| `sts_check.py` | Status of the servo and an optional RD6006 (Modbus). `--zero` stores the hanging pendulum position. `--rate` measures the read loop |
| `record_sts.py` | Records one BAM trajectory, or with `--replay <log>` replays the exact goal/torque sequence of an existing raw log. D = 0. The acceleration profile is off by default (`--accel-profile 0 0`). P/D, 85/41 and torque-off are restored afterwards |
| `all_record_sts.py` | Full sweep for one mass/length: kp 4/8/16/32 × 4 trajectories |
| `replay_rhoban.py` | Replays all Rhoban raw logs of one load configuration. Skips logs that were already recorded |
| `compare_rhoban.py` | Tracking error and position difference against the replayed Rhoban logs, plus an optional plot |

All register writes are done with the EEPROM lock on, so they are lost at power-off. The defaults (`--port`, `--id`) match the setup in [measurements/C001](../../measurements/C001/README.md). Adjust them for your own setup.
