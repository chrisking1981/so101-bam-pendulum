"""Fixed goal trajectories for the two-link pendulum (radians), shared by the real runner and the simulation replay."""
import numpy as np

D = np.radians


def _steps(t, seq, dt):
    return seq[min(int(t // dt), len(seq) - 1)]


TRAJ = {
    # name: (duration s, function t -> (hip goal, knee goal))
    "hip_sine":   (8.0, lambda t: (D(60) * np.sin(2 * np.pi * 0.4 * t) * min(t, 1.0), 0.0)),
    "knee_sine":  (8.0, lambda t: (0.0, D(70) * np.sin(2 * np.pi * 0.6 * t) * min(t, 1.0))),
    "both_sine":  (10.0, lambda t: (D(50) * np.sin(2 * np.pi * 0.3 * t) * min(t, 1.0), D(60) * np.sin(2 * np.pi * 0.7 * t + 1.0) * min(t, 1.0))),
    "steps":      (9.0, lambda t: (_steps(t, [0, D(40), D(40), D(-40), D(-40), 0, 0, D(20), 0], 1.0),
                                    _steps(t, [0, 0, D(60), D(60), D(-60), D(-60), 0, D(-30), 0], 1.0))),
    "fast_knee":  (6.0, lambda t: (D(30), D(50) * np.sign(np.sin(2 * np.pi * 1.0 * t)) * (t > 0.5))),
}


def goals(name, t):
    return np.array(TRAJ[name][1](t), float)
