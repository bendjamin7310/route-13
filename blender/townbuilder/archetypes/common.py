"""Shared helpers for archetypes: finishes, exterior add-ons, unit layouts."""

from __future__ import annotations

import math

from ..archi.plan import Plan, Room, R, Facade, Roof
from ..geom import Sink, Rect, rot_x, Xform
from .. import palette as pal

SIDING = ["siding_white", "siding_blue", "siding_green", "siding_yellow", "siding_gray",
          "siding_tan", "siding_teal", "siding_red", "shingle_wall"]
SIDING_OLD = ["siding_faded", "siding_gray", "siding_tan", "siding_green", "siding_blue",
              "stucco_gray"]
STUCCO = ["stucco_cream", "stucco_peach", "stucco_mint", "stucco_sky", "stucco_mustard",
          "stucco_white", "stucco_terracotta"]
BRICK = ["brick_red", "brick_brown", "brick_tan", "brick_dark", "brick_cream"]
ROOF_SHINGLE = ["roof_shingle_dark", "roof_shingle_brown", "roof_shingle_red",
                "roof_shingle_green", "roof_shingle_blue"]
TRIMS = ["trim_white", "trim_cream", "trim_dark", "trim_green", "trim_brown", "trim_blue"]
SHUTTERS = [None, None, "trim_green", "trim_dark", "trim_blue", "trim_red", "trim_brown"]

WET = {"bathroom", "unit_bath", "motel_bath", "halfbath", "restroom"}
SERVICE = {"garage", "utility", "storage", "basement", "stockroom", "mechanical", "electrical",
           "warehouse", "factory_floor", "garage_bay", "loading", "walkin", "cold_storage",
           "apparatus", "sallyport", "boat_storage", "storage_unit", "storage_corridor",
           "workshop", "parking", "fish_processing", "evidence", "gear"}
OFFICE = {"office", "office_private", "office_open", "reception", "meeting", "bullpen",
          "briefing", "dispatch", "control_room", "records", "security", "parts", "service_hall",
          "waiting", "lobby", "chamber", "interview"}


