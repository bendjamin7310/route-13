"""Room furnishing: a small layout engine plus per-room-type rules.

Every room gets furniture appropriate to its *kind*, the building's quality
(cheap / normal / nice / abandoned) and the detail level.  Placement respects
the room's real doors and windows: nothing blocks a doorway, tall furniture
avoids windows, wall decor avoids openings and tall pieces, and ceiling
fixtures (with their light sources) are laid out on a grid.
"""

from __future__ import annotations

import math
import random
import zlib

from ..geom import Rect
from ..records import PropPlace, LightRec
from ..kit import KIT, WARM, NEUTRAL, COOL
from .. import palette as pal

SLAB = 1.0
HALF_PI = math.pi / 2
SIDE_YAW = {"N": 0.0, "S": math.pi, "W": HALF_PI, "E": -HALF_PI}


class Placed:
    __slots__ = ("name", "x", "y", "z", "yaw", "rect", "side", "u0", "u1", "top", "scale")

    def __init__(self, name, x, y, z, yaw, rect, side=None, u0=0, u1=0, top=0, scale=1.0):
        self.name, self.x, self.y, self.z, self.yaw = name, x, y, z, yaw
        self.rect, self.side, self.u0, self.u1, self.top = rect, side, u0, u1, top
        self.scale = scale


