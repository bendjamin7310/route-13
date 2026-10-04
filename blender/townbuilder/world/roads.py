"""Road network: centrelines, height profiles, junctions, bridges and swept geometry.

Geometry is described as *sweeps* (a cross-section profile dragged along a run of
centreline samples) and *patches* (junction polygons).  The Blender realiser turns these
into meshes; the Roblox exporter can also turn every sweep segment into a Part.
"""

from __future__ import annotations

import math
from collections import defaultdict

from . import layout as Lay
from ..geom import catmull_rom, seg_point_dist, point_in_poly
from ..records import PropPlace, LightRec, Marker
from .. import palette as paints

STEP = 4.0
PRIORITY = {"major": 6, "arterial": 5, "street": 4, "service": 3, "residential": 2,
            "rural": 2, "lot": 1, "alley": 1, "dirt": 1}
CURB = 0.5          # sidewalk height above the road


class Road:
    def __init__(self, rd: Lay.RoadDef, idx: int):
        self.d = rd
        self.idx = idx
        self.name = rd.name
        self.kind = rd.kind
        self.w, self.sw, self.surface, self.marking = Lay.ROAD_SPECS[rd.kind]
        self.prio = PRIORITY[rd.kind]
        pts = catmull_rom(rd.pts, STEP) if rd.smooth else _resample(rd.pts, STEP)
        pts = _dedupe(pts)
        self.P = [(p[0], p[1]) for p in pts]
        n = len(self.P)
        self.S = [0.0]
        for i in range(1, n):
            self.S.append(self.S[-1] + math.hypot(self.P[i][0] - self.P[i - 1][0],
                                                  self.P[i][1] - self.P[i - 1][1]))
        self.length = self.S[-1]
        self.Tg = []
        for i in range(n):
            a = self.P[max(0, i - 1)]
            b = self.P[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dy) or 1.0
            self.Tg.append((dx / l, dy / l))
        self.Z = [0.0] * n
        self.bridge = [False] * n
        self.zone = [False] * n
        self.water = [None] * n      # water level under bridge samples

    @property
    def half(self):
        return self.w / 2

    @property
    def corridor(self):
        """Half width of road + sidewalks (lots must stay outside)."""
        return self.w / 2 + self.sw

    def normal(self, i):
        tx, ty = self.Tg[i]
        return (-ty, tx)

    def index_at(self, s):
        lo, hi = 0, len(self.S) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.S[mid] < s:
                lo = mid + 1
            else:
                hi = mid
        return max(0, min(len(self.S) - 1, lo))

    def at(self, s):
        s = min(max(s, 0.0), self.length)
        i = max(1, self.index_at(s))
        s0, s1 = self.S[i - 1], self.S[i]
        t = 0.0 if s1 - s0 < 1e-9 else (s - s0) / (s1 - s0)
        x = self.P[i - 1][0] + (self.P[i][0] - self.P[i - 1][0]) * t
        y = self.P[i - 1][1] + (self.P[i][1] - self.P[i - 1][1]) * t
        z = self.Z[i - 1] + (self.Z[i] - self.Z[i - 1]) * t
        tx, ty = self.Tg[i]
        return x, y, z, tx, ty

    def nearest(self, x, y, i_hint=None, span=None):
        best = (1e18, 0.0, 0)
        rng = range(len(self.P) - 1)
        if i_hint is not None and span:
            rng = range(max(0, i_hint - span), min(len(self.P) - 1, i_hint + span))
        for i in rng:
            (ax, ay), (bx, by) = self.P[i], self.P[i + 1]
            d, t = seg_point_dist(ax, ay, bx, by, x, y)
            if d < best[0]:
                best = (d, self.S[i] + t * (self.S[i + 1] - self.S[i]), i)
        return best


def _dedupe(pts, eps=0.5):
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    return out


