"""Turn a floor ``Plan`` into geometry, props, lights, markers and signs.

Pipeline (per building):
  1. derive wall *runs* per level from the room rectangles
  2. place doors (interior + exterior) as openings on runs
  3. place windows on exterior runs, aligned to facade bays, sized by the room
     behind them (bathrooms get small high windows, shops get storefronts ...)
  4. emit wall layers (facade skin outside, per-room paint inside) minus openings
  5. emit floor slabs / ceilings / foundations / roofs, with stair holes
  6. emit stairs, railings, roof structures and access bulkheads
  7. facade dressing: plinth, bands, cornice, awnings, signs, exterior lights
  8. furnish every room (see furnish.py)
"""

from __future__ import annotations

import math
import random

from ..geom import Sink, Rect, rot_x, rot_z, mat_mul, Xform, subtract_many
from ..records import PropPlace, LightRec, Marker, SignRec
from ..kit import KIT, WARM, NEUTRAL
from ..kit.doors import NOMINAL as DOOR_NOMINAL
from .plan import Plan, Room, Door

EXT_T = 1.0      # exterior wall total thickness
FAC_T = 0.8      # facade skin part of it
INT_T = 0.6      # interior wall thickness
SLAB = 1.0       # floor/ceiling sandwich thickness
FIN = 0.2        # floor finish layer
EPS = 0.05

DOOR_DIMS = {   # kind: (width, height, prop)
    "interior": (4.0, 7.6, "door_interior"),
    "exterior": (4.0, 7.6, "door_exterior"),
    "metal": (4.0, 7.6, "door_metal"),
    "glass": (4.0, 7.6, "door_glass"),
    "glass_double": (7.0, 7.6, "door_glass_double"),
    "double": (7.0, 7.6, "door_glass_double"),
    "opening": (5.0, 8.0, None),
    "arch": (8.0, 8.5, None),
    "garage": (10.0, 8.0, "door_garage"),
    "garage2": (16.0, 8.0, "door_garage"),
    "rollup": (12.0, 12.0, "door_rollup"),
    "rollup_small": (10.0, 10.0, "door_rollup"),
    "bay": (14.0, 14.0, "door_bay"),
    "sliding": (8.0, 7.6, "door_sliding_glass"),
    "cell": (4.0, 7.6, "door_cell"),
    "bifold": (4.0, 7.6, "door_bifold"),
}

# window policies: w = width, sill/head relative to the level floor (head is
# clamped to the clear height); "single" = at most one per run
POLICIES = {
    "res": dict(w=4.5, sill=3.0, head=8.6),
    "wide": dict(w=7.0, sill=2.6, head=8.6),
    "small": dict(w=2.6, sill=6.0, head=8.6, single=True),
    "office": dict(w=6.0, sill=2.6, head=9.2),
    "shop": dict(w=5.5, sill=2.4, head=9.4),
    "tall": dict(w=3.0, sill=2.4, head=9.6, single=True),
    "high": dict(w=8.0, sill=-5.0, head=-1.6),
    "highsmall": dict(w=4.0, sill=-4.0, head=-1.8),
    "storefront": dict(w=0, sill=1.0, head=10.5),
    "open": dict(w=0, sill=3.6, head=0.0),          # parking decks: open bays between columns
    "lantern": dict(w=0, sill=1.2, head=0.0),       # glass all round (lighthouse lantern)
    "none": None,
}

KIND_POLICY = {
    "living": "wide", "family": "wide", "bedroom": "res", "master": "res", "kids": "res",
    "kitchen": "res", "dining": "res", "kitchen_dining": "res", "study": "res", "entry": "small",
    "foyer": "tall", "hall": "small", "corridor": "small", "bathroom": "small",
    "halfbath": "small", "closet": None, "laundry": "small", "utility": None, "garage": "highsmall",
    "storage": None, "basement": None, "stair": "tall", "attic": "small", "pantry": None,
    "office": "office", "office_open": "office", "office_private": "office", "reception": "office",
    "meeting": "office", "breakroom": "res", "lobby": "shop", "waiting": "shop",
    "retail": "storefront", "shop": "storefront", "dining_room": "shop", "bar_main": "shop",
    "laundromat": "storefront", "showroom": "storefront", "pawn_floor": "storefront",
    "kitchen_pro": "highsmall", "stockroom": None, "walkin": None, "restroom": "small",
    "employee": "res", "warehouse": "high", "factory_floor": "high", "garage_bay": "high",
    "loading": "high", "control_room": "office", "locker": "highsmall", "mechanical": None,
    "electrical": None, "cell": None, "holding": None, "interview": None, "evidence": None,
    "bullpen": "office", "briefing": "office", "dispatch": "office", "sallyport": "high",
    "apparatus": "high", "dorm": "res", "lounge": "res", "chamber": "tall", "records": None,
    "motel_room": "res", "motel_office": "shop", "motel_bath": "small", "vending": None,
    "boat_storage": "high", "marina_shop": "storefront", "fish_processing": "high",
    "cold_storage": None, "storage_unit": None, "storage_corridor": None, "security": "office",
    "service_hall": "shop", "gear": "highsmall", "workshop": "high", "parts": "office",
    "unit_living": "wide", "unit_bedroom": "res", "unit_kitchen": "res", "unit_bath": "small",
    "unit_entry": None, "unit_closet": None, "lantern": "none", "studio": "res",
    "parking": None, "booth": "office", "chapel": "tall", "projection": "small",
}


class Built:
    """Output of building one plan (all in plan-local coordinates)."""

    def __init__(self, plan: Plan):
        self.plan = plan
        self.ext = Sink()
        self.int = Sink()
        self.props: list[PropPlace] = []
        self.lights: list[LightRec] = []
        self.markers: list[Marker] = []
        self.signs: list[SignRec] = []
        self.openings = {}      # (room, level) -> [dict]
        self.entrances = []     # dicts describing exterior doors
        self.warnings = []
        self.room_info = []


class Opening:
    __slots__ = ("u0", "u1", "z0", "z1", "kind", "door", "policy")

    def __init__(self, u0, u1, z0, z1, kind, door=None, policy=None):
        self.u0, self.u1, self.z0, self.z1 = u0, u1, z0, z1
        self.kind = kind
        self.door = door
        self.policy = policy


class Run:
    __slots__ = ("o", "c", "a", "b", "neg", "pos", "level", "openings")

    def __init__(self, o, c, a, b, neg, pos, level):
        self.o, self.c, self.a, self.b = o, c, a, b
        self.neg, self.pos = neg, pos
        self.level = level
        self.openings: list[Opening] = []

    @property
    def exterior(self):
        return self.neg is None or self.pos is None

    @property
    def room(self):
        return self.pos if self.neg is None else self.neg

    @property
    def length(self):
        return self.b - self.a

    @property
    def side(self):
        """Building side this exterior run faces."""
        if self.o == "H":
            return "front" if self.neg is None else "back"
        return "left" if self.neg is None else "right"

    @property
    def out_dir(self):
        """+1 if the outside is on the positive side of the run line."""
        return 1 if self.pos is None else -1

    def point(self, u, offset=0.0, z=0.0):
        """Plan point at coordinate ``u`` along the run, ``offset`` along +normal axis."""
        if self.o == "H":
            return (u, self.c + offset, z)
        return (self.c + offset, u, z)

    def free(self, u0, u1, pad=0.3):
        for op in self.openings:
            if u0 < op.u1 + pad and op.u0 - pad < u1:
                return False
        return True


# -----------------------------------------------------------------------------