class RoomCtx:
    def __init__(self, B, room, L, rect, rng, schedule):
        self.B = B
        self.room = room
        self.L = L
        self.rect = rect
        self.inner = B.inner_rect(L, room.id, rect)
        self.z = B.z(L)
        # tall spaces (warehouse halls, bays) span several plan levels
        top = L
        while (top + 1) in room.cells and any(rc.contains(rect.cx, rect.cy)
                                             for rc in room.cells[top + 1]):
            top += 1
        self.h = B.z(top) + B.h(top) - self.z - SLAB
        self.detail = B.p.detail
        self.q = B.p.quality
        for t in room.tags:
            if t.startswith("q:"):
                self.q = t[2:]
        self.rng = rng
        self.schedule = schedule
        self.cheap = self.q in ("cheap", "abandoned")
        self.nice = self.q == "nice"
        self.abandoned = self.q == "abandoned"
        self.occ: list[tuple[Rect, float]] = []      # footprint, height
        self.decor_used = {s: [] for s in "NSWE"}    # (u0,u1,z0,z1)
        self.door_zones: list[Rect] = []
        self.openings = {s: [] for s in "NSWE"}
        self.lights = 0
        self.stair_rects = [s.rect for s in B.p.stairs
                            if (s.level == L or (s.to_roof and L == B.p.top)) and
                            s.rect.overlaps(rect)]
        for sr in self.stair_rects:
            self.occ.append((sr.expand(1.0), 99.0))
        # holes above (stairs arriving from below) are also floor-less
        for s in B.p.stairs:
            if s.level + 1 == L and s.rect.overlaps(rect):
                self.occ.append((s.rect.expand(0.6), 99.0))
        edge = {"S": rect.y0, "N": rect.y1, "W": rect.x0, "E": rect.x1}
        for o in B.out.openings.get((room.id, L), []):
            if abs(o["c"] - edge[o["side"]]) > 1e-3:
                continue
            span = (rect.x0, rect.x1) if o["side"] in "SN" else (rect.y0, rect.y1)
            if o["u1"] <= span[0] or o["u0"] >= span[1]:
                continue
            self.openings[o["side"]].append(o)
            if o["kind"] == "door":
                a, b = o["u0"] - 0.8, o["u1"] + 0.8
                dz = self._strip(o["side"], a, b, 5.0)
                self.door_zones.append(dz)

    # -- geometry helpers ------------------------------------------------------------
    def face(self, side):
        i = self.inner
        return {"S": i.y0, "N": i.y1, "W": i.x0, "E": i.x1}[side]

    def span(self, side):
        i = self.inner
        return (i.x0, i.x1) if side in "SN" else (i.y0, i.y1)

    def wall_len(self, side):
        a, b = self.span(side)
        return b - a

    def _strip(self, side, u0, u1, depth, off=0.0):
        f = self.face(side)
        if side == "S":
            return Rect(u0, f + off, u1, f + off + depth)
        if side == "N":
            return Rect(u0, f - off - depth, u1, f - off)
        if side == "W":
            return Rect(f + off, u0, f + off + depth, u1)
        return Rect(f - off - depth, u0, f - off, u1)

    @property
    def area(self):
        return self.inner.area

    @property
    def w(self):
        return self.inner.w

    @property
    def d(self):
        return self.inner.d

    def far_side(self):
        """Wall opposite the room's main door (or the longest wall)."""
        doors = [(s, o) for s in "NSWE" for o in self.openings[s] if o["kind"] == "door"]
        if doors:
            s = doors[0][0]
            return {"N": "S", "S": "N", "W": "E", "E": "W"}[s]
        return "N" if self.w >= self.d else "E"

    def sides_by_pref(self, first=None):
        order = [first] if first else []
        f = self.far_side()
        for s in [f, "N", "E", "W", "S"]:
            if s not in order:
                order.append(s)
        return order

    def windows_on(self, side):
        return [o for o in self.openings[side] if o["kind"] in ("window", "storefront")]

    def has_window(self, side):
        return bool(self.windows_on(side))

    def blocked(self, side, z0, z1):
        out = []
        for o in self.openings[side]:
            if o["kind"] == "door":
                out.append((o["u0"] - 0.8, o["u1"] + 0.8))
            elif z1 > o["z0"] - 0.2 and z0 < o["z1"]:
                out.append((o["u0"] - 0.4, o["u1"] + 0.4))
        return out

    def fits(self, r: Rect, clearance=0.0, ignore_doors=False):
        i = self.inner
        if r.x0 < i.x0 - 1e-3 or r.y0 < i.y0 - 1e-3 or r.x1 > i.x1 + 1e-3 or r.y1 > i.y1 + 1e-3:
            return False
        rr = r.expand(clearance) if clearance else r
        for (o, _h) in self.occ:
            if rr.overlaps(o):
                return False
        if not ignore_doors:
            for dz in self.door_zones:
                if r.overlaps(dz):
                    return False
        return True

    def _emit(self, name, x, y, z, yaw, channels=None, scale=(1.0, 1.0, 1.0), meta=None):
        d = KIT[name]
        self.B.out.props.append(PropPlace(name, x, y, z, yaw, scale, channels or {}, True,
                                          self.room.id, meta))
        if d.light and self.schedule != "dark" and self.lights < 6:
            lt = d.light
            c, s = math.cos(yaw), math.sin(yaw)
            ax, ay, az = lt["at"]
            ax, ay, az = ax * scale[0], ay * scale[1], az * scale[2]
            sched = lt.get("schedule", self.schedule)
            self.B.out.lights.append(LightRec(x + c * ax - s * ay, y + s * ax + c * ay, z + az,
                                              lt["color"], lt["range"], lt["brightness"],
                                              lt.get("kind", "point"), sched, self.room.id))
            self.lights += 1

    def _footprint(self, name, yaw):
        bx0, by0, bz0, bx1, by1, bz1 = KIT[name].bbox
        c, s = round(math.cos(yaw)), round(math.sin(yaw))
        pts = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
        xs = [c * px - s * py for px, py in pts]
        ys = [s * px + c * py for px, py in pts]
        return min(xs), min(ys), max(xs), max(ys), bz1

    # -- placement primitives -----------------------------------------------------------
    def wall(self, name, sides=None, align="center", channels=None, gap=0.15, z=0.0,
             clear_front=0.0, avoid_windows=None, u=None, meta=None, record=True):
        """Place a floor prop with its back against a wall."""
        if name not in KIT or KIT[name].detail > self.detail:
            return None
        d = KIT[name]
        bx0, by0, bz0, bx1, by1, bz1 = d.bbox
        pw, pd = bx1 - bx0, by1 - by0
        ph = bz1 + z
        sides = sides or self.sides_by_pref()
        if isinstance(sides, str):
            sides = [sides]
        sides = [s for s in sides if s]
        for side in sides:
            a, b = self.span(side)
            if b - a < pw + 2 * gap:
                continue
            aw = avoid_windows if avoid_windows is not None else ph > 2.6
            blocked = [iv for iv in self.blocked(side, z, ph if aw else min(ph, 2.0))]
            # existing furniture against this wall
            strip = self._strip(side, a, b, pd + clear_front)
            for (o, _h) in self.occ:
                if o.overlaps(strip):
                    if side in "SN":
                        blocked.append((o.x0, o.x1))
                    else:
                        blocked.append((o.y0, o.y1))
            free = _free_intervals(a + gap, b - gap, blocked)
            cands = [(fa, fb) for (fa, fb) in free if fb - fa >= pw]
            if not cands:
                continue
            if u is not None:
                pos = _closest_in(cands, u, pw)
            elif align == "center":
                pos = _closest_in(cands, (a + b) / 2, pw)
            elif align == "start":
                pos = cands[0][0] + pw / 2
            elif align == "end":
                pos = cands[-1][1] - pw / 2
            else:
                fa, fb = self.rng.choice(cands)
                pos = self.rng.uniform(fa + pw / 2, fb - pw / 2)
            p = self._wall_place(name, side, pos, z, gap, clear_front, channels, meta, record)
            if p:
                return p
        return None

    def _wall_place(self, name, side, ucen, z, gap, clear_front, channels, meta, record):
        d = KIT[name]
        bx0, by0, bz0, bx1, by1, bz1 = d.bbox
        cx = (bx0 + bx1) / 2
        f = self.face(side)
        yaw = SIDE_YAW[side]
        if side == "N":
            ox, oy = ucen - cx, f - by1 - gap
        elif side == "S":
            ox, oy = ucen + cx, f + by1 + gap
        elif side == "W":
            ox, oy = f + by1 + gap, ucen - cx
        else:
            ox, oy = f - by1 - gap, ucen + cx
        fx0, fy0, fx1, fy1, top = self._footprint(name, yaw)
        rect = Rect(ox + fx0, oy + fy0, ox + fx1, oy + fy1)
        check = rect
        if clear_front:
            check = _grow_front(rect, side, clear_front)
        if not self.fits(check):
            return None
        if record:
            self.occ.append((rect, top + z))
        self._emit(name, ox, oy, self.z + z, yaw, channels, meta=meta)
        half = (bx1 - bx0) / 2
        self.decor_used[side].append((ucen - half, ucen + half, 0.0, z + top))
        return Placed(name, ox, oy, self.z + z, yaw, rect, side, ucen - half, ucen + half, top + z)

    def center(self, name, yaw=None, near=None, clearance=1.5, channels=None, align_long=True,
               meta=None, record=True):
        if name not in KIT or KIT[name].detail > self.detail:
            return None
        if yaw is None:
            sx, sy, _ = KIT[name].size
            yaw = 0.0
            if align_long and ((sx > sy) != (self.w > self.d)):
                yaw = HALF_PI
        fx0, fy0, fx1, fy1, top = self._footprint(name, yaw)
        i = self.inner
        tx, ty = near if near else (i.cx, i.cy)
        best = None
        step = 1.0
        nx = int((i.w - (fx1 - fx0)) / step) + 1
        ny = int((i.d - (fy1 - fy0)) / step) + 1
        if nx <= 0 or ny <= 0:
            return None
        cands = []
        for ix in range(nx):
            for iy in range(ny):
                x = i.x0 - fx0 + ix * step
                y = i.y0 - fy0 + iy * step
                cands.append(((x - tx) ** 2 + (y - ty) ** 2, x, y))
        cands.sort()
        for (_, x, y) in cands[:900]:
            r = Rect(x + fx0, y + fy0, x + fx1, y + fy1)
            if self.fits(r, clearance):
                best = (x, y, r)
                break
        if not best:
            return None
        x, y, r = best
        if record:
            self.occ.append((r, top))
        self._emit(name, x, y, self.z, yaw, channels, meta=meta)
        return Placed(name, x, y, self.z, yaw, r, None, 0, 0, top)

    def at(self, name, x, y, yaw=0.0, channels=None, z=0.0, check=True, clearance=0.0,
           record=True, scale=(1.0, 1.0, 1.0), ignore_doors=False):
        if name not in KIT or KIT[name].detail > self.detail:
            return None
        fx0, fy0, fx1, fy1, top = self._footprint(name, yaw)
        r = Rect(x + fx0, y + fy0, x + fx1, y + fy1)
        if check and not self.fits(r, clearance, ignore_doors):
            return None
        if record:
            self.occ.append((r, top + z))
        self._emit(name, x, y, self.z + z, yaw, channels, scale=scale)
        return Placed(name, x, y, self.z + z, yaw, r, None, 0, 0, top + z)

    def grid(self, name, area=None, yaw=0.0, gap_x=4.0, gap_y=4.0, channels=None, limit=999,
             margin=0.5, channels_fn=None):
        if name not in KIT or KIT[name].detail > self.detail:
            return []
        area = area or self.inner.inset(margin)
        fx0, fy0, fx1, fy1, top = self._footprint(name, yaw)
        pw, pd = fx1 - fx0, fy1 - fy0
        nx = max(0, int((area.w + gap_x) / (pw + gap_x)))
        ny = max(0, int((area.d + gap_y) / (pd + gap_y)))
        if nx == 0 or ny == 0:
            return []
        used_w = nx * pw + (nx - 1) * gap_x
        used_d = ny * pd + (ny - 1) * gap_y
        x0 = area.x0 + (area.w - used_w) / 2
        y0 = area.y0 + (area.d - used_d) / 2
        out = []
        for ix in range(nx):
            for iy in range(ny):
                if len(out) >= limit:
                    return out
                x = x0 + ix * (pw + gap_x) - fx0
                y = y0 + iy * (pd + gap_y) - fy0
                ch = channels_fn(len(out)) if channels_fn else channels
                p = self.at(name, x, y, yaw, ch)
                if p:
                    out.append(p)
        return out

    def on(self, parent: Placed, name, dx=0.0, dy=0.0, dyaw=0.0, channels=None):
        """Put a small prop on top of a placed prop (parent-local offset)."""
        if parent is None or name not in KIT or KIT[name].detail > self.detail:
            return None
        c, s = math.cos(parent.yaw), math.sin(parent.yaw)
        x = parent.x + c * dx - s * dy
        y = parent.y + s * dx + c * dy
        self._emit(name, x, y, parent.z + KIT[parent.name].bbox[5], parent.yaw + dyaw, channels)
        return Placed(name, x, y, parent.z + KIT[parent.name].bbox[5], parent.yaw + dyaw,
                      parent.rect, parent.side, 0, 0, 0)

    def beside(self, parent: Placed, name, which="both", gap=0.2, channels=None):
        if parent is None or parent.side is None:
            return []
        d = KIT.get(name)
        if d is None or d.detail > self.detail:
            return []
        pw = d.size[0]
        out = []
        for sgn in ((-1, 1) if which == "both" else ((-1,) if which == "left" else (1,))):
            if sgn < 0:
                u = parent.u0 - gap - pw / 2
            else:
                u = parent.u1 + gap + pw / 2
            p = self._wall_place(name, parent.side, u, 0.0, 0.15, 0.0, channels, None, True)
            if p:
                out.append(p)
        return out

    def in_front(self, parent: Placed, name, dist=1.0, channels=None, yaw_extra=0.0):
        """Place a prop in front of a wall-placed prop (e.g. coffee table before a sofa)."""
        if parent is None or name not in KIT or KIT[name].detail > self.detail:
            return None
        pd = KIT[parent.name].size[1]
        nd = KIT[name].size[1]
        off = pd / 2 + dist + nd / 2
        c, s = math.cos(parent.yaw), math.sin(parent.yaw)
        bb = KIT[parent.name].bbox
        cy = (bb[1] + bb[4]) / 2
        lx, ly = (bb[0] + bb[3]) / 2, cy - off
        x = parent.x + c * lx - s * ly
        y = parent.y + s * lx + c * ly
        return self.at(name, x, y, parent.yaw + yaw_extra, channels)

    def facing(self, parent: Placed, name, dist=7.0, channels=None):
        """Place a wall prop on the opposite wall facing ``parent`` (TV opposite sofa)."""
        if parent is None or parent.side is None:
            return None
        opp = {"N": "S", "S": "N", "W": "E", "E": "W"}[parent.side]
        u = (parent.u0 + parent.u1) / 2
        return self.wall(name, sides=[opp], u=u, channels=channels)

    def decor(self, name, z=5.0, sides=None, channels=None, u=None):
        if name not in KIT or KIT[name].detail > self.detail:
            return None
        d = KIT[name]
        bx0, by0, bz0, bx1, by1, bz1 = d.bbox
        pw = bx1 - bx0
        top = z + bz1
        if top > self.h - 0.3:
            z = self.h - 0.3 - bz1
            top = z + bz1
        sides = [s for s in (sides or []) if s] or self.rng.sample("NSWE", 4)
        for side in sides:
            a, b = self.span(side)
            blocked = [(o["u0"] - 0.5, o["u1"] + 0.5) for o in self.openings[side]
                       if top > o["z0"] - 0.3 and z + bz0 < o["z1"] + 0.3]
            for (u0, u1, z0, z1) in self.decor_used[side]:
                if z1 > z + bz0 - 0.3 and z0 < top:
                    blocked.append((u0 - 0.4, u1 + 0.4))
            free = _free_intervals(a + 0.6, b - 0.6, blocked)
            cands = [(fa, fb) for (fa, fb) in free if fb - fa >= pw]
            if not cands:
                continue
            pos = _closest_in(cands, u if u is not None else (a + b) / 2, pw)
            p = self._wall_place(name, side, pos, z, 0.02, 0.0, channels, None, False)
            if p:
                self.decor_used[side].append((pos - pw / 2, pos + pw / 2, z + bz0, top))
                return p
        return None

    def window_dressing(self, kind="curtains", channels=None, prob=1.0, sides="NSWE"):
        if KIT[kind].detail > self.detail:
            return
        for side in sides:
            for o in self.openings[side]:
                if o["kind"] != "window" or self.rng.random() > prob:
                    continue
                w = o["u1"] - o["u0"]
                u = (o["u0"] + o["u1"]) / 2
                f = self.face(side)
                yaw = SIDE_YAW[side]
                if side == "N":
                    x, y = u, f
                elif side == "S":
                    x, y = u, f
                elif side == "W":
                    x, y = f, u
                else:
                    x, y = f, u
                zs = o["z0"]
                hz = (o["z1"] - o["z0"]) / 5.0 if kind != "curtains" else (o["z1"] - zs + 0.4) / 5.4
                self._emit(kind, x, y, self.z + zs, yaw, channels,
                           scale=(w / 5.0, 1.0, max(0.4, hz)))

    def ceiling(self, name=None, spacing=14.0, max_n=12):
        if name is None:
            name = "ceiling_light"
        if name == "none" or name not in KIT:
            return
        i = self.inner.inset(1.0)
        if i.w <= 0 or i.d <= 0:
            return
        nx = max(1, int(round(i.w / spacing)))
        ny = max(1, int(round(i.d / spacing)))
        while nx * ny > max_n:
            if nx >= ny:
                nx -= 1
            else:
                ny -= 1
        zc = self.z + self.h
        for ix in range(nx):
            for iy in range(ny):
                x = i.x0 + (ix + 0.5) * i.w / nx
                y = i.y0 + (iy + 0.5) * i.d / ny
                if any(sr.expand(1.0).contains(x, y) for sr in self.stair_rects):
                    continue
                yaw = 0.0 if i.w >= i.d else HALF_PI
                self._emit(name, x, y, zc, yaw)

    # -- convenience -----------------------------------------------------------------
    def pick(self, seq):
        return self.rng.choice(seq)

    def chance(self, p):
        return self.rng.random() < p

    def fabric(self):
        if self.cheap:
            return self.pick(pal.FABRICS_CHEAP)
        if self.nice:
            return self.pick(pal.FABRICS_NICE)
        return self.pick(pal.FABRICS)

    def wood(self):
        if self.cheap:
            return self.pick(["wood", "wood_light", "wood_white"])
        return self.pick(pal.WOODS)

    def clutter(self, n=2, items=("boxes_stack", "clutter_pile", "trash_bags", "laundry_basket")):
        for _ in range(n):
            self.wall(self.pick(items), align="random")


def _free_intervals(a, b, blocked):
    blocked = sorted((max(a, x0), min(b, x1)) for (x0, x1) in blocked if x1 > a and x0 < b)
    out = []
    u = a
    for (x0, x1) in blocked:
        if x0 > u:
            out.append((u, x0))
        u = max(u, x1)
    if b > u:
        out.append((u, b))
    return out


