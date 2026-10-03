"""Lot placement: landmark sites first, then buildings along every road frontage."""

from __future__ import annotations

import math
import random

from . import layout as Lay
from ..geom import Xform, obb_corners, polys_overlap, point_in_poly, seg_point_dist, catmull_rom
from ..archetypes import ARCH

# district -> [(archetype, weight)]
MIX = {
    "DOWNTOWN": [("mixed_use", 5.0), ("bar", 1.6), ("pawn_shop", 1.0), ("restaurant", 1.4),
                 ("laundromat", 0.8), ("shop", 1.2), ("office_small", 1.0),
                 ("convenience_store", 0.6), ("diner", 0.5)],
    "MIXED_USE": [("mixed_use", 3.0), ("apartment_lowrise", 1.6), ("laundromat", 1.0),
                  ("pawn_shop", 0.6), ("bar", 0.8), ("shop", 0.8), ("convenience_store", 0.7),
                  ("restaurant", 0.7), ("house_old", 0.8)],
    "LOW_INCOME": [("house_old", 6.0), ("apartment_lowrise", 1.0), ("trailer", 0.4),
                   ("convenience_store", 0.4), ("laundromat", 0.3), ("auto_shop", 0.5),
                   ("bar", 0.3), ("house_small", 1.0)],
    "RESIDENTIAL": [("house_small", 4.0), ("house_medium", 4.0), ("house_nice", 1.0),
                    ("apartment_lowrise", 0.4)],
    "RESIDENTIAL_N": [("house_medium", 4.0), ("house_nice", 2.0), ("house_small", 2.0)],
    "COMMERCIAL": [("shop", 3.0), ("restaurant", 1.4), ("diner", 0.6), ("gas_station", 0.8),
                   ("convenience_store", 1.0), ("office_small", 1.0), ("auto_shop", 0.8),
                   ("laundromat", 0.4)],
    "MOTEL": [("diner", 0.8), ("gas_station", 0.6), ("auto_shop", 1.0),
              ("convenience_store", 0.6), ("bar", 0.5), ("trailer", 0.8),
              ("warehouse_small", 0.5)],
    "INDUSTRIAL": [("warehouse", 2.5), ("warehouse_small", 3.0), ("auto_shop", 0.8),
                   ("storage_facility", 0.3)],
    "WATERFRONT": [("harbor_shed", 1.5), ("boat_storage", 0.8), ("waterfront_restaurant", 0.8),
                   ("bar", 0.5), ("fish_warehouse", 0.5), ("shop", 0.4)],
    "CIVIC": [("office_small", 2.0), ("restaurant", 0.5), ("shop", 0.5)],
    "OUTSKIRTS": [("trailer", 2.0), ("house_small", 1.5), ("house_old", 1.5),
                  ("warehouse_small", 0.4), ("auto_shop", 0.3)],
}

FILL = {"DOWNTOWN": 1.0, "MIXED_USE": 0.95, "LOW_INCOME": 0.85, "RESIDENTIAL": 0.85,
        "RESIDENTIAL_N": 0.8, "COMMERCIAL": 0.85, "MOTEL": 0.7, "INDUSTRIAL": 0.85,
        "WATERFRONT": 0.8, "CIVIC": 0.7, "OUTSKIRTS": 0.18}

GAP = {"DOWNTOWN": (0.0, 0.0), "MIXED_USE": (0.0, 6.0), "LOW_INCOME": (6.0, 12.0),
       "RESIDENTIAL": (10.0, 18.0), "RESIDENTIAL_N": (12.0, 22.0), "COMMERCIAL": (10.0, 24.0),
       "MOTEL": (14.0, 30.0), "INDUSTRIAL": (14.0, 30.0), "WATERFRONT": (10.0, 20.0),
       "CIVIC": (12.0, 24.0), "OUTSKIRTS": (40.0, 120.0)}