def finishes(plan: Plan, rng, district="RESIDENTIAL"):
    """Fill in floor/wall/ceiling materials for rooms that don't specify them."""
    q = plan.quality
    unit_paint = {}
    for r in plan.rooms:
        rq = q
        for t in r.tags:
            if t.startswith("q:"):
                rq = t[2:]
        k = r.kind
        cheap = rq in ("cheap", "abandoned")
        nice = rq == "nice"
        key = r.unit or "_"
        if key not in unit_paint:
            if cheap:
                unit_paint[key] = rng.choice(pal.PAINT_CHEAP)
            elif rng.random() < 0.25:
                unit_paint[key] = rng.choice(pal.PAINT_ACCENT)
            else:
                unit_paint[key] = rng.choice(pal.PAINT_WARM)
        base_paint = unit_paint[key]
        if k in WET:
            fl = rng.choice(["floor_tile_white", "floor_tile_blue", "floor_tile_green",
                             "floor_tile_check"]) if not cheap else "floor_vinyl_worn"
            wl = rng.choice(["tile_bath_white", "tile_bath_blue", "tile_bath_mint",
                             "tile_bath_pink"]) if not cheap else "tile_institutional"
            if k == "restroom":
                fl, wl = "floor_tile_check", "tile_institutional" if cheap else "tile_subway"
            cl = "ceiling_white"
        elif k in SERVICE:
            fl = "floor_concrete" if k not in ("evidence", "gear") else "floor_vinyl_gray"
            if k in ("garage_bay", "apparatus", "sallyport", "workshop", "factory_floor"):
                fl = "floor_epoxy_gray"
            wl = "block_painted" if k not in ("garage", "basement", "utility") else \
                rng.choice(["block_gray", "concrete_light", "plywood"]) if k == "garage" else \
                "concrete_light"
            if k == "storage_unit":
                wl = "metal_wall_white"
            cl = "ceiling_dark" if k in ("warehouse", "factory_floor", "loading", "boat_storage")\
                else "concrete_light" if k in ("garage", "basement", "parking") else "ceiling_tile"
        elif k in ("kitchen", "unit_kitchen", "kitchen_dining"):
            fl = rng.choice(["floor_tile_check", "floor_tile_terracotta", "floor_vinyl",
                             "floor_linoleum_red"]) if not nice else rng.choice(
                ["floor_tile_white", "floor_wood"])
            if cheap:
                fl = rng.choice(["floor_vinyl_worn", "floor_linoleum_red", "floor_vinyl"])
            wl = base_paint if rng.random() < 0.6 else "tile_kitchen"
            cl = "ceiling_white" if not cheap else "ceiling_stained"
        elif k in ("kitchen_pro",):
            fl, wl, cl = "floor_tile_terracotta", "tile_subway", "ceiling_tile"
        elif k in ("dining_room", "bar_main"):
            fl = rng.choice(["floor_wood_dark", "floor_tile_check", "floor_wood", "carpet_red"])
            wl = rng.choice(["paint_oxblood", "paint_darkgreen", "wood_panel", "paint_mustard",
                             "paint_cream", "paint_terracotta"])
            cl = "ceiling_wood" if rng.random() < 0.3 else "ceiling_dark" if k == "bar_main" \
                else "ceiling_tile"
        elif k in ("retail", "shop", "showroom", "laundromat", "pawn_floor", "marina_shop",
                   "motel_office"):
            fl = rng.choice(["floor_vinyl", "floor_tile_white", "floor_terrazzo",
                             "floor_vinyl_gray"]) if not cheap else "floor_vinyl_worn"
            if k == "showroom":
                fl = "floor_terrazzo"
            wl = rng.choice(["paint_white", "paint_cream", "paint_warmgray"]) if not cheap \
                else rng.choice(pal.PAINT_CHEAP)
            cl = "ceiling_tile"
        elif k in OFFICE:
            fl = rng.choice(["carpet_gray", "carpet_blue", "floor_vinyl", "carpet_beige"])
            if k in ("lobby", "service_hall", "chamber"):
                fl = "floor_terrazzo" if not cheap else "floor_vinyl"
            if k in ("interview",):
                fl = "floor_vinyl_gray"
            wl = rng.choice(["paint_white", "paint_cream", "paint_institutional",
                             "paint_warmgray", "paint_blue"])
            if k == "chamber":
                wl = "wood_panel"
            cl = "ceiling_tile"
        elif k in ("cell", "holding"):
            fl, wl, cl = "floor_concrete_sealed", "block_painted", "concrete_light"
        elif k in ("hall", "corridor", "stair", "entry", "foyer", "unit_entry"):
            if r.unit is None and plan.archetype.startswith(("apartment", "motel", "mixed",
                                                             "office", "police", "town",
                                                             "fire")):
                fl = "floor_vinyl" if not cheap else "floor_vinyl_worn"
                if nice:
                    fl = "floor_terrazzo"
                wl = rng.choice(["paint_cream", "paint_institutional", "paint_beige"])
                cl = "ceiling_tile"
            else:
                fl = rng.choice(["floor_wood", "floor_wood_light", "floor_laminate"]) \
                    if not cheap else rng.choice(["floor_wood_worn", "carpet_stained"])
                wl = base_paint
                cl = "ceiling_white"
        elif k in ("motel_room",):
            fl = rng.choice(["carpet_brown", "carpet_red", "carpet_green", "carpet_stained"])
            wl = rng.choice(["paint_beige", "paint_faded", "paint_mint", "paint_cream",
                             "wood_panel"])
            cl = "ceiling_stained" if cheap else "ceiling_white"
        else:  # living, bedroom, etc.
            if cheap:
                fl = rng.choice(["carpet_stained", "floor_wood_worn", "floor_vinyl_worn",
                                 "carpet_brown"])
            elif nice:
                fl = rng.choice(["floor_wood", "floor_wood_dark", "carpet_beige",
                                 "floor_wood_light"])
            else:
                fl = rng.choice(["carpet_beige", "carpet_blue", "carpet_gray", "floor_laminate",
                                 "floor_wood", "carpet_green"])
            wl = base_paint if rng.random() < 0.75 else rng.choice(pal.PAINT_ACCENT +
                                                                   pal.PAINT_WARM)
            cl = "ceiling_white" if not cheap else "ceiling_stained"
        r.floor = r.floor or fl
        r.wall = r.wall or wl
        r.ceiling = r.ceiling or cl