def _closest_in(cands, target, pw):
    best, bd = None, 1e18
    for (fa, fb) in cands:
        p = min(max(target, fa + pw / 2), fb - pw / 2)
        dd = abs(p - target)
        if dd < bd:
            best, bd = p, dd
    return best


def _grow_front(r, side, d):
    if side == "S":
        return Rect(r.x0, r.y0, r.x1, r.y1 + d)
    if side == "N":
        return Rect(r.x0, r.y0 - d, r.x1, r.y1)
    if side == "W":
        return Rect(r.x0, r.y0, r.x1 + d, r.y1)
    return Rect(r.x0 - d, r.y0, r.x1, r.y1)


# =============================================================================
# Rules
# =============================================================================

RULES = {}


def rule(*kinds):
    def deco(fn):
        for k in kinds:
            RULES[k] = fn
        return fn
    return deco


# --- residential ----------------------------------------------------------------

@rule("living", "family", "unit_living")
def r_living(c: RoomCtx):
    fab = {"$fabric": c.fabric(), "$wood": c.wood()}
    if c.abandoned:
        c.wall("sofa_2", channels={"$fabric": "fabric_brown"}, align="random")
        c.clutter(3, ("boxes_stack", "clutter_pile", "trash_bags", "boxes_moving"))
        c.ceiling("bare_bulb")
        return
    big = c.area > 220
    sofa = place_primary(c, ["sofa_3" if c.area > 150 else "sofa_2", "sofa_2", "armchair"],
                         channels=fab, clear_front=1.0)
    if sofa:
        c.in_front(sofa, "coffee_table", 1.2, channels={"$wood": fab["$wood"]})
        tvs = c.facing(sofa, "tv_stand", channels={"$wood": fab["$wood"]})
        if tvs:
            c.on(tvs, "tv_crt" if c.cheap else "tv_flat")
            if c.chance(0.4):
                c.on(tvs, "game_console", dx=1.8)
        c.beside(sofa, "side_table", "left", channels={"$wood": fab["$wood"]})
        if c.detail >= 2:
            c.decor("picture_large", 5.0, sides=[sofa.side], u=(sofa.u0 + sofa.u1) / 2,
                    channels={"$fabric": c.pick(pal.FABRICS), "$fabric2": c.pick(pal.FABRICS),
                              "$wood": "wood_dark"})
    c.wall("armchair" if not c.cheap else "recliner", channels={"$fabric": c.fabric()},
           align="random")
    if big:
        c.wall("bookshelf", channels={"$wood": fab["$wood"]})
        c.wall("armchair", channels={"$fabric": c.fabric()}, align="random")
    if c.chance(0.6):
        c.wall("floor_lamp", align="random")
    c.center("rug_rect", channels={"$fabric": c.fabric(), "$fabric2": c.pick(pal.FABRICS)},
             record=False)
    c.wall("plant_tall" if c.nice else "plant_pot", align="end")
    if c.cheap:
        c.clutter(1, ("boxes_stack", "clutter_pile", "laundry_basket"))
    if c.detail >= 3:
        c.decor("photo_frames", 5.4)
        c.decor("clock_wall", 7.0)
    c.window_dressing("curtains" if not c.cheap else "blinds",
                      channels={"$fabric": c.pick(pal.FABRICS)})
    c.ceiling("ceiling_fan_light" if c.chance(0.4) else "ceiling_light", spacing=16)


@rule("bedroom", "master", "kids", "unit_bedroom", "dorm_room")
def r_bedroom(c: RoomCtx):
    sheet = {"$sheet": c.pick(pal.SHEETS), "$wood": c.wood()}
    if c.abandoned:
        c.wall("mattress_floor", channels={"$sheet": "sheet_gray"})
        c.clutter(2, ("clutter_pile", "boxes_stack", "trash_bags"))
        c.window_dressing("newspaper_cover", prob=0.6)
        c.ceiling("bare_bulb")
        return
    kids = c.room.kind == "kids" or "kids" in c.room.tags
    if kids:
        bed = c.wall("bunk_bed" if c.chance(0.4) else "bed_single", channels=sheet,
                     avoid_windows=True)
        c.wall("toy_box", channels={"$paint": c.pick(["wood_white", "wood_blue", "wood_green"])},
               align="random")
        c.center("toys_floor", record=False)
        c.wall("desk_home", channels={"$wood": "wood_white"})
        c.decor("picture_small", 5.0, channels={"$fabric": c.pick(pal.FABRICS)})
    else:
        if c.cheap:
            name = c.pick(["bed_metal_cheap", "mattress_floor", "bed_double", "bed_single"])
        elif c.nice or c.room.kind == "master":
            name = "bed_queen_nice" if c.nice else "bed_double"
        else:
            name = "bed_double" if c.area > 120 else "bed_single"
        bed = place_primary(c, [name, "bed_double", "bed_single"], channels=sheet,
                            clear_front=2.5)
        if bed:
            for ns in c.beside(bed, "nightstand", "both" if name != "bed_single" else "left",
                               channels={"$wood": sheet["$wood"]}):
                c.on(ns, "table_lamp")
                if c.detail >= 3 and c.chance(0.3):
                    c.on(ns, "radio", dx=0.0)
            c.decor("picture_large" if c.nice else "picture_small", 6.0, sides=[bed.side],
                    u=(bed.u0 + bed.u1) / 2,
                    channels={"$fabric": c.pick(pal.FABRICS), "$fabric2": c.pick(pal.FABRICS),
                              "$wood": "wood_dark"})
    dr = c.wall("dresser", channels={"$wood": sheet["$wood"]}, align="random")
    if dr and c.chance(0.4):
        c.on(dr, "tv_crt" if c.cheap else "tv_flat")
    if "closet" not in c.room.tags:
        c.wall("wardrobe", channels={"$wood": sheet["$wood"]}, align="random")
    if c.chance(0.4) and not kids:
        d = c.wall("desk_home", channels={"$wood": c.wood()})
        if d:
            c.in_front(d, "office_chair", -0.6, channels={"$fabric": "fabric_dark"},
                       yaw_extra=math.pi)
    if c.nice:
        c.center("rug_rect", channels={"$fabric": c.fabric(), "$fabric2": "fabric_cream"},
                 record=False)
        c.wall("armchair", channels={"$fabric": c.fabric()})
    c.wall("laundry_basket", align="random")
    if c.cheap:
        c.clutter(c.rng.randint(1, 2), ("clutter_pile", "laundry_basket", "boxes_stack"))
        c.wall("suitcase", align="random", channels={"$fabric": c.fabric()})
    c.decor("mirror_wall", 3.5)
    c.window_dressing("blinds_closed" if c.chance(0.35) else "curtains",
                      channels={"$fabric": c.pick(pal.FABRICS)})
    c.ceiling("ceiling_light", spacing=18)


@rule("kitchen", "unit_kitchen", "kitchen_dining")
def r_kitchen(c: RoomCtx):
    paint = c.pick(["wood_white", "wood", "wood_green", "wood_blue", "wood_dark"]) if not c.cheap \
        else c.pick(["wood", "wood_white", "metal_beige"])
    ch = {"$paint": paint, "$metal": "metal_chrome" if c.nice else
          ("metal_beige" if c.cheap else "metal_white")}
    side = c.sides_by_pref()[0]
    # pick the longest wall without a door for the counter run
    best = None
    for s in "NSWE":
        L = c.wall_len(s)
        nd = sum(1 for o in c.openings[s] if o["kind"] == "door")
        score = L - nd * 30
        if best is None or score > best[0]:
            best = (score, s)
    side = best[1]
    seq = ["fridge_old" if c.cheap else "fridge", "counter_base", "stove_old" if c.cheap else
           "stove", "counter_drawers", "counter_sink", "dishwasher" if not c.cheap else
           "counter_base", "counter_base_wide", "counter_base"]
    placed = []
    a, b = c.span(side)
    u = a + 0.2
    for name in seq:
        if name not in KIT:
            continue
        pw = KIT[name].size[0]
        if u + pw > b - 0.2:
            break
        p = c.wall(name, sides=[side], u=u + pw / 2, channels=ch, gap=0.05, avoid_windows=(
            name.startswith("fridge")))
        if p:
            placed.append(p)
            u = p.u1 + 0.02
        else:
            u += 1.0
    for p in placed:
        if p.name.startswith("counter") and c.detail >= 2:
            if not c.blocked(side, 4.8, 7.4) or True:
                c.decor("upper_cabinet", 4.9, sides=[side], u=(p.u0 + p.u1) / 2, channels=ch)
        if p.name.startswith("stove") and c.detail >= 2:
            c.decor("range_hood", 5.2, sides=[side], u=(p.u0 + p.u1) / 2)
    counters = [p for p in placed if p.name.startswith("counter")]
    if counters:
        c.on(counters[0], "microwave", channels={"$metal": ch["$metal"]})
        if len(counters) > 1:
            c.on(counters[-1], "coffee_maker")
            c.on(counters[1], "fruit_bowl")
        if c.detail >= 3:
            c.on(counters[-1], "toaster", dx=1.0)
            c.on(counters[min(2, len(counters) - 1)], "dish_rack")
    if c.room.kind == "kitchen_dining" or c.area > 200:
        t = c.center("kitchen_table_formica" if c.cheap else "dining_table",
                     channels={"$wood": c.wood()}, clearance=2.0)
        _chairs_around(c, t, "kitchen_chair_vinyl" if c.cheap else "dining_chair",
                       {"$wood": c.wood()})
    elif c.area > 150 and c.nice:
        c.center("kitchen_island", channels=ch, clearance=3.0)
    c.wall("trash_can_small", align="end")
    if c.cheap:
        c.clutter(1, ("trash_bags", "boxes_stack"))
    if c.detail >= 3:
        c.decor("calendar_wall", 0.0)
        c.decor("clock_wall", 7.0)
    c.window_dressing("blinds", prob=0.7)
    c.ceiling("ceiling_light" if not c.cheap else "fluor_strip", spacing=14)


