"""Waterfront archetypes: marina office, boat storage, harbour maintenance, a waterfront
restaurant with a deck.  Industrial waterfront (fish warehouse) lives in industrial.py."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import finishes, _pp
from .commercial import _restaurant, biz_facade
from .industrial import _ind_facade
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..records import LightRec, Marker


def deck(x0, x1, y0, y1, z=0.0, rail=True, tables=0, lights=True):
    def fn(B):
        s = B.out.ext
        s.box("deck_teak", x0, y0, z - 1.0, x1, y1, z, True)
        for x in (x0 + 1, x1 - 1):
            for y in (y0 + 1, y1 - 1):
                s.box("wood_weathered", x - 0.5, y - 0.5, z - 9.0, x + 0.5, y + 0.5, z - 1.0)
        if rail:
            s.box("wood_white", x0, y1 - 0.3, z + 3.0, x1, y1, z + 3.3, True)
            s.box("wood_white", x0, y0, z + 3.0, x0 + 0.3, y1, z + 3.3, True)
            s.box("wood_white", x1 - 0.3, y0, z + 3.0, x1, y1, z + 3.3, True)
            n = int((x1 - x0) / 4)
            for i in range(n + 1):
                x = x0 + i * (x1 - x0) / max(1, n)
                s.box("wood_white", x - 0.15, y1 - 0.3, z, x + 0.15, y1, z + 3.0, False)
        import random
        r = random.Random(int(x0 * 7 + y0 * 13))
        for k in range(tables):
            tx = x0 + 5 + (k % 4) * ((x1 - x0 - 10) / 3)
            ty = y0 + (y1 - y0) * (0.35 if k < 4 else 0.75)
            B.out.props.append(_pp("patio_set", tx, ty, z, 0.0,
                                   {"$fabric": r.choice(["fabric_teal", "fabric_cream",
                                                         "fabric_red"])}))
        if lights:
            n = max(1, int((x1 - x0) / 12))
            for i in range(n):
                lx = x0 + (i + 0.5) * (x1 - x0) / n
                B.out.lights.append(LightRec(lx, (y0 + y1) / 2, z + 9.0, (1.0, 0.82, 0.6), 18,
                                             0.8, "point", "late"))
                s.box("wood_weathered", lx - 0.2, y1 - 0.5, z, lx + 0.2, y1 - 0.1, z + 10.0,
                      False)
                s.box("lamp_warm", lx - 0.3, y1 - 0.6, z + 9.5, lx + 0.3, y1, z + 10.1, False)
    return fn


@archetype("marina_office", (40, 52), (34, 44), "WATERFRONT", "COMMERCIAL", front_setback=12,
           rear_clear=4, side_gap=10, yard="parking")
def marina_office(c: Ctx) -> Plan:
    w, d = c.w, c.d
    p = Plan(w, d, [13.0, 12.0], quality="normal", detail=c.detail,
             name=c.name or "Solace Harbor Marina")
    p.facade = Facade(mat=c.pick(["siding_white", "siding_blue", "shingle_wall", "siding_teal"]),
                      trim="trim_white", frame="trim_white", base="concrete",
                      storefront=("front",), awning="awning_blue", bay=9.0)
    p.roof = Roof("gable", c.pick(["roof_metal", "roof_shingle_blue", "roof_metal_red"]),
                  pitch=0.45, ridge="x", overhang=1.6)
    sx = round(w * 0.55 * 2) / 2
    hy = round(d * 0.5 * 2) / 2
    p.room("shop", "marina_shop", R(0, 0, sx, d), name="Bait & Tackle")
    p.room("harbor", "office", R(sx, 0, w, hy), name="Harbormaster")
    p.room("stair", "stair", R(sx, hy, sx + 8, d), name="Stair")
    p.room("wc_m", "restroom", R(sx + 8, hy, w, hy + (d - hy) / 2), name="Boaters' Showers M",
           tags={"mens"})
    p.room("wc_w", "restroom", R(sx + 8, hy + (d - hy) / 2, w, d), name="Boaters' Showers W")
    p.stair(R(sx + 0.8, hy + 5.0, sx + 5.4, d - 0.6), 0, "straight", "-y")
    p.door("shop", None, kind="glass", side="front", role="main")
    p.door("shop", None, kind="exterior", side="back", role="dock")
    p.door("shop", "harbor")
    p.door("harbor", "stair", kind="opening")
    p.door("wc_m", None, kind="exterior", side="right", role="boaters")
    p.door("wc_w", None, kind="exterior", side="back", role="boaters")
    p.door("harbor", None, kind="exterior", side="front", role="office")
    # dock master's lookout upstairs
    p.room("lookout", "control_room", R(0, 0, w, hy), 1, name="Dockmaster Lookout")
    p.room("ustair", "stair", R(sx, hy, sx + 8, d), 1, name="Landing")
    p.room("lounge", "lounge", R(0, hy, sx, d), 1, name="Crew Lounge")
    p.room("ustore", "storage", R(sx + 8, hy, w, d), 1, name="Sail Loft Storage")
    p.door("ustair", "lookout", 1)
    p.door("ustair", "lounge", 1)
    p.door("ustair", "ustore", 1)
    p.extras.append(deck(-2, w + 2, d, d + 10, 0.0, rail=False, tables=0))
    p.signs.append(Sign(p.name.upper(), "front", 0, "board", bg="sign_blue", fg="sign_white",
                        width=min(30.0, w * 0.7)))
    p.lighting = "biz"
    p.tags |= {"marina"}
    p.exterior_props += [("life_ring", 4.0, 0.0, 0.0, 0.0, None),
                         ("buoy_stack", w + 3.0, 6.0, -0.6, 0.0, None),
                         ("ice_merchandiser", sx * 0.5, -2.4, -0.6, 0.0, None)]
    finishes(p, c.rng)
    return p


@archetype("boat_storage", (70, 96), (60, 84), "WATERFRONT", "INDUSTRIAL", front_setback=20,
           rear_clear=10, side_gap=12, yard="loading")
def boat_storage(c: Ctx) -> Plan:
    w, d = c.w, c.d
    p = Plan(w, d, [14.0, 12.0], quality="normal", detail=c.detail,
             name=c.name or c.pick_name(["Harbor Boat Storage", "Drydock Boat Barn"]))
    p.facade = _ind_facade(c)
    p.facade.mat = c.pick(["metal_wall_blue", "metal_wall_white", "metal_wall_green"])
    p.roof = Roof("gable", "roof_metal", pitch=0.3, ridge="y", overhang=1.0)
    barn = p.room("barn", "boat_storage", R(18, 0, w, d), name="Boat Barn",
                  window={0: "none", 1: "high"})
    barn.cells[1] = [R(18, 0, w, d)]
    p.room("office", "office", R(0, 0, 18, 18), name="Storage Office")
    p.room("shop", "workshop", R(0, 18, 18, d - 10), name="Engine Shop")
    p.room("wc", "restroom", R(0, d - 10, 18, d), name="Restroom")
    p.room("loft", "storage", R(0, 0, 18, d), 1, name="Sail Loft", light="bare_bulb")
    p.stair(R(0.8, 20.0, 5.0, 33.0), 0, "straight", "+y")
    p.door("office", None, kind="exterior", side="front", role="main")
    p.door("office", "barn")
    p.door("shop", "barn", kind="rollup_small")
    p.door("shop", "wc")
    p.door("shop", "office")
    p.door("barn", None, kind="bay", side="front", role="boats", at=18 + (w - 18) * 0.5,
           width=22.0, height=12.5)
    p.door("barn", None, kind="bay", side="back", role="boats", at=18 + (w - 18) * 0.5,
           width=22.0, height=12.5)
    p.door("barn", None, kind="metal", side="right", role="secondary")
    p.roof.masses = [(R(0, 0, w, d), "y")]
    p.signs.append(Sign(p.name.upper(), "front", 1, "board", bg="sign_white",
                        fg="sign_blue", at=18 + (w - 18) * 0.5, width=34.0))
    p.lighting = "work"
    finishes(p, c.rng)
    return p


@archetype("waterfront_restaurant", (52, 66), (50, 62), "WATERFRONT", "COMMERCIAL",
           front_setback=10, rear_clear=16, side_gap=10, yard="parking")
def waterfront_restaurant(c: Ctx) -> Plan:
    c.name = c.name or c.pick_name(["Pier 9 Seafood", "The Salt Shack", "Captain's Table",
                               "Lighthouse Oyster Bar"])
    p = _restaurant(c, "restaurant")
    p.facade.mat = c.pick(["shingle_wall", "siding_white", "siding_blue", "wood_weathered"])
    if p.facade.mat == "wood_weathered":
        p.facade.mat = "siding_gray"
    p.facade.awning = "awning_teal"
    # outdoor deck on the water side (the plan's back)
    p.extras.append(deck(-2, p.w + 2, p.d, p.d + 16, 0.0, tables=6))
    p.tags.add("waterfront")
    return p


@archetype("harbor_shed", (50, 70), (40, 56), "WATERFRONT", "INDUSTRIAL", front_setback=12,
           rear_clear=8, side_gap=8, yard="loading")
def harbor_shed(c: Ctx) -> Plan:
    from .industrial import warehouse_small
    c.name = c.name or c.pick_name(["Harbor Maintenance", "Port Works Dept.", "Breakwater Boatworks",
                                     "Tidewater Marine Repair", "Gull Point Boat Works",
                                     "Harbor Rigging Co."])
    p = warehouse_small(c)
    p.facade.mat = c.pick(["metal_wall_rust", "metal_wall_green", "metal_wall_gray"])
    p.tags.add("waterfront")
    return p