# --- exterior add-ons (plan.extras callables) ------------------------------------

def porch(x0, x1, depth=7.0, roof_mat="roof_shingle_dark", post="trim_white",
          deck="wood_weathered", z_roof=10.4, rail=True):
    def fn(B):
        s = B.out.ext
        s.box(deck, x0, -depth, -1.0, x1, 0.0, 0.0)
        cx = (x0 + x1) / 2
        s.box("concrete_light", cx - 3.0, -depth - 1.4, -1.2, cx + 3.0, -depth, -0.5)
        for x in (x0 + 0.1, x1 - 0.7):
            s.box(post, x, -depth + 0.1, 0.0, x + 0.6, -depth + 0.7, z_roof - 0.6)
        th = math.atan2(0.9, depth + 1.0)
        L = math.hypot(depth + 1.0, 0.9)
        s.obox(roof_mat, cx, -(depth + 1.0) / 2, z_roof - 0.45, x1 - x0 + 1.0, L, 0.4,
               rot_x(th))
        s.box(post, x0 - 0.3, -depth - 1.2, z_roof - 1.5, x1 + 0.3, -depth - 0.9, z_roof - 0.8,
              False)
        if rail:
            for (a, b) in ((x0 + 0.7, cx - 3.0), (cx + 3.0, x1 - 0.7)):
                if b - a > 0.5:
                    s.box(post, a, -depth + 0.2, 2.6, b, -depth + 0.5, 2.9, False)
                    for i in range(int((b - a) / 0.8) + 1):
                        x = a + i * 0.8
                        s.box(post, x, -depth + 0.25, 0.0, x + 0.15, -depth + 0.45, 2.6, False)
        B.out.props.append(_pp("armchair", x1 - 3.0, -depth / 2, 0.0, math.pi * 0.9,
                               {"$fabric": "fabric_green"}))
    return fn


def back_patio(x0, x1, depth=8.0, mat="concrete_light", props=True):
    def fn(B):
        d = B.p.d
        s = B.out.ext
        s.box(mat, x0, d, -1.0, x1, d + depth, -0.3)
        if props:
            B.out.props.append(_pp("patio_set", (x0 + x1) / 2 + 2, d + depth / 2, -0.3, 0.0,
                                   {"$fabric": B.rng.choice(["fabric_red", "fabric_teal",
                                                             "fabric_cream", "fabric_green"])}))
            B.out.props.append(_pp("bbq_grill", x0 + 2.5, d + depth - 2.0, -0.3, 0.0))
    return fn