def place_primary(c: RoomCtx, names, channels=None, clear_front=1.5):
    """Place a room's key piece, relaxing constraints step by step so it always lands:
    window-free walls first, then any wall (under a window), smaller variants, then the
    room centre."""
    tried = []
    for nm in names:
        if nm in tried:
            continue
        tried.append(nm)
        no_win = [s for s in c.sides_by_pref() if not c.has_window(s)]
        p = c.wall(nm, sides=no_win, channels=channels, clear_front=clear_front) if no_win \
            else None
        if p:
            return p
        p = c.wall(nm, sides=c.sides_by_pref(), channels=channels, clear_front=clear_front,
                   avoid_windows=False)
        if p:
            return p
        p = c.wall(nm, sides=c.sides_by_pref(), channels=channels, clear_front=0.5,
                   avoid_windows=False)
        if p:
            return p
    for nm in names:
        p = c.center(nm, channels=channels, clearance=0.6)
        if p:
            return p
    return None


def _chairs_around(c, t, chair, ch, n=None):
    if t is None:
        return
    sx, sy, _ = KIT[t.name].size
    long_x = abs(math.cos(t.yaw)) > 0.5
    w, d = (sx, sy) if long_x else (sy, sx)
    spots = []
    per = max(1, int(w / 2.6))
    for i in range(per):
        x = t.x - w / 2 + (i + 0.5) * w / per
        spots.append((x, t.y - d / 2 - 0.9, 0.0))
        spots.append((x, t.y + d / 2 + 0.9, math.pi))
    if d > 3:
        spots.append((t.x - w / 2 - 0.9, t.y, -HALF_PI))
        spots.append((t.x + w / 2 + 0.9, t.y, HALF_PI))
    if n:
        spots = spots[:n]
    for (x, y, yaw) in spots:
        c.at(chair, x, y, yaw + math.pi, ch, check=True, clearance=0.0, record=True)


@rule("dining")
def r_dining(c: RoomCtx):
    t = c.center("dining_table_big" if c.area > 220 else "dining_table",
                 channels={"$wood": c.wood()}, clearance=2.4)
    _chairs_around(c, t, "dining_chair", {"$wood": c.wood()})
    if t:
        c.B.out.props.append(PropPlace("pendant_light" if not c.nice else "chandelier", t.x, t.y,
                                       c.z + c.h, 0.0, room=c.room.id))
        lt = KIT["chandelier" if c.nice else "pendant_light"].light
        c.B.out.lights.append(LightRec(t.x, t.y, c.z + c.h + lt["at"][2], lt["color"], lt["range"],
                                       lt["brightness"], "point", c.schedule, c.room.id))
    c.wall("dresser", channels={"$wood": c.wood()})
    c.decor("picture_large", 5.5, channels={"$fabric": c.pick(pal.FABRICS),
                                            "$fabric2": c.pick(pal.FABRICS), "$wood": "wood_dark"})
    c.wall("plant_pot", align="end")
    c.window_dressing("curtains", channels={"$fabric": c.pick(pal.FABRICS)})


@rule("bathroom", "unit_bath", "motel_bath", "halfbath")
def r_bath(c: RoomCtx):
    half = c.room.kind == "halfbath" or c.area < 50
    if not half:
        if c.w >= 6.2 or c.d >= 6.2:
            tub = c.wall("bathtub", align="end", avoid_windows=False)
            if not tub:
                c.wall("shower_stall", align="end", avoid_windows=False)
        else:
            c.wall("shower_stall", align="end", avoid_windows=False)
    t = c.wall("toilet", align="start", avoid_windows=False)
    s = c.wall("vanity_sink" if c.nice else "sink_pedestal",
               channels={"$paint": c.pick(["wood_white", "wood", "wood_blue"])})
    if s:
        c.decor("mirror_bath", 3.6, sides=[s.side], u=(s.u0 + s.u1) / 2)
    c.decor("towel_rack", 0.0, channels={"$fabric": c.pick(["fabric_white", "fabric_blue",
                                                             "fabric_teal", "fabric_pink"])})
    if c.cheap:
        c.wall("trash_can_small", align="random")
    c.ceiling("ceiling_light", spacing=20, max_n=1)


@rule("entry", "foyer", "unit_entry")
def r_entry(c: RoomCtx):
    c.wall("coat_rack", align="start")
    c.wall("shoes_mat", align="center", avoid_windows=False)
    if c.area > 60:
        c.wall("side_table", channels={"$wood": c.wood()})
        c.wall("plant_pot", align="end")
    c.decor("mirror_wall", 3.5)
    c.decor("picture_small", 5.0, channels={"$fabric": c.pick(pal.FABRICS)})
    c.ceiling("pendant_light" if c.nice else "ceiling_light", spacing=20, max_n=2)


@rule("hall", "corridor")
def r_hall(c: RoomCtx):
    long_x = c.w > c.d
    if c.area > 30 and min(c.w, c.d) >= 3.0:
        c.center("rug_runner", yaw=HALF_PI if long_x else 0.0,
                 channels={"$fabric": c.fabric()}, record=False, clearance=0.0)
    if c.detail >= 2:
        for _ in range(2):
            c.decor("picture_small", 5.0, channels={"$fabric": c.pick(pal.FABRICS)})
    c.decor("thermostat", 0.0)
    c.ceiling("ceiling_light", spacing=14, max_n=4)


@rule("closet", "unit_closet", "pantry")
def r_closet(c: RoomCtx):
    if c.room.kind == "pantry":
        c.wall("pantry_shelf")
    else:
        c.wall("shelf_low", channels={"$wood": "wood_white"})
        c.wall("boxes_stack", align="random")
        c.wall("vacuum", align="random")
    c.ceiling("bare_bulb", max_n=1)


@rule("laundry", "utility")
def r_laundry(c: RoomCtx):
    if c.room.kind == "laundry":
        c.wall("washer", channels={"$metal": "metal_white"}, avoid_windows=False)
        c.wall("dryer_stack" if c.nice else "washer_topload", channels={"$metal": "metal_white"},
               avoid_windows=False)
        c.wall("laundry_basket")
        c.wall("ironing_board", align="random")
    c.wall("water_heater")
    c.wall("furnace")
    c.decor("electrical_panel", 0.0)
    c.wall("shelf_low", channels={"$wood": "wood_light"})
    c.ceiling("bare_bulb" if c.cheap else "fluor_strip", max_n=1)


@rule("garage")
def r_garage(c: RoomCtx):
    tags = c.room.tags
    cars = ["car_sedan", "car_suv", "car_pickup", "car_compact", "car_wagon", "car_coupe"]
    if c.cheap:
        cars = ["car_pickup_old", "car_sedan", "car_wreck", "car_compact"]
    paint = c.pick(pal.CAR_PAINTS_OLD if c.cheap else pal.CAR_PAINTS)
    nveh = 2 if c.w > 18 else 1
    if "empty" in tags:
        nveh = 0
    i = c.inner
    long_x = c.w > c.d * 1.4
    for k in range(nveh):
        name = c.pick(cars)
        if long_x:
            x = i.x0 + (k + 0.5) * i.w / nveh
            p = c.at(name, x, i.cy, HALF_PI, {"$car": paint}, clearance=0.3, ignore_doors=True)
        else:
            x = i.x0 + (k + 0.5) * i.w / nveh
            p = c.at(name, x, i.y0 + i.d * 0.45, 0.0, {"$car": paint}, clearance=0.3,
                     ignore_doors=True)
        if p:
            c.B.out.markers.append(_vehicle_marker(c, p))
        paint = c.pick(pal.CAR_PAINTS)
    wb = c.wall("workbench", sides=c.sides_by_pref("N"))
    c.wall("spare_parts_shelf", align="random")
    c.wall("tool_chest_roll", align="random")
    c.wall("bicycle", align="random", channels={"$plastic": c.pick(["plastic_red", "plastic_blue",
                                                                    "plastic_green"])})
    c.wall("boxes_stack", align="random")
    c.wall("garbage_cans", align="random")
    if c.chance(0.4):
        c.wall("lawn_mower", align="random")
    if c.chance(0.3):
        c.wall("tire_stack", align="random")
    if c.chance(0.4):
        c.wall("air_compressor", align="random")
    if c.detail >= 3 and c.chance(0.5):
        c.decor("pegboard_tools", 3.4)
    c.ceiling("fluor_strip", spacing=12, max_n=3)


def _vehicle_marker(c, p):
    from ..records import Marker
    return Marker("vehicle", p.x, p.y, p.z, p.yaw, p.name, {"room": c.room.id})


@rule("storage", "stockroom", "records", "evidence_storage")
def r_storage(c: RoomCtx):
    k = c.room.kind
    if k == "records":
        for _ in range(6):
            c.wall("file_cabinet", channels={"$metal": "metal_beige"}, align="random")
        c.grid("shelf_wall_retail", yaw=0.0, gap_x=1.0, gap_y=4.5, limit=4)
    else:
        for _ in range(4):
            c.wall("wire_shelf" if k == "stockroom" else "shelf_wall_retail", align="random")
        c.center("pallet_boxes", clearance=2.0)
        c.wall("boxes_stack", align="random")
        c.wall("boxes_moving", align="random")
        if k == "stockroom":
            c.wall("mop_sink", align="end")
            c.wall("pallet_jack", align="random")
            c.decor("bulletin_board", 4.5)
    c.ceiling("fluor_strip", spacing=14)


@rule("basement")
def r_basement(c: RoomCtx):
    c.wall("furnace")
    c.wall("water_heater")
    c.decor("electrical_panel", 0.0)
    c.decor("pipes_wall", 0.0)
    for _ in range(3):
        c.wall(c.pick(["boxes_stack", "boxes_moving", "shelf_low", "clutter_pile", "woodpile"]),
               align="random")
    if c.chance(0.6):
        c.center("sofa_2", channels={"$fabric": c.pick(pal.FABRICS_CHEAP)})
    if c.chance(0.5):
        c.wall("washer_topload")
    if c.chance(0.4):
        c.wall("workbench")
    c.ceiling("bare_bulb", spacing=14, max_n=4)


@rule("study", "office_home")
def r_study(c: RoomCtx):
    d = c.wall("desk_home", channels={"$wood": c.wood()})
    if d:
        c.in_front(d, "office_chair", -0.6, channels={"$fabric": "leather_black"},
                   yaw_extra=math.pi)
        c.on(d, "desk_lamp", dx=-1.6)
    c.wall("bookshelf", channels={"$wood": c.wood()})
    c.wall("file_cabinet", channels={"$metal": "metal_gray"})
    c.wall("armchair", channels={"$fabric": c.fabric()})
    c.decor("picture_large", 5.5, channels={"$fabric": c.pick(pal.FABRICS),
                                            "$fabric2": c.pick(pal.FABRICS), "$wood": "wood_dark"})
    c.window_dressing("blinds")
    c.ceiling("ceiling_light")


