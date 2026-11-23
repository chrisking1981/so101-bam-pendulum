# Helpers for recording a Feetech STS3215 with rustypot (replaces the pypot-based
# record.py, which hardcodes /dev/ttyACM0 and id 1).
#
# Conventions:
#   - BAM's Pendulum model has q = 0 when the arm hangs straight down.
#   - The raw position of the hanging arm is stored as "zero" in sts_zero.json
#     (see `python -m bam.feetech.sts_check --zero`).
#   - Register writes (P/D gain, angle limits) are done with the EEPROM lock
#     ON, so they are NOT saved: a power cycle restores the original values.

import json
import os
import numpy as np
import rustypot

STEP = 2 * np.pi / 4096
ZERO_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "sts_zero.json")


def sm(v: int, bit: int) -> int:
    """Feetech sign-magnitude decode."""
    return -(v & ((1 << bit) - 1)) if v & (1 << bit) else v


class STS:
    def __init__(self, port: str, sid: int, baud: int = 1000000):
        self.c = rustypot.Sts3215PyController(port, baud, 0.05)
        self.id = sid
        if not self.c.ping(sid):
            raise RuntimeError(f"No STS3215 with id {sid} on {port}")
        if not self.c.read_lock(sid)[0]:
            raise RuntimeError("EEPROM lock is OFF: refusing to write gains (would be persisted)")

    timeouts = 0

    def _retry(self, fn, *args, tries=3):
        for i in range(tries):
            try:
                return fn(*args)
            except RuntimeError as e:
                if "timed out" not in str(e) or i == tries - 1:
                    raise
                STS.timeouts += 1

    def read_raw(self):
        r = self._retry(self.c.read_raw_data, self.id, 56, 8)
        pos = sm(r[0] | r[1] << 8, 15)
        speed = sm(r[2] | r[3] << 8, 15)
        load = sm(r[4] | r[5] << 8, 10)
        return pos, speed, load, r[6] * 0.1, r[7]

    def torque(self, on: bool):
        self._retry(self.c.write_torque_enable, self.id, on)
        if not on and self._retry(self.c.read_torque_enable, self.id)[0]:
            self._retry(self.c.write_torque_enable, self.id, False)

    def goal_raw(self, raw: float):
        # goal_position in rustypot is (raw - 2048) * STEP
        self._retry(self.c.write_goal_position, self.id, (raw - 2048) * STEP)

    def set_gains(self, kp: int, kd: int = 0):
        self.c.write_p_coefficient(self.id, int(kp))
        self.c.write_d_coefficient(self.id, int(kd))
        self.c.write_i_coefficient(self.id, 0)

    def accel_profile(self, max_acc: int, acc: int):
        """Firmware acceleration profile. 85 = 0 then 41 = 0 disables it (85 only takes
        effect after a write to 41). Rhoban's BAM data matches the profile-off behaviour.
        LeRobot writes 254/254 on connect. RAM only while the lock is on."""
        self._retry(self.c.write_maximum_acceleration, self.id, int(max_acc))
        self._retry(self.c.write_acceleration, self.id, int(acc))

    def read_accel_profile(self):
        return (self._retry(self.c.read_maximum_acceleration, self.id)[0],
                self._retry(self.c.read_acceleration, self.id)[0])

    def open_limits(self):
        self.c.write_raw_min_angle_limit(self.id, 0)
        self.c.write_raw_max_angle_limit(self.id, 4095)


def load_zero(port_id_key: str | None = None) -> int:
    if not os.path.exists(ZERO_FILE):
        raise RuntimeError("No sts_zero.json: run `python -m bam.feetech.sts_check --zero` first")
    return int(json.load(open(ZERO_FILE))["zero"])
