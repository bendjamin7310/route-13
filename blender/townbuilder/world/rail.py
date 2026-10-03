"""The freight line: embankment, ballast, ties, rails, bridges over roads and the creek,
yard sidings with parked rolling stock."""

from __future__ import annotations

import math

from . import layout as Lay
from .roads import Sweep, _smooth, _seg_intersect, STEP
from ..geom import catmull_rom, Prim, rot_z
from ..records import PropPlace, Marker, LightRec
from .. import palette as pal

GAUGE = 4.6


class RailLine:
    def __init__(self, pts, terrain, net, main=True, name="Solace Freight Line"):
        self.name = name
        self.T = terrain
        self.net = net
        P = catmull_rom(pts, STEP)
        self.P = [(p[0], p[1]) for p in P]
        n = len(self.P)
        self.Tg = []
        for i in range(n):
            a = self.P[max(0, i - 1)]
            b = self.P[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dy) or 1.0
            self.Tg.append((dx / l, dy / l))
        self.S = [0.0]
        for i in range(1, n):
            self.S.append(self.S[-1] + math.hypot(self.P[i][0] - self.P[i - 1][0],
                                                  self.P[i][1] - self.P[i - 1][1]))
        self.bridge = [False] * n
        self.over_water = [False] * n
        self.crossings = []           # (index, road)
        z = _smooth([terrain.T(x, y) + 2.0 for (x, y) in self.P], 25)
        lift = [0.0] * n
        for i, (x, y) in enumerate(self.P):
            if terrain.is_water(x, y, margin=6.0):
                self.over_water[i] = True
                lift[i] = max(lift[i], terrain.water_level(x, y) + 11.0)
        # road crossings -> underpasses (the rail rises over the road)
        for i in range(n - 1):
            for (ri, j) in net.near_segments(self.P[i][0], self.P[i][1], 10.0):
                r = net.roads[ri]
                if _seg_intersect(self.P[i], self.P[i + 1], r.P[j], r.P[j + 1]):
                    self.crossings.append((i, r))
                    lift[i] = max(lift[i], r.Z[j] + 14.0)
        self.Z = list(z)
        for i in range(n):
            self.Z[i] = max(self.Z[i], lift[i])
        # 3% ramps either side of every raised point
        for _ in range(2):
            for i in range(1, n):
                self.Z[i] = max(self.Z[i], self.Z[i - 1] - 0.03 * STEP)
            for i in range(n - 2, -1, -1):
                self.Z[i] = max(self.Z[i], self.Z[i + 1] - 0.03 * STEP)
        self.Z = _smooth(self.Z, 3)
        for (i, r) in self.crossings:
            span = int((r.corridor + 10) / STEP) + 1
            for k in range(max(0, i - span), min(n, i + span + 1)):
                self.bridge[k] = True
        for i in range(n):
            if self.over_water[i]:
                for k in range(max(0, i - 4), min(n, i + 5)):
                    self.bridge[k] = True

    def samples(self, idxs, zoff=0.0):
        out = []
        for i in idxs:
            x, y = self.P[i]
            tx, ty = self.Tg[i]
            out.append((x, y, self.Z[i] + zoff, -ty, tx))
        return out

    def runs(self, pred, maxlen=50):
        out, cur = [], []
        for i in range(len(self.P)):
            if pred(i):
                cur.append(i)
                if len(cur) >= maxlen:
                    out.append(cur)
                    cur = [i]
            else:
                if len(cur) >= 2:
                    out.append(cur)
                cur = []
        if len(cur) >= 2:
            out.append(cur)
        return out

    def stamp(self):
        for i in range(len(self.P) - 1):
            if self.bridge[i] or self.bridge[i + 1]:
                continue
            (ax, ay), (bx, by) = self.P[i], self.P[i + 1]
            self.T.stamp_segment(ax, ay, self.Z[i] - 1.6, bx, by, self.Z[i + 1] - 1.6, 9.0,
                                 32.0, paint="gravel")

    def geometry(self, world):
        sw = world.sweeps
        # ballast everywhere off bridges, deck + girders on bridges
        for run in self.runs(lambda i: not self.bridge[i]):
            sw.append(Sweep("RAIL", "ballast", self.samples(run),
                            [(-8.0, -1.8), (-5.5, 0.0), (5.5, 0.0), (8.0, -1.8)][::-1],
                            name="ballast"))
        for run in self.runs(lambda i: self.bridge[i]):
            smp = self.samples(run)
            sw.append(Sweep("RAIL", "concrete", smp, [(-6.5, -3.0), (-6.5, 0.0), (6.5, 0.0),
                                                     (6.5, -3.0)][::-1], closed=True,
                            name="rail bridge deck"))
            for side in (-1, 1):
                c = side * 6.6
                sw.append(Sweep("RAIL", "metal_rust", smp, [(c - 0.3, -3.0), (c - 0.3, 4.0),
                                                           (c + 0.3, 4.0), (c + 0.3, -3.0)][::-1],
                                closed=True, name="rail bridge side"))
            water = any(self.over_water[i] for i in run)
            if water:
                self._truss(world, run)
            else:
                self._abutments(world, run)
        # rails + ties
        for run in self.runs(lambda i: True):
            smp = self.samples(run)
            for side in (-1, 1):
                c = side * GAUGE / 2
                sw.append(Sweep("RAIL", "rail_steel", smp, [(c - 0.2, 0.6), (c - 0.2, 1.3),
                                                           (c + 0.2, 1.3), (c + 0.2, 0.6)][::-1],
                                closed=True, name="rail", collide=False))
        s = 0.0
        while s < self.S[-1]:
            i = min(len(self.P) - 1, int(s / STEP))
            x, y = self.P[i]
            tx, ty = self.Tg[i]
            world.boxes.append(("RAIL", Prim("box", "rail_tie", (x, y, self.Z[i] + 0.3),
                                             (9.0, 1.1, 0.6),
                                             rot_z(math.atan2(ty, tx) - math.pi / 2), True)))
            s += 3.2

    def _abutments(self, world, run):
        """Concrete abutment walls either side of the road passing underneath."""
        for (i, r) in self.crossings:
            if i not in run:
                continue
            x, y = self.P[i]
            tx, ty = self.Tg[i]
            # road direction at the crossing
            d, s, j = r.nearest(x, y)
            rx, ry, rz, rtx, rty = r.at(s)
            nx, ny = -rty, rtx
            off = r.corridor + 2.0
            h = self.Z[i] - 3.0 - (rz - 1.0)
            if h < 3:
                continue
            yaw = math.atan2(rty, rtx)
            for side in (-1, 1):
                px, py = rx + nx * off * side, ry + ny * off * side
                world.boxes.append(("RAIL", Prim("box", "concrete", (px, py, rz - 1.0 + h / 2),
                                                 (26.0, 2.5, h), rot_z(yaw), True)))
            world.lights.append(LightRec(rx, ry, self.Z[i] - 3.5, (1.0, 0.85, 0.65), 26, 0.9,
                                         "point", "night"))
            world.markers.append(Marker("underpass", rx, ry, rz, yaw, f"{r.name} underpass"))

    def _truss(self, world, run):
        """Steel through-truss over Solace Creek (landmark)."""
        i0, i1 = run[0], run[-1]
        n = i1 - i0
        H = 14.0
        for side in (-1, 1):
            c = side * 6.6
            top = []
            for i in range(i0, i1 + 1):
                x, y = self.P[i]
                tx, ty = self.Tg[i]
                top.append((x, y, self.Z[i] + H, -ty, tx))
            world.sweeps.append(Sweep("LANDMARKS", "metal_rust", top,
                                      [(c - 0.6, -0.6), (c - 0.6, 0.6), (c + 0.6, 0.6),
                                       (c + 0.6, -0.6)][::-1], closed=True,
                                      name="rail truss chord"))
            for k in range(i0, i1 + 1, 3):
                x, y = self.P[k]
                tx, ty = self.Tg[k]
                px, py = x - ty * c, y + tx * c
                world.boxes.append(("LANDMARKS", Prim("box", "metal_rust",
                                                      (px, py, self.Z[k] + H / 2),
                                                      (0.6, 0.6, H), rot_z(0.0), False)))
            for k in range(i0, i1 - 2, 3):
                xa, ya = self.P[k]
                xb, yb = self.P[k + 3]
                tx, ty = self.Tg[k]
                pa = (xa - ty * c, ya + tx * c, self.Z[k])
                pb = (xb - ty * c, yb + tx * c, self.Z[k + 3] + H)
                if (k // 3) % 2:
                    pa = (pa[0], pa[1], self.Z[k] + H)
                    pb = (pb[0], pb[1], self.Z[k + 3])
                L = math.dist(pa, pb)
                from ..geom import mat_mul, rot_x
                yaw = math.atan2(pb[1] - pa[1], pb[0] - pa[0]) - math.pi / 2
                pitch = math.atan2(pb[2] - pa[2], math.hypot(pb[0] - pa[0], pb[1] - pa[1]))
                world.boxes.append(("LANDMARKS", Prim("box", "metal_rust",
                                                      ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2,
                                                       (pa[2] + pb[2]) / 2), (0.5, L, 0.5),
                                                      mat_mul(rot_z(yaw), rot_x(pitch)), False)))
        mid = run[len(run) // 2]
        x, y = self.P[mid]
        world.markers.append(Marker("landmark", x, y, self.Z[mid], 0.0, "Creek Rail Bridge"))
        # piers
        for k in range(i0 + 4, i1 - 3, 10):
            x, y = self.P[k]
            wl = self.T.water_level(x, y)
            h = self.Z[k] - 3.0 - (wl - 8.0)
            world.boxes.append(("RAIL", Prim("box", "concrete", (x, y, wl - 8.0 + h / 2),
                                             (14.0, 4.0, h),
                                             rot_z(math.atan2(self.Tg[k][1], self.Tg[k][0])),
                                             True)))

    def park_train(self, world, rng):
        """A short freight consist standing in the yard plus a few loose cars."""
        L = self.S[-1]
        s = L * 0.62
        cars = ["rail_locomotive", "rail_boxcar", "rail_flatcar", "rail_boxcar", "rail_flatcar",
                "rail_boxcar"]
        for k, name in enumerate(cars):
            i = min(len(self.P) - 1, int(s / STEP))
            x, y = self.P[i]
            tx, ty = self.Tg[i]
            yaw = math.atan2(-tx, ty)            # local -Y (front) along the track
            ch = {"$car": rng.choice(["car_rust", "car_maroon", "car_brown", "car_teal",
                                      "car_navy"]),
                  "$metal": rng.choice(["metal_blue", "metal_red", "metal_green", "metal_white",
                                        "metal_orange"])}
            if name == "rail_locomotive":
                ch["$car"] = "car_yellow"
            world.props.append((PropPlace(name, x, y, self.Z[i] + 1.0, yaw, channels=ch,
                                          interior=False), "VEHICLES"))
            s += 50.0 if name != "rail_locomotive" else 54.0
        world.markers.append(Marker("poi", self.P[int(L * 0.62 / STEP)][0],
                                    self.P[int(L * 0.62 / STEP)][1], 0.0, 0.0, "Rail Yard"))