@rule("studio")
def r_studio(c: RoomCtx):
    # studio apartment main room: sleeping + living corner
    r_bedroom(c)
    s = c.wall("sofa_2", channels={"$fabric": c.fabric()})
    if s:
        c.in_front(s, "coffee_table", 1.0)


@rule("attic")
def r_attic(c: RoomCtx):
    c.clutter(4, ("boxes_stack", "boxes_moving", "clutter_pile", "suitcase"))
    c.ceiling("bare_bulb", max_n=2)


# --- commercial -------------------------------------------------------------------

@rule("retail", "shop")
def r_retail(c: RoomCtx):
    store = c.B.p.tags
    i = c.inner
    if "pharmacy" in store:
        c.wall("pharmacy_counter", sides=[c.far_side()])
        aisle = "pharmacy_shelf"
    elif "hardware" in store:
        c.wall("lumber_rack", sides=[c.far_side()])
        c.wall("paint_shelf")
        c.decor("pegboard_tools", 1.0)
        c.decor("pegboard_tools", 1.0)
        aisle = "shelf_gondola"
    elif "electronics" in store:
        c.decor("tv_display_wall", 2.0, sides=[c.far_side()])
        c.wall("shelf_wall_retail")
        c.grid("electronics_table", area=i.inset(4.0, 12.0, 4.0, 6.0), yaw=0.0, gap_x=4.0,
               gap_y=4.5, limit=6, channels={"$wood": "wood_white"})
        aisle = None
    elif "clothing" in store:
        c.wall("shelf_wall_retail")
        c.grid("clothing_rack", area=i.inset(4.0, 12.0, 4.0, 5.0), yaw=0.0, gap_x=4.0, gap_y=4.0,
               limit=10, channels_fn=lambda n: {"$fabric": pal.FABRICS[n % len(pal.FABRICS)],
                                                "$fabric2": pal.FABRICS[(n * 3) % len(pal.FABRICS)]})
        for _ in range(3):
            c.wall("mannequin", channels={"$fabric": c.pick(pal.FABRICS)})
        aisle = None
    elif "furniture" in store:
        for nm in ("furniture_display_sofa", "bed_double", "dining_table", "dresser", "sofa_3",
                   "wardrobe", "bookshelf", "armchair"):
            c.center(nm, clearance=2.5, channels={"$fabric": c.pick(pal.FABRICS),
                                                  "$wood": c.wood(), "$sheet": "sheet_white"})
        aisle = None
    else:
        aisle = "shelf_gondola"
    # coolers along the back wall
    if "grocery" in store or "convenience" in store:
        for _ in range(3):
            c.wall("cooler_display", sides=[c.far_side()])
    # checkout near the main entrance
    door_side = c.far_side()
    door_side = {"N": "S", "S": "N", "W": "E", "E": "W"}[door_side]
    co = c.wall("checkout_counter", sides=[door_side, "W", "E"], align="start", clear_front=2.0,
                avoid_windows=False, channels={"$wood": c.wood()})
    if co and "convenience" in store:
        c.wall("magazine_rack", sides=[door_side], avoid_windows=False)
    if aisle:
        area = i.inset(5.0, 9.0, 5.0, 5.5) if door_side == "S" else i.inset(5.0, 5.5, 5.0, 9.0)
        if door_side in "WE":
            area = i.inset(9.0 if door_side == "W" else 5.0, 5.0, 5.0 if door_side == "W" else 9.0,
                           5.0)
        c.grid(aisle, area=area, yaw=HALF_PI, gap_x=6.0, gap_y=4.5, limit=14)
    if "convenience" in store:
        c.wall("atm", align="random")
        c.wall("snack_machine", align="random", avoid_windows=False)
    c.decor("exit_sign", 8.5)
    c.decor("fire_extinguisher", 0.0)
    c.ceiling("fluor_panel", spacing=10, max_n=20)


@rule("showroom")
def r_showroom(c: RoomCtx):
    cars = ["car_sedan", "car_suv", "car_coupe", "car_pickup", "car_wagon"]
    i = c.inner
    placed = 0
    for k, name in enumerate(cars):
        p = c.center(name, clearance=3.0, channels={"$car": pal.CAR_PAINTS[k * 3 % 15]},
                     align_long=False)
        if p:
            placed += 1
            c.B.out.markers.append(_vehicle_marker(c, p))
    d = c.wall("desk_office", channels={"$wood": "wood_white"})
    if d:
        c.in_front(d, "office_chair", -0.6, yaw_extra=math.pi, channels={"$fabric": "fabric_dark"})
    c.wall("plant_tall", align="start")
    c.wall("plant_tall", align="end")
    c.wall("water_cooler")
    c.ceiling("fluor_panel", spacing=12, max_n=16)


@rule("dining_room")
def r_dining_room(c: RoomCtx):
    tags = c.B.p.tags
    diner = "diner" in tags
    fab = c.pick(["vinyl_red", "vinyl_teal", "leather_brown", "fabric_green", "fabric_red"])
    # booths along window walls
    for s in "NSWE":
        if c.has_window(s):
            for _ in range(4):
                c.wall("booth", sides=[s], avoid_windows=False, channels={"$fabric": fab},
                       align="start")
    if diner:
        bc = c.wall("bar_counter", sides=[c.far_side()], channels={"$wood": "wood_dark"})
        if bc:
            sx = KIT["bar_counter"].size[0]
            for k in range(4):
                lx = -sx / 2 + 1.4 + k * 2.4
                cc, ss = math.cos(bc.yaw), math.sin(bc.yaw)
                ly = -3.0
                c.at("bar_stool", bc.x + cc * lx - ss * ly, bc.y + ss * lx + cc * ly, bc.yaw,
                     check=True)
            c.on(bc, "pie_case", dx=2.5)
            c.on(bc, "cash_register", dx=-3.6)
        c.wall("jukebox", align="random")
        c.decor("menu_board", 7.0, sides=[c.far_side()])
    c.grid("restaurant_table_4" if c.area > 300 else "restaurant_table_2",
           area=c.inner.inset(7.5), gap_x=4.0, gap_y=4.0, limit=10,
           channels={"$wood": c.wood(), "$fabric": fab})
    c.wall("plant_pot", align="random")
    if c.detail >= 2:
        c.decor("picture_large", 5.5, channels={"$fabric": c.pick(pal.FABRICS),
                                                "$fabric2": c.pick(pal.FABRICS),
                                                "$wood": "wood_dark"})
        c.decor("clock_wall", 8.0)
    c.ceiling("pendant_light", spacing=10, max_n=12)


@rule("kitchen_pro")
def r_kitchen_pro(c: RoomCtx):
    side = None
    for s in c.sides_by_pref():
        if not any(o["kind"] == "door" for o in c.openings[s]):
            side = s
            break
    side = side or c.far_side()
    line = ["commercial_range", "flat_grill", "fryer", "fryer", "steel_counter"]
    placed = []
    for nm in line:
        p = c.wall(nm, sides=[side], align="start", gap=0.05)
        if p:
            placed.append(p)
    if placed:
        u = (placed[0].u0 + placed[-1].u1) / 2
        c.decor("hood_commercial", 7.0, sides=[side], u=u)
    c.wall("prep_sink", align="random")
    c.wall("dish_machine", align="random")
    c.wall("reach_in_fridge", align="random")
    c.wall("wire_shelf", align="random")
    c.wall("ice_machine", align="random")
    c.center("steel_counter", clearance=2.5)
    if c.area > 400:
        c.center("steel_counter", clearance=2.5)
    c.wall("food_crates", align="random")
    c.decor("fire_extinguisher", 0.0)
    c.decor("first_aid", 0.0)
    c.ceiling("fluor_panel", spacing=10)


@rule("walkin", "cold_storage")
def r_walkin(c: RoomCtx):
    for _ in range(4):
        c.wall("wire_shelf", align="random")
    c.center("food_crates", clearance=1.0)
    c.center("sack_stack", clearance=1.0)
    if c.room.kind == "cold_storage":
        c.wall("fish_crates", align="random")
        c.wall("ice_bin_fish", align="random")
    c.ceiling("fluor_panel", max_n=2)


@rule("restroom")
def r_restroom(c: RoomCtx):
    if c.area > 90:
        n = 0
        side = c.far_side()
        for _ in range(4):
            if c.wall("toilet_stall", sides=[side], align="start", avoid_windows=False, gap=0.0):
                n += 1
        if "mens" in c.room.tags:
            for _ in range(2):
                c.decor("urinal", 0.0)
        s = c.wall("sink_commercial")
        if s:
            c.decor("mirror_wall", 3.6, sides=[s.side], u=(s.u0 + s.u1) / 2)
        c.decor("hand_dryer", 4.0)
    else:
        c.wall("toilet", align="start", avoid_windows=False)
        s = c.wall("sink_pedestal")
        if s:
            c.decor("mirror_bath", 3.6, sides=[s.side], u=(s.u0 + s.u1) / 2)
        c.decor("hand_dryer", 4.0)
    c.wall("trash_can_small", align="random")
    c.ceiling("fluor_panel", spacing=14, max_n=2)


@rule("employee", "breakroom")
def r_breakroom(c: RoomCtx):
    t = c.center("kitchen_table_formica", clearance=1.8)
    _chairs_around(c, t, "kitchen_chair_vinyl", {}, n=4)
    c.wall("fridge_old" if c.cheap else "fridge", channels={"$metal": "metal_white"})
    cs = c.wall("coffee_station", channels={"$paint": "wood_white"})
    if cs:
        c.on(cs, "microwave", dx=1.0)
    c.wall("locker_row", channels={"$metal": c.pick(["metal_gray", "metal_blue", "metal_green"])})
    c.wall("vending_machine" if c.area > 160 else "trash_can_small",
           channels={"$plastic": c.pick(["plastic_red", "plastic_blue"])})
    if c.area > 160:
        c.wall("sofa_2", channels={"$fabric": c.pick(pal.FABRICS_CHEAP)})
    c.decor("bulletin_board", 4.5)
    c.decor("clock_wall", 7.5)
    c.decor("time_clock", 0.0)
    c.ceiling("fluor_panel", spacing=12)


