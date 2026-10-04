"""Terrain: macro elevation, water, flattening stamps and the final height/material grids.

The terrain is a 4-stud height grid over the whole 2560 x 2560 map.  ``macro(x, y)`` is a
smooth town-scale elevation used to lay roads, so any two roads agree where they meet.
Detail noise is added away from roads and lots; roads, building pads and the rail
embankment are then "stamped" in (nearest stamp wins).
"""

from __future__ import annotations

import math

import numpy as np

from . import layout as L
from ..geom import catmull_rom, point_in_poly

RES = 4.0
N = int(2 * L.HALF / RES) + 1        # vertices per side (641)

MAT_IDS = ["grass", "lawn", "grass_dry", "dirt", "sand", "sand_wet", "rock", "gravel", "mud",
           "grass_lush", "paving"]
MAT = {m: i for i, m in enumerate(MAT_IDS)}


def grid_xy():
    xs = -L.HALF + np.arange(N) * RES
    ys = -L.HALF + np.arange(N) * RES
    X, Y = np.meshgrid(xs, ys)
    return X, Y


def _poly_mask(X, Y, poly):
    """Vectorised even-odd point-in-polygon."""
    inside = np.zeros(X.shape, dtype=bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = (yi > Y) != (yj > Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi
        inside ^= cond & (X < xint)
        j = i
    return inside


def _dist_to_polyline(X, Y, pts, closed=False):
    d = np.full(X.shape, 1e9)
    t_best = np.zeros(X.shape)
    segs = list(zip(pts[:-1], pts[1:]))
    if closed:
        segs.append((pts[-1], pts[0]))
    acc = 0.0
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs)
    for (a, b) in segs:
        ax, ay = a[0], a[1]
        dx, dy = b[0] - ax, b[1] - ay
        l2 = dx * dx + dy * dy
        if l2 < 1e-9:
            continue
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
        qx, qy = ax + t * dx, ay + t * dy
        dd = np.hypot(X - qx, Y - qy)
        m = dd < d
        d = np.where(m, dd, d)
        seglen = math.sqrt(l2)
        t_best = np.where(m, (acc + t * seglen) / max(total, 1e-6), t_best)
        acc += seglen
    return d, t_best


class Terrain:
    def __init__(self, seed=7):
        self.seed = seed
        X, Y = grid_xy()
        self.X, self.Y = X, Y
        self.sea = _poly_mask(X, Y, L.SEA)
        # signed distance to the coastline (positive on land)
        dcoast, _ = _dist_to_polyline(X, Y, L.SEA, closed=True)
        self.coast_d = np.where(self.sea, -dcoast, dcoast)
        # creek: centreline, half widths and water level along it
        cpts = catmull_rom([(x, y, w) for (x, y, w) in L.CREEK], 6.0)
        self.creek_pts = [(p[0], p[1]) for p in cpts]
        self.creek_hw = [p[2] for p in cpts]
        dcreek, tcreek = _dist_to_polyline(X, Y, self.creek_pts)
        self.creek_d = dcreek
        self.creek_t = tcreek
        hw = np.interp(tcreek, np.linspace(0, 1, len(self.creek_hw)), self.creek_hw)
        self.creek_hw_grid = hw
        self.macro = self._macro()
        self.creek_level = self._creek_levels()
        self.H = None
        self.mat = None
        # stamps: nearest-wins target heights
        self.best_d = np.full(X.shape, 1e9)
        self.best_h = np.zeros(X.shape)
        self.best_blend = np.full(X.shape, 1.0)
        self.best_core = np.zeros(X.shape)
        self.paint = np.full(X.shape, -1, dtype=np.int16)

    # -- macro elevation ---------------------------------------------------------------
    def _macro(self):
        X, Y = self.X, self.Y
        T = 5.0 + 0.006 * (Y + 600).clip(0) - 0.003 * (X - 400).clip(0)
        T += 6.0 * np.clip((-X - 500) / 700.0, 0, 1)
        for (hx, hy, r, h) in L.HILLS:
            T += h * np.exp(-((X - hx) ** 2 + (Y - hy) ** 2) / (r * r))
        # coast: fall to a beach at the shoreline, sea floor offshore
        cd = self.coast_d
        land_f = np.clip(cd / 220.0, 0, 1)
        T = 1.6 + (T - 1.6) * (land_f * land_f * (3 - 2 * land_f))
        T = np.where(cd < 0, np.maximum(-40.0, 1.0 + cd * 0.12), T)
        # creek valley
        valley = np.clip((self.creek_d - self.creek_hw_grid) / 90.0, 0, 1)
        T = T * (0.55 + 0.45 * valley) + 0.0
        self._T_smooth = T
        return T

    def T(self, x, y):
        """Bilinear sample of the macro elevation."""
        fx = (x + L.HALF) / RES
        fy = (y + L.HALF) / RES
        i0 = int(min(max(math.floor(fy), 0), N - 2))
        j0 = int(min(max(math.floor(fx), 0), N - 2))
        ty = min(max(fy - i0, 0.0), 1.0)
        tx = min(max(fx - j0, 0.0), 1.0)
        M = self.macro
        return float((M[i0, j0] * (1 - tx) + M[i0, j0 + 1] * tx) * (1 - ty) +
                     (M[i0 + 1, j0] * (1 - tx) + M[i0 + 1, j0 + 1] * tx) * ty)

    def _creek_levels(self):
        """Water surface along the creek: follows the valley, monotonic toward the sea."""
        lv = []
        for (x, y) in self.creek_pts:
            lv.append(max(0.0, self.T(x, y) - 6.0))
        # monotonic non-decreasing upstream (index 0 = mouth)
        out = []
        cur = 0.0
        for v in lv:
            cur = max(cur, v) if out else 0.0
            out.append(cur)
        # gentle smoothing
        sm = []
        for i in range(len(out)):
            a = max(0, i - 6)
            b = min(len(out), i + 7)
            sm.append(sum(out[a:b]) / (b - a))
        sm[0] = 0.0
        return sm

    def creek_level_at(self, x, y):
        best, bi = 1e9, 0
        for i in range(0, len(self.creek_pts), 2):
            px, py = self.creek_pts[i]
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best:
                best, bi = d, i
        return self.creek_level[bi], math.sqrt(best), self.creek_hw[bi]

    def is_water(self, x, y, margin=0.0):
        if point_in_poly(x, y, L.SEA):
            return True
        lvl, d, hw = self.creek_level_at(x, y)
        return d < hw + margin

    def water_level(self, x, y):
        if point_in_poly(x, y, L.SEA):
            return 0.0
        lvl, d, hw = self.creek_level_at(x, y)
        return lvl

    # -- stamps ---------------------------------------------------------------------------
    def _region(self, x0, y0, x1, y1):
        j0 = max(0, int(math.floor((x0 + L.HALF) / RES)))
        j1 = min(N - 1, int(math.ceil((x1 + L.HALF) / RES)))
        i0 = max(0, int(math.floor((y0 + L.HALF) / RES)))
        i1 = min(N - 1, int(math.ceil((y1 + L.HALF) / RES)))
        return i0, i1 + 1, j0, j1 + 1

    def stamp_segment(self, ax, ay, az, bx, by, bz, core, blend, paint=None, bias=0.0):
        """Flatten along a segment: within ``core`` the target height, then blend out."""
        r = core + blend
        i0, i1, j0, j1 = self._region(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r,
                                      max(ay, by) + r)
        if i0 >= i1 or j0 >= j1:
            return
        X = self.X[i0:i1, j0:j1]
        Y = self.Y[i0:i1, j0:j1]
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        if l2 < 1e-9:
            t = np.zeros(X.shape)
        else:
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) + bias
        h = az + t * (bz - az)
        self._apply(i0, i1, j0, j1, d, h, core, blend, paint)

    def cap_segment(self, ax, ay, az, bx, by, bz, core, slope):
        """After finalize: lower the surface to at most the segment height within ``core``,
        rising ``slope`` per stud outside it (cuts banks under bridge decks)."""
        r = core + 60.0
        i0, i1, j0, j1 = self._region(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r,
                                      max(ay, by) + r)
        if i0 >= i1 or j0 >= j1:
            return
        X = self.X[i0:i1, j0:j1]
        Y = self.Y[i0:i1, j0:j1]
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        t = np.zeros(X.shape) if l2 < 1e-9 else \
            np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        cap = az + t * (bz - az) + np.maximum(d - core, 0.0) * slope
        self.H[i0:i1, j0:j1] = np.minimum(self.H[i0:i1, j0:j1], cap)

    def stamp_rect(self, corners, z, margin, blend, paint=None):
        """Flatten an oriented rectangle (lot pad) plus margin, blending outside."""
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        r = margin + blend
        i0, i1, j0, j1 = self._region(min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)
        if i0 >= i1 or j0 >= j1:
            return
        X = self.X[i0:i1, j0:j1]
        Y = self.Y[i0:i1, j0:j1]
        # distance to a convex polygon (0 inside)
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = corners
        ux, uy = x1 - x0, y1 - y0
        vx, vy = x3 - x0, y3 - y0
        lu = math.hypot(ux, uy)
        lv = math.hypot(vx, vy)
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        pu = (X - x0) * ux + (Y - y0) * uy
        pv = (X - x0) * vx + (Y - y0) * vy
        du = np.maximum(np.maximum(-pu, pu - lu), 0)
        dv = np.maximum(np.maximum(-pv, pv - lv), 0)
        d = np.hypot(du, dv)
        h = np.full(X.shape, z)
        self._apply(i0, i1, j0, j1, d, h, margin, blend, paint)

    def _apply(self, i0, i1, j0, j1, d, h, core, blend, paint):
        bd = self.best_d[i0:i1, j0:j1]
        m = (d - core) < (bd - self.best_core[i0:i1, j0:j1])
        m &= d < core + blend
        self.best_d[i0:i1, j0:j1] = np.where(m, d, bd)
        self.best_h[i0:i1, j0:j1] = np.where(m, h, self.best_h[i0:i1, j0:j1])
        self.best_core[i0:i1, j0:j1] = np.where(m, core, self.best_core[i0:i1, j0:j1])
        self.best_blend[i0:i1, j0:j1] = np.where(m, blend, self.best_blend[i0:i1, j0:j1])
        if paint is not None:
            pm = m & (d <= core + 0.5)
            self.paint[i0:i1, j0:j1] = np.where(pm, MAT[paint], self.paint[i0:i1, j0:j1])

    # -- final grids ----------------------------------------------------------------------
    def finalize(self, district_grid=None):
        X, Y = self.X, self.Y
        rng = np.random.default_rng(self.seed)
        # value noise (two octaves) for natural ground
        def vnoise(scale, amp):
            n = int(2 * L.HALF / scale) + 3
            g = rng.standard_normal((n, n))
            fx = (X + L.HALF) / scale
            fy = (Y + L.HALF) / scale
            i0 = np.floor(fy).astype(int)
            j0 = np.floor(fx).astype(int)
            tx = fx - j0
            ty = fy - i0
            tx = tx * tx * (3 - 2 * tx)
            ty = ty * ty * (3 - 2 * ty)
            a = g[i0, j0] * (1 - tx) + g[i0, j0 + 1] * tx
            b = g[i0 + 1, j0] * (1 - tx) + g[i0 + 1, j0 + 1] * tx
            return amp * (a * (1 - ty) + b * ty)
        noise = vnoise(160.0, 3.0) + vnoise(48.0, 1.0)
        urban = np.zeros(X.shape)
        if district_grid is not None:
            urban = district_grid
        detail_amp = np.where(urban > 0, 0.25, 1.0)
        H = self.macro + noise * detail_amp * (self.coast_d > 30)
        # creek channel
        lvl = np.interp(self.creek_t, np.linspace(0, 1, len(self.creek_level)), self.creek_level)
        hw = self.creek_hw_grid
        bank = np.clip((self.creek_d - hw) / 26.0, 0, 1)
        bed = lvl - 5.0 * (1 - np.clip(self.creek_d / np.maximum(hw, 1), 0, 1)) - 1.0
        in_creek = self.creek_d < hw + 26
        H = np.where(in_creek, np.minimum(H, bed * (1 - bank) + np.maximum(H, lvl + 1.2) * bank), H)
        self.creek_level_grid = lvl
        # shore: heights follow the continuous coast distance so the waterline runs smoothly
        # between grid vertices instead of stepping along the 4-stud sea mask
        shore = self.coast_d * 0.22 + 0.35
        H = np.where(self.coast_d < 10.0, np.minimum(H, shore), H)
        # stamps
        bd = self.best_d
        core = self.best_core
        blend = np.maximum(self.best_blend, 1e-3)
        w = np.clip(1.0 - (bd - core) / blend, 0, 1)
        w = w * w * (3 - 2 * w)
        H = H * (1 - w) + self.best_h * w
        # sea stays below the shore profile; the first few studs of land rise on a steep
        # ramp from the same edge height (stamps may have lifted them), so the waterline
        # stays continuous; dry land stays walkable above the water
        cd = self.coast_d
        H = np.where(cd < 0, np.minimum(H, shore),
                     np.where(cd < 8.0, np.minimum(H, 0.35 + cd * 1.0), H))
        H = np.where(cd >= 0, np.maximum(H, np.minimum(0.4, shore)), H)
        self.H = H
        # materials
        slope = np.hypot(*np.gradient(H, RES))
        mat = np.full(X.shape, MAT["grass"], dtype=np.int16)
        mat = np.where(noise > 1.8, MAT["grass_dry"], mat)
        mat = np.where(noise < -2.2, MAT["grass_lush"], mat)
        if district_grid is not None:
            mat = np.where(district_grid == 2, MAT["lawn"], mat)       # residential
            mat = np.where(district_grid == 3, MAT["dirt"], mat)       # industrial
            mat = np.where(district_grid == 4, MAT["grass_dry"], mat)  # outskirts dry fields
            mat = np.where(district_grid == 5, MAT["paving"], mat)     # downtown hardscape
        # beach: an irregular inland edge, wet sand only below the waterline (cell-sized
        # material steps are hidden under the water instead of drawn along the shore)
        mat = np.where((self.coast_d < 55 + noise * 5) & (self.coast_d > -20), MAT["sand"], mat)
        mat = np.where((self.coast_d < -2.5) & (self.coast_d > -40), MAT["sand_wet"], mat)
        mat = np.where(self.creek_d < hw + 8, MAT["mud"], mat)
        mat = np.where(slope > 0.65, MAT["rock"], mat)
        mat = np.where(self.paint >= 0, self.paint, mat)
        self.mat = mat
        return H

    def h(self, x, y):
        """Final terrain height (after finalize)."""
        fx = (x + L.HALF) / RES
        fy = (y + L.HALF) / RES
        i0 = int(min(max(math.floor(fy), 0), N - 2))
        j0 = int(min(max(math.floor(fx), 0), N - 2))
        ty = min(max(fy - i0, 0.0), 1.0)
        tx = min(max(fx - j0, 0.0), 1.0)
        M = self.H
        return float((M[i0, j0] * (1 - tx) + M[i0, j0 + 1] * tx) * (1 - ty) +
                     (M[i0 + 1, j0] * (1 - tx) + M[i0 + 1, j0 + 1] * tx) * ty)

    # -- mesh tiles -----------------------------------------------------------------------
    def tile_meshes(self, tile=256.0):
        """Yield (tx, ty, {material: (verts, faces)}) per tile."""
        cells = int(tile / RES)
        ntiles = int(2 * L.HALF / tile)
        H = self.H
        for ti in range(ntiles):
            for tj in range(ntiles):
                i0, j0 = ti * cells, tj * cells
                per = {}
                x_org = -L.HALF + tj * tile
                y_org = -L.HALF + ti * tile
                verts = []
                for i in range(cells + 1):
                    for j in range(cells + 1):
                        verts.append((x_org + j * RES, y_org + i * RES, float(H[i0 + i, j0 + j])))
                stride = cells + 1
                for i in range(cells):
                    for j in range(cells):
                        m = int(self.mat[i0 + i, j0 + j])
                        a = i * stride + j
                        per.setdefault(MAT_IDS[m], []).append((a, a + 1, a + stride + 1,
                                                               a + stride))
                yield ti, tj, (x_org, y_org), verts, per