def _resample(pts, step):
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for k in range(1, n + 1):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _seg_intersect(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-9:
        return None
    ua = ((p4[0] - p3[0]) * (p1[1] - p3[1]) - (p4[1] - p3[1]) * (p1[0] - p3[0])) / d
    ub = ((p2[0] - p1[0]) * (p1[1] - p3[1]) - (p2[1] - p1[1]) * (p1[0] - p3[0])) / d
    if 0 <= ua <= 1 and 0 <= ub <= 1:
        return ua, ub
    return None


class Junction:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.z = 0.0
        self.members = {}      # road idx -> station s
        self.arms = []
        self.signal = False
        self.corner_pts = []

    @property
    def key_road(self):
        return None


class Arm:
    __slots__ = ("road", "end", "dirn", "theta", "lc", "rc", "lo", "ro", "z")


# =============================================================================

class RoadNetwork:
    def __init__(self, terrain):
        self.T = terrain
        self.roads = [Road(rd, i) for i, rd in enumerate(Lay.ROADS)]
        self.by_name = {r.name: r for r in self.roads}
        self._build_hash()
        self.junctions: list[Junction] = []
        self.issues = []
        self.find_junctions()
        self.profiles()
        self.mark_zones()
        self.build_arms()

    # -- spatial hash of segments ------------------------------------------------------
    def _build_hash(self, cell=48.0):
        self.cell = cell
        self.hash = defaultdict(list)
        for r in self.roads:
            for i in range(len(r.P) - 1):
                (ax, ay), (bx, by) = r.P[i], r.P[i + 1]
                for cx in range(int(math.floor(min(ax, bx) / cell)),
                                int(math.floor(max(ax, bx) / cell)) + 1):
                    for cy in range(int(math.floor(min(ay, by) / cell)),
                                    int(math.floor(max(ay, by) / cell)) + 1):
                        self.hash[(cx, cy)].append((r.idx, i))

    def near_segments(self, x, y, radius):
        c = self.cell
        out = set()
        for cx in range(int(math.floor((x - radius) / c)), int(math.floor((x + radius) / c)) + 1):
            for cy in range(int(math.floor((y - radius) / c)),
                            int(math.floor((y + radius) / c)) + 1):
                out.update(self.hash.get((cx, cy), ()))
        return out

    def dist_to_road(self, x, y, radius=80.0, exclude=None):
        """Nearest road (by corridor clearance) -> (clearance, road, dist)."""
        best = (1e9, None, 1e9)
        for (ri, i) in self.near_segments(x, y, radius):
            if exclude is not None and ri in exclude:
                continue
            r = self.roads[ri]
            (ax, ay), (bx, by) = r.P[i], r.P[i + 1]
            d, _ = seg_point_dist(ax, ay, bx, by, x, y)
            cl = d - r.corridor
            if cl < best[0]:
                best = (cl, r, d)
        return best

    # -- junctions -------------------------------------------------------------------
    def find_junctions(self):
        pts = []
        # crossings
        for r in self.roads:
            for i in range(len(r.P) - 1):
                cands = self.near_segments(r.P[i][0], r.P[i][1], 12.0)
                for (rj, j) in cands:
                    if rj <= r.idx:
                        continue
                    o = self.roads[rj]
                    hit = _seg_intersect(r.P[i], r.P[i + 1], o.P[j], o.P[j + 1])
                    if hit:
                        ua, ub = hit
                        x = r.P[i][0] + ua * (r.P[i + 1][0] - r.P[i][0])
                        y = r.P[i][1] + ua * (r.P[i + 1][1] - r.P[i][1])
                        pts.append((x, y, {r.idx: r.S[i] + ua * (r.S[i + 1] - r.S[i]),
                                           o.idx: o.S[j] + ub * (o.S[j + 1] - o.S[j])}))
        # T-junctions: road ends near another road
        for r in self.roads:
            for end in (0, len(r.P) - 1):
                x, y = r.P[end]
                best = None
                for o in self.roads:
                    if o is r:
                        continue
                    d, s, _ = o.nearest(x, y)
                    if d < o.half + 10 and (best is None or d < best[0]):
                        best = (d, o, s)
                if best:
                    d, o, s = best
                    jx, jy, _, _, _ = o.at(s)
                    pts.append((jx, jy, {r.idx: r.S[end], o.idx: s}))
        # cluster
        for (x, y, mem) in pts:
            for j in self.junctions:
                if math.hypot(j.x - x, j.y - y) < 16.0:
                    for k, v in mem.items():
                        j.members.setdefault(k, v)
                    break
            else:
                j = Junction(x, y)
                j.members.update(mem)
                self.junctions.append(j)
        for j in self.junctions:
            kinds = sorted((self.roads[k].prio for k in j.members), reverse=True)
            j.signal = len(kinds) >= 2 and kinds[1] >= 4 and len(j.members) >= 2

    # -- profiles -------------------------------------------------------------------
    def profiles(self):
        T = self.T
        for r in self.roads:
            z = [T.T(x, y) for (x, y) in r.P]
            for _ in range(3):
                z = _smooth(z, 10)
            r.Z = z
        # bridges over water
        for r in self.roads:
            for i, (x, y) in enumerate(r.P):
                if T.is_water(x, y, margin=r.half * 0.4 + 3.0):
                    r.bridge[i] = True
                    r.water[i] = T.water_level(x, y)
            # bridge decks: clear the water, ramps either side
            if any(r.bridge):
                deck = list(r.Z)
                for i in range(len(deck)):
                    if r.bridge[i]:
                        clear = 9.0 if r.water[i] > 0.5 else 11.0
                        deck[i] = max(deck[i], r.water[i] + clear)
                # flatten deck spans and ramp the approaches at <= 6%
                for _ in range(2):
                    for i in range(1, len(deck)):
                        deck[i] = max(deck[i], deck[i - 1] - 0.06 * STEP) if not r.bridge[i] \
                            else deck[i]
                    for i in range(len(deck) - 2, -1, -1):
                        deck[i] = max(deck[i], deck[i + 1] - 0.06 * STEP) if not r.bridge[i] \
                            else deck[i]
                r.Z = _smooth(deck, 3)
                # extend bridge flags over the banks so the deck has abutments
                flags = list(r.bridge)
                for i in range(len(flags)):
                    if r.bridge[i]:
                        for k in range(max(0, i - 3), min(len(flags), i + 4)):
                            flags[k] = True
                r.bridge = flags
        # junction height agreement: the most important road sets the height
        for it in range(4):
            corrections = defaultdict(list)
            for j in self.junctions:
                mem = [(self.roads[k], s) for k, s in j.members.items()]
                top = max(m[0].prio for m in mem)
                zs = [m[0].at(m[1])[2] for m in mem if m[0].prio == top]
                zt = sum(zs) / len(zs)
                j.z = zt
                for (road, s) in mem:
                    dz = zt - road.at(s)[2]
                    if abs(dz) > 0.02:
                        corrections[road.idx].append((s, dz))
            if not corrections:
                break
            for ri, lst in corrections.items():
                r = self.roads[ri]
                z = list(r.Z)
                for i, si in enumerate(r.S):
                    acc = 0.0
                    for (s, dz) in lst:
                        dd = abs(si - s)
                        if dd < 140.0:
                            acc += dz * (1 - dd / 140.0)
                    z[i] += acc
                r.Z = z
        # bridge decks run straight between fixed anchors (the banks and any junction on the
        # span): a junction tent on one approach could otherwise drop the deck steeply through
        # the bank.  A bank much higher than the far anchor is cut down along the approach at
        # <= 12% so the deck stays drivable.  Never below the water clearance.
        MAX_DECK, MAX_APPROACH = 0.15, 0.12
        for r in self.roads:
            n = len(r.Z)
            fixed = [self._near_junction(r, k) for k in range(n)]
            i = 0
            while i < n:
                if not r.bridge[i]:
                    i += 1
                    continue
                a = i
                while i < n and r.bridge[i]:
                    i += 1
                b = i - 1
                lo, hi = max(0, a - 1), min(n - 1, b + 1)
                anchors = [lo] + [k for k in range(a, b + 1) if fixed[k]] + [hi]
                for _ in range(3):
                    # cut a bank that is too high for the next anchor
                    for u, v in zip(anchors, anchors[1:]):
                        if v == u:
                            continue
                        limit = MAX_DECK * STEP * (v - u)
                        if r.Z[u] - r.Z[v] > limit and u == lo:
                            r.Z[u] = r.Z[v] + limit
                            self._cut_approach(r, fixed, u, -1, MAX_APPROACH)
                        if r.Z[v] - r.Z[u] > limit and v == hi:
                            r.Z[v] = r.Z[u] + limit
                            self._cut_approach(r, fixed, v, 1, MAX_APPROACH)
                # water clearance as a floor, spread into ramps so sea/creek clearances
                # meet smoothly, then the straight deck line lifted onto that floor
                g = MAX_APPROACH * STEP
                floor = [-1e9] * n
                for k in range(a, b + 1):
                    if r.water[k] is not None:
                        floor[k] = r.water[k] + (9.0 if r.water[k] > 0.5 else 11.0)
                for k in range(a + 1, b + 1):
                    floor[k] = max(floor[k], floor[k - 1] - g)
                for k in range(b - 1, a - 1, -1):
                    floor[k] = max(floor[k], floor[k + 1] - g)
                z0 = list(r.Z)
                for u, v in zip(anchors, anchors[1:]):
                    for k in range(u + 1, v):
                        lin = z0[u] + (z0[v] - z0[u]) * (k - u) / (v - u)
                        r.Z[k] = max(lin, floor[k])

    def _cut_approach(self, r, fixed, start, step, grade):
        """Lower the approach outward from a bank at ``grade`` until it meets the profile;
        if a junction is reached first, blend linearly from the junction to the bank."""
        n = len(r.Z)
        g = grade * STEP
        k = start + step
        while 0 <= k < n:
            if fixed[k]:
                lo, hi = (k, start) if step < 0 else (start, k)
                for m in range(lo + 1, hi):
                    r.Z[m] = r.Z[lo] + (r.Z[hi] - r.Z[lo]) * (m - lo) / (hi - lo)
                return
            if r.Z[k] <= r.Z[k - step] + g:
                return
            r.Z[k] = r.Z[k - step] + g
            k += step

    def _near_junction(self, r, k, pad=2.0):
        x, y = r.P[k]
        for j in self.junctions:
            if r.idx in j.members and math.hypot(x - j.x, y - j.y) < r.half + pad:
                return True
        return False

    def clear_under_bridges(self, T, clearance=4.0):
        """Cut terrain (after stamping) so nothing rises above or close under a bridge deck."""
        for r in self.roads:
            for i in range(len(r.P) - 1):
                if not (r.bridge[i] and r.bridge[i + 1]):
                    continue
                (ax, ay), (bx, by) = r.P[i], r.P[i + 1]
                T.cap_segment(ax, ay, r.Z[i] - clearance, bx, by, r.Z[i + 1] - clearance,
                              r.half + 3.0, 1.0)

    # -- zones & arms ------------------------------------------------------------------
    def mark_zones(self):
        for j in self.junctions:
            mem = list(j.members.items())
            j.zone_ranges = {}
            for (ri, s) in mem:
                r = self.roads[ri]
                others = [self.roads[k] for k, _ in mem if k != ri]
                i0 = r.index_at(s)
                lo = hi = i0

                def inside(i):
                    x, y = r.P[i]
                    for o in others:
                        d, _, _ = o.nearest(x, y, o.index_at(j.members[o.idx]), 40)
                        if d < o.half + o.sw + 1.5 + 0.5 * r.half * 0:
                            return True
                    return math.hypot(x - j.x, y - j.y) < 4.0
                while lo > 0 and inside(lo - 1):
                    lo -= 1
                while hi < len(r.P) - 1 and inside(hi + 1):
                    hi += 1
                # widen slightly so the side curbs clear the crossing road's sidewalk
                lo = max(0, lo - 1)
                hi = min(len(r.P) - 1, hi + 1)
                for i in range(lo, hi + 1):
                    r.zone[i] = True
                j.zone_ranges[ri] = (lo, hi)

    def build_arms(self):
        for j in self.junctions:
            arms = []
            for ri, (lo, hi) in j.zone_ranges.items():
                r = self.roads[ri]
                for dirn, end in ((-1, lo), (1, hi)):
                    # arm must continue at least 3 samples beyond the zone
                    if dirn < 0 and end < 3:
                        continue
                    if dirn > 0 and end > len(r.P) - 4:
                        continue
                    a = Arm()
                    a.road = r
                    a.end = end
                    a.dirn = dirn
                    tx, ty = r.Tg[end]
                    tx, ty = tx * dirn, ty * dirn       # pointing away from the junction
                    a.theta = math.atan2(ty, tx)
                    x, y = r.P[end]
                    nlx, nly = -ty, tx                    # left of the outward direction
                    a.z = r.Z[end]
                    a.lc = (x + nlx * r.half, y + nly * r.half)
                    a.rc = (x - nlx * r.half, y - nly * r.half)
                    a.lo = (x + nlx * (r.half + r.sw), y + nly * (r.half + r.sw))
                    a.ro = (x - nlx * (r.half + r.sw), y - nly * (r.half + r.sw))
                    arms.append(a)
            arms.sort(key=lambda a: a.theta)
            j.arms = arms


def _smooth(v, k):
    n = len(v)
    if n < 3:
        return list(v)
    out = []
    pre = [0.0]
    for x in v:
        pre.append(pre[-1] + x)
    for i in range(n):
        a = max(0, i - k)
        b = min(n, i + k + 1)
        out.append((pre[b] - pre[a]) / (b - a))
    return out


# =============================================================================
# Geometry

class Sweep:
    """A cross-section dragged along a run of samples [(x, y, z, nx, ny), ...]."""

    __slots__ = ("cat", "mat", "samples", "profile", "closed", "name", "collide")

    def __init__(self, cat, mat, samples, profile, closed=False, name="", collide=True):
        self.cat, self.mat, self.samples = cat, mat, samples
        self.profile, self.closed, self.name, self.collide = profile, closed, name, collide

    def mesh(self):
        prof = self.profile
        m = len(prof)
        verts, faces = [], []
        for (x, y, z, nx, ny) in self.samples:
            for (lat, dz) in prof:
                verts.append((x + nx * lat, y + ny * lat, z + dz))
        nseg = m if self.closed else m - 1
        for i in range(len(self.samples) - 1):
            a = i * m
            b = (i + 1) * m
            for k in range(nseg):
                k1 = (k + 1) % m
                faces.append((a + k, b + k, b + k1, a + k1))
        if self.closed and len(self.samples) >= 2:
            faces.append(tuple(range(m - 1, -1, -1)))
            last = (len(self.samples) - 1) * m
            faces.append(tuple(last + k for k in range(m)))
        return verts, faces

    def center(self):
        s = self.samples[len(self.samples) // 2]
        return (s[0], s[1])


class RoadGeometry:
    """Everything the road network contributes to the world."""

    def __init__(self, net: RoadNetwork, district_at, rng):
        self.net = net
        self.district_at = district_at
        self.rng = rng
        self.sweeps: list[Sweep] = []
        self.patches = []     # (cat, mat, verts, faces, center)
        self.boxes = []       # (cat, Prim) piers, abutments, girders etc.
        self.props: list[PropPlace] = []
        self.lights: list[LightRec] = []
        self.markers: list[Marker] = []
        self.signs = []

    # -- helpers ------------------------------------------------------------------------
    def runs(self, r: Road, pred, maxlen=60):
        """Contiguous sample index runs where pred(i) holds, split every ``maxlen``."""
        out = []
        cur = []
        for i in range(len(r.P)):
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

    def samples(self, r: Road, idxs, zoff=0.0):
        out = []
        for i in idxs:
            x, y = r.P[i]
            nx, ny = r.normal(i)
            out.append((x, y, r.Z[i] + zoff, nx, ny))
        return out

    # -- build ------------------------------------------------------------------------------
    def build(self):
        for r in self.net.roads:
            self._road(r)
        for j in self.net.junctions:
            self._junction(j)
        self._furniture()

    def _road(self, r: Road):
        hw, sw = r.half, r.sw
        surf = r.surface
        # carriageway outside junction zones (junction patches fill the zones)
        for run in self.runs(r, lambda i: not r.zone[i]):
            self.sweeps.append(Sweep("ROADS", surf, self.samples(r, run),
                                     [(-hw, 0.0), (hw, 0.0)], name=r.name))
            # road shoulders down to the terrain where there is no sidewalk
            if sw == 0:
                for side in (-1, 1):
                    prof = [(side * hw, 0.0), (side * (hw + 2.0), -1.6)] if side > 0 else \
                        [(side * (hw + 2.0), -1.6), (side * hw, 0.0)]
                    self.sweeps.append(Sweep("ROADS", "gravel" if r.kind in ("rural", "dirt")
                                             else surf, self.samples(r, run), prof,
                                             name=r.name + " shoulder", collide=False))
        # sidewalks + curbs (not on bridges: bridges get a walkway and parapet)
        if sw > 0:
            for run in self.runs(r, lambda i: not r.zone[i] and not r.bridge[i]):
                smp = self.samples(r, run)
                mat = "sidewalk" if self.district_at(*r.P[run[0]]) not in ("LOW_INCOME",
                                                                          "OUTSKIRTS") \
                    else "sidewalk_old"
                self.sweeps.append(Sweep("SIDEWALKS", mat, smp,
                                         [(hw, 0.0), (hw, CURB), (hw + sw, CURB),
                                          (hw + sw, -1.6)], name=r.name + " sidewalk L"))
                self.sweeps.append(Sweep("SIDEWALKS", mat, smp,
                                         [(-hw - sw, -1.6), (-hw - sw, CURB), (-hw, CURB),
                                          (-hw, 0.0)], name=r.name + " sidewalk R"))
        # bridges
        for run in self.runs(r, lambda i: r.bridge[i]):
            self._bridge(r, run)
        # markings
        if r.d.markings and r.marking != "none":
            self._markings(r)

    def _markings(self, r: Road):
        hw = r.half
        z = 0.04
        ok = lambda i: not r.zone[i]
        dashed = lambda i: ok(i) and (r.S[i] % 16.0) < 8.0

        def stripe(pred, c, width, mat):
            for run in self.runs(r, pred):
                self.sweeps.append(Sweep("ROADS", mat, self.samples(r, run, z),
                                         [(c - width / 2, 0.0), (c + width / 2, 0.0)],
                                         name=r.name + " marking", collide=False))
        if r.marking in ("double_yellow", "double_yellow_4lane"):
            stripe(ok, -0.45, 0.35, "paint_line_yellow")
            stripe(ok, 0.45, 0.35, "paint_line_yellow")
        elif r.marking == "dashed_yellow":
            stripe(dashed, 0.0, 0.35, "paint_line_yellow")
        if r.marking == "double_yellow_4lane":
            stripe(dashed, hw / 2, 0.35, "paint_line_white")
            stripe(dashed, -hw / 2, 0.35, "paint_line_white")
        if r.kind in ("major", "arterial", "service", "rural"):
            stripe(ok, hw - 1.2, 0.35, "paint_line_white")
            stripe(ok, -hw + 1.2, 0.35, "paint_line_white")

    def _bridge(self, r: Road, run):
        hw, sw = r.half, max(r.sw, 4.0)
        smp = self.samples(r, run)
        harbor = "coastal" in r.d.tags
        # walkway + parapets + deck slab
        self.sweeps.append(Sweep("BRIDGES", "concrete_light", smp,
                                 [(hw, 0.0), (hw, CURB), (hw + sw, CURB), (hw + sw, 0.0)],
                                 name=r.name + " bridge walk L"))
        self.sweeps.append(Sweep("BRIDGES", "concrete_light", smp,
                                 [(-hw - sw, 0.0), (-hw - sw, CURB), (-hw, CURB), (-hw, 0.0)],
                                 name=r.name + " bridge walk R"))
        for side in (-1, 1):
            a = side * (hw + sw)
            b = side * (hw + sw + 1.0)
            lo, hi = min(a, b), max(a, b)
            self.sweeps.append(Sweep("BRIDGES", "concrete", smp,
                                     [(lo, -0.2), (lo, 3.6), (hi, 3.6), (hi, -0.2)], closed=True,
                                     name=r.name + " parapet"))
            if harbor:
                self.sweeps.append(Sweep("BRIDGES", "metal_white", smp,
                                         [(lo, 3.6), (lo, 4.0), (hi, 4.0), (hi, 3.6)],
                                         closed=True, name=r.name + " rail", collide=False))
        self.sweeps.append(Sweep("BRIDGES", "concrete", smp,
                                 [(-hw - sw - 1.0, -2.6), (-hw - sw - 1.0, -0.02),
                                  (hw + sw + 1.0, -0.02), (hw + sw + 1.0, -2.6)][::-1],
                                 closed=True, name=r.name + " deck"))
        for side in (-1, 1):
            c = side * (hw * 0.55)
            self.sweeps.append(Sweep("BRIDGES", "metal_gray" if harbor else "concrete_dark", smp,
                                     [(c - 1.0, -5.0), (c - 1.0, -2.6), (c + 1.0, -2.6),
                                      (c + 1.0, -5.0)][::-1], closed=True,
                                     name=r.name + " girder"))
        # piers
        from ..geom import Prim, rot_z
        span = 44.0 if not harbor else 60.0
        s0, s1 = r.S[run[0]], r.S[run[-1]]
        L = s1 - s0
        n = max(1, int(L / span))
        for k in range(1, n + 1 if L > span else 1):
            s = s0 + k * L / (n + 1)
            x, y, z, tx, ty = r.at(s)
            wl = self.net.T.water_level(x, y)
            zb = wl - 8.0
            h = (z - 5.0) - zb
            if h < 2:
                continue
            yaw = math.atan2(ty, tx)
            self.boxes.append(("BRIDGES", Prim("box", "concrete", (x, y, zb + h / 2),
                                               (4.0, r.w + 2 * sw, h), rot_z(yaw), True)))
        if harbor:
            self._arches(r, run)
        mx, my = r.P[run[len(run) // 2]]
        self.markers.append(Marker("bridge", mx, my, r.Z[run[len(run) // 2]], 0.0,
                                   r.name + " Bridge"))

    def _arches(self, r: Road, run):
        """Harbor Bridge: two painted steel arches with hangers (landmark)."""
        hw, sw = r.half, max(r.sw, 4.0)
        s0, s1 = r.S[run[0]] + 8.0, r.S[run[-1]] - 8.0
        L = s1 - s0
        H = 34.0
        from ..geom import Prim, rot_z, mat_mul, rot_y
        for side in (-1, 1):
            off = side * (hw + sw + 2.2)
            smp = []
            n = 40
            for k in range(n + 1):
                s = s0 + L * k / n
                x, y, z, tx, ty = r.at(s)
                nx, ny = -ty, tx
                zz = z + 2.0 + H * math.sin(math.pi * k / n)
                smp.append((x + nx * off, y + ny * off, zz, nx, ny))
            self.sweeps.append(Sweep("LANDMARKS", "metal_white", smp,
                                     [(-1.0, -1.2), (-1.0, 1.2), (1.0, 1.2), (1.0, -1.2)][::-1],
                                     closed=True, name="Harbor Bridge arch"))
            for k in range(2, n - 1, 2):
                s = s0 + L * k / n
                x, y, z, tx, ty = r.at(s)
                nx, ny = -ty, tx
                top = z + 2.0 + H * math.sin(math.pi * k / n)
                hx, hy = x + nx * off, y + ny * off
                self.boxes.append(("LANDMARKS", Prim("box", "metal_white",
                                                     (hx, hy, (z + top) / 2), (0.3, 0.3, top - z),
                                                     rot_z(math.atan2(ty, tx)), False)))
                if k % 8 == 4:
                    self.lights.append(LightRec(hx, hy, top + 1.5, (1.0, 0.85, 0.6), 30, 1.0,
                                                "point", "night"))
        x, y, z, _, _ = r.at((s0 + s1) / 2)
        self.markers.append(Marker("landmark", x, y, z, 0.0, "Harbor Bridge"))

    def _junction(self, j: Junction):
        arms = j.arms
        if len(arms) < 2:
            return
        # asphalt patch: arm end curb points + rounded corners
        poly = []
        sidewalk_corners = []
        n = len(arms)
        for k in range(n):
            a = arms[k]
            b = arms[(k + 1) % n]
            poly.append((a.rc[0], a.rc[1], a.z))
            poly.append((a.lc[0], a.lc[1], a.z))
            dth = (b.theta - a.theta) % (2 * math.pi)
            if dth < 1e-3:
                continue
            curve = _corner_curve(a.lc, a.theta + math.pi / 2, b.rc, b.theta - math.pi / 2,
                                  dth, (j.x, j.y))
            for (x, y) in curve[1:-1]:
                poly.append((x, y, (a.z + b.z) / 2))
            sw = min(a.road.sw, b.road.sw)
            if sw > 0 and dth < math.pi * 0.97:
                outer = _corner_curve(a.lo, a.theta + math.pi / 2, b.ro, b.theta - math.pi / 2,
                                      dth, (j.x, j.y))
                if len(outer) == len(curve):
                    sidewalk_corners.append((curve, outer, (a.z + b.z) / 2, a, b))
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        verts = [(cx, cy, j.z)] + poly
        faces = [(0, i + 1, (i + 1) % len(poly) + 1) for i in range(len(poly))]
        # winding: make the patch face up
        if _signed_area([(p[0], p[1]) for p in poly]) < 0:
            faces = [(f[0], f[2], f[1]) for f in faces]
        mat = max((a.road for a in arms), key=lambda r: r.prio).surface
        self.patches.append(("ROADS", mat, verts, faces, (cx, cy),
                             {"kind": "fan", "z": j.z, "poly": [(p[0], p[1]) for p in poly]}))
        for (inner, outer, z, a, b) in sidewalk_corners:
            self._corner_sidewalk(inner, outer, z, a, b)
        j.corner_pts = [((c[0][len(c[0]) // 2]), c[2]) for c in sidewalk_corners]

    def _corner_sidewalk(self, inner, outer, z, a, b):
        """Rounded sidewalk corner with a curb face."""
        mat = "sidewalk"
        verts = []
        faces = []
        m = len(inner)
        for (x, y) in inner:
            verts.append((x, y, z + CURB))
        for (x, y) in outer:
            verts.append((x, y, z + CURB))
        for (x, y) in inner:
            verts.append((x, y, z))
        for (x, y) in outer:
            verts.append((x, y, z - 1.6))
        for i in range(m - 1):
            faces.append((i, i + 1, m + i + 1, m + i))              # top
            faces.append((2 * m + i, 2 * m + i + 1, i + 1, i))      # curb face
            faces.append((m + i, m + i + 1, 3 * m + i + 1, 3 * m + i))  # outer skirt
        if _signed_area(list(inner) + list(reversed(outer))) > 0:
            faces = [tuple(reversed(f)) for f in faces]
        cx, cy = inner[m // 2]
        self.patches.append(("SIDEWALKS", mat, verts, faces, (cx, cy),
                             {"kind": "corner", "z": z, "inner": list(inner),
                              "outer": list(outer)}))

    # -- street furniture -------------------------------------------------------------------
    def _furniture(self):
        rng = self.rng
        net = self.net
        for r in net.roads:
            dist = self.district_at(*r.P[len(r.P) // 2])
            town = dist not in ("OUTSKIRTS",)
            if not r.d.lights:
                continue
            spacing = {"major": 64.0, "arterial": 70.0, "street": 56.0, "residential": 90.0,
                       "service": 90.0, "rural": 0.0, "dirt": 0.0}.get(r.kind, 0.0)
            if not town and r.kind in ("residential",):
                spacing = 0.0
            if spacing:
                s = spacing * 0.5
                side = 1
                while s < r.length - 8:
                    i = r.index_at(s)
                    if not r.zone[i] and not r.bridge[i]:
                        self._side_prop(r, s, side, "streetlight" if dist not in ("DOWNTOWN",
                                                                                 "CIVIC")
                                        else "lamppost_classic", inset=0.8)
                    if r.kind in ("major", "arterial") or dist in ("DOWNTOWN", "MIXED_USE"):
                        side = -side
                    s += spacing
            # utility poles + wires on the opposite side for residential/industrial/rural
            if r.kind in ("residential", "service", "rural", "arterial") and \
                    dist not in ("DOWNTOWN", "CIVIC"):
                self._poles(r)
            # hydrants
            if town and r.kind not in ("alley", "dirt", "rural"):
                s = 40.0
                while s < r.length - 10:
                    i = r.index_at(s)
                    if not r.zone[i] and not r.bridge[i]:
                        self._side_prop(r, s, -1 if int(s / 160) % 2 else 1, "fire_hydrant",
                                        inset=1.6)
                    s += 160.0
            # downtown sidewalk life
            if dist in ("DOWNTOWN", "MIXED_USE", "CIVIC") and r.kind == "street":
                s = 20.0
                k = 0
                while s < r.length - 10:
                    i = r.index_at(s)
                    if not r.zone[i] and not r.bridge[i]:
                        side = 1 if k % 2 == 0 else -1
                        choice = ["tree_street", "bench_park", "trash_bin_street", "tree_street",
                                  "parking_meter", "newspaper_box", "tree_street", "bike_rack",
                                  "planter_box"][k % 9]
                        self._side_prop(r, s, side, choice, inset=2.6,
                                        ch={"$leaf": rng.choice(["leaf", "leaf_light",
                                                                  "leaf_dark"]),
                                            "$plastic": rng.choice(["plastic_red",
                                                                    "plastic_blue",
                                                                    "plastic_yellow"])})
                    s += 15.0
                    k += 1
            # parked cars along town streets
            if r.kind in ("street", "residential") and town and dist not in ("CIVIC",):
                self._parked_cars(r, dist)
            # bus stops on arterials / Route 13
            if r.kind in ("major", "arterial") and town:
                s = 120.0
                while s < r.length - 60:
                    i = r.index_at(s)
                    if not r.zone[i] and not r.bridge[i] and r.sw >= 6:
                        p = self._side_prop(r, s, 1, "bus_shelter", inset=r.sw * 0.5 + 1.2)
                        if p:
                            x, y, z, tx, ty = r.at(s)
                            self.markers.append(Marker("bus_stop", p.x, p.y, p.z, p.yaw,
                                                       f"{r.name} stop"))
                    s += 420.0
        # junction furniture: signals / stop signs / street name signs
        for j in net.junctions:
            self._junction_furniture(j)
        # billboards
        for (x, y, yaw) in Lay.BILLBOARDS:
            self.props.append(PropPlace("billboard", x, y, self.net.T.h(x, y) - 0.6, yaw,
                                        channels={"$sign": rng.choice(["sign_blue", "sign_red",
                                                                       "sign_teal",
                                                                       "sign_yellow"])},
                                        interior=False))

    def _side_prop(self, r: Road, s, side, name, inset=1.0, ch=None, back=False):
        """Place a prop on the sidewalk (side=+1 left, -1 right) facing the road."""
        x, y, z, tx, ty = r.at(s)
        nx, ny = -ty, tx
        off = r.half + (r.sw - inset if r.sw > 0 else 2.5 + inset)
        if r.sw == 0:
            off = r.half + 3.0
        px, py = x + nx * off * side, y + ny * off * side
        zz = z + (CURB if r.sw > 0 else self.net.T.h(px, py) - z - 0.4)
        # yaw so that the prop's front (local -Y) points toward the road centre
        fx, fy = -nx * side, -ny * side
        yaw = math.atan2(fx, -fy)
        if back:
            yaw += math.pi
        p = PropPlace(name, px, py, zz, yaw, channels=ch or {}, interior=False)
        self.props.append(p)
        from ..kit import KIT
        d = KIT.get(name)
        if d and d.light:
            lt = d.light
            c, sn = math.cos(yaw), math.sin(yaw)
            ax, ay, az = lt["at"]
            self.lights.append(LightRec(px + c * ax - sn * ay, py + sn * ax + c * ay, zz + az,
                                        lt["color"], lt["range"], lt["brightness"],
                                        lt.get("kind", "point"), lt.get("schedule", "night")))
        return p

    def _poles(self, r: Road):
        s = 30.0
        poles = []
        while s < r.length - 10:
            i = r.index_at(s)
            if not r.zone[i] and not r.bridge[i]:
                side = -1
                x, y, z, tx, ty = r.at(s)
                nx, ny = -ty, tx
                off = r.half + r.sw + 3.0
                px, py = x - nx * off, y - ny * off
                pz = self.net.T.h(px, py) - 0.6
                yaw = math.atan2(ty, tx) + math.pi / 2
                name = "utility_pole_transformer" if len(poles) % 5 == 2 else "utility_pole"
                self.props.append(PropPlace(name, px, py, pz, yaw, interior=False))
                poles.append((px, py, pz, yaw))
            else:
                if poles:
                    poles.append(None)
            s += 80.0
        # wires between consecutive poles (thin sweeps)
        prev = None
        for p in poles:
            if p is None:
                prev = None
                continue
            if prev is not None:
                for k, off in enumerate((-3.4, -1.2, 1.2, 3.4)):
                    c, sn = math.cos(p[3]), math.sin(p[3])
                    ax, ay = prev[0] + c * off, prev[1] + sn * off
                    bx, by = p[0] + c * off, p[1] + sn * off
                    za, zb = prev[2] + 28.1, p[2] + 28.1
                    self._wire(ax, ay, za, bx, by, zb)
            prev = p

    def _wire(self, ax, ay, az, bx, by, bz, sag=1.6):
        smp = []
        n = 6
        L = math.hypot(bx - ax, by - ay) or 1.0
        tx, ty = (bx - ax) / L, (by - ay) / L
        for k in range(n + 1):
            t = k / n
            z = az + (bz - az) * t - sag * 4 * t * (1 - t)
            smp.append((ax + (bx - ax) * t, ay + (by - ay) * t, z, -ty, tx))
        self.sweeps.append(Sweep("PROPS", "rubber", smp, [(-0.06, -0.06), (-0.06, 0.06),
                                                         (0.06, 0.06), (0.06, -0.06)][::-1],
                                 closed=True, name="power line", collide=False))

    def _parked_cars(self, r: Road, dist):
        rng = self.rng
        cars = ["car_sedan", "car_compact", "car_suv", "car_pickup", "car_wagon", "car_van",
                "car_coupe"]
        if dist in ("LOW_INCOME",):
            cars = ["car_sedan", "car_pickup_old", "car_compact", "car_wagon", "car_van",
                    "car_wreck"]
            pl = paints.CAR_PAINTS_OLD + paints.CAR_PAINTS[:5]
        else:
            pl = paints.CAR_PAINTS
        prob = 0.22 if r.kind == "street" else 0.12
        s = 30.0
        while s < r.length - 30:
            i = r.index_at(s)
            ok = not r.zone[i] and not r.bridge[i]
            for k in (-12, 12):
                j = r.index_at(min(r.length, max(0, s + k)))
                ok = ok and not r.zone[j]
            if ok and rng.random() < prob:
                side = rng.choice((-1, 1))
                x, y, z, tx, ty = r.at(s)
                nx, ny = -ty, tx
                off = r.half - 3.6
                px, py = x + nx * off * side, y + ny * off * side
                # drive on the right: the vehicle front (local -Y) follows the traffic flow
                yaw = math.atan2(tx if side < 0 else -tx, -(ty if side < 0 else -ty))
                name = rng.choice(cars)
                self.props.append(PropPlace(name, px, py, z, yaw,
                                            channels={"$car": rng.choice(pl)}, interior=False))
                self.markers.append(Marker("vehicle", px, py, z, yaw, name, {"parked": True,
                                                                             "street": r.name}))
                s += 20.0
            s += 10.0

    def _junction_furniture(self, j: Junction):
        rng = self.rng
        if len(j.arms) < 2:
            return
        roads = {a.road.idx: a.road for a in j.arms}
        top = max(r.prio for r in roads.values())
        names = sorted({a.road.name for a in j.arms})
        placed_sign = False
        for a in j.arms:
            r = a.road
            # corner point: right curb corner of the arm, pulled onto the sidewalk
            x, y = r.P[a.end]
            tx, ty = r.Tg[a.end]
            tx, ty = tx * a.dirn, ty * a.dirn
            nx, ny = -ty, tx
            off = r.half + max(r.sw, 2.0) * 0.6
            px, py = x - nx * off + tx * 2.0, y - ny * off + ty * 2.0
            z = a.z + (CURB if r.sw > 0 else 0.0)
            yaw_face_in = math.atan2(-tx, ty)     # local -Y toward the junction
            if j.signal and r.prio >= 3:
                # the mast arm (local -Y) reaches from the corner over the carriageway
                fx, fy = nx, ny
                yaw = math.atan2(fx, -fy)
                self.props.append(PropPlace("traffic_signal", px, py, z, yaw, interior=False))
                self.markers.append(Marker("traffic_signal", px, py, z, yaw, r.name))
            elif r.prio < top and r.kind not in ("alley", "dirt"):
                self.props.append(PropPlace("stop_sign", px, py, z, yaw_face_in + math.pi,
                                            interior=False))
            if not placed_sign and r.kind not in ("alley", "dirt") and len(names) >= 2:
                self.props.append(PropPlace("street_sign", px + tx * 2.0, py + ty * 2.0, z,
                                            yaw_face_in, interior=False))
                self.markers.append(Marker("street_sign", px, py, z, yaw_face_in,
                                           " / ".join(names)))
                placed_sign = True
            # crosswalk stripes across each arm in town centres
            dist = self.district_at(j.x, j.y)
            if dist in ("DOWNTOWN", "MIXED_USE", "CIVIC", "COMMERCIAL") and r.prio >= 4:
                self._crosswalk(r, a)

    def _crosswalk(self, r: Road, a: Arm):
        from ..geom import Prim, rot_z
        x, y = r.P[a.end]
        tx, ty = r.Tg[a.end]
        tx, ty = tx * a.dirn, ty * a.dirn
        nx, ny = -ty, tx
        yaw = math.atan2(ty, tx)
        n = int(r.w / 2.4)
        cx, cy = x + tx * 4.0, y + ty * 4.0
        for k in range(n):
            o = -r.half + 1.2 + k * 2.4
            px, py = cx + nx * o, cy + ny * o
            self.boxes.append(("ROADS", Prim("box", "paint_line_white", (px, py, a.z + 0.04),
                                             (5.0, 1.2, 0.06), rot_z(yaw), False)))


def _corner_curve(p0, d0_ang, p1, d1_ang, dth, center, n=7):
    """Quadratic curve from p0 to p1 bulging toward the corner between two arms."""
    # control point: intersection of the curb lines (p0 along arm a inward, p1 along arm b)
    ax, ay = p0
    bx, by = p1
    # curb line directions pointing toward the junction centre
    ux, uy = center[0] - ax, center[1] - ay
    vx, vy = center[0] - bx, center[1] - by
    # line through p0 parallel to arm a = direction perpendicular to its left normal
    da = (math.cos(d0_ang - math.pi / 2), math.sin(d0_ang - math.pi / 2))
    db = (math.cos(d1_ang + math.pi / 2), math.sin(d1_ang + math.pi / 2))
    den = da[0] * db[1] - da[1] * db[0]
    if abs(den) < 0.15:
        cx, cy = (ax + bx) / 2, (ay + by) / 2
    else:
        t = ((bx - ax) * db[1] - (by - ay) * db[0]) / den
        cx, cy = ax + da[0] * t, ay + da[1] * t
        # keep the control point near the junction (avoid long spikes on shallow angles)
        if math.hypot(cx - center[0], cy - center[1]) > 60:
            cx, cy = (ax + bx) / 2, (ay + by) / 2
    pts = []
    for k in range(n + 1):
        t = k / n
        x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx
        y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t * t * by
        pts.append((x, y))
    return pts


def _signed_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2