@rule("office", "office_private")
def r_office(c: RoomCtx):
    nice = c.nice or "chief" in c.room.tags
    d = c.wall("desk_office", channels={"$wood": "wood_dark" if nice else c.wood()}, clear_front=3)
    if d:
        c.in_front(d, "office_chair", -0.8, yaw_extra=math.pi,
                   channels={"$fabric": "leather_black" if nice else "fabric_dark"})
        c.on(d, "desk_lamp", dx=-1.8, dy=0.4)
        c.in_front(d, "dining_chair", 1.6, channels={"$wood": "wood_dark"})
    c.wall("file_cabinet", channels={"$metal": c.pick(["metal_gray", "metal_beige"])})
    c.wall("bookshelf" if nice else "file_cabinet", channels={"$wood": c.wood(),
                                                             "$metal": "metal_gray"})
    c.wall("plant_pot", align="random")
    if "safe" in c.room.tags or "pawn" in c.B.p.tags:
        c.wall("safe_box", align="random")
    if "chief" in c.room.tags:
        c.wall("flag_pole_indoor", align="end")
    c.decor("picture_large" if nice else "calendar_wall", 5.0,
            channels={"$fabric": c.pick(pal.FABRICS), "$fabric2": c.pick(pal.FABRICS),
                      "$wood": "wood_dark"})
    c.window_dressing("blinds", prob=0.9)
    c.ceiling("fluor_panel", spacing=12)


@rule("office_open", "bullpen")
def r_office_open(c: RoomCtx):
    cop = c.room.kind == "bullpen"
    desk = "desk_cop" if cop else "desk_workstation"
    if not cop and c.area > 500 and c.chance(0.5):
        c.grid("cubicle", area=c.inner.inset(3.0), gap_x=1.0, gap_y=5.0, limit=16,
               channels={"$wood": "wood_light"})
    else:
        desks = c.grid(desk, area=c.inner.inset(3.5), gap_x=3.0, gap_y=5.0, limit=16,
                       channels={"$wood": c.wood()})
        for p in desks:
            cc, ss = math.cos(p.yaw), math.sin(p.yaw)
            # chair sits in front of the desk (desk-local -Y), facing it
            c.at("office_chair", p.x + ss * 2.1, p.y - cc * 2.1, p.yaw + math.pi,
                 {"$fabric": "fabric_dark"}, check=False, record=False)
    for _ in range(3):
        c.wall("file_cabinet", channels={"$metal": "metal_gray"}, align="random")
    c.wall("printer_copier", align="random")
    c.wall("water_cooler", align="random")
    if not cop:
        c.wall("plant_tall", align="random")
    else:
        c.decor("map_board", 4.0)
        c.decor("bulletin_board", 4.5)
    c.decor("clock_wall", 8.0)
    c.window_dressing("blinds", prob=0.8)
    c.ceiling("fluor_panel", spacing=10, max_n=20)


@rule("reception", "lobby", "waiting", "service_hall")
def r_reception(c: RoomCtx):
    tags = c.B.p.tags
    k = c.room.kind
    counter = "service_counter" if k == "service_hall" or "civic" in tags or "police" in tags \
        else "reception_desk"
    rd = c.wall(counter, sides=[c.far_side()], channels={"$wood": "wood_dark" if c.nice else
                                                                   c.wood()})
    for _ in range(2 if c.area > 200 else 1):
        c.wall("waiting_chairs", channels={"$fabric": c.pick(["fabric_blue", "fabric_gray",
                                                               "fabric_teal", "vinyl_red"])},
               align="random")
    c.wall("plant_tall", align="start")
    c.wall("plant_tall", align="end")
    if "police" in tags or "civic" in tags:
        c.wall("flag_pole_indoor", align="end")
        if "police" in tags:
            c.center("metal_detector", clearance=1.0)
        c.wall("ticket_kiosk", align="random")
        c.decor("bulletin_board", 4.5)
    if "motel" in tags:
        c.decor("key_board", 4.5, sides=[c.far_side()])
        c.wall("vending_machine", channels={"$plastic": "plastic_red"})
    c.wall("water_cooler", align="random")
    c.decor("picture_large", 5.5, channels={"$fabric": c.pick(pal.FABRICS),
                                            "$fabric2": c.pick(pal.FABRICS), "$wood": "wood_dark"})
    c.decor("clock_wall", 8.5)
    c.ceiling("pendant_light" if c.nice else "fluor_panel", spacing=12)


@rule("meeting", "briefing", "chamber")
def r_meeting(c: RoomCtx):
    k = c.room.kind
    if k == "meeting":
        t = c.center("conference_table", channels={"$wood": "wood_dark"}, clearance=2.0)
        _chairs_around(c, t, "office_chair", {"$fabric": "fabric_dark"})
        c.decor("whiteboard_wall", 3.4)
        c.decor("tv_wall", 3.8)
    elif k == "briefing":
        c.wall("podium", sides=[c.far_side()])
        c.decor("briefing_board", 3.2, sides=[c.far_side()])
        c.grid("chair_row", area=c.inner.inset(3.0, 3.0, 3.0, 8.0), gap_x=2.0, gap_y=2.4,
               channels={"$fabric": "fabric_blue"}, limit=8)
        c.decor("flag_wall", 6.5)
    else:
        c.wall("council_dais", sides=[c.far_side()])
        c.wall("flag_pole_indoor", align="start")
        c.wall("flag_pole_indoor", align="end")
        c.center("podium", clearance=2.0)
        c.grid("chair_row", area=c.inner.inset(4.0, 4.0, 4.0, 14.0), gap_x=3.0, gap_y=2.6,
               channels={"$fabric": "fabric_red"}, limit=12)
    c.ceiling("fluor_panel" if k != "chamber" else "chandelier", spacing=12)


@rule("laundromat")
def r_laundromat(c: RoomCtx):
    fs = c.far_side()
    for _ in range(8):
        c.wall("dryer_stack", sides=[fs], align="start", gap=0.05,
               channels={"$metal": "metal_white"})
    i = c.inner
    c.grid("washer", area=i.inset(6.0, 9.0, 6.0, 9.0), gap_x=0.1, gap_y=7.0, limit=20,
           channels={"$metal": "metal_white"})
    c.wall("folding_table", align="random")
    c.wall("waiting_chairs", channels={"$fabric": "vinyl_teal"}, align="random")
    c.wall("vending_machine", channels={"$plastic": "plastic_blue"}, align="random")
    c.wall("snack_machine", align="random")
    c.wall("laundry_cart", align="random")
    c.decor("bulletin_board", 4.5)
    c.decor("clock_wall", 8.5)
    c.ceiling("fluor_strip", spacing=10)


@rule("pawn_floor")
def r_pawn(c: RoomCtx):
    fs = c.far_side()
    co = c.wall("display_case", sides=[fs], channels={"$wood": "wood_dark"}, clear_front=3.0)
    if co:
        c.on(co, "cash_register", dx=1.5)
    for s in ("W", "E"):
        c.wall("shelf_wall_retail", sides=[s])
        c.wall("display_case", sides=[s], channels={"$wood": "wood_dark"})
    c.grid("display_case", area=c.inner.inset(6.0, 10.0, 6.0, 9.0), gap_x=5.0, gap_y=5.0,
           limit=4, channels={"$wood": "wood_dark"})
    if c.detail >= 2:
        c.decor("tv_display_wall", 3.0, sides=[fs])
    c.wall("tire_stack", align="random")
    c.wall("bicycle", align="random", channels={"$plastic": "plastic_red"})
    c.wall("arcade_cabinet", align="random", channels={"$plastic": "plastic_blue"})
    c.ceiling("fluor_strip", spacing=10)


@rule("bar_main")
def r_bar(c: RoomCtx):
    fs = c.far_side()
    bar = c.wall("bar_counter", sides=[fs], channels={"$wood": "wood_dark"}, clear_front=3.5,
                 gap=4.0)
    if bar:
        c.wall("back_bar", sides=[fs], u=(bar.u0 + bar.u1) / 2)
        sx = KIT["bar_counter"].size[0]
        cc, ss = math.cos(bar.yaw), math.sin(bar.yaw)
        for k in range(4):
            lx = -sx / 2 + 1.2 + k * 2.5
            ly = -2.8
            c.at("bar_stool", bar.x + cc * lx - ss * ly, bar.y + ss * lx + cc * ly, bar.yaw,
                 check=True)
        c.on(bar, "cash_register", dx=3.2)
    for s in "NSWE":
        if s != fs:
            c.wall("booth", sides=[s], channels={"$fabric": "leather_red"}, avoid_windows=False)
    if c.area > 380:
        pt = c.center("pool_table", clearance=3.5)
        if pt:
            c.B.out.props.append(PropPlace("pool_light", pt.x, pt.y, c.z + c.h, pt.yaw,
                                           room=c.room.id))
            c.B.out.lights.append(LightRec(pt.x, pt.y, c.z + c.h - 3.5, WARM, 16, 1.0, "point",
                                           c.schedule, c.room.id))
    c.grid("high_top", area=c.inner.inset(8.0), gap_x=5.0, gap_y=5.0, limit=4,
           channels={"$wood": "wood_dark"})
    c.wall("jukebox", align="random")
    c.wall("arcade_cabinet", align="random", channels={"$plastic": "plastic_teal"})
    c.decor("dartboard", 4.0)
    c.decor("tv_wall", 7.0)
    c.ceiling("pendant_light", spacing=11)


@rule("garage_bay", "workshop")
def r_garage_bay(c: RoomCtx):
    i = c.inner
    long_x = i.w >= i.d
    n = max(1, int((i.w if long_x else i.d) / 22))
    for k in range(n):
        if long_x:
            x, y = i.x0 + (k + 0.5) * i.w / n, i.cy
            yaw = 0.0
        else:
            x, y = i.cx, i.y0 + (k + 0.5) * i.d / n
            yaw = HALF_PI
        lift = c.at("car_lift", x, y, yaw, check=True, clearance=0.5)
        if lift and c.room.kind == "garage_bay":
            car = c.pick(["car_sedan", "car_pickup_old", "car_suv", "car_compact", "car_van"])
            c.at(car, x, y, yaw, {"$car": c.pick(pal.CAR_PAINTS)}, z=3.3, check=False)
    for nm in ("tool_cabinet", "workbench", "tire_rack", "air_compressor", "oil_drums_rack",
               "spare_parts_shelf", "tool_chest_roll", "engine_hoist", "welding_cart",
               "engine_block", "tire_stack"):
        c.wall(nm, align="random", channels={"$metal": c.pick(["metal_red", "metal_blue"])})
    c.decor("pegboard_tools", 3.0)
    c.decor("safety_sign", 0.0)
    c.decor("fire_extinguisher", 0.0)
    c.ceiling("highbay_light", spacing=18)


