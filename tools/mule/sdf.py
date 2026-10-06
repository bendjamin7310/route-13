"""Signed distance field primitives and operators (numpy, float32).

Every function takes coordinate arrays (any shape, broadcast together) and
returns a distance array: negative inside, positive outside.

Coordinates used by the Mule build: metres, +X = right side of the truck,
+Y = forward, +Z = up, ground at Z = 0.
"""

import math

import numba
import numpy as np

F = np.float32


# ---------------------------------------------------------------- operators

def union(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.minimum(out, d)
    return out


def inter(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.maximum(out, d)
    return out


def sub(a, b):
    """a minus b."""
    return np.maximum(a, -b)


def union_round(a, b, r):
    """Union with a circular fillet of radius r in the concave corner."""
    r = F(r)
    ua = np.maximum(r - a, 0)
    ub = np.maximum(r - b, 0)
    return np.maximum(r, np.minimum(a, b)) - np.sqrt(ua * ua + ub * ub)


def inter_round(a, b, r):
    """Intersection with the convex edge rounded to radius r."""
    r = F(r)
    ua = np.maximum(r + a, 0)
    ub = np.maximum(r + b, 0)
    return np.minimum(-r, np.maximum(a, b)) + np.sqrt(ua * ua + ub * ub)


def sub_round(a, b, r):
    return inter_round(a, -b, r)


def smin(a, b, k):
    """Polynomial smooth minimum (soft blend of width k)."""
    k = F(k)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def shell(d, t):
    """Hollow shell of thickness t (centred on the surface)."""
    return np.abs(d) - F(t * 0.5)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# --------------------------------------------------------------- primitives

def plane(x, y, z, n, d):
    """Half-space n.p <= d (n is normalised here)."""
    n = np.asarray(n, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return F(n[0]) * x + F(n[1]) * y + F(n[2]) * z - F(d)


def box(x, y, z, c, half, r=0.0):
    """Axis aligned box centred at c with half extents `half`, edges rounded by r."""
    qx = np.abs(x - F(c[0])) - F(half[0] - r)
    qy = np.abs(y - F(c[1])) - F(half[1] - r)
    qz = np.abs(z - F(c[2])) - F(half[2] - r)
    ox = np.maximum(qx, 0)
    oy = np.maximum(qy, 0)
    oz = np.maximum(qz, 0)
    outside = np.sqrt(ox * ox + oy * oy + oz * oz)
    inside = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0)
    return outside + inside - F(r)


def box2(u, v, c, half, r=0.0):
    """2D rounded rectangle."""
    qx = np.abs(u - F(c[0])) - F(half[0] - r)
    qy = np.abs(v - F(c[1])) - F(half[1] - r)
    ox = np.maximum(qx, 0)
    oy = np.maximum(qy, 0)
    return np.sqrt(ox * ox + oy * oy) + np.minimum(np.maximum(qx, qy), 0) - F(r)


def circle2(u, v, c, r):
    return np.sqrt((u - F(c[0])) ** 2 + (v - F(c[1])) ** 2) - F(r)


def sphere(x, y, z, c, r):
    return np.sqrt((x - F(c[0])) ** 2 + (y - F(c[1])) ** 2 + (z - F(c[2])) ** 2) - F(r)


def ellipsoid(x, y, z, c, rad):
    """Approximate ellipsoid distance (IQ)."""
    px = (x - F(c[0])) / F(rad[0])
    py = (y - F(c[1])) / F(rad[1])
    pz = (z - F(c[2])) / F(rad[2])
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / F(rad[0])) ** 2 + (py / F(rad[1])) ** 2 + (pz / F(rad[2])) ** 2)
    return k0 * (k0 - 1) / np.maximum(k1, F(1e-6))


def capsule(x, y, z, a, b, r):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    ba = b - a
    bb = float(np.dot(ba, ba))
    px, py, pz = x - a[0], y - a[1], z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / F(bb), 0, 1)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz) - F(r)


