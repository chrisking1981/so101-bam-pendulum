"""Build cad/viewer/assembly.json (meshes for the 3D viewer) from double_pendulum.py and the official servo STEP.

    uv run --no-project --with build123d --with trimesh --with manifold3d python cad/viewer/build_assembly.py
"""
import json, base64, numpy as np, build123d as b, trimesh
src = open('cad/double_pendulum.py').read().split('up, lo = upper_link(), lower_link()')[0]
g = {'__file__': 'cad/double_pendulum.py'}; exec(src, g)
L1, T, BACK_Z, HORN_TOP, NANO_R = g['L1'], g['T'], g['BACK_Z'], g['HORN_TOP'], g['NANO_R']
up, lo = g['upper_link'](), g['lower_link']()
servo = b.import_step('cad/vendor/STS3215_03a.step')


def tm(shape, tol):
    vs, fs = shape.tessellate(tol); return trimesh.Trimesh(np.array([[v.X, v.Y, v.Z] for v in vs]), np.array(fs))


zl = T - BACK_Z + HORN_TOP
parts = [("Bovenarm (print)", tm(up, 0.08), "#d2a05a")]
s1 = tm(servo, 0.12); s1.apply_translation([-12.5, 0, -HORN_TOP]); parts.append(("Servo 1 (vast)", s1, "#3b3f4a"))
s2 = tm(servo, 0.12); s2.apply_translation([L1 - 12.5, 0, T - BACK_Z]); parts.append(("Servo 2 (in bakje)", s2, "#3b3f4a"))
l2 = tm(lo, 0.08); l2.apply_translation([L1, 0, zl]); parts.append(("Onderarm (print)", l2, "#e3b873"))
nano = []
for y in (-7.62, 7.62):
    sp = trimesh.creation.box([2.54 * 15, 2.54, 2.5]); sp.apply_translation([L1 + NANO_R, y, zl + T + 1.25]); nano.append(sp)
board = trimesh.creation.box([43.16, 17.77, 1.6]); board.apply_translation([L1 + NANO_R, 0, zl + T + 2.5 + 0.8]); nano.append(board)
usb = trimesh.creation.box([5.6, 7.5, 2.6]); usb.apply_translation([L1 + NANO_R - 43.16 / 2 + 1.8, 0, zl + T + 2.5 + 1.6 + 1.3]); nano.append(usb)
parts.append(("Nano 33 IoT", trimesh.util.concatenate(nano), "#1f8a70"))
stand = trimesh.creation.box([50, 34, 6]); stand.apply_translation([-12.5, 0, -HORN_TOP - 17.7 - 3]); parts.append(("Steun (tafel)", stand, "#9aa3ad"))
R = np.array([[0, 1, 0], [0, 0, 1], [-1, 0, 0]], float)   # model x -> down, y -> world x, z -> world y (servo axes horizontal)
out = [dict(name=n, color=c, pos=base64.b64encode((m.vertices @ R.T).astype(np.float32).tobytes()).decode(),
            idx=base64.b64encode(m.faces.astype(np.uint32).tobytes()).decode()) for n, m, c in parts]
json.dump(out, open('cad/viewer/assembly.json', 'w'))
print("assembly.json written")