QUALITY = {"DOWNTOWN": ("normal", "normal", "cheap", "nice"),
           "MIXED_USE": ("normal", "cheap", "cheap"),
           "LOW_INCOME": ("cheap", "cheap", "cheap", "normal", "abandoned"),
           "RESIDENTIAL": ("normal", "normal", "nice"),
           "RESIDENTIAL_N": ("normal", "nice"),
           "COMMERCIAL": ("normal",), "MOTEL": ("cheap", "normal"),
           "INDUSTRIAL": ("normal", "cheap"), "WATERFRONT": ("normal",),
           "CIVIC": ("normal", "nice"), "OUTSKIRTS": ("cheap", "normal", "abandoned")}


def district_at(x, y):
    for name, poly in Lay.DISTRICTS.items():
        if point_in_poly(x, y, poly):
            return name
    return "OUTSKIRTS"


class Lot:
    def __init__(self, arch, x, y, yaw, w, d, district, road=None, s=0.0, side=0,
                 setback=0.0):
        self.arch = arch
        self.fx, self.fy = x, y            # front-centre of the facade
        self.yaw = yaw
        self.w, self.d = w, d
        self.district = district
        self.road = road
        self.s = s
        self.side = side
        self.setback = setback
        a = ARCH[arch]
        self.rear = a.rear_clear
        self.side_gap = a.side_gap
        c, sn = math.cos(yaw), math.sin(yaw)
        self.xdir = (c, sn)
        self.ydir = (-sn, c)               # local +Y: from the facade into the lot
        self.ox = x - c * w / 2
        self.oy = y - sn * w / 2
        self.z = 0.0
        self.name = ""
        self.opts = {}
        self.quality = "normal"
        self.blind = set()
        self.id = ""

    def local_to_world(self, lx, ly):
        return (self.ox + self.xdir[0] * lx + self.ydir[0] * ly,
                self.oy + self.xdir[1] * lx + self.ydir[1] * ly)

    def rect(self, x0, y0, x1, y1):
        return [self.local_to_world(x0, y0), self.local_to_world(x1, y0),
                self.local_to_world(x1, y1), self.local_to_world(x0, y1)]

    @property
    def footprint(self):
        return self.rect(0, 0, self.w, self.d)

    @property
    def claim(self):
        """Area this lot reserves against other lots (half the gaps on each side)."""
        g = self.side_gap / 2
        return self.rect(-g, -self.setback + 1.0, self.w + g, self.d + self.rear / 2)

    @property
    def yard_rect(self):
        return self.rect(-self.side_gap / 2, -self.setback, self.w + self.side_gap / 2,
                         self.d + self.rear / 2)

    @property
    def center(self):
        return self.local_to_world(self.w / 2, self.d / 2)

    def xform(self):
        return Xform(self.ox, self.oy, self.z, self.yaw)


