"""Printable STS3215 horn coupon and BAM arm. All dimensions in mm."""
from pathlib import Path
from math import sqrt
import build123d as b
import trimesh
from zipfile import ZipFile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
PITCH_RADIUS = 7.0
MOUNT_DIAM = 3.4
CENTER_CLEARANCE = 6.5
WEIGHT_DIAM = 4.5
# One short arm for light-load tests and one long arm for comparison.
def make_arm(stations):
    tip = stations[-1]
    offset = PITCH_RADIUS / sqrt(2)
    holes = [(0, 0, CENTER_CLEARANCE)]
    holes.extend((x, y, MOUNT_DIAM) for x in (-offset, offset) for y in (-offset, offset))
    holes.extend((x, 0, WEIGHT_DIAM) for x in stations)
    outline = b.Circle(12) + b.Pos(tip/2, 0) * b.Rectangle(tip, 20) + b.Pos(tip, 0) * b.Circle(10)
    solid = b.extrude(outline, amount=8)
    # Flat 4 mm mounting face under the M3 heads, rising gently to 8 mm.
    cut_profile = b.Plane.XZ * b.Polygon((-15,4),(12,4),(28,8),(28,10),(-15,10),align=None)
    solid -= b.extrude(cut_profile, amount=16, both=True)
    for x,y,d in holes:
        solid -= b.Pos(x,y,4) * b.Cylinder(d/2, 12)
    return solid, holes

for stations, name in [((50,75,100), "BAM-kort-100"), ((150,), "BAM-lang-150")]:
    solid, holes = make_arm(stations)
    assert solid.is_valid and len(solid.solids()) == 1
    writer = b.Mesher()
    writer.add_shape(solid, linear_deflection=0.025, angular_deflection=0.1)
    path = OUT / (name + ".3mf")
    writer.write(path)
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
    assert root.get("unit") == "millimeter"
    vertices = [[float(v.get(k)) for k in ("x", "y", "z")] for v in root.findall(".//{*}vertex")]
    triangles = [[int(t.get(k)) for k in ("v1", "v2", "v3")] for t in root.findall(".//{*}triangle")]
    mesh = trimesh.Trimesh(vertices=vertices, faces=triangles)
    mesh.merge_vertices()
    assert mesh.is_volume and len(mesh.split()) == 1
    assert abs(mesh.extents[2] - 8) < 0.001
    section = mesh.section(plane_origin=[0,0,2.5], plane_normal=[0,0,1])
    loops = section.discrete
    assert len(loops) == len(holes) + 1
    for x,y,d in holes:
        assert any(max(abs((line[:,0].max()+line[:,0].min())/2-x),
                       abs((line[:,1].max()+line[:,1].min())/2-y),
                       abs((line[:,0].max()-line[:,0].min())-d)) < 0.05 for line in loops)
    assert abs(max(z for x,y,z in vertices if abs(x)<10) - 4) < 0.001
    print(name, mesh.extents, "verified holes", len(holes))