def capsule_r(x, y, z, a, b, ra, rb):
    """Capsule whose radius blends from ra at a to rb at b (cheap, not exact)."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    ba = b - a
    bb = float(np.dot(ba, ba))
    px, py, pz = x - a[0], y - a[1], z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / F(bb), 0, 1)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (F(ra) + F(rb - ra) * h)


def cyl_axis(u, v, w, cu, cv, r, w0, w1, rr=0.0):
    """Capped cylinder whose axis runs along the w coordinate.

    (u, v) is the cross-section plane, centre (cu, cv), radius r, spanning
    w0..w1 with edge rounding rr.
    """
    d_rad = np.sqrt((u - F(cu)) ** 2 + (v - F(cv)) ** 2) - F(r - rr)
    wc = F((w0 + w1) * 0.5)
    d_ax = np.abs(w - wc) - F((w1 - w0) * 0.5 - rr)
    ox = np.maximum(d_rad, 0)
    oy = np.maximum(d_ax, 0)
    return np.sqrt(ox * ox + oy * oy) + np.minimum(np.maximum(d_rad, d_ax), 0) - F(rr)


def torus_axis(u, v, w, cu, cv, cw, R, r):
    """Torus around an axis parallel to w through (cu, cv, cw)."""
    q = np.sqrt((u - F(cu)) ** 2 + (v - F(cv)) ** 2) - F(R)
    return np.sqrt(q * q + (w - F(cw)) ** 2) - F(r)


def slab(w, w0, w1):
    return np.maximum(F(w0) - w, w - F(w1))


def extrude(d2, w, w0, w1, r=0.0):
    """Extrude a 2D distance along w between w0..w1 with rounded caps r."""
    if r <= 0:
        return np.maximum(d2, slab(w, w0, w1))
    return inter_round(d2, slab(w, w0, w1), r)


# ------------------------------------------------------------ 2D polygons

@numba.njit(parallel=True, fastmath=True, cache=True)
def _poly_sdf(u, v, px, py, out):
    n = px.shape[0]
    m = u.shape[0]
    for i in numba.prange(m):
        uu = u[i]
        vv = v[i]
        dx0 = uu - px[0]
        dy0 = vv - py[0]
        d = dx0 * dx0 + dy0 * dy0
        s = 1.0
        j = n - 1
        for k in range(n):
            ex = px[j] - px[k]
            ey = py[j] - py[k]
            wx = uu - px[k]
            wy = vv - py[k]
            ee = ex * ex + ey * ey
            t = 0.0
            if ee > 0:
                t = (wx * ex + wy * ey) / ee
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
            bx = wx - ex * t
            by = wy - ey * t
            dd = bx * bx + by * by
            if dd < d:
                d = dd
            c1 = vv >= py[k]
            c2 = vv < py[j]
            c3 = ex * wy > ey * wx
            if (c1 and c2 and c3) or ((not c1) and (not c2) and (not c3)):
                s = -s
            j = k
        out[i] = s * math.sqrt(d)


def poly2(u, v, pts):
    """Exact signed distance to a closed 2D polygon (list of (u, v))."""
    pts = np.asarray(pts, dtype=np.float64)
    shape = np.broadcast(u, v).shape
    uu = np.ascontiguousarray(np.broadcast_to(u, shape), dtype=np.float64).ravel()
    vv = np.ascontiguousarray(np.broadcast_to(v, shape), dtype=np.float64).ravel()
    out = np.empty(uu.shape[0], dtype=np.float64)
    _poly_sdf(uu, vv, pts[:, 0].copy(), pts[:, 1].copy(), out)
    return out.reshape(shape).astype(np.float32)


def fillet_polygon(pts, radii, seg=10):
    """Replace each polygon corner with a circular arc.

    radii: one radius per vertex (0 = keep sharp). Works for convex and
    concave corners.
    """
    pts = np.asarray(pts, dtype=np.float64)
    n = len(pts)
    if np.isscalar(radii):
        radii = [radii] * n
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        r = radii[i]
        if r <= 0:
            out.append(p1)
            continue
        a = p0 - p1
        b = p2 - p1
        la, lb = np.linalg.norm(a), np.linalg.norm(b)
        a /= la
        b /= lb
        cosang = np.clip(np.dot(a, b), -1, 1)
        ang = math.acos(cosang)
        if ang < 1e-3 or abs(ang - math.pi) < 1e-3:
            out.append(p1)
            continue
        t = r / math.tan(ang / 2)
        t = min(t, la * 0.49, lb * 0.49)
        r_eff = t * math.tan(ang / 2)
        s0 = p1 + a * t
        s1 = p1 + b * t
        bis = a + b
        bis /= np.linalg.norm(bis)
        c = p1 + bis * (r_eff / math.sin(ang / 2))
        a0 = math.atan2(s0[1] - c[1], s0[0] - c[0])
        a1 = math.atan2(s1[1] - c[1], s1[0] - c[0])
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(seg + 1):
            aa = a0 + da * k / seg
            out.append(c + r_eff * np.array([math.cos(aa), math.sin(aa)]))
    return np.array(out)


def spline_pts(ctrl, n=64):
    """Catmull-Rom through control points (open curve)."""
    ctrl = np.asarray(ctrl, dtype=np.float64)
    pts = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    pts = np.array(pts)
    out = []
    segs = len(ctrl) - 1
    per = max(2, n // segs)
    for i in range(segs):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(ctrl[-1])
    return np.array(out)


def interp(x, xs, ys):
    """Piecewise linear lookup that keeps float32."""
    return np.interp(x, xs, ys).astype(np.float32)


_LUTS = {}


def smooth_interp(x, xs, ys):
    """Smooth monotone cubic (PCHIP) interpolation through key values.

    Evaluated through a dense lookup table so it stays cheap on big grids.
    Outside the key range the end values are held.
    """
    key = (tuple(xs), tuple(ys))
    lut = _LUTS.get(key)
    if lut is None:
        from scipy.interpolate import PchipInterpolator
        xs_ = np.asarray(xs, dtype=np.float64)
        dense = np.linspace(xs_[0], xs_[-1], 4096)
        lut = (dense, PchipInterpolator(xs_, np.asarray(ys, dtype=np.float64))(dense))
        _LUTS[key] = lut
    return np.interp(x, lut[0], lut[1]).astype(np.float32)