@rule("parts")
def r_parts(c: RoomCtx):
    c.wall("parts_counter", sides=[c.far_side()], clear_front=3)
    c.wall("spare_parts_shelf", align="random")
    c.wall("tire_rack", align="random")
    c.wall("waiting_chairs", channels={"$fabric": "vinyl_red"})
    c.wall("vending_machine", channels={"$plastic": "plastic_red"})
    c.decor("calendar_wall", 0.0)
    c.ceiling("fluor_strip")


@rule("warehouse", "loading")
def r_warehouse(c: RoomCtx):
    i = c.inner
    if c.room.kind == "warehouse":
        long_x = i.w >= i.d
        area = i.inset(6.0, 10.0, 6.0, 6.0)
        c.grid("pallet_rack", area=area, yaw=0.0 if long_x else HALF_PI, gap_x=11.0 if not long_x
               else 2.0, gap_y=2.0 if not long_x else 11.0, limit=24)
    for _ in range(3):
        c.center(c.pick(["pallet_boxes", "pallet_boxes_tall", "pallet_sacks", "pallet_drums",
                         "ibc_tote", "crate_stack"]), clearance=2.5)
    fl = c.center("forklift", clearance=2.0)
    if fl:
        from ..records import Marker
        c.B.out.markers.append(Marker("vehicle", fl.x, fl.y, fl.z, fl.yaw, "forklift"))
    c.wall("pallet_jack", align="random")
    c.wall("workbench", align="random")
    c.wall("barrels_group", align="random")
    c.decor("safety_sign", 0.0)
    c.decor("fire_extinguisher", 0.0)
    c.ceiling("highbay_light", spacing=20, max_n=24)


@rule("factory_floor")
def r_factory(c: RoomCtx):
    i = c.inner
    machines = ["cnc_machine", "lathe", "drill_press", "conveyor", "mixer_vat", "tank_vertical",
                "control_panel", "industrial_boiler"]
    if "cannery" in c.B.p.tags:
        machines = ["conveyor", "conveyor", "mixer_vat", "mixer_vat", "tank_vertical",
                    "control_panel", "steel_counter", "conveyor"]
    for nm in machines:
        c.center(nm, clearance=4.0)
    c.center("pipe_rack", clearance=1.0)
    for _ in range(3):
        c.wall(c.pick(["pallet_boxes", "barrels_group", "ibc_tote", "crate_stack",
                       "spare_parts_shelf"]), align="random")
    c.decor("safety_sign", 0.0)
    c.decor("pipes_wall", 2.0)
    c.decor("electrical_panel", 0.0)
    c.ceiling("highbay_light", spacing=18, max_n=24)


@rule("control_room", "dispatch", "security")
def r_control(c: RoomCtx):
    c.wall("radio_dispatch", sides=[c.far_side()])
    c.wall("control_panel", align="random")
    c.wall("server_rack", align="random")
    c.wall("file_cabinet", channels={"$metal": "metal_gray"})
    c.wall("coffee_station", channels={"$paint": "wood_white"}, align="random")
    c.decor("map_board", 4.0)
    c.ceiling("fluor_panel")


@rule("locker", "gear")
def r_locker(c: RoomCtx):
    k = c.room.kind
    if k == "gear":
        for _ in range(3):
            c.wall("gear_rack", align="random")
        c.wall("scba_rack", align="random")
        c.decor("hose_rack", 0.0)
    else:
        for _ in range(4):
            c.wall("locker_row", align="random",
                   channels={"$metal": c.pick(["metal_gray", "metal_blue", "metal_green"])})
        c.center("locker_bench", clearance=1.5)
    c.ceiling("fluor_panel")


@rule("mechanical", "electrical")
def r_mech(c: RoomCtx):
    c.wall("boiler")
    c.wall("water_heater")
    c.decor("electrical_panel", 0.0)
    c.decor("electrical_panel", 0.0)
    c.decor("pipes_wall", 1.0)
    c.wall("server_rack" if c.room.kind == "electrical" else "furnace", align="random")
    c.ceiling("fluor_strip", max_n=2)


@rule("cell", "holding")
def r_cell(c: RoomCtx):
    c.wall("cell_bench", sides=[c.far_side()], avoid_windows=False)
    c.wall("cell_toilet", align="end", avoid_windows=False)
    c.ceiling("fluor_panel", max_n=1)


@rule("interview")
def r_interview(c: RoomCtx):
    t = c.center("interview_table", clearance=1.0)
    if t:
        c.at("dining_chair", t.x, t.y - 2.4, 0.0, {"$wood": "metal_gray"}, check=False)
        c.at("dining_chair", t.x - 1.0, t.y + 2.4, math.pi, {"$wood": "metal_gray"}, check=False)
        c.at("dining_chair", t.x + 1.2, t.y + 2.4, math.pi, {"$wood": "metal_gray"}, check=False)
    c.decor("mirror_wall", 3.0)
    c.decor("clock_wall", 7.5)
    c.ceiling("fluor_panel", max_n=1)


@rule("evidence")
def r_evidence(c: RoomCtx):
    for _ in range(4):
        c.wall("evidence_cage", align="random")
    c.center("boxes_stack", clearance=1.5)
    c.wall("safe_box", align="random")
    c.ceiling("fluor_panel")


@rule("sallyport", "apparatus", "parking")
def r_vehicle_bay(c: RoomCtx):
    tags = c.B.p.tags
    i = c.inner
    if c.room.kind == "apparatus":
        trucks = ["fire_engine", "ladder_truck", "ambulance", "fire_engine"]
    elif c.room.kind == "sallyport":
        trucks = ["police_cruiser", "police_suv", "police_cruiser"]
    else:
        trucks = []
    doors = [o for s in "NSWE" for o in c.openings[s] if o["kind"] == "door" and
             o.get("door") in ("bay", "garage", "garage2", "rollup", "rollup_small")]
    from ..records import Marker
    k = 0
    for o in doors:
        if k >= len(trucks):
            break
        u = (o["u0"] + o["u1"]) / 2
        name = trucks[k]
        size = KIT[name].size
        if o["side"] in "SN":
            x = u
            y = i.y0 + size[1] / 2 + 3.0 if o["side"] == "S" else i.y1 - size[1] / 2 - 3.0
            yaw = 0.0 if o["side"] == "S" else math.pi
        else:
            y = u
            x = i.x0 + size[1] / 2 + 3.0 if o["side"] == "W" else i.x1 - size[1] / 2 - 3.0
            yaw = -HALF_PI if o["side"] == "W" else HALF_PI
        p = c.at(name, x, y, yaw, check=True, clearance=0.3, ignore_doors=True)
        if p:
            c.B.out.markers.append(Marker("vehicle", p.x, p.y, p.z, p.yaw, name,
                                          {"service": c.room.kind}))
            k += 1
    if c.room.kind == "apparatus":
        c.wall("gear_rack", align="random")
        c.decor("hose_rack", 0.0)
    c.wall("tool_cabinet", align="random", channels={"$metal": "metal_red"})
    c.wall("spare_parts_shelf", align="random")
    c.decor("fire_extinguisher", 0.0)
    c.ceiling("highbay_light", spacing=18)


@rule("lounge")
def r_lounge(c: RoomCtx):
    s = c.wall("sofa_3", channels={"$fabric": c.pick(pal.FABRICS_CHEAP)})
    if s:
        c.in_front(s, "coffee_table", 1.2)
        tv = c.facing(s, "tv_stand")
        if tv:
            c.on(tv, "tv_flat")
    c.wall("recliner", channels={"$fabric": "leather_brown"})
    c.wall("recliner", channels={"$fabric": "fabric_brown"})
    c.wall("bookshelf")
    c.wall("arcade_cabinet", channels={"$plastic": "plastic_red"}, align="random")
    c.decor("dartboard", 4.0)
    c.ceiling("ceiling_light")


@rule("dorm")
def r_dorm(c: RoomCtx):
    c.grid("bed_single", area=c.inner.inset(1.5, 1.5, 1.5, 4.5), yaw=math.pi, gap_x=3.0,
           gap_y=6.0, limit=8, channels={"$sheet": "sheet_gray", "$wood": "metal_dark"})
    for _ in range(2):
        c.wall("locker_row", channels={"$metal": "metal_gray"}, align="random")
    c.window_dressing("blinds_closed")
    c.ceiling("ceiling_light")


@rule("motel_room")
def r_motel_room(c: RoomCtx):
    worn = c.cheap or "worn" in c.room.tags
    sheet = {"$sheet": c.pick(["sheet_white", "sheet_white", "sheet_yellow", "sheet_blue"]),
             "$wood": c.pick(["wood", "wood_dark", "wood_light"])}
    two = c.area > 210 and c.chance(0.5)
    bed = place_primary(c, ["bed_double", "bed_single"], channels=sheet, clear_front=2.5)
    if bed:
        ns = c.beside(bed, "nightstand", "right" if two else "both", channels={"$wood": sheet["$wood"]})
        for n in ns[:1]:
            c.on(n, "table_lamp")
        if two:
            b2 = c.wall("bed_double", sides=[bed.side], channels=sheet, clear_front=2.5)
        c.decor("picture_large", 6.0, sides=[bed.side], u=(bed.u0 + bed.u1) / 2,
                channels={"$fabric": "fabric_teal", "$fabric2": "fabric_orange",
                          "$wood": "wood_dark"})
        dr = c.facing(bed, "dresser", channels={"$wood": sheet["$wood"]})
        if dr:
            c.on(dr, "tv_crt" if worn else "tv_flat")
    t = c.center("side_table", channels={"$wood": sheet["$wood"]}, clearance=1.5)
    if t:
        c.at("dining_chair", t.x + 1.6, t.y, -HALF_PI, {"$wood": sheet["$wood"]}, check=True)
    c.wall("luggage_rack", channels={"$wood": sheet["$wood"]}, align="random")
    if c.chance(0.6):
        c.wall(c.pick(["suitcase", "duffel_bag"]), align="random",
               channels={"$fabric": c.pick(pal.FABRICS)})
    if worn and c.chance(0.5):
        c.clutter(1, ("trash_bags", "clutter_pile", "boxes_stack"))
    c.window_dressing("curtains", channels={"$fabric": c.pick(["fabric_orange", "fabric_teal",
                                                                "fabric_mustard", "fabric_brown"])})
    c.ceiling("ceiling_light", max_n=1)