def fire_escape(side, levels, u0, u1, plan_w, plan_d, mat="metal_dark"):
    """Exterior fire-escape platforms + stairs on a facade (alternate route up/down)."""
    def fn(B):
        s = Sink()
        depth = 4.5
        # canonical: along x from u0..u1, projecting toward -y from the wall face at y=0
        for L in levels:
            z = B.z(L)
            s.box("diamond_plate", u0, -depth, z - 0.3, u1, 0.0, z, True)
            s.box(mat, u0, -depth, z + 3.2, u1, -depth + 0.2, z + 3.45, True)
            s.box(mat, u0, -depth, z, u0 + 0.2, 0.0, z + 3.45, False)
            s.box(mat, u1 - 0.2, -depth, z, u1, 0.0, z + 3.45, False)
            for i in range(int((u1 - u0) / 2.0) + 1):
                x = u0 + i * 2.0
                s.box(mat, x, -depth, z, x + 0.12, -depth + 0.12, z + 3.2, False)
            # stair flight down to the level below (or a drop ladder at level 1)
            zb = B.z(L - 1) if L > 1 else None
            if zb is not None:
                n = 10
                run = (u1 - u0) - 4.0
                for k in range(n):
                    zt = z - (k + 1) * (z - zb) / n
                    xa = u0 + 1.0 + k * run / n
                    s.box("diamond_plate", xa, -depth + 0.5, zt - 0.2, xa + run / n + 0.3,
                          -depth + 3.0, zt, True)
            else:
                for k in range(8):
                    s.box(mat, u1 - 2.4, -depth + 0.3, z - 1.0 - k * 1.0, u1 - 2.2,
                          -depth + 0.5, z - 0.9 - k * 1.0, False)
                s.box(mat, u1 - 2.6, -depth + 0.25, z - 9.0, u1 - 2.45, -depth + 0.55, z, False)
                s.box(mat, u1 - 1.0, -depth + 0.25, z - 9.0, u1 - 0.85, -depth + 0.55, z, False)
        if side == "front":
            xf = Xform(0, 0, 0, 0.0)
        elif side == "back":
            xf = Xform(plan_w, plan_d, 0, math.pi)
        elif side == "left":
            xf = Xform(0, plan_d, 0, -math.pi / 2)
        else:
            xf = Xform(plan_w, 0, 0, math.pi / 2)
        B.out.ext.add_transformed(s.prims, xf)
        from ..records import Marker
        p = xf.point(((u0 + u1) / 2, -2.0, 0.0))
        B.out.markers.append(Marker("fire_escape", p[0], p[1], 0.0, xf.yaw, "fire escape"))
    return fn


def canopy(x0, y0, x1, y1, z, mat="roof_metal", post="metal_white", posts=None, band=None):
    """Free-standing canopy (gas station, loading dock, drive-thru)."""
    def fn(B):
        s = B.out.ext
        s.box(mat, x0, y0, z, x1, y1, z + 1.2, True)
        if band:
            s.box(band, x0 - 0.1, y0 - 0.1, z + 0.2, x1 + 0.1, y1 + 0.1, z + 1.0, False)
        pts = posts or [(x0 + 1.5, y0 + 1.5), (x1 - 1.5, y0 + 1.5), (x0 + 1.5, y1 - 1.5),
                        (x1 - 1.5, y1 - 1.5)]
        for (px, py) in pts:
            s.box(post, px - 0.6, py - 0.6, -1.0, px + 0.6, py + 0.6, z, True)
        from ..records import LightRec
        nx = max(1, int((x1 - x0) / 14))
        ny = max(1, int((y1 - y0) / 14))
        for i in range(nx):
            for j in range(ny):
                lx = x0 + (i + 0.5) * (x1 - x0) / nx
                ly = y0 + (j + 0.5) * (y1 - y0) / ny
                s.box("lamp_cool", lx - 1.5, ly - 1.5, z - 0.1, lx + 1.5, ly + 1.5, z, False)
                B.out.lights.append(LightRec(lx, ly, z - 0.6, (0.95, 0.97, 1.0), 30, 1.3,
                                             "point", "night"))
    return fn


def loading_dock(x0, x1, depth=8.0, side_y=None):
    """Concrete apron with bollards in front of roll-up doors at the back of the plan."""
    def fn(B):
        d = B.p.d if side_y is None else side_y
        s = B.out.ext
        s.box("concrete", x0, d, -1.0, x1, d + depth, -0.4)
        for x in (x0 + 1, x1 - 2):
            s.box("hazard_yellow", x, d + 0.4, -0.4, x + 1.0, d + 1.4, 3.0)
    return fn


def _pp(name, x, y, z, yaw=0.0, ch=None):
    from ..records import PropPlace
    return PropPlace(name, x, y, z, yaw, channels=ch or {}, interior=False)


# --- apartment units ------------------------------------------------------------

UNIT_TAGS = [("q:cheap", "messy"), ("q:normal",), ("q:normal", "tidy"), ("q:nice",),
             ("q:normal", "kids"), ("q:cheap",), ("q:normal",)]


