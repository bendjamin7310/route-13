"""Geometry primitives shared by every generator.

Everything in the town is described as a list of *primitives* before it ever
touches Blender: boxes, wedges, cylinders, balls and (rarely) free meshes.
Keeping the description engine-agnostic lets one generator feed three outputs:

* the Blender scene (primitives merged into per-material meshes),
* FBX files for Roblox's 3D Importer, and
* native Roblox Parts / colliders (a box *is* a Part, a wedge *is* a WedgePart).

Coordinates follow Blender: +X east, +Y north, +Z up, 1 unit = 1 Roblox stud.
Roblox space is (x, z, -y); see ``to_roblox``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

IDENT = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# ---------------------------------------------------------------------------
# 3x3 rotations (row-major tuples; columns are the local axes in world space)
# ---------------------------------------------------------------------------

def rot_z(a: float):
    c, s = math.cos(a), math.sin(a)
    return (c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0)


def rot_x(a: float):
    c, s = math.cos(a), math.sin(a)
    return (1.0, 0.0, 0.0, 0.0, c, -s, 0.0, s, c)


def rot_y(a: float):
    c, s = math.cos(a), math.sin(a)
    return (c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c)


def mat_mul(a, b):
    return (
        a[0] * b[0] + a[1] * b[3] + a[2] * b[6],
        a[0] * b[1] + a[1] * b[4] + a[2] * b[7],
        a[0] * b[2] + a[1] * b[5] + a[2] * b[8],
        a[3] * b[0] + a[4] * b[3] + a[5] * b[6],
        a[3] * b[1] + a[4] * b[4] + a[5] * b[7],
        a[3] * b[2] + a[4] * b[5] + a[5] * b[8],
        a[6] * b[0] + a[7] * b[3] + a[8] * b[6],
        a[6] * b[1] + a[7] * b[4] + a[8] * b[7],
        a[6] * b[2] + a[7] * b[5] + a[8] * b[8],
    )


def mat_vec(m, v):
    return (
        m[0] * v[0] + m[1] * v[1] + m[2] * v[2],
        m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
        m[6] * v[0] + m[7] * v[1] + m[8] * v[2],
    )


def yaw_of(m) -> float:
    return math.atan2(m[3], m[0])


# ---------------------------------------------------------------------------
# Primitive record
# ---------------------------------------------------------------------------

class Prim:
    """One solid. ``pos`` is the centre, ``size`` the full extents in local axes.

    kinds:
      box    - rectangular block
      wedge  - Roblox WedgePart convention: full height at local -Y, sloping
               down to zero height at local +Y (Roblox front face).
      cyl    - cylinder with its axis along local Z (``sides`` facets)
      ball   - sphere/ellipsoid fitted to size
      mesh   - free mesh in ``data=(verts, faces)`` (local coordinates)
    """

    __slots__ = ("kind", "mat", "pos", "size", "rot", "collide", "data")

    def __init__(self, kind, mat, pos, size, rot=IDENT, collide=True, data=None):
        self.kind = kind
        self.mat = mat
        self.pos = pos
        self.size = size
        self.rot = rot
        self.collide = collide
        self.data = data

    def transformed(self, xf: "Xform") -> "Prim":
        return Prim(self.kind, self.mat, xf.point(self.pos), self.size,
                    mat_mul(xf.rot, self.rot), self.collide, self.data)

    def __repr__(self):
        return f"Prim({self.kind},{self.mat},{self.pos},{self.size})"


class Xform:
    """Rigid transform: rotation about Z by ``yaw`` then translation."""

    __slots__ = ("x", "y", "z", "yaw", "rot", "_c", "_s")

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=0.0):
        self.x, self.y, self.z, self.yaw = x, y, z, yaw
        self._c, self._s = math.cos(yaw), math.sin(yaw)
        self.rot = rot_z(yaw)

    def point(self, p):
        c, s = self._c, self._s
        return (self.x + c * p[0] - s * p[1], self.y + s * p[0] + c * p[1], self.z + p[2])

    def vec(self, v):
        c, s = self._c, self._s
        return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])

    def then(self, inner: "Xform") -> "Xform":
        """Compose: apply ``inner`` first, then self."""
        p = self.point((inner.x, inner.y, inner.z))
        return Xform(p[0], p[1], p[2], self.yaw + inner.yaw)

    def inverse_point(self, p):
        dx, dy = p[0] - self.x, p[1] - self.y
        c, s = self._c, self._s
        return (c * dx + s * dy, -s * dx + c * dy, p[2] - self.z)


# ---------------------------------------------------------------------------
# Sink: convenient emitters used by kit props, buildings and the world
# ---------------------------------------------------------------------------

class Sink:
    """Collects primitives in a local frame."""

    def __init__(self):
        self.prims: list[Prim] = []

    # Axis-aligned box from min/max corners (local frame).
    def box(self, mat, x0, y0, z0, x1, y1, z1, collide=True):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        if sx < 1e-4 or sy < 1e-4 or sz < 1e-4:
            return None
        p = Prim("box", mat, ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5),
                 (sx, sy, sz), IDENT, collide)
        self.prims.append(p)
        return p

    # Centered, rotated box.
    def obox(self, mat, cx, cy, cz, sx, sy, sz, rot=IDENT, collide=True):
        if sx < 1e-4 or sy < 1e-4 or sz < 1e-4:
            return None
        p = Prim("box", mat, (cx, cy, cz), (sx, sy, sz), rot, collide)
        self.prims.append(p)
        return p

    def wedge(self, mat, cx, cy, cz, sx, sy, sz, yaw=0.0, collide=True, rot=None):
        p = Prim("wedge", mat, (cx, cy, cz), (sx, sy, sz),
                 rot if rot is not None else rot_z(yaw), collide)
        self.prims.append(p)
        return p

    def cyl(self, mat, cx, cy, z0, radius, height, sides=12, collide=True, rot=None,
            ry=None):
        """Vertical cylinder standing on z0 (or rotated with ``rot`` about its centre)."""
        r2 = ry if ry is not None else radius
        p = Prim("cyl", mat, (cx, cy, z0 + height * 0.5), (radius * 2, r2 * 2, height),
                 rot if rot is not None else IDENT, collide, sides)
        self.prims.append(p)
        return p

    def hcyl(self, mat, cx, cy, cz, radius, length, axis="x", sides=12, collide=True, yaw=0.0):
        """Horizontal cylinder centred at (cx,cy,cz) lying along local axis."""
        if axis == "x":
            rot = mat_mul(rot_z(yaw), rot_y(math.pi / 2))
        else:
            rot = mat_mul(rot_z(yaw), rot_x(math.pi / 2))
        p = Prim("cyl", mat, (cx, cy, cz), (radius * 2, radius * 2, length), rot, collide, sides)
        self.prims.append(p)
        return p

    def ball(self, mat, cx, cy, cz, rx, ry=None, rz=None, collide=False):
        ry = rx if ry is None else ry
        rz = rx if rz is None else rz
        p = Prim("ball", mat, (cx, cy, cz), (rx * 2, ry * 2, rz * 2), IDENT, collide)
        self.prims.append(p)
        return p

    def mesh(self, mat, verts, faces, pos=(0.0, 0.0, 0.0), collide=False):
        p = Prim("mesh", mat, pos, (1.0, 1.0, 1.0), IDENT, collide, (verts, faces))
        self.prims.append(p)
        return p

    def extend(self, prims):
        self.prims.extend(prims)

    def add_transformed(self, prims, xf: Xform, remap=None):
        for p in prims:
            q = p.transformed(xf)
            if remap and q.mat in remap:
                q.mat = remap[q.mat]
            self.prims.append(q)


# ---------------------------------------------------------------------------
# 2D rectangles (axis aligned) used for floor plans
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def w(self):
        return self.x1 - self.x0

    @property
    def d(self):
        return self.y1 - self.y0

    @property
    def area(self):
        return max(0.0, self.w) * max(0.0, self.d)

    @property
    def cx(self):
        return (self.x0 + self.x1) * 0.5

    @property
    def cy(self):
        return (self.y0 + self.y1) * 0.5

    def valid(self, eps=1e-3):
        return self.x1 - self.x0 > eps and self.y1 - self.y0 > eps

    def contains(self, x, y, eps=1e-6):
        return self.x0 - eps <= x <= self.x1 + eps and self.y0 - eps <= y <= self.y1 + eps

    def strictly_contains(self, x, y, eps=1e-6):
        return self.x0 + eps < x < self.x1 - eps and self.y0 + eps < y < self.y1 - eps

    def intersect(self, o: "Rect"):
        r = Rect(max(self.x0, o.x0), max(self.y0, o.y0), min(self.x1, o.x1), min(self.y1, o.y1))
        return r if r.valid() else None

    def overlaps(self, o: "Rect", eps=1e-6):
        return (self.x0 < o.x1 - eps and o.x0 < self.x1 - eps and
                self.y0 < o.y1 - eps and o.y0 < self.y1 - eps)

    def subtract(self, o: "Rect"):
        """Self minus o, as up to 4 rectangles."""
        i = self.intersect(o)
        if i is None:
            return [self]
        out = []
        if i.y0 > self.y0:
            out.append(Rect(self.x0, self.y0, self.x1, i.y0))
        if i.y1 < self.y1:
            out.append(Rect(self.x0, i.y1, self.x1, self.y1))
        if i.x0 > self.x0:
            out.append(Rect(self.x0, i.y0, i.x0, i.y1))
        if i.x1 < self.x1:
            out.append(Rect(i.x1, i.y0, self.x1, i.y1))
        return [r for r in out if r.valid()]

    def inset(self, l, b=None, r=None, t=None):
        b = l if b is None else b
        r = l if r is None else r
        t = b if t is None else t
        return Rect(self.x0 + l, self.y0 + b, self.x1 - r, self.y1 - t)

    def expand(self, m):
        return Rect(self.x0 - m, self.y0 - m, self.x1 + m, self.y1 + m)

    def mirror_x(self, w):
        return Rect(w - self.x1, self.y0, w - self.x0, self.y1)


def subtract_many(rects, holes):
    out = list(rects)
    for h in holes:
        nxt = []
        for r in out:
            nxt.extend(r.subtract(h))
        out = nxt
    return out


# ---------------------------------------------------------------------------
# 2D helpers for oriented rectangles (lots) and polylines (roads)
# ---------------------------------------------------------------------------

def obb_corners(cx, cy, hw, hd, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    pts = []
    for dx, dy in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)):
        pts.append((cx + c * dx - s * dy, cy + s * dx + c * dy))
    return pts


def polys_overlap(a, b):
    """Separating-axis test for two convex polygons (lists of (x,y))."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = y1 - y2, x2 - x1
            amin = amax = None
            for (px, py) in a:
                v = nx * px + ny * py
                amin = v if amin is None or v < amin else amin
                amax = v if amax is None or v > amax else amax
            bmin = bmax = None
            for (px, py) in b:
                v = nx * px + ny * py
                bmin = v if bmin is None or v < bmin else bmin
                bmax = v if bmax is None or v > bmax else bmax
            if amax <= bmin or bmax <= amin:
                return False
    return True


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def seg_point_dist(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy), t


def catmull_rom(points, spacing=4.0, closed=False):
    """Smooth a control polyline and resample it at roughly ``spacing``."""
    pts = list(points)
    if len(pts) < 2:
        return pts
    if closed:
        ext = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        ext = [pts[0]] + pts + [pts[-1]]
    out = []
    segs = len(ext) - 3
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        seglen = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        n = max(1, int(seglen / spacing))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            pt = []
            for d in range(len(p1)):
                pt.append(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t +
                                 (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 +
                                 (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3))
            out.append(tuple(pt))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def polyline_length(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1))


def to_roblox_pos(p):
    return (p[0], p[2], -p[1])


# Blender->Roblox basis change C (rows): rbx = C * bl
_C = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0)
_CT = (1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0)


def to_roblox_rot(rot):
    """Rotation matrix of a primitive in Roblox space.

    Roblox local axes: X = Blender local x, Y = Blender local z, Z = Blender local -y.
    """
    return mat_mul(mat_mul(_C, rot), _CT)


def to_roblox_size(size):
    return (size[0], size[2], size[1])