@rule("motel_office")
def r_motel_office(c: RoomCtx):
    r_reception(c)


@rule("vending")
def r_vending(c: RoomCtx):
    c.wall("ice_vending_alcove", avoid_windows=False)
    c.wall("snack_machine", avoid_windows=False)
    c.ceiling("fluor_panel", max_n=1)


@rule("boat_storage")
def r_boat_storage(c: RoomCtx):
    i = c.inner
    boats = ["boat_motor", "boat_sail", "boat_dinghy", "boat_motor", "boat_pontoon"]
    for nm in boats:
        p = c.center(nm, clearance=2.5, channels={"$hull": c.pick(pal.HULLS),
                                                  "$fabric": "fabric_white"})
        if p and nm != "boat_pontoon":
            c.at("boat_trailer", p.x, p.y, p.yaw, check=False, record=False)
    c.wall("kayak_rack", align="random")
    c.wall("outboard_stand", align="random")
    c.wall("workbench", align="random")
    c.wall("buoy_stack", align="random")
    c.decor("life_ring", 0.0)
    c.ceiling("highbay_light", spacing=20)


@rule("marina_shop")
def r_marina_shop(c: RoomCtx):
    c.wall("bait_fridge", sides=[c.far_side()])
    co = c.wall("checkout_counter", align="start", clear_front=2.0, channels={"$wood": "wood"})
    c.grid("shelf_gondola", area=c.inner.inset(5.0, 8.0, 5.0, 6.0), yaw=HALF_PI, gap_x=6.0,
           gap_y=4.0, limit=4)
    c.wall("kayak_rack", align="random")
    c.wall("buoy_stack", align="random")
    c.decor("life_ring", 0.0)
    c.decor("map_board", 4.0)
    c.ceiling("fluor_panel", spacing=12)


@rule("fish_processing")
def r_fish(c: RoomCtx):
    for _ in range(3):
        c.center("steel_counter", clearance=2.5)
    c.center("conveyor", clearance=2.5)
    for _ in range(4):
        c.wall(c.pick(["fish_crates", "ice_bin_fish", "net_pile", "pallet_boxes", "barrels_group"]),
               align="random")
    c.wall("prep_sink", align="random")
    c.center("forklift", clearance=2.0)
    c.ceiling("highbay_light", spacing=18)


@rule("storage_corridor")
def r_storage_corridor(c: RoomCtx):
    c.ceiling("fluor_strip", spacing=14, max_n=12)


@rule("storage_unit")
def r_storage_unit(c: RoomCtx):
    if "empty" in c.room.tags:
        return
    for _ in range(c.rng.randint(1, 3)):
        c.wall(c.pick(["boxes_moving", "boxes_stack", "sofa_2", "dresser", "bicycle",
                       "clutter_pile", "crate_stack", "tire_stack", "mattress_floor"]),
               align="random", channels={"$fabric": c.pick(pal.FABRICS), "$wood": c.wood(),
                                         "$plastic": "plastic_red", "$sheet": "sheet_gray"})
    if c.chance(0.15):
        c.center(c.pick(["car_wreck", "motorcycle", "car_coupe"]), clearance=0.5,
                 channels={"$car": c.pick(pal.CAR_PAINTS)})


@rule("lantern", "projection", "stair", "unit_closet_none", "void", "chapel")
def r_minimal(c: RoomCtx):
    c.ceiling("ceiling_light", max_n=2)


def _generic(c: RoomCtx):
    c.wall("boxes_stack", align="random")
    c.wall("shelf_low", align="random")
    c.ceiling("ceiling_light")


# =============================================================================

SCHEDULE_BY_FAMILY = {
    "res": "res", "biz": "biz", "late": "late", "work": "work", "always": "always",
    "dark": "dark",
}


def furnish_building(B):
    p = B.p
    # str hash() is salted per process; crc32 keeps interiors identical between runs
    rng = random.Random(zlib.crc32(f"{p.name}|{p.w}|{p.d}|{len(p.rooms)}".encode()))
    fam = "dark" if p.quality == "abandoned" else p.lighting
    for room in p.rooms:
        if not room.furnish:
            continue
        sched = SCHEDULE_BY_FAMILY.get(fam, "res")
        if "always_lit" in room.tags:
            sched = "always"
        if room.light == "none":
            sched = "dark"
        fn = RULES.get(room.kind, _generic)
        for L in room.levels():
            rect = room.main_rect(L)
            # only furnish the level where a multi-level space starts
            if (L - 1) in room.cells and any(r.overlaps(rect) for r in room.cells[L - 1]):
                continue
            c = RoomCtx(B, room, L, rect, random.Random(rng.random()), sched)
            if c.inner.w < 2 or c.inner.d < 2:
                continue
            if room.light and room.light != "none":
                orig = c.ceiling

                def forced(name=None, _o=orig, _l=room.light, **kw):
                    return _o(_l, **kw)
                c.ceiling = forced
            if room.light == "none":
                c.ceiling = lambda *a, **k: None
            try:
                fn(c)
            except Exception as e:  # keep the town building even if one rule misbehaves
                B.out.warnings.append(f"furnish {room.id}/{room.kind}: {e!r}")
            if p.detail >= 2 and room.kind not in ("closet", "unit_closet", "storage_unit",
                                                    "cell", "walkin", "stair", "pantry"):
                c.decor("light_switch", 0.0)


# --- specialised rooms added for landmarks -------------------------------------------

@rule("supermarket")
def r_supermarket(c: RoomCtx):
    i = c.inner
    back = c.far_side()
    for _ in range(12):
        if not c.wall("cooler_display", sides=[back], align="start", gap=0.05):
            break
    c.wall("deli_counter", sides=["W"], align="end", clear_front=3.0)
    c.wall("deli_counter", sides=["W"], align="end", clear_front=3.0)
    c.wall("pharmacy_counter", sides=["E"], align="end", clear_front=3.0)
    for _ in range(4):
        c.wall("shelf_wall_retail", sides=["E", "W"], align="random")
    # produce in the front-left, checkouts across the front
    front = {"N": "S", "S": "N", "W": "E", "E": "W"}[back]
    fy = i.y0 if front == "S" else i.y1
    sgn = 1 if front == "S" else -1
    n = max(4, int(i.w * 0.5 / 7.0))
    x0 = i.x0 + i.w * 0.35
    for k in range(n):
        x = x0 + k * 7.0
        if x > i.x1 - 20:
            break
        c.at("checkout_lane", x, fy + sgn * 16.0, 0.0 if sgn > 0 else math.pi, check=True)
    c.grid("produce_bin", area=Rect(i.x0 + 8, fy + 8 if sgn > 0 else fy - 40, i.x0 + i.w * 0.3,
                                    fy + 40 if sgn > 0 else fy - 8), gap_x=4, gap_y=4,
           limit=6)
    aisles = Rect(i.x0 + 10, (fy + 30) if sgn > 0 else i.y0 + 14, i.x1 - 14,
                  (i.y1 - 14) if sgn > 0 else fy - 30)
    if aisles.valid():
        c.grid("shelf_gondola", area=aisles, yaw=HALF_PI, gap_x=7.0, gap_y=6.0, limit=40)
    c.wall("shopping_carts", sides=[front], align="start", avoid_windows=False)
    c.decor("exit_sign", 10.0)
    c.ceiling("fluor_panel", spacing=14, max_n=40)


@rule("parking")
def r_parking(c: RoomCtx):
    """Painted stalls with parked cars; lights on a grid; ramps/stair holes stay clear."""
    i = c.inner
    rng = c.rng
    cars = ["car_sedan", "car_compact", "car_suv", "car_pickup", "car_van", "car_coupe",
            "car_wagon", "taxi"]
    stall_w = 9.0
    row_d = 18.0
    aisle = 24.0
    y = i.y0 + 1.0
    rowi = 0
    from ..records import Marker
    while y + row_d <= i.y1 - 1.0:
        facing = 0.0 if rowi % 2 == 0 else math.pi
        x = i.x0 + 1.0
        while x + stall_w <= i.x1 - 1.0:
            r = Rect(x, y, x + stall_w, y + row_d)
            if c.fits(r, 0.0, ignore_doors=False):
                # stall lines
                c.B.out.int.box("paint_line_white", x, y, c.z + 0.0, x + 0.25, y + row_d,
                                c.z + 0.05, False)
                if rng.random() < 0.6:
                    nm = rng.choice(cars)
                    p = c.at(nm, x + stall_w / 2, y + row_d / 2, facing,
                             {"$car": rng.choice(pal.CAR_PAINTS)}, check=False)
                    if p:
                        c.B.out.markers.append(Marker("vehicle", p.x, p.y, p.z, p.yaw, nm,
                                                      {"parked": True}))
                else:
                    c.B.out.markers.append(Marker("parking_spot", x + stall_w / 2,
                                                  y + row_d / 2, c.z, facing, "stall"))
                c.occ.append((r, 6.0))
            x += stall_w
        y += row_d + (aisle if rowi % 2 == 0 else 0.0)
        rowi += 1
    c.decor("exit_sign", 6.0)
    c.ceiling("fluor_strip", spacing=18, max_n=30)


@rule("radio_studio")
def r_radio_studio(c: RoomCtx):
    desk = c.wall("radio_dispatch", sides=[c.far_side()], clear_front=3.0)
    if desk:
        c.in_front(desk, "office_chair", -0.8, yaw_extra=math.pi,
                   channels={"$fabric": "leather_black"})
    c.wall("bookshelf", channels={"$wood": "wood_dark"})
    c.wall("bookshelf", channels={"$wood": "wood_dark"})
    c.wall("jukebox", align="random")
    s = c.wall("sofa_2", channels={"$fabric": "fabric_orange"})
    if s:
        c.in_front(s, "coffee_table", 1.0, channels={"$wood": "wood_dark"})
    c.wall("server_rack", align="random")
    c.wall("plant_pot", align="random")
    c.decor("picture_large", 5.5, channels={"$fabric": "fabric_teal", "$fabric2": "fabric_orange",
                                            "$wood": "wood_dark"})
    c.decor("clock_wall", 8.0)
    c.window_dressing("blinds", prob=0.6)
    c.ceiling("pendant_light", spacing=10)


@rule("lantern")
def r_lantern(c: RoomCtx):
    pass
