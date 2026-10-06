"""Window glass as thin two-sided sheets that tuck into the frame openings."""

import numpy as np
from scipy.spatial import Delaunay

import body
from dims import *  # noqa: F401,F403
from spec import MeshPart

T = 0.005        # glass thickness
INSET = 0.011    # outer face of the glass below the body surface
TUCK = 0.013     # how far the glass edge runs under the frame


def _offset_poly(pts, d):
    pts = np.asarray(pts, dtype=np.float64)
    # drop duplicate consecutive points
    keep = np.ones(len(pts), bool)
    keep[1:] = np.linalg.norm(np.diff(pts, axis=0), axis=1) > 1e-6
    pts = pts[keep]
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    sgn = 1.0 if area > 0 else -1.0
    prev = np.roll(pts, 1, axis=0)
    nxt = np.roll(pts, -1, axis=0)
    e1 = pts - prev
    e2 = nxt - pts
    n1 = np.stack([e1[:, 1], -e1[:, 0]], 1) * sgn
    n2 = np.stack([e2[:, 1], -e2[:, 0]], 1) * sgn
    n1 /= np.linalg.norm(n1, axis=1, keepdims=True)
    n2 /= np.linalg.norm(n2, axis=1, keepdims=True)
    n = n1 + n2
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    cosh = np.clip(np.einsum("ij,ij->i", n, n1), 0.5, 1)
    return pts + n * (d / cosh)[:, None]


def _resample(pts, step):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        k = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        for j in range(k):
            out.append(a + (b - a) * j / k)
    return np.array(out)


def _inside(poly, p):
    from sdf import poly2
    p = np.asarray(p, dtype=np.float64)
    return poly2(p[:, 0], p[:, 1], poly) < 0


def sheet(poly2d, to3d, step=0.07, grid=0.16):
    """Thin closed sheet over a 2D outline. to3d(u, v, off) -> (N, 3)."""
    outline = _resample(_offset_poly(poly2d, TUCK), step)
    lo, hi = outline.min(0), outline.max(0)
    gu = np.arange(lo[0] + grid / 2, hi[0], grid)
    gv = np.arange(lo[1] + grid / 2, hi[1], grid)
    G = np.array([(u, v) for u in gu for v in gv])
    inner = _offset_poly(outline, -grid * 0.35)
    if len(G):
        G = G[_inside(inner, G)]
    pts2 = np.concatenate([outline, G]) if len(G) else outline
    tri = Delaunay(pts2).simplices
    cen = pts2[tri].mean(axis=1)
    tri = tri[_inside(outline, cen)]
    nb = len(outline)
    n2 = len(pts2)
    outer = to3d(pts2[:, 0], pts2[:, 1], INSET)
    inner3 = to3d(pts2[:, 0], pts2[:, 1], INSET + T)
    verts = np.concatenate([outer, inner3])
    faces = [list(t) for t in tri] + [[t[0] + n2, t[2] + n2, t[1] + n2] for t in tri]
    for i in range(nb):
        j = (i + 1) % nb
        faces.append([i, j, j + n2, i + n2])
    verts = np.asarray(verts, dtype=np.float32)
    # orient: outer layer faces must point away from the inner layer
    f0 = np.array(faces[0])
    a, b, c = verts[f0[0]], verts[f0[1]], verts[f0[2]]
    nrm = np.cross(b - a, c - a)
    if np.dot(nrm, verts[f0[0]] - verts[f0[0] + n2]) < 0:
        faces = [list(reversed(f)) for f in faces]
    # rim quads: orient outward from the sheet centroid
    cen3 = verts.mean(axis=0)
    fixed = []
    for f in faces:
        if len(f) == 4:
            p = verts[f]
            nrm = np.cross(p[1] - p[0], p[2] - p[0])
            if np.dot(nrm, p.mean(axis=0) - cen3) < 0:
                f = list(reversed(f))
        fixed.append(f)
    return verts, fixed


# ------------------------------------------------------------------ mappings

def _ws_map(u, v, off):
    L, run, rise = body.WS_L, body.WS_RUN, body.WS_RISE
    y = Y_WS_BASE - body.WS_WRAP * u * u - v * run / L - off * rise / L
    z = Z_WS_BASE + v * rise / L - off * run / L
    return np.stack([u, y, z], 1)


def _side_map(sign):
    def m(y, z, off):
        x = (body.GH_BELT_W - (z - Z_BELT_F) * body.GH_TUMBLE - off) * sign
        return np.stack([x, y, z], 1)
    return m


def _rear_map(x, z, off):
    y = Y_RW_BOT + 0.035 * (x / 0.7) ** 2 + (z - 1.300) * body.RW_DY / body.RW_DZ + off
    return np.stack([x, y, z], 1)


def parts():
    P = []
    v, f = sheet(body._WS, _ws_map)
    P.append(MeshPart("Glass_Windshield", v, f, "Glass", group="Glass", sharp=60))
    v, f = sheet(body._RW, _rear_map)
    P.append(MeshPart("Glass_Rear", v, f, "Glass", group="Glass", sharp=60))
    for sign, side in ((1, "R"), (-1, "L")):
        for poly, door in ((body._FW, "F"), (body._RWS, "R")):
            v, f = sheet(poly, _side_map(sign))
            P.append(MeshPart(f"Door_{door}{side}_Glass", v, f, "Glass", group="Doors", sharp=60))
    return P