class Builder:
    def __init__(self, plan: Plan, seed=0):
        self.p = plan
        self.rng = random.Random(seed)
        self.out = Built(plan)
        self.cells = {}           # level -> [(Rect, room_id)]
        self.rooms = {r.id: r for r in plan.rooms}
        for r in plan.rooms:
            for L, rs in r.cells.items():
                for rc in rs:
                    self.cells.setdefault(L, []).append((rc, r.id))
        self.runs = {}            # level -> [Run]
        self.levels = plan.all_levels()

    # -- queries ---------------------------------------------------------------
    def room_at(self, L, x, y):
        for rc, rid in self.cells.get(L, ()):
            if rc.x0 < x < rc.x1 and rc.y0 < y < rc.y1:
                return rid
        return None

    def inside(self, L, x, y):
        return self.room_at(L, x, y) is not None

    def z(self, L):
        return self.p.level_z(L)

    def h(self, L):
        return self.p.level_h(L)

    # -- 1. runs -----------------------------------------------------------------
    def derive_runs(self):
        for L in self.levels:
            cells = self.cells.get(L, [])
            xs = sorted({r.x0 for r, _ in cells} | {r.x1 for r, _ in cells})
            ys = sorted({r.y0 for r, _ in cells} | {r.y1 for r, _ in cells})
            atoms = {}

            def add(o, c, lo, hi, rid, which):
                bps = [v for v in (xs if o == "H" else ys) if lo + 1e-6 < v < hi - 1e-6]
                pts = [lo] + bps + [hi]
                for i in range(len(pts) - 1):
                    key = (o, c, pts[i], pts[i + 1])
                    ent = atoms.setdefault(key, [None, None])
                    ent[0 if which == "neg" else 1] = rid

            for rc, rid in cells:
                add("H", rc.y0, rc.x0, rc.x1, rid, "pos")
                add("H", rc.y1, rc.x0, rc.x1, rid, "neg")
                add("V", rc.x0, rc.y0, rc.y1, rid, "pos")
                add("V", rc.x1, rc.y0, rc.y1, rid, "neg")
            runs = []
            for key in sorted(atoms):
                o, c, a, b = key
                neg, pos = atoms[key]
                if neg == pos:
                    continue
                if runs:
                    last = runs[-1]
                    if (last.o == o and abs(last.c - c) < 1e-6 and abs(last.b - a) < 1e-6
                            and last.neg == neg and last.pos == pos):
                        last.b = b
                        continue
                runs.append(Run(o, c, a, b, neg, pos, L))
            self.runs[L] = runs

    # -- helpers for wall extents ---------------------------------------------------
    def end_kind(self, run, at_start):
        """'concave' if the footprint continues past this end on the inside, else 'flush'."""
        L = run.level
        u = run.a - 0.3 if at_start else run.b + 0.3
        if run.exterior:
            inward = -run.out_dir * 0.5
            p = run.point(u, inward)
            return "concave" if self.inside(L, p[0], p[1]) else "flush"
        p = run.point(u, 0.0)
        return "interior" if self.inside(L, p[0], p[1]) else "exterior"

    def rect_inset(self, L, rc, rid):
        """Inner faces of a room rectangle (distance from each edge to the wall face)."""
        def side_inset(pts):
            best = 0.0
            for (x, y) in pts:
                other = self.room_at(L, x, y)
                if other is None:
                    best = max(best, EXT_T)
                elif other != rid:
                    best = max(best, INT_T / 2)
            return best
        e = 0.15
        xs = [rc.x0 + rc.w * f for f in (0.2, 0.5, 0.8)]
        ys = [rc.y0 + rc.d * f for f in (0.2, 0.5, 0.8)]
        left = side_inset([(rc.x0 - e, y) for y in ys])
        right = side_inset([(rc.x1 + e, y) for y in ys])
        front = side_inset([(x, rc.y0 - e) for x in xs])
        back = side_inset([(x, rc.y1 + e) for x in xs])
        return left, front, right, back

    def inner_rect(self, L, rid, rc=None):
        rc = rc or self.rooms[rid].main_rect(L)
        l, f, r, b = self.rect_inset(L, rc, rid)
        return Rect(rc.x0 + l, rc.y0 + f, rc.x1 - r, rc.y1 - b)

    def continues_above(self, L, x, y, rid):
        return (L + 1) in self.cells and self.room_at(L + 1, x, y) == rid

    # -- 2. doors ------------------------------------------------------------------
    def place_doors(self):
        for d in self.p.doors:
            self._place_door(d)

    def _place_door(self, d: Door):
        L = d.level
        runs = self.runs.get(L, [])
        w, h, _ = DOOR_DIMS.get(d.kind, DOOR_DIMS["interior"])
        if d.width:
            w = d.width
        if d.height:
            h = d.height
        clear = self.h(L) - SLAB - 0.4
        h = min(h, clear)
        if d.b is None:
            cands = [r for r in runs if r.exterior and r.room == d.a and
                     (d.side is None or r.side == d.side) and r.side not in self.p.facade.blind]
        else:
            cands = [r for r in runs if not r.exterior and {r.neg, r.pos} == {d.a, d.b}]
        if not cands:
            self.out.warnings.append(f"no wall for door {d.a}->{d.b} L{L} {d.side}")
            return
        margin = 1.4 if d.b is None else 1.0
        if d.at is not None:
            def score(r):
                if r.a + margin <= d.at <= r.b - margin:
                    return -r.length
                return min(abs(d.at - r.a), abs(d.at - r.b)) * 10
            cands.sort(key=score)
        else:
            cands.sort(key=lambda r: -r.length)
        for run in cands:
            avail = run.length - 2 * margin
            ww = w
            if avail < ww:
                if avail < 3.0:
                    continue
                ww = avail
            lo, hi = run.a + margin + ww / 2, run.b - margin - ww / 2
            if d.at is not None:
                centre = min(hi, max(lo, d.at))
            else:
                centre = (lo + hi) / 2
                if d.b is not None and run.length > 3 * ww and d.kind == "interior":
                    # interior doors sit near a corner, like real rooms
                    centre = self.rng.choice([lo, (lo + hi) / 2, hi])
            # dodge other openings
            pos = None
            for delta in [0, 2, -2, 4, -4, 6, -6, 8, -8, 11, -11, 14, -14]:
                c = centre + delta
                if lo - 1e-6 <= c <= hi + 1e-6 and run.free(c - ww / 2, c + ww / 2, 0.8):
                    pos = c
                    break
            if pos is None:
                continue
            op = Opening(pos - ww / 2, pos + ww / 2, 0.0, h, "door", d)
            run.openings.append(op)
            self._emit_door(run, op, d)
            return
        self.out.warnings.append(f"door {d.a}->{d.b} L{L} did not fit")

    def _emit_door(self, run, op, d):
        L = run.level
        z0 = self.z(L)
        w = op.u1 - op.u0
        uc = (op.u0 + op.u1) / 2
        prop = DOOR_DIMS.get(d.kind, DOOR_DIMS["interior"])[2]
        if run.exterior:
            plane = run.c - run.out_dir * EXT_T / 2
        else:
            plane = run.c
        x, y = (uc, plane) if run.o == "H" else (plane, uc)
        if run.exterior:
            yaw = {"front": 0.0, "back": math.pi, "left": -math.pi / 2,
                   "right": math.pi / 2}[run.side]
        else:
            yaw = 0.0 if run.o == "H" else math.pi / 2
        if prop:
            nw, nh = DOOR_NOMINAL[prop]
            q = self.p.quality
            ch = {}
            if prop in ("door_interior", "door_bifold"):
                ch["$paint"] = "door_white" if q in ("nice", "normal") and self.rng.random() < 0.6 \
                    else "door_wood"
            elif prop == "door_exterior":
                ch["$paint"] = self.rng.choice(["door_red", "door_green", "door_blue", "door_wood",
                                                "door_white", "door_mustard"])
            elif prop in ("door_garage", "door_bay"):
                ch["$paint"] = "garage_door" if prop == "door_garage" else "fire_red" \
                    if "fire" in self.p.tags else "garage_door"
            elif prop == "door_metal":
                ch["$metal"] = "door_metal_dark" if self.rng.random() < 0.4 else "door_metal"
            meta = {"door": d.kind, "rooms": [d.a, d.b], "hinge": -w / 2,
                    "locked": d.locked, "role": d.role or ("interior" if d.b else "exterior"),
                    "width": w, "height": op.z1}
            self.out.props.append(PropPlace(prop, x, y, z0, yaw, (w / nw, 1.0, op.z1 / nh),
                                            ch, interior=not run.exterior, room=d.a, meta=meta))
        # casings
        trim = self.p.facade.trim if run.exterior else ("wood_dark" if self.p.quality == "cheap"
                                                       else "trim_white")
        self._casing(run, op, trim)
        if run.exterior:
            side = run.side
            nx, ny = {"front": (0, -1), "back": (0, 1), "left": (-1, 0), "right": (1, 0)}[side]
            mx, my = x + nx * 3.5, y + ny * 3.5
            role = d.role or ("garage" if d.kind in ("garage", "garage2") else
                              "service" if d.kind in ("metal", "rollup", "rollup_small") else "main")
            myaw = math.atan2(nx, -ny)
            self.out.markers.append(Marker("entrance", mx, my, z0, myaw, role,
                                           {"room": d.a, "door": d.kind, "level": L}))
            self.out.entrances.append({"room": d.a, "side": side, "role": role, "kind": d.kind,
                                       "x": x, "y": y, "z": z0, "w": w, "level": L})
            if self.p.detail >= 2 and d.kind not in ("garage", "garage2", "bay", "rollup",
                                                     "rollup_small", "opening", "arch"):
                lz = z0 + op.z1 + 0.6
                fx, fy = x + nx * (0.5), y + ny * (0.5)
                if run.o == "H":
                    fx = x + (w / 2 + 0.8)
                else:
                    fy = y + (w / 2 + 0.8)
                self.out.props.append(PropPlace("wall_sconce", fx + nx * 0.6, fy + ny * 0.6, lz,
                                                yaw, interior=False))
                self.out.lights.append(LightRec(fx + nx * 1.4, fy + ny * 1.4, lz + 0.4, WARM, 16,
                                                0.8, "point", "night"))
        for rid in (d.a, d.b):
            if rid:
                self._register_opening(run, op, rid, "door")

    def _register_opening(self, run, op, rid, kind):
        if run.o == "H":
            side = "S" if run.pos == rid else "N"
        else:
            side = "W" if run.pos == rid else "E"
        self.out.openings.setdefault((rid, run.level), []).append(
            {"side": side, "u0": op.u0, "u1": op.u1, "z0": op.z0, "z1": op.z1, "kind": kind,
             "c": run.c, "o": run.o, "exterior": run.exterior,
             "door": op.door.kind if op.door else None})

    # -- 3. windows ----------------------------------------------------------------
    def place_windows(self):
        f = self.p.facade
        for L in self.levels:
            for run in self.runs.get(L, []):
                if not run.exterior or run.side in f.blind:
                    continue
                room = self.rooms[run.room]
                if L < 0:
                    continue
                pol_name = room.window
                if isinstance(pol_name, dict):
                    pol_name = pol_name.get(L, pol_name.get("default", "none"))
                pol_name = pol_name or KIND_POLICY.get(room.kind, "res")
                if pol_name == "storefront" and not (L == 0 and run.side in f.storefront):
                    pol_name = "shop"
                if pol_name is None or pol_name == "none":
                    continue
                pol = POLICIES[pol_name]
                if pol is None:
                    continue
                clear = self.h(L) - SLAB
                if pol_name == "storefront":
                    self._storefront(run, clear)
                    continue
                if pol_name in ("open", "lantern"):
                    self._open_bays(run, clear, pol_name)
                    continue
                w = f.window_w if (f.window_w and pol_name in ("res", "office", "shop")) else pol["w"]
                sill, head = pol["sill"], pol["head"]
                if sill < 0:
                    sill = clear + sill
                if head < 0:
                    head = clear + head
                head = min(head, clear - 1.2)
                if head - sill < 1.5:
                    continue
                margin = w / 2 + 1.3
                lo, hi = run.a + margin, run.b - margin
                if hi < lo - 1e-6:
                    if run.length >= w + 2.2 and pol.get("single"):
                        lo = hi = (run.a + run.b) / 2
                    else:
                        continue
                side_len = self.p.w if run.side in ("front", "back") else self.p.d
                n = max(1, int(round(side_len / f.bay)))
                bay = side_len / n
                centres = [(i + 0.5) * bay for i in range(n)]
                centres = [c for c in centres if lo - 1e-6 <= c <= hi + 1e-6]
                if not centres:
                    centres = [(lo + hi) / 2]
                if pol.get("single"):
                    centres = [min(centres, key=lambda c: abs(c - (lo + hi) / 2))]
                for c0 in centres:
                    for dc in (0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0, 3.0, -3.0, 4.0,
                               -4.0, 5.0, -5.0, 6.0, -6.0):
                        c = c0 + dc
                        if lo - 1e-6 <= c <= hi + 1e-6 and run.free(c - w / 2, c + w / 2, 0.8):
                            op = Opening(c - w / 2, c + w / 2, sill, head, "window", None,
                                         pol_name)
                            run.openings.append(op)
                            self._register_opening(run, op, run.room, "window")
                            break

    def _storefront(self, run, clear):
        head = min(POLICIES["storefront"]["head"], clear - 1.4)
        doors = sorted([op for op in run.openings if op.kind == "door"], key=lambda o: o.u0)
        segs = []
        u = run.a + 1.3
        for d in doors:
            if d.u0 - 0.5 - u > 2.5:
                segs.append((u, d.u0 - 0.5))
            u = d.u1 + 0.5
        if run.b - 1.3 - u > 2.5:
            segs.append((u, run.b - 1.3))
        for (u0, u1) in segs:
            op = Opening(u0, u1, 1.0, head, "storefront", None, "storefront")
            run.openings.append(op)
            self._register_opening(run, op, run.room, "storefront")
        # transoms over doors in a storefront
        for d in doors:
            if head - d.z1 > 1.2:
                op = Opening(d.u0, d.u1, d.z1 + 0.4, head, "transom", None, "storefront")
                run.openings.append(op)

    def _open_bays(self, run, clear, pol_name):
        """Column-and-bay openings (parking decks) or continuous glazing (lantern room)."""
        pol = POLICIES[pol_name]
        sill = pol["sill"]
        head = clear - 0.6 if pol_name == "lantern" else clear
        doors = sorted([op for op in run.openings if op.kind == "door"], key=lambda o: o.u0)
        segs = []
        u = run.a + 1.0
        for d in doors:
            if d.u0 - 0.7 - u > 2.0:
                segs.append((u, d.u0 - 0.7))
            u = d.u1 + 0.7
        if run.b - 1.0 - u > 2.0:
            segs.append((u, run.b - 1.0))
        kind = "storefront" if pol_name == "lantern" else "open"
        for (a, b) in segs:
            n = max(1, int(round((b - a) / 10.0)))
            step = (b - a) / n
            for i in range(n):
                u0 = a + i * step + (0.7 if i > 0 else 0.0)
                u1 = a + (i + 1) * step - (0.7 if i < n - 1 else 0.0)
                if u1 - u0 < 1.5:
                    continue
                op = Opening(u0, u1, sill, head, kind, None, pol_name)
                run.openings.append(op)
                self._register_opening(run, op, run.room, "window" if kind == "storefront"
                                       else "open")

    # -- 4. walls --------------------------------------------------------------------
    def emit_walls(self):
        for L in self.levels:
            for run in self.runs.get(L, []):
                if run.exterior:
                    self._ext_wall(run)
                else:
                    self._int_wall(run)

    def _ext_wall(self, run):
        L = run.level
        z0 = self.z(L)
        h = self.h(L)
        f = self.p.facade
        side = run.side
        if L < 0:
            mat = "concrete"
        elif side in f.side_mats:
            mat = f.side_mats[side]
        elif L == 0 and f.ground:
            mat = f.ground
        else:
            mat = f.mat
        od = run.out_dir
        # side walls (V) stop short of convex corners so the front/back (H) walls own the
        # corner block -- no coplanar overlap on the outer faces
        ea = eb = 0.0
        if run.o == "V":
            if self.line_end_convex(L, run.o, run.c, run.a, od, True):
                ea = -FAC_T
            if self.line_end_convex(L, run.o, run.c, run.b, od, False):
                eb = -FAC_T
        zb = z0 - (1.2 if L == self.p.lowest else 0.0)
        zt = z0 + h
        ops = run.openings
        # facade skin
        n0, n1 = sorted((run.c, run.c - od * FAC_T))
        for (u0, u1, za, zb_) in solid_rects(run.a - ea, run.b + eb, zb, zt, ops, z0):
            self._wallbox(self.out.ext, mat, run.o, u0, u1, n0, n1, za, zb_, True)
        # interior finish (per room rect actually behind it)
        room = self.rooms[run.room]
        paint = room.wall or "paint_cream"
        f0, f1 = sorted((run.c - od * FAC_T, run.c - od * EXT_T))
        mid = (run.a + run.b) / 2
        inner_pt = run.point(mid, -od * (EXT_T + 0.3))
        full = self.continues_above(L, inner_pt[0], inner_pt[1], run.room)
        top = zt if full else zt - SLAB
        for rc in room.rects(L):
            lo, hi = self._rect_span_on_run(L, rc, run)
            if hi - lo < 0.05:
                continue
            for (u0, u1, za, zb_) in solid_rects(lo, hi, z0, top, ops, z0):
                self._wallbox(self.out.int, paint, run.o, u0, u1, f0, f1, za, zb_, False)
            if self.p.detail >= 2 and room.kind not in ("garage", "warehouse", "factory_floor",
                                                          "storage", "utility", "mechanical",
                                                          "garage_bay", "apparatus", "loading",
                                                          "boat_storage", "sallyport", "parking"):
                self._baseboard(run, lo, hi, f0, f1, z0, ops, od)
        for op in ops:
            if op.kind == "window":
                self._window(run, op, mat)
            elif op.kind in ("storefront", "transom"):
                self._storefront_glass(run, op)

    def _rect_span_on_run(self, L, rc, run):
        """Portion of the run (u-range) that is the inner face of room rect ``rc``."""
        if run.o == "H":
            if not (abs(rc.y0 - run.c) < 1e-6 or abs(rc.y1 - run.c) < 1e-6):
                return (0, 0)
            l, f, r, b = self.rect_inset(L, rc, run.room)
            lo, hi = max(run.a, rc.x0 + l), min(run.b, rc.x1 - r)
        else:
            if not (abs(rc.x0 - run.c) < 1e-6 or abs(rc.x1 - run.c) < 1e-6):
                return (0, 0)
            l, f, r, b = self.rect_inset(L, rc, run.room)
            lo, hi = max(run.a, rc.y0 + f), min(run.b, rc.y1 - b)
        return (lo, hi)

    def _int_wall(self, run):
        L = run.level
        z0 = self.z(L)
        h = self.h(L)
        ra, rb = self.rooms[run.neg], self.rooms[run.pos]
        pa, pb = ra.wall or "paint_cream", rb.wall or "paint_cream"
        sa = 0.5 if self.end_kind(run, True) == "exterior" else 0.0
        sb = 0.5 if self.end_kind(run, False) == "exterior" else 0.0
        mid = (run.a + run.b) / 2
        pn = run.point(mid, -0.4)
        pp = run.point(mid, 0.4)
        full = (self.continues_above(L, pn[0], pn[1], run.neg) and
                self.continues_above(L, pp[0], pp[1], run.pos))
        top = z0 + (h if full else h - SLAB)
        ops = run.openings
        rects = solid_rects(run.a + sa, run.b - sb, z0, top, ops, z0)
        if pa == pb:
            for (u0, u1, za, zb) in rects:
                self._wallbox(self.out.int, pa, run.o, u0, u1, run.c - INT_T / 2,
                              run.c + INT_T / 2, za, zb, True)
        else:
            for (u0, u1, za, zb) in rects:
                self._wallbox(self.out.int, pa, run.o, u0, u1, run.c - INT_T / 2, run.c, za, zb,
                              True)
                self._wallbox(self.out.int, pb, run.o, u0, u1, run.c, run.c + INT_T / 2, za, zb,
                              True)
        if self.p.detail >= 2:
            for rid, sgn in ((run.neg, -1), (run.pos, 1)):
                rk = self.rooms[rid].kind
                if rk in ("garage", "warehouse", "factory_floor", "storage", "utility",
                          "mechanical", "garage_bay", "apparatus", "parking"):
                    continue
                face = run.c + sgn * INT_T / 2
                n0, n1 = sorted((face, face + sgn * 0.12))
                for (u0, u1, za, zb) in solid_rects(run.a + sa, run.b - sb, z0, z0 + 0.5, ops, z0):
                    self._wallbox(self.out.int, "trim_white" if self.p.quality != "cheap"
                                  else "wood_dark", run.o, u0, u1, n0, n1, za, zb, False)

    def _baseboard(self, run, lo, hi, f0, f1, z0, ops, od):
        face = run.c - od * EXT_T
        n0, n1 = sorted((face, face - od * 0.12))
        mat = "trim_white" if self.p.quality != "cheap" else "wood_dark"
        for (u0, u1, za, zb) in solid_rects(lo, hi, z0, z0 + 0.5, ops, z0):
            self._wallbox(self.out.int, mat, run.o, u0, u1, n0, n1, za, zb, False)

    @staticmethod
    def _wallbox(sink, mat, o, u0, u1, n0, n1, z0, z1, collide):
        if o == "H":
            sink.box(mat, u0, n0, z0, u1, n1, z1, collide)
        else:
            sink.box(mat, n0, u0, z0, n1, u1, z1, collide)

    def _casing(self, run, op, trim):
        L = run.level
        z0 = self.z(L)
        faces = []
        if run.exterior:
            od = run.out_dir
            faces.append((run.c, od))                     # outer face, protrude outward
            faces.append((run.c - od * EXT_T, -od))       # inner face
        else:
            faces.append((run.c + INT_T / 2, 1))
            faces.append((run.c - INT_T / 2, -1))
        cw = 0.45
        for face, sgn in faces:
            n0, n1 = sorted((face, face + sgn * 0.1))
            sink = self.out.ext if (run.exterior and sgn == run.out_dir) else self.out.int
            mat = trim
            self._wallbox(sink, mat, run.o, op.u0 - cw, op.u0, n0, n1, z0, z0 + op.z1, False)
            self._wallbox(sink, mat, run.o, op.u1, op.u1 + cw, n0, n1, z0, z0 + op.z1, False)
            self._wallbox(sink, mat, run.o, op.u0 - cw, op.u1 + cw, n0, n1, z0 + op.z1,
                          z0 + op.z1 + cw, False)

    def _window(self, run, op, wallmat):
        f = self.p.facade
        L = run.level
        z0 = self.z(L)
        od = run.out_dir
        outer = run.c
        inner = run.c - od * EXT_T
        za, zb = z0 + op.z0, z0 + op.z1
        fr = f.frame
        glass = f.glass if self.p.quality != "abandoned" else "glass_dirty"
        # glass pane in the wall's centre plane
        g0, g1 = sorted((run.c - od * (EXT_T / 2 - 0.06), run.c - od * (EXT_T / 2 + 0.06)))
        self._wallbox(self.out.ext, glass, run.o, op.u0, op.u1, g0, g1, za, zb, True)
        # frame ring (thin) around the glass
        t = 0.22
        f0, f1 = sorted((run.c - od * 0.25, run.c - od * 0.6))
        self._wallbox(self.out.ext, fr, run.o, op.u0, op.u0 + t, f0, f1, za, zb, False)
        self._wallbox(self.out.ext, fr, run.o, op.u1 - t, op.u1, f0, f1, za, zb, False)
        self._wallbox(self.out.ext, fr, run.o, op.u0 + t, op.u1 - t, f0, f1, zb - t, zb, False)
        self._wallbox(self.out.ext, fr, run.o, op.u0 + t, op.u1 - t, f0, f1, za, za + t, False)
        w = op.u1 - op.u0
        zm = None
        if (zb - za) > 4.5 and op.policy in ("res", "wide", "tall"):
            zm = za + (zb - za) * 0.55
            self._wallbox(self.out.ext, fr, run.o, op.u0 + t, op.u1 - t, f0, f1, zm - 0.1,
                          zm + 0.1, False)
        if w >= 4.4 and op.policy in ("res", "wide", "office", "shop"):
            cu = (op.u0 + op.u1) / 2
            spans = [(za + t, zb - t)] if zm is None else [(za + t, zm - 0.1), (zm + 0.1, zb - t)]
            for (m0, m1) in spans:
                self._wallbox(self.out.ext, fr, run.o, cu - 0.1, cu + 0.1, f0, f1, m0, m1, False)
        # sill outside + head trim
        s0, s1 = sorted((outer - od * 0.2, outer + od * 0.45))
        self._wallbox(self.out.ext, f.trim, run.o, op.u0 - 0.35, op.u1 + 0.35, s0, s1, za - 0.3,
                      za, False)
        if op.policy not in ("high", "highsmall"):
            h0, h1 = sorted((outer, outer + od * 0.18))
            self._wallbox(self.out.ext, f.trim, run.o, op.u0 - 0.3, op.u1 + 0.3, h0, h1, zb,
                          zb + 0.45, False)
        # shutters on houses
        if f.shutters and op.policy in ("res", "wide") and L >= 0:
            h0, h1 = sorted((outer, outer + od * 0.15))
            sw = min(1.8, w * 0.4)
            self._wallbox(self.out.ext, f.shutters, run.o, op.u0 - 0.3 - sw, op.u0 - 0.3, h0, h1,
                          za, zb, False)
            self._wallbox(self.out.ext, f.shutters, run.o, op.u1 + 0.3, op.u1 + 0.3 + sw, h0, h1,
                          za, zb, False)
        # interior window board
        b0, b1 = sorted((inner, inner - od * 0.35))
        self._wallbox(self.out.int, "trim_white" if self.p.quality != "cheap" else "wood",
                      run.o, op.u0 - 0.2, op.u1 + 0.2, b0, b1, za - 0.15, za, False)

    def _storefront_glass(self, run, op):
        L = run.level
        z0 = self.z(L)
        od = run.out_dir
        za, zb = z0 + op.z0, z0 + op.z1
        glass = "glass_store" if self.p.quality != "abandoned" else "glass_dirty"
        g0, g1 = sorted((run.c - od * 0.3, run.c - od * 0.42))
        self._wallbox(self.out.ext, glass, run.o, op.u0, op.u1, g0, g1, za, zb, True)
        f0, f1 = sorted((run.c - od * 0.15, run.c - od * 0.55))
        fr = "frame_alu" if self.p.facade.frame in ("trim_white", "frame_alu") else \
            self.p.facade.frame
        n = max(1, int(round((op.u1 - op.u0) / 5.0)))
        for i in range(n + 1):
            u = op.u0 + (op.u1 - op.u0) * i / n
            a, b = max(op.u0, u - 0.2), min(op.u1, u + 0.2)
            self._wallbox(self.out.ext, fr, run.o, a, b, f0, f1, za + 0.3, zb - 0.3, False)
        self._wallbox(self.out.ext, fr, run.o, op.u0, op.u1, f0, f1, zb - 0.3, zb, False)
        self._wallbox(self.out.ext, fr, run.o, op.u0, op.u1, f0, f1, za, za + 0.3, False)
        if op.kind == "storefront":
            k0, k1 = sorted((run.c, run.c + od * 0.12))
            self._wallbox(self.out.ext, self.p.facade.trim, run.o, op.u0, op.u1, k0, k1,
                          z0 - 0.3, za, False)

    # -- 5. slabs, foundations, roofs ---------------------------------------------------
    def emit_slabs(self):
        holes = {}  # level of the slab (upper level) -> [Rect]
        for s in self.p.stairs:
            target = (self.p.top + 1) if s.to_roof else s.level + 1
            holes.setdefault(target, []).append(s.rect)
        lv = self.levels
        for L in lv:
            zL = self.z(L)
            below = self.cells.get(L - 1, []) if (L - 1) in lv else []
            for rc, rid in self.cells.get(L, []):
                room = self.rooms[rid]
                pieces = [rc]
                for drc, did in below:
                    inter = rc.intersect(drc)
                    if inter is None:
                        continue
                    if did != rid:
                        for pc in subtract_many([inter], holes.get(L, [])):
                            self._slab_piece(L, pc, room, self.rooms[did])
                    pieces = subtract_many(pieces, [drc])
                for pc in subtract_many(pieces, holes.get(L, [])):
                    if L <= 0 or zL <= 0.5:
                        self._foundation(L, pc, room)
                    else:
                        self._soffit(L, pc, room)
        # roofs over every cell not covered from above
        for L in lv:
            above = self.cells.get(L + 1, [])
            for rc, rid in self.cells.get(L, []):
                pieces = subtract_many([rc], [a for a, _ in above])
                pieces = subtract_many(pieces, holes.get(L + 1, []))
                for pc in pieces:
                    self._roof_piece(L, pc, self.rooms[rid])

    def _inset_piece(self, L_list, pc, inset=FAC_T):
        def outside(x, y):
            return all(not self.inside(L, x, y) for L in L_list)
        e = 0.2
        l = inset if outside(pc.x0 - e, pc.cy) else 0.0
        r = inset if outside(pc.x1 + e, pc.cy) else 0.0
        f = inset if outside(pc.cx, pc.y0 - e) else 0.0
        b = inset if outside(pc.cx, pc.y1 + e) else 0.0
        return Rect(pc.x0 + l, pc.y0 + f, pc.x1 - r, pc.y1 - b)

    def _slab_piece(self, L, pc, upper: Room, lower: Room):
        z = self.z(L)
        p = self._inset_piece([L, L - 1], pc)
        if not p.valid():
            return
        self.out.int.box(lower.ceiling or "ceiling_white", p.x0, p.y0, z - SLAB, p.x1, p.y1,
                         z - FIN, True)
        self.out.int.box(upper.floor or "floor_wood", p.x0, p.y0, z - FIN, p.x1, p.y1, z, True)

    def _foundation(self, L, pc, room: Room):
        z = self.z(L)
        p = self._inset_piece([L], pc)
        if not p.valid():
            return
        self.out.int.box("concrete", p.x0, p.y0, z - 4.0, p.x1, p.y1, z - FIN, True)
        self.out.int.box(room.floor or "floor_concrete", p.x0, p.y0, z - FIN, p.x1, p.y1, z, True)

    def _soffit(self, L, pc, room: Room):
        z = self.z(L)
        p = self._inset_piece([L], pc, 0.0)
        self.out.ext.box(self.p.facade.trim, p.x0, p.y0, z - SLAB, p.x1, p.y1, z - FIN, True)
        self.out.int.box(room.floor or "floor_wood", p.x0, p.y0, z - FIN, p.x1, p.y1, z, True)

    def _roof_piece(self, L, pc, room: Room):
        zt = self.z(L) + self.h(L)
        p = self._inset_piece([L, L + 1], pc)
        if not p.valid():
            return
        self.out.int.box(room.ceiling or "ceiling_white", p.x0, p.y0, zt - SLAB, p.x1, p.y1,
                         zt - FIN, True)
        mat = self.p.roof.mat if self.p.roof.kind == "flat" or L < self.p.top else "roof_membrane"
        if L < self.p.top:
            mat = "roof_gravel" if self.p.roof.kind == "flat" else "roof_membrane"
        self.out.ext.box(mat, p.x0, p.y0, zt - FIN, p.x1, p.y1, zt, True)

    # -- 6. stairs ------------------------------------------------------------------------
    def emit_stairs(self):
        for s in self.p.stairs:
            if s.to_roof:
                L = self.p.top
            else:
                L = s.level
            z0 = self.z(L)
            h = self.h(L)
            rail = "metal_dark" if self.p.quality != "nice" else "wood_dark"
            tread_mat = self._stair_mat(s, L)
            if s.kind == "u":
                self._u_stair(s.rect, s.up, z0, h, tread_mat, rail)
            elif s.kind == "ramp":
                self._ramp(s.rect, s.up, z0, h)
            else:
                self._straight_stair(s.rect, s.up, z0, h, tread_mat, rail)
            rid = self.room_at(L, s.rect.cx, s.rect.cy)
            self.out.markers.append(Marker("stair", s.rect.cx, s.rect.cy, z0, 0.0,
                                           "to_roof" if s.to_roof else f"L{L}->L{L + 1}",
                                           {"room": rid}))
            if s.to_roof:
                self._bulkhead(s)
            else:
                self._hole_rails(s, L + 1, rail)

    def _stair_mat(self, s, L):
        rid = self.room_at(L, s.rect.cx, s.rect.cy)
        room = self.rooms.get(rid) if rid else None
        if room is None:
            return "concrete"
        f = room.floor or "floor_wood"
        if f.startswith("carpet") or f.startswith("floor_wood") or f.startswith("floor_lam"):
            return "floor_wood_dark" if self.p.quality != "cheap" else "floor_wood_worn"
        if f.startswith("floor_tile") or f.startswith("floor_vinyl") or f == "floor_terrazzo":
            return "floor_terrazzo" if self.p.quality == "nice" else "concrete_light"
        return "concrete"

    def _flight(self, x0, y0, x1, y1, axis, sign, za, zb, n, mat, rail):
        """Steps covering rect (x0..x1, y0..y1) rising from za to zb along axis*sign."""
        sink = self.out.int
        length = (y1 - y0) if axis == "y" else (x1 - x0)
        tread = length / n
        rise = (zb - za) / n
        for i in range(n):
            top = za + (i + 1) * rise
            bot = max(za, top - rise - 0.9)
            if axis == "y":
                if sign > 0:
                    a, b = y0 + i * tread, y0 + (i + 1) * tread
                else:
                    a, b = y1 - (i + 1) * tread, y1 - i * tread
                sink.box(mat, x0, a, bot, x1, b, top, True)
            else:
                if sign > 0:
                    a, b = x0 + i * tread, x0 + (i + 1) * tread
                else:
                    a, b = x1 - (i + 1) * tread, x1 - i * tread
                sink.box(mat, a, y0, bot, b, y1, top, True)
        # handrails (pitched bars) on both long sides
        ang = math.atan2(zb - za, length)
        slope_len = math.hypot(length, zb - za)
        zc = (za + zb) / 2 + 3.2
        if axis == "y":
            for x in (x0 + 0.15, x1 - 0.15):
                rot = rot_x(ang if sign > 0 else -ang)
                sink.obox(rail, x, (y0 + y1) / 2, zc, 0.15, slope_len, 0.15, rot, False)
        else:
            for y in (y0 + 0.15, y1 - 0.15):
                rot = mat_mul(rot_z(math.pi / 2), rot_x(ang if sign < 0 else -ang))
                sink.obox(rail, (x0 + x1) / 2, y, zc, 0.15, slope_len, 0.15, rot, False)

    def _ramp(self, rc, up, z0, h):
        """Vehicle ramp: one sloped slab plus curbs (parking structures)."""
        sink = self.out.int
        along_y = up in ("+y", "-y")
        L = rc.d if along_y else rc.w
        W = rc.w if along_y else rc.d
        th = math.atan2(h, L)
        slope = math.hypot(L, h) + 0.6
        sgn = 1 if up[0] == "+" else -1
        # canonical: ascending toward +y; top surface from (y=-L/2, z0) to (y=+L/2, z0+h)
        nrm = (0.0, -math.sin(th), math.cos(th))
        cx, cy, cz = 0.0, 0.0, z0 + h / 2
        loc = Sink()
        loc.obox("concrete", cx, cy - nrm[1] * 0.5, cz - nrm[2] * 0.5, W, slope, 1.0, rot_x(th),
                 True)
        for x in (-W / 2 + 0.4, W / 2 - 0.4):
            loc.obox("concrete_light", x, cy + nrm[1] * 0.4, cz + nrm[2] * 0.4, 0.8, slope, 0.8,
                     rot_x(th), True)
        loc.obox("paint_line_yellow", 0.0, cy + nrm[1] * 0.02, cz + nrm[2] * 0.02, 0.3,
                 slope - 2.0, 0.04, rot_x(th), False)
        yaw = {"+y": 0.0, "-y": math.pi, "+x": -math.pi / 2, "-x": math.pi / 2}[up]
        sink.add_transformed(loc.prims, Xform(rc.cx, rc.cy, 0.0, yaw))

    def _straight_stair(self, rc, up, z0, h, mat, rail):
        n = max(6, int(round(h / 0.95)))
        axis = "y" if up in ("+y", "-y") else "x"
        sign = 1 if up[0] == "+" else -1
        self._flight(rc.x0, rc.y0, rc.x1, rc.y1, axis, sign, z0, z0 + h, n, mat, rail)

    def _u_stair(self, rc, up, z0, h, mat, rail):
        n = max(6, int(round(h / 0.95)))
        n1 = n // 2
        n2 = n - n1
        zm = z0 + h * n1 / n
        axis = "y" if up in ("+y", "-y") else "x"
        sign = 1 if up[0] == "+" else -1
        sink = self.out.int
        if axis == "y":
            wid = rc.w
            sw = (wid - 0.4) / 2
            land = min(sw + 0.5, rc.d * 0.35)
            if sign > 0:
                fa = (rc.y0, rc.y1 - land)
                ly = (rc.y1 - land, rc.y1)
            else:
                fa = (rc.y0 + land, rc.y1)
                ly = (rc.y0, rc.y0 + land)
            ax0, ax1 = rc.x0, rc.x0 + sw
            bx0, bx1 = rc.x1 - sw, rc.x1
            self._flight(ax0, fa[0], ax1, fa[1], "y", sign, z0, zm, n1, mat, rail)
            sink.box(mat, rc.x0, ly[0], zm - 1.0, rc.x1, ly[1], zm, True)
            self._flight(bx0, fa[0], bx1, fa[1], "y", -sign, zm, z0 + h, n2, mat, rail)
            sink.box("paint_white", ax1, fa[0], z0, bx0, fa[1], z0 + h, True)
        else:
            wid = rc.d
            sw = (wid - 0.4) / 2
            land = min(sw + 0.5, rc.w * 0.35)
            if sign > 0:
                fa = (rc.x0, rc.x1 - land)
                lx = (rc.x1 - land, rc.x1)
            else:
                fa = (rc.x0 + land, rc.x1)
                lx = (rc.x0, rc.x0 + land)
            ay0, ay1 = rc.y0, rc.y0 + sw
            by0, by1 = rc.y1 - sw, rc.y1
            self._flight(fa[0], ay0, fa[1], ay1, "x", sign, z0, zm, n1, mat, rail)
            sink.box(mat, lx[0], rc.y0, zm - 1.0, lx[1], rc.y1, zm, True)
            self._flight(fa[0], by0, fa[1], by1, "x", -sign, zm, z0 + h, n2, mat, rail)
            sink.box("paint_white", fa[0], ay1, z0, fa[1], by0, z0 + h, True)

    def _hole_rails(self, s, L, rail):
        """Railings around the stair hole on the upper level (open sides only)."""
        if L not in self.cells:
            return
        rc = s.rect
        z = self.z(L)
        continuing = any((t.level == L and t.rect == rc) for t in self.p.stairs)
        edges = {
            "-y": (rc.x0, rc.y0, rc.x1, rc.y0), "+y": (rc.x0, rc.y1, rc.x1, rc.y1),
            "-x": (rc.x0, rc.y0, rc.x0, rc.y1), "+x": (rc.x1, rc.y0, rc.x1, rc.y1),
        }
        start = {"+y": "-y", "-y": "+y", "+x": "-x", "-x": "+x"}[s.up]
        for key, (x0, y0, x1, y1) in edges.items():
            if s.kind in ("straight", "ramp") and key == s.up:
                continue                       # arrival edge
            if s.kind == "ramp" and key == start and continuing:
                continue                       # next ramp starts here
            if s.kind == "u" and key == start:
                if continuing:
                    continue                   # next flight starts here
                if key in ("-y", "+y"):        # top floor: rail the flight-1 half only
                    x1 = (x0 + x1) / 2
                else:
                    y1 = (y0 + y1) / 2
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            nx, ny = {"-y": (0, -0.6), "+y": (0, 0.6), "-x": (-0.6, 0), "+x": (0.6, 0)}[key]
            if not self.inside(L, mx + nx, my + ny):
                continue
            if self.room_at(L, mx + nx, my + ny) != self.room_at(L, mx - nx, my - ny):
                continue                       # a wall already closes this edge
            self._railing(x0, y0, x1, y1, z, rail)

    def _railing(self, x0, y0, x1, y1, z, mat, h=3.4):
        sink = self.out.int
        length = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(length / 3.5))
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            sink.box(mat, x - 0.1, y - 0.1, z, x + 0.1, y + 0.1, z + h, False)
        if abs(y1 - y0) < 1e-6:
            sink.box(mat, x0, y0 - 0.12, z + h - 0.2, x1, y0 + 0.12, z + h, True)
            sink.box(mat, x0, y0 - 0.06, z + h / 2, x1, y0 + 0.06, z + h / 2 + 0.12, False)
        else:
            sink.box(mat, x0 - 0.12, y0, z + h - 0.2, x0 + 0.12, y1, z + h, True)
            sink.box(mat, x0 - 0.06, y0, z + h / 2, x0 + 0.06, y1, z + h / 2 + 0.12, False)

    def _bulkhead(self, s):
        rc = s.rect
        zr = self.z(self.p.top) + self.h(self.p.top)
        hb = 9.0
        x0, y0, x1, y1 = rc.x0 - 0.6, rc.y0 - 0.6, rc.x1 + 0.6, rc.y1 + 0.6
        ext = self.out.ext
        door_side = {"+y": "-y", "-y": "+y", "+x": "-x", "-x": "+x"}[s.up] if s.kind == "u" \
            else s.up
        mat = "block_gray"
        walls = {
            "-y": ("H", y0, y0 + 0.6, x0, x1), "+y": ("H", y1 - 0.6, y1, x0, x1),
            "-x": ("V", x0, x0 + 0.6, y0, y1), "+x": ("V", x1 - 0.6, x1, y0, y1),
        }
        for key, (o, n0, n1, a, b) in walls.items():
            ops = []
            if key == door_side:
                c = (a + b) / 2
                ops = [Opening(c - 2.0, c + 2.0, 0.0, 7.6, "door")]
            for (u0, u1, za, zb) in solid_rects(a, b, zr, zr + hb, ops, zr):
                self._wallbox(ext, mat, o, u0, u1, n0, n1, za, zb, True)
            if ops:
                c = (a + b) / 2
                if o == "H":
                    px, py = c, (n0 + n1) / 2
                    yaw = 0.0 if key == "-y" else math.pi
                else:
                    px, py = (n0 + n1) / 2, c
                    yaw = -math.pi / 2 if key == "-x" else math.pi / 2
                self.out.props.append(PropPlace("door_metal", px, py, zr, yaw, (1.0, 1.0, 7.6 / 7.5),
                                                {"$metal": "door_metal"}, interior=False,
                                                meta={"door": "metal", "role": "roof",
                                                      "hinge": -2.0, "width": 4.0,
                                                      "height": 7.6}))
                nx, ny = {"-y": (0, -1), "+y": (0, 1), "-x": (-1, 0), "+x": (1, 0)}[key]
                self.out.markers.append(Marker("roof_access", px + nx * 3, py + ny * 3, zr,
                                               math.atan2(nx, -ny), "roof door"))
                self.out.lights.append(LightRec(px + nx * 1.0, py + ny * 1.0, zr + 8.4, WARM, 18,
                                                0.8, "point", "night"))
        ext.box("roof_membrane", x0 - 0.3, y0 - 0.3, zr + hb, x1 + 0.3, y1 + 0.3, zr + hb + 0.5,
                True)
        self.roof_reserved.append(Rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3))

    # -- 7. roofs & facade dressing ------------------------------------------------------
    def emit_roof(self):
        rf = self.p.roof
        top = self.p.top
        zt = self.z(top) + self.h(top)
        f = self.p.facade
        # parapets / eaves along merged facade lines whose top is open sky
        for L in self.levels:
            if L < 0:
                continue
            zl = self.z(L) + self.h(L)
            pitched_here = rf.kind in ("gable", "shed") and (L == top or rf.masses)
            if pitched_here:
                continue
            for (o, c, a, b, od, side) in self.facade_lines(L, open_top=True):
                mat = f.side_mats.get(side, f.mat if (L > 0 or not f.ground) else f.ground)
                para = rf.parapet if L == top else 1.2
                cva = self.line_end_convex(L, o, c, a, od, True)
                cvb = self.line_end_convex(L, o, c, b, od, False)
                n0, n1 = sorted((c, c - od * EXT_T))
                pa = -EXT_T if (o == "V" and cva) else 0.0
                pb = -EXT_T if (o == "V" and cvb) else 0.0
                self._wallbox(self.out.ext, mat, o, a - pa, b + pb, n0, n1, zl, zl + para, True)
                c0, c1 = sorted((c + od * 0.25, c - od * (EXT_T + 0.15)))
                ea = self._end_ext(o, cva, 0.25, EXT_T + 0.15)
                eb = self._end_ext(o, cvb, 0.25, EXT_T + 0.15)
                self._wallbox(self.out.ext, rf.coping, o, a - ea, b + eb, c0, c1, zl + para,
                              zl + para + 0.35, False)
                if f.cornice and L == top:
                    for (dep, z0c, z1c) in ((0.7, zl - 1.2, zl - 0.2), (0.35, zl - 1.8, zl - 1.2)):
                        k0, k1 = sorted((c, c + od * dep))
                        ka = self._end_ext(o, cva, dep, 0.0)
                        kb = self._end_ext(o, cvb, dep, 0.0)
                        self._wallbox(self.out.ext, f.trim, o, a - ka, b + kb, k0, k1, z0c, z1c,
                                      False)
        if rf.kind in ("gable", "shed"):
            if rf.masses:
                for (rc, ridge) in rf.masses:
                    zm = zt
                    for L in self.levels:
                        if any(self.inside(L, rc.cx + ox, rc.cy + oy)
                               for (ox, oy) in ((0.37, 0.41), (-0.37, -0.41), (0.37, -0.41))):
                            zm = self.z(L) + self.h(L)
                    self._pitched(rc, zm, rf, f, ridge)
            else:
                cells = [rc for rc, _ in self.cells.get(top, [])]
                bb = Rect(min(r.x0 for r in cells), min(r.y0 for r in cells),
                          max(r.x1 for r in cells), max(r.y1 for r in cells))
                self._pitched(bb, zt, rf, f)
        if rf.kind == "flat" and rf.equipment == "auto" and self.p.detail >= 2:
            self._roof_equipment(zt)

    def _pitched(self, rc, zt, rf, f, ridge=None):
        ext = self.out.ext
        ridge = ridge or rf.ridge
        if ridge == "auto":
            ridge = "x" if rc.w >= rc.d else "y"
        # canonical frame: ridge along local x, span along local y
        if ridge == "x":
            W, D = rc.w, rc.d
            xf = Xform(rc.x0, rc.y0, 0.0, 0.0)
        else:
            W, D = rc.d, rc.w
            xf = Xform(rc.x1, rc.y0, 0.0, math.pi / 2)
        loc = Sink()
        ov = rf.overhang
        gm = rf.gable_mat or f.mat
        if rf.kind == "gable":
            rise = rf.pitch * D / 2
            loc.wedge(gm, W / 2, 3 * D / 4, zt + rise / 2, W, D / 2, rise, yaw=0.0)
            loc.wedge(gm, W / 2, D / 4, zt + rise / 2, W, D / 2, rise, yaw=math.pi)
            th = math.atan(rf.pitch)
            run_len = D / 2 + ov
            slope = run_len / math.cos(th)
            for sgn in (1, -1):
                # sgn=1 back slope (descends toward +y), -1 front slope
                ym = D / 2 + sgn * (run_len / 2)
                zm = zt + rise - (run_len / 2) * rf.pitch
                nrm = (0.0, sgn * math.sin(th), math.cos(th))
                rot = rot_x(-th if sgn > 0 else th)
                loc.obox(rf.mat, W / 2, ym + nrm[1] * 0.25, zm + nrm[2] * 0.25, W + 2 * ov,
                         slope, 0.5, rot, True)
                # fascia board at the eave
                ye = D / 2 + sgn * run_len
                loc.box(f.trim, -ov, min(ye, ye - sgn * 0.3), zt - ov * rf.pitch - 0.6, W + ov,
                        max(ye, ye - sgn * 0.3), zt - ov * rf.pitch + 0.2, False)
            loc.box(rf.mat, -ov, D / 2 - 0.5, zt + rise - 0.1, W + ov, D / 2 + 0.5, zt + rise + 0.6,
                    False)
            if rf.chimney:
                cx = W * (0.22 if self.rng.random() < 0.5 else 0.78)
                loc.box("brick_red", cx - 1.4, D / 2 - 1.2, zt - 1.0, cx + 1.4, D / 2 + 1.6,
                        zt + rise + 3.5, True)
                loc.box("concrete_dark", cx - 1.6, D / 2 - 1.4, zt + rise + 3.5, cx + 1.6,
                        D / 2 + 1.8, zt + rise + 4.0, False)
        else:  # shed: high at the back
            rise = rf.pitch * D
            loc.wedge(gm, W / 2, D / 2, zt + rise / 2, W, D, rise, yaw=math.pi)
            th = math.atan(rf.pitch)
            run_len = D + 2 * ov
            slope = run_len / math.cos(th)
            nrm = (0.0, -math.sin(th), math.cos(th))
            loc.obox(rf.mat, W / 2, D / 2 + nrm[1] * 0.25, zt + rise / 2 + nrm[2] * 0.25,
                     W + 2 * ov, slope, 0.5, rot_x(th), True)
        ext.add_transformed(loc.prims, xf)

    def _roof_equipment(self, zt):
        top = self.p.top
        pieces = []
        above = []
        for rc, rid in self.cells.get(top, []):
            pieces.append(self._inset_piece([top], rc, EXT_T + 2.0))
        rng = self.rng
        tags = self.p.tags
        area = sum(p.area for p in pieces if p.valid())
        items = []
        n_hvac = max(1, int(area / 1600))
        items += ["hvac_rooftop"] * min(n_hvac, 6)
        items += ["roof_vent"] * max(1, int(area / 900))
        if "kitchen" in tags:
            items += ["exhaust_fan", "exhaust_fan"]
        if "apartments" in tags:
            items += ["satellite_dish", "satellite_dish", "antenna_mast"]
        if "water_tank" in tags:
            items.insert(0, "water_tank_roof")
        if "skylights" in tags:
            items += ["skylight"] * 3
        placed = list(self.roof_reserved)
        for name in items:
            d = KIT[name]
            sx, sy, _ = d.size
            for _ in range(25):
                pc = rng.choice(pieces)
                if not pc.valid() or pc.w < sx + 1 or pc.d < sy + 1:
                    continue
                x = rng.uniform(pc.x0 + sx / 2, pc.x1 - sx / 2)
                y = rng.uniform(pc.y0 + sy / 2, pc.y1 - sy / 2)
                fp = Rect(x - sx / 2 - 1, y - sy / 2 - 1, x + sx / 2 + 1, y + sy / 2 + 1)
                if any(fp.overlaps(o) for o in placed):
                    continue
                placed.append(fp)
                self.out.props.append(PropPlace(name, x, y, zt, 0.0, interior=False))
                break

    def facade_lines(self, L, open_top=False):
        """Exterior runs at level L merged into straight facade lines.

        Returns (o, c, a, b, out_dir, side).  ``open_top`` keeps only the parts whose top
        is exposed (no level above just inside the wall)."""
        segs = []
        for run in self.runs.get(L, []):
            if not run.exterior:
                continue
            if open_top:
                mid = (run.a + run.b) / 2
                inner = run.point(mid, -run.out_dir * 1.5)
                if self.inside(L + 1, inner[0], inner[1]):
                    continue
            segs.append((run.o, run.c, run.out_dir, run.a, run.b, run.side))
        segs.sort()
        out = []
        for (o, c, od, a, b, side) in segs:
            if out and out[-1][0] == o and abs(out[-1][1] - c) < 1e-6 and out[-1][4] == od \
                    and abs(out[-1][3] - a) < 1e-6:
                last = out[-1]
                out[-1] = (o, c, last[2], b, od, side)
            else:
                out.append((o, c, a, b, od, side))
        return out

    @staticmethod
    def _end_ext(o, convex, out_amount, v_shrink):
        """How far a facade-line decoration extends past a line end.

        Front/back (H) lines wrap convex corners by ``out_amount``; side (V) lines stop
        short of them by ``v_shrink`` so decorations never overlap coplanar.  At concave
        ends both stop inside the neighbouring wall."""
        if convex:
            return out_amount if o == "H" else -v_shrink
        return -EXT_T

    def line_end_convex(self, L, o, c, u, od, at_start):
        """True if a facade line ends at an outside (convex) corner."""
        t = -0.3 if at_start else 0.3
        inward = -od * 0.5
        p = (u + t, c + inward) if o == "H" else (c + inward, u + t)
        return not self.inside(L, p[0], p[1])

    def emit_facade_dressing(self):
        f = self.p.facade
        if f.base:
            ops_by_line = {}
            for run in self.runs.get(0, []):
                if run.exterior:
                    ops_by_line.setdefault((run.o, run.c, run.out_dir), []).extend(
                        o for o in run.openings if o.z0 < 1.0)
            for (o, c, a, b, od, side) in self.facade_lines(0):
                if side in f.blind and "attached" in self.p.tags:
                    continue
                n0, n1 = sorted((c, c + od * 0.15))
                ea = self._end_ext(o, self.line_end_convex(0, o, c, a, od, True), 0.15, 0.0)
                eb = self._end_ext(o, self.line_end_convex(0, o, c, b, od, False), 0.15, 0.0)
                ops = ops_by_line.get((o, c, od), [])
                for (u0, u1, za, zb) in solid_rects(a - ea, b + eb, -1.2, 1.0, ops, 0.0):
                    self._wallbox(self.out.ext, f.base, o, u0, u1, n0, n1, za, zb, False)
        if f.band:
            for L in self.levels:
                if L <= 0:
                    continue
                zl = self.z(L)
                for (o, c, a, b, od, side) in self.facade_lines(L):
                    n0, n1 = sorted((c, c + od * 0.25))
                    ea = self._end_ext(o, self.line_end_convex(L, o, c, a, od, True), 0.25, 0.0)
                    eb = self._end_ext(o, self.line_end_convex(L, o, c, b, od, False), 0.25, 0.0)
                    self._wallbox(self.out.ext, f.trim, o, a - ea, b + eb, n0, n1, zl - 0.9,
                                  zl - 0.2, False)
        if f.awning:
            for run in self.runs.get(0, []):
                if not run.exterior or run.side not in f.awning_sides:
                    continue
                spans = [o for o in run.openings if o.kind in ("storefront", "door", "window")
                         and (o.kind != "door" or o.door.kind not in ("garage", "rollup", "bay"))]
                if not spans:
                    continue
                if any(o.kind == "storefront" for o in spans):
                    u0 = min(o.u0 for o in spans) - 0.6
                    u1 = max(o.u1 for o in spans) + 0.6
                    groups = [(u0, u1, max(o.z1 for o in spans))]
                else:
                    groups = [(o.u0 - 0.6, o.u1 + 0.6, o.z1) for o in spans]
                for (u0, u1, zh) in groups:
                    self._awning(run, u0, u1, zh + 0.5, f.awning)
        for sg in self.p.signs:
            self._sign(sg)

    def _awning(self, run, u0, u1, z, mat, depth=4.5, drop=1.6):
        loc = Sink()
        th = math.atan2(drop, depth)
        slope = math.hypot(depth, drop)
        # canonical: spans x in [u0, u1], projects toward -y from the wall face at y = 0
        loc.obox(mat, (u0 + u1) / 2, -depth / 2, z - drop / 2, u1 - u0, slope, 0.25, rot_x(th),
                 False)
        loc.box(mat, u0, -depth - 0.1, z - drop - 1.0, u1, -depth + 0.05, z - drop, False)
        for x in (u0, u1):
            loc.obox("metal_dark", x, -depth / 2, z - drop / 2, 0.12, slope, 0.12, rot_x(th), False)
        side = run.side
        if side == "front":
            xf = Xform(0, run.c, 0, 0.0)
        elif side == "back":
            xf = Xform(u0 + u1, run.c, 0, math.pi)
        elif side == "left":
            xf = Xform(run.c, u0 + u1, 0, -math.pi / 2)
        else:
            xf = Xform(run.c, 0, 0, math.pi / 2)
        self.out.ext.add_transformed(loc.prims, xf)

    def _side_frame(self, side):
        """(origin, yaw) such that local x runs along the side and -y points outward."""
        w, d = self.p.w, self.p.d
        if side == "front":
            return Xform(0, 0, 0, 0.0), w
        if side == "back":
            return Xform(w, d, 0, math.pi), w
        if side == "left":
            return Xform(0, d, 0, -math.pi / 2), d
        return Xform(w, 0, 0, math.pi / 2), d

    def _side_local(self, side, at):
        """Convert a plan coordinate along a side (x for front/back, y for left/right)
        into the side frame's local x."""
        if side == "front" or side == "right":
            return at
        if side == "back":
            return self.p.w - at
        return self.p.d - at

    def _sign(self, sg):
        xf, length = self._side_frame(sg.side)
        L = sg.level
        z0 = self.z(max(0, L))
        top = self.z(max(0, L)) + self.h(max(0, L))
        at = self._side_local(sg.side, sg.at) if sg.at is not None else length / 2
        if sg.style == "board":
            w = sg.width or min(length - 4, max(10, len(sg.text) * 2.0))
            h = 3.2
            zc = (min(top - 2.4, z0 + 12.8) if L == 0 else top - 2.6)
            loc_center = (at, -0.25, zc)
            yaw_l = 0.0
            depth = 0.4
        elif sg.style == "blade":
            w = 3.6
            h = sg.width or 9.0
            zc = z0 + 14.0 if self.p.height > 16 else z0 + self.h(0) * 0.7
            loc_center = (at, -3.0, zc)
            yaw_l = math.pi / 2
            depth = 0.5
        elif sg.style == "roof":
            w = sg.width or min(length, max(14, len(sg.text) * 3.0))
            h = 6.0
            zc = self.p.height + (self.p.roof.parapet if self.p.roof.kind == "flat" else 0) + 3.4
            loc_center = (at, 1.5, zc)
            yaw_l = 0.0
            depth = 0.5
        elif sg.style == "pole":
            w = sg.width or 14.0
            h = 7.0
            zc = sg.z if sg.z is not None else 24.0
            off = sg.offset
            loc_center = (at, -off, zc)
            yaw_l = 0.0
            depth = 1.0
            ps = Sink()
            if sg.z is None:
                for dx in (-w / 3, w / 3):
                    ps.cyl("metal_gray", at + dx, -off, -1.0, 0.45, zc - h / 2 + 1.0, 8, True)
            self.out.ext.add_transformed(ps.prims, xf)
        else:  # letters
            w = sg.width or len(sg.text) * 2.4
            h = 3.0
            zc = top - 2.0
            loc_center = (at, -0.3, zc)
            yaw_l = 0.0
            depth = 0.3
        p = xf.point(loc_center)
        yaw = xf.yaw + yaw_l
        self.out.signs.append(SignRec(sg.text, p[0], p[1], p[2], yaw, w, h, sg.bg, sg.fg, sg.neon,
                                      sg.style != "letters"))
        if sg.style == "blade":
            # bracket
            bs = Sink()
            bs.box("metal_dark", at - 0.1, -1.2, zc + h / 2 - 0.3, at + 0.1, 0.0, zc + h / 2, False)
            bs.box("metal_dark", at - 0.1, -1.2, zc - h / 2, at + 0.1, 0.0, zc - h / 2 + 0.3, False)
            self.out.ext.add_transformed(bs.prims, xf)
        if sg.neon or self.p.facade.lit_sign:
            lp = xf.point((loc_center[0], loc_center[1] - 2.5, loc_center[2]))
            col = {"neon_red": (1, 0.35, 0.3), "neon_blue": (0.4, 0.6, 1), "neon_green":
                   (0.4, 1, 0.6), "neon_pink": (1, 0.45, 0.7)}.get(sg.fg, (1, 0.85, 0.65))
            self.out.lights.append(LightRec(lp[0], lp[1], lp[2], col, max(16, w), 0.9, "point",
                                            "late" if sg.neon else "night"))

    # -- exterior props listed by the archetype ----------------------------------------
    def emit_exterior_props(self):
        for (name, x, y, z, yaw, ch) in self.p.exterior_props:
            if name not in KIT:
                self.out.warnings.append(f"unknown prop {name}")
                continue
            if KIT[name].detail > self.p.detail:
                continue
            self.out.props.append(PropPlace(name, x, y, z, yaw, channels=ch or {}, interior=False))

    # -- driver ------------------------------------------------------------------------
    def build(self) -> Built:
        self.roof_reserved = []
        self.derive_runs()
        self.place_doors()
        self.place_windows()
        self.emit_walls()
        self.emit_slabs()
        self.emit_stairs()
        self.emit_roof()
        self.emit_facade_dressing()
        self.emit_exterior_props()
        from . import furnish
        furnish.furnish_building(self)
        for fn in self.p.extras:
            fn(self)
        self.out.room_info = [
            {"id": r.id, "kind": r.kind, "name": r.name or r.kind, "unit": r.unit,
             "levels": r.levels(), "area": round(r.area(), 1), "tags": sorted(r.tags)}
            for r in self.p.rooms]
        return self.out


