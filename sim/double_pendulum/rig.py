"""Hardware setups of the two-link pendulum. Every script takes --rig <name>.

Each joint: serial port of its bus, servo ID, BAM model file, supply voltage for the model, servo mass (kg).
The 12 V followers and the 7.4 V leader servos must never share a bus (the supply runs through the bus cable).
"""
import glob, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F12 = os.path.join(REPO, "fits", "STS3215-12V", "m5.json")
C044 = os.path.join(REPO, "fits", "C044", "m4.json")
BUS12 = "/dev/cu.usbmodem5B421346401"      # SO-101 follower USB board + 12 V adapter
BUS_LEADER = "/dev/cu.usbmodem5B421351891" # SO-101 leader USB board + 5 V adapter

RIGS = {
    "12v": dict(hip=dict(port=BUS12, id=6, params=F12, vin=12.0, mass=0.059),
                knee=dict(port=BUS12, id=2, params=F12, vin=12.0, mass=0.059)),
    "c044both": dict(hip=dict(port=BUS_LEADER, id=3, params=C044, vin=5.0, mass=0.057),
                     knee=dict(port=BUS_LEADER, id=1, params=C044, vin=5.0, mass=0.057)),
    "c044knee": dict(hip=dict(port=BUS12, id=6, params=F12, vin=12.0, mass=0.059),
                     knee=dict(port=BUS_LEADER, id=None, params=C044, vin=5.0, mass=0.057)),   # id set with --knee-id
}


def nano_port():
    """The Nano's USB port name changes when it is plugged into another socket: take the one that is not a servo board."""
    ports = [p for p in glob.glob("/dev/cu.usbmodem*") if p not in (BUS12, BUS_LEADER)]
    if len(ports) != 1:
        raise RuntimeError(f"cannot tell which port is the Nano: {ports}")
    return ports[0]


def get(name, knee_id=None):
    r = {k: dict(v) for k, v in RIGS[name].items()}
    if knee_id is not None:
        r["knee"]["id"] = knee_id
    if r["knee"]["id"] is None and name != "c044both":
        raise SystemExit("this rig needs --knee-id (which leader servo is in the pocket)")
    return r