class Placer:
    def __init__(self, net, terrain, seed=13, density=1.0):
        self.net = net
        self.T = terrain
        self.rng = random.Random(seed)
        self.lots: list[Lot] = []
        self.density = density
        self.rail = catmull_rom(Lay.RAIL, 8.0)
        self.park_polys = list(Lay.PARKS.values())
        self.reject = {}

    # -- checks ----------------------------------------------------------------------------
    def ok(self, lot: Lot, frontage_road=None, check_lots=True):
        fp = lot.footprint
        for (x, y) in fp:
            if abs(x) > Lay.HALF - 30 or abs(y) > Lay.HALF - 30:
                return self._no("bounds")
        # sample the footprint + setback strip
        pts = []
        nx = max(2, int(lot.w / 8) + 1)
        ny = max(2, int(lot.d / 8) + 1)
        for i in range(nx):
            for j in range(ny):
                pts.append(lot.local_to_world(lot.w * i / (nx - 1), lot.d * j / (ny - 1)))
        back = [lot.local_to_world(lot.w * i / (nx - 1), lot.d + lot.rear * 0.5)
                for i in range(nx)]
        for (x, y) in pts:
            if self.T.is_water(x, y, margin=8.0):
                return self._no("water")
        excl = {lot.road.idx} if lot.road is not None else None
        for (x, y) in pts + back:
            cl, road, d = self.net.dist_to_road(x, y, 90.0, exclude=excl)
            if cl < 2.0:
                self.last_road = road.name if road else None
                return self._no("road")
        if lot.road is not None:
            for (x, y) in pts:
                d, _, _ = lot.road.nearest(x, y)
                if d - lot.road.corridor < -0.2:
                    self.last_road = lot.road.name
                    return self._no("road")
        for (x, y) in pts:
            for i in range(0, len(self.rail) - 1):
                (ax, ay), (bx, by) = self.rail[i][:2], self.rail[i + 1][:2]
                if abs(ax - x) > 80 and abs(bx - x) > 80:
                    continue
                dd, _ = seg_point_dist(ax, ay, bx, by, x, y)
                if dd < 30.0:
                    return self._no("rail")
            for poly in self.park_polys:
                if point_in_poly(x, y, poly):
                    return self._no("park")
        if check_lots:
            claim = lot.claim
            cx, cy = lot.center
            r0 = math.hypot(lot.w, lot.d) + lot.setback + lot.rear
            for o in self.lots:
                ox, oy = o.center
                if math.hypot(ox - cx, oy - cy) > r0 + math.hypot(o.w, o.d) + o.setback + o.rear:
                    continue
                if polys_overlap(claim, o.claim):
                    return self._no("lot")
        # slope across the footprint (macro elevation)
        hs = [self.T.T(x, y) for (x, y) in fp]
        if max(hs) - min(hs) > 9.0:
            return self._no("slope")
        return True

    def _no(self, why):
        self.reject[why] = self.reject.get(why, 0) + 1
        return False

    # -- construction ------------------------------------------------------------------------
    def lot_on_road(self, arch, road, s, side, w, d, district, setback=None):
        a = ARCH[arch]
        sb = a.front_setback if setback is None else setback
        x, y, z, tx, ty = road.at(s + w / 2)
        nx, ny = -ty, tx
        off = road.corridor + sb + 0.1
        fx, fy = x + nx * off * side, y + ny * off * side
        yaw = math.atan2(-nx * side, ny * side)
        lot = Lot(arch, fx, fy, yaw, w, d, district, road, s, side, sb)
        lot.road_z = z
        return lot

    def place_sites(self):
        for site in Lay.SITES:
            arch = site["arch"]
            a = ARCH[arch]
            w = site.get("w") or (a.w[0] + a.w[1]) / 2
            d = site.get("d") or (a.d[0] + a.d[1]) / 2
            if "road" in site:
                road = self.net.by_name[site["road"]]
                side = 1 if site["side"] == "left" else -1
                placed = None
                if "near" in site:
                    s_mid = road.nearest(*site["near"])[1]
                else:
                    s_mid = site["t"] * road.length
                for ds in (0, 6, -6, 12, -12, 20, -20, 30, -30, 45, -45, 60, -60, 80, -80):
                    s = s_mid + ds - w / 2
                    if s < 0 or s + w > road.length:
                        continue
                    lot = self.lot_on_road(arch, road, s, side, w, d, site.get("district"),
                                           setback=site.get("setback"))
                    if self.ok(lot):
                        placed = lot
                        break
                if not placed:
                    print(f"[placement] site {arch} on {site['road']} did not fit "
                          f"({self.reject})")
                    continue
                lot = placed
            else:
                yaw = site["yaw"]
                c, sn = math.cos(yaw), math.sin(yaw)
                lot = Lot(arch, site["x"], site["y"], yaw, w, d, site.get("district"))
                lot.road_z = None
            lot.name = site.get("name", "")
            lot.opts = site.get("opts", {})
            lot.district = site.get("district") or district_at(*lot.center)
            lot.quality = "normal"
            lot.site = True
            self.lots.append(lot)

    def fill(self):
        roads = sorted(self.net.roads, key=lambda r: -r.prio)
        for road in roads:
            if road.d.frontage == "none" or road.kind in ("alley", "dirt"):
                continue
            sides = {"both": (1, -1), "left": (1,), "right": (-1,)}[road.d.frontage]
            for side in sides:
                self._fill_side(road, side)

    def _fill_side(self, road, side):
        rng = self.rng
        s = rng.uniform(6.0, 20.0)
        while s < road.length - 20:
            x, y, z, tx, ty = road.at(s)
            nx, ny = -ty, tx
            probe = (x + nx * side * (road.corridor + 30), y + ny * side * (road.corridor + 30))
            dist = district_at(*probe)
            if "avenue" in road.d.tags and dist in ("DOWNTOWN", "MIXED_USE"):
                # downtown avenues: corner buildings belong to the cross streets
                s += 12.0
                continue
            if rng.random() > FILL.get(dist, 0.5) * self.density:
                s += rng.uniform(20.0, 60.0)
                continue
            placed = False
            for attempt in range(4):
                arch = self._pick(dist, road)
                if arch is None:
                    break
                a = ARCH[arch]
                if attempt < 2:
                    w = round(rng.uniform(*a.w) * 2) / 2
                    d = round(rng.uniform(*a.d) * 2) / 2
                else:  # squeeze into the remaining frontage with the smallest variant
                    w, d = a.w[0], a.d[0]
                if dist == "DOWNTOWN":
                    d = min(d, 48.0) if arch not in ("office_tower",) else d
                if a.d[0] > d:
                    d = a.d[0]
                lot = self.lot_on_road(arch, road, s, side, w, d, dist)
                if self.ok(lot):
                    lot.quality = rng.choice(QUALITY.get(dist, ("normal",)))
                    if arch in ("supermarket", "office_tower", "police_station", "town_hall"):
                        lot.quality = "normal"
                    lot.site = False
                    self.lots.append(lot)
                    g0, g1 = GAP.get(dist, (8.0, 16.0))
                    s += w + max(a.side_gap if dist not in ("DOWNTOWN", "MIXED_USE") else 0.0,
                                 rng.uniform(g0, g1))
                    placed = True
                    break
            if not placed:
                s += 8.0

    def _pick(self, dist, road):
        mix = MIX.get(dist)
        if not mix:
            return None
        cands = []
        for (arch, wgt) in mix:
            a = ARCH.get(arch)
            if a is None:
                continue
            # big footprints only on bigger roads
            if a.w[0] > 90 and road.prio < 3:
                continue
            if arch in ("house_small", "house_medium", "house_nice", "house_old", "trailer") \
                    and road.kind == "major":
                continue
            cands.append((arch, wgt))
        if not cands:
            return None
        tot = sum(wt for _, wt in cands)
        r = self.rng.uniform(0, tot)
        for arch, wt in cands:
            r -= wt
            if r <= 0:
                return arch
        return cands[-1][0]

    # -- after placement ------------------------------------------------------------------
    def finish(self):
        """Ids, pad heights and party walls (blind sides)."""
        counters = {}
        for i, lot in enumerate(self.lots):
            lot.id = f"B{i:03d}"
            cx, cy = lot.center
            tc = self.T.T(cx, cy)
            if getattr(lot, "road_z", None) is not None:
                rz = lot.road_z + 0.6
                lot.z = rz + max(-2.0, min(4.0, tc - rz)) * 0.5
            else:
                lot.z = tc + 0.6
        for lot in self.lots:
            for side, (a, b) in (("left", ((0, 0), (0, lot.d))),
                                 ("right", ((lot.w, 0), (lot.w, lot.d))),
                                 ("back", ((0, lot.d), (lot.w, lot.d)))):
                probe = []
                for t in (0.25, 0.5, 0.75):
                    lx = a[0] + (b[0] - a[0]) * t
                    ly = a[1] + (b[1] - a[1]) * t
                    dx = -2.5 if side == "left" else 2.5 if side == "right" else 0
                    dy = 2.5 if side == "back" else 0
                    probe.append(lot.local_to_world(lx + dx, ly + dy))
                for o in self.lots:
                    if o is lot:
                        continue
                    fp = o.footprint
                    if sum(1 for p in probe if point_in_poly(p[0], p[1], fp)) >= 2:
                        lot.blind.add(side)
                        break