def solid_rects(u0, u1, z0, z1, openings, zbase):
    """Rectangles covering [u0,u1]x[z0,z1] minus openings (opening z relative to zbase)."""
    if u1 - u0 < 1e-4 or z1 - z0 < 1e-4:
        return []
    ops = [(max(u0, o.u0), min(u1, o.u1), zbase + o.z0, zbase + o.z1) for o in openings
           if o.u1 > u0 and o.u0 < u1 and zbase + o.z1 > z0 and zbase + o.z0 < z1]
    if not ops:
        return [(u0, u1, z0, z1)]
    us = sorted({u0, u1} | {o[0] for o in ops} | {o[1] for o in ops})
    cols = []
    for i in range(len(us) - 1):
        a, b = us[i], us[i + 1]
        if b - a < 1e-4:
            continue
        cuts = sorted((max(z0, o[2]), min(z1, o[3])) for o in ops if o[0] <= a + 1e-6 and
                      o[1] >= b - 1e-6)
        segs = []
        z = z0
        for (ca, cb) in cuts:
            if ca > z + 1e-4:
                segs.append((z, ca))
            z = max(z, cb)
        if z1 > z + 1e-4:
            segs.append((z, z1))
        cols.append((a, b, tuple(segs)))
    out = []
    # merge neighbouring columns with identical vertical segments
    i = 0
    while i < len(cols):
        a, b, segs = cols[i]
        j = i + 1
        while j < len(cols) and cols[j][2] == segs and abs(cols[j][0] - b) < 1e-6:
            b = cols[j][1]
            j += 1
        for (za, zb) in segs:
            out.append((a, b, za, zb))
        i = j
    return out


def build_plan(plan: Plan, seed=0) -> Built:
    return Builder(plan, seed).build()