def apartment_unit(plan: Plan, uid, rect: Rect, level, corridor_side, rng, corridor_id,
                   quality="normal", kind=None):
    """Lay out one apartment inside ``rect``. ``corridor_side`` ('front'/'back') is the
    rect side that touches the corridor (the unit's entrance side)."""
    w, d = rect.w, rect.d
    x0, x1 = rect.x0, rect.x1
    flip = corridor_side == "front"   # corridor at the rect's y0 edge
    tags = set(rng.choice(UNIT_TAGS))
    if quality == "cheap":
        tags = set(rng.choice([("q:cheap", "messy"), ("q:cheap",), ("q:normal",)]))
    if quality == "nice":
        tags = set(rng.choice([("q:nice",), ("q:normal", "tidy"), ("q:nice", "kids")]))
    strip = 8.0  # kitchen/bath strip depth along the corridor

    def ys(a, b):
        # map unit-local depth (0 = outer facade, d = corridor) into plan y
        if flip:
            return (rect.y1 - b, rect.y1 - a)
        return (rect.y0 + a, rect.y0 + b)

    if kind is None:
        kind = "studio" if w < 17 else ("2br" if w >= 30 else "1br")
    ids = {}

    def add(rid, k, xa, xb, da, db, name, extra_tags=()):
        y0, y1 = ys(da, db)
        r = plan.room(f"{uid}_{rid}", k, R(xa, y0, xb, y1), level, unit=uid,
                      name=f"Apt {uid} {name}", tags=set(tags) | set(extra_tags))
        ids[rid] = r.id
        return r

    if kind == "studio":
        add("main", "studio", x0, x1, 0, d - strip, "Studio")
        add("kit", "unit_kitchen", x0, x0 + w * 0.55, d - strip, d, "Kitchenette")
        add("bath", "unit_bath", x0 + w * 0.55, x1, d - strip, d, "Bath")
        plan.door(corridor_id, ids["kit"], level, role="unit")
        plan.door(ids["kit"], ids["main"], level, kind="opening")
        plan.door(ids["main"], ids["bath"], level)
    elif kind == "1br":
        lw = round(w * 0.56 * 2) / 2
        add("liv", "unit_living", x0, x0 + lw, 0, d - strip, "Living")
        add("bed", "unit_bedroom", x0 + lw, x1, 0, d - strip, "Bedroom")
        add("kit", "unit_kitchen", x0, x0 + lw, d - strip, d, "Kitchen")
        add("bath", "unit_bath", x0 + lw, x1, d - strip, d, "Bath")
        plan.door(corridor_id, ids["kit"], level, role="unit")
        plan.door(ids["kit"], ids["liv"], level, kind="opening")
        plan.door(ids["liv"], ids["bed"], level)
        plan.door(ids["bed"], ids["bath"], level)
    else:  # 2br
        lw = round(w * 0.42 * 2) / 2
        bw = (w - lw) / 2
        add("liv", "unit_living", x0, x0 + lw, 0, d - strip, "Living")
        add("bed1", "unit_bedroom", x0 + lw, x0 + lw + bw, 0, d - strip, "Bedroom 1")
        add("bed2", "unit_bedroom", x0 + lw + bw, x1, 0, d - strip, "Bedroom 2",
            ("kids",) if "kids" in tags else ())
        add("kit", "unit_kitchen", x0, x0 + lw, d - strip, d, "Kitchen")
        add("hall", "hall", x0 + lw, x0 + lw + bw, d - strip, d, "Hall")
        add("bath", "unit_bath", x0 + lw + bw, x1, d - strip, d, "Bath")
        plan.door(corridor_id, ids["kit"], level, role="unit")
        plan.door(ids["kit"], ids["liv"], level, kind="opening")
        plan.door(ids["kit"], ids["hall"], level)
        plan.door(ids["hall"], ids["bed1"], level)
        plan.door(ids["hall"], ids["bath"], level)
        plan.door(ids["bed2"], ids["bath"], level)
        plan.door(ids["bed1"], ids["liv"], level)
    return ids
