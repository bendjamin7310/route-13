"""Licence plates. The plate face is UV-mapped 0..1 so a plate texture
(or a SurfaceGui) can be dropped straight on. The front plate and its
bracket are the Two-Faced Car upgrade from the design doc; the setup
module hides them by default.
"""

import numpy as np

from dims import *  # noqa: F401,F403
from spec import MeshPart

PLATE = (0.36, 0.18)


def plate_box(center, size, facing):
    """Box with the face pointing along `facing` (+1 = +Y, -1 = -Y) UV-mapped 0..1."""
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    verts, faces, uvs = [], [], []

    def quad(pts, uv):
        base = len(verts)
        verts.extend(pts)
        faces.append([base, base + 1, base + 2, base + 3])
        uvs.extend(uv)

    yf = cy + sy * facing
    yb = cy - sy * facing
    # main face, wound so its normal points along `facing`; viewer's right is -X*facing
    l, r = (cx - sx * -facing, cx + sx * -facing)
    pts = [(l, yf, cz - sz), (r, yf, cz - sz), (r, yf, cz + sz), (l, yf, cz + sz)]
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    quad(pts, uv)
    z0 = [(0.0, 0.0)] * 4
    quad([(l, yb, cz - sz), (l, yb, cz + sz), (r, yb, cz + sz), (r, yb, cz - sz)], z0)
    quad([(l, yb, cz + sz), (l, yf, cz + sz), (r, yf, cz + sz), (r, yb, cz + sz)], z0)
    quad([(l, yb, cz - sz), (r, yb, cz - sz), (r, yf, cz - sz), (l, yf, cz - sz)], z0)
    quad([(l, yb, cz - sz), (l, yf, cz - sz), (l, yf, cz + sz), (l, yb, cz + sz)], z0)
    quad([(r, yb, cz - sz), (r, yb, cz + sz), (r, yf, cz + sz), (r, yf, cz - sz)], z0)
    v = np.array(verts, dtype=np.float32)
    f = np.array(faces, dtype=np.int32)
    # make every quad face away from the box centre
    c = np.array(center)
    for i, q in enumerate(f):
        p = v[q]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(n, p.mean(axis=0) - c) < 0:
            f[i] = q[::-1]
            uvs[i * 4:i * 4 + 4] = uvs[i * 4:i * 4 + 4][::-1]
    return v, f, np.array(uvs, dtype=np.float32)


def parts():
    P = []
    v, f, uv = plate_box((0.0, Y_TAIL + 0.006, 0.574), (PLATE[0], 0.004, PLATE[1]), -1)
    P.append(MeshPart("Plate_Rear", v, f, "Plate", group="Plates", uv=uv, sharp=30))
    v, f, uv = plate_box((0.0, Y_NOSE + 0.0145, 0.620), (PLATE[0], 0.004, PLATE[1]), 1)
    P.append(MeshPart("Plate_Front", v, f, "Plate", group="Plates", uv=uv, sharp=30))
    v, f, uv = plate_box((0.0, Y_NOSE + 0.0065, 0.620), (PLATE[0] + 0.024, 0.012, PLATE[1] + 0.02), 1)
    P.append(MeshPart("PlateBracket_Front", v, f, "TrimBlack", group="Plates", uv=uv, sharp=30))
    return P
