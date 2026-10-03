"""Residential archetypes: bungalows, two-storey houses, aging houses with basements,
hilltop mansion, mobile homes and apartment blocks with varied units."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import (SIDING, SIDING_OLD, STUCCO, BRICK, ROOF_SHINGLE, TRIMS, SHUTTERS, finishes,
                     porch, back_patio, fire_escape, apartment_unit, _pp)
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect


def _house_facade(c: Ctx, old=False):
    mat = c.pick(SIDING_OLD if old else SIDING + STUCCO[:3] + ["brick_red", "brick_tan"])
    trim = c.pick(["trim_white", "trim_white", "trim_cream", "trim_dark"]) if not old \
        else c.pick(["trim_white", "trim_brown", "trim_cream"])
    return Facade(mat=mat, trim=trim, frame=trim, base="concrete" if not old else "stone_base",
                  shutters=None if old else c.pick(SHUTTERS), bay=9.0)


@archetype("house_small", (30, 40), (36, 46), "RESIDENTIAL", "RESIDENTIAL", front_setback=16,
           rear_clear=18, side_gap=10, yard="residential")
def house_small(c: Ctx) -> Plan:
    w, d = c.w, c.d
    garage = w >= 38 and c.chance(0.7)
    gw = 12.0 if garage else 0.0
    bx = gw
    bw = w - gw
    p = Plan(w, d, [12.0], quality=c.quality, detail=c.detail, name=c.name)
    p.facade = _house_facade(c, old=c.quality == "cheap")
    p.roof = Roof("gable", c.pick(ROOF_SHINGLE), pitch=c.pick([0.45, 0.55, 0.6]), ridge="x",
                  overhang=1.4, chimney=c.chance(0.4))
    fy, hd = 15.0, 6.0
    la = round(bw * 0.55 * 2) / 2
    ka = round(bw * 0.45 * 2) / 2
    p.room("living", "living", R(bx, 0, bx + la, fy), name="Living Room")
    p.room("bed2", "kids" if c.chance(0.5) else "bedroom", R(bx + la, 0, w, fy), name="Bedroom 2")
    p.room("hall", "hall", R(bx, fy, w, fy + hd), name="Hall")
    yb = fy + hd
    p.room("kitchen", "kitchen_dining", R(bx, yb, bx + ka, d), name="Kitchen")
    p.room("bath", "bathroom", R(bx + ka, yb, bx + ka + 7.5, yb + 9.0), name="Bathroom")
    if d - (yb + 9.0) >= 6.0:
        p.room("laundry", "laundry", R(bx + ka, yb + 9.0, bx + ka + 7.5, d), name="Laundry")
        p.door("laundry", "kitchen")
    else:
        p.get("bath").cells[0] = [R(bx + ka, yb, bx + ka + 7.5, d)]
    p.room("bed1", "master", R(bx + ka + 7.5, yb, w, d), name="Main Bedroom")
    for r in ("living", "bed2", "kitchen", "bath", "bed1"):
        p.door("hall", r, kind="opening" if r == "living" else "interior")
    p.door("living", None, kind="exterior", side="front", role="main")
    p.door("kitchen", None, kind="exterior", side="back", role="secondary")
    p.door("hall", None, kind="exterior", side="right" if not garage else "right",
           role="side")
    masses = [(Rect(bx, 0, w, d), "x")]
    if garage:
        p.room("garage", "garage", R(0, 0, gw, 23), name="Garage")
        p.door("garage", None, kind="garage", side="front", role="garage")
        p.door("garage", "hall")
        p.door("garage", None, kind="exterior", side="left", role="side")
        masses.append((Rect(0, 0, gw, 23), "y"))
    p.roof.masses = masses
    if c.chance(0.6):
        p.extras.append(porch(bx + 1, bx + la, 6.5, p.roof.mat, p.facade.trim))
    if c.chance(0.5):
        p.extras.append(back_patio(bx + 2, bx + ka, 8.0))
    p.exterior_props += [("ac_condenser", w + 2.2, d * 0.6, -0.6, 0.0, None),
                         ("gas_meter", w, d * 0.35, 0.0, -math.pi / 2, None)]
    if garage:
        p.exterior_props.append(("garbage_cans", -2.6, 18.0, -0.6, math.pi / 2, None))
    p.tags.add("house")
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("house_medium", (44, 56), (44, 58), "RESIDENTIAL", "RESIDENTIAL", front_setback=20,
           rear_clear=22, side_gap=12, yard="residential")
def house_medium(c: Ctx) -> Plan:
    w, d = c.w, c.d
    p = Plan(w, d, [12.0, 12.0], quality=c.quality, detail=c.detail, name=c.name)
    p.facade = _house_facade(c)
    p.facade.band = c.chance(0.4)
    p.roof = Roof("gable", c.pick(ROOF_SHINGLE), pitch=c.pick([0.5, 0.6, 0.7]), ridge="x",
                  overhang=1.5, chimney=c.chance(0.5))
    gx, fd = 22.0, 24.0
    fw = 12.0
    lx = gx + fw
    # ground floor
    p.room("garage", "garage", R(0, 0, gx, fd), name="Garage")
    p.room("foyer", "foyer", R(gx, 0, lx, fd), name="Foyer")
    p.room("living", "living", R(lx, 0, w, fd), name="Living Room")
    p.room("laundry", "laundry", R(0, fd, 10, fd + 10), name="Mudroom & Laundry")
    p.room("halfbath", "halfbath", R(0, fd + 10, 10, d), name="Powder Room")
    p.room("kitchen", "kitchen", R(10, fd, lx, d), name="Kitchen")
    p.room("family", "family", R(lx, fd, w, d), name="Family Room")
    p.stair(R(gx + 0.6, 3.5, gx + 5.0, 18.5), 0, "straight", "+y")
    p.door("garage", None, kind="garage2", side="front", role="garage")
    p.door("garage", "laundry")
    p.door("laundry", "kitchen")
    p.door("laundry", None, kind="exterior", side="left", role="side")
    p.door("halfbath", "kitchen")
    p.door("kitchen", "foyer", kind="opening")
    p.door("kitchen", "family", kind="arch")
    p.door("foyer", "living", kind="arch")
    p.door("living", "family", kind="opening")
    p.door("foyer", None, kind="exterior", side="front", role="main", at=gx + 8.5)
    p.door("family", None, kind="sliding", side="back", role="secondary")
    # upper floor
    p.room("bed3", "kids", R(0, 0, gx, fd), 1, name="Bedroom 3")
    p.room("uphall", "hall", R(gx, 0, lx, fd + 6), 1, name="Upstairs Hall")
    p.room("master", "master", R(lx, 0, w, fd), 1, name="Main Bedroom")
    p.room("bath2", "bathroom", R(0, fd, 10, d), 1, name="Bathroom")
    p.room("linen", "closet", R(10, fd, gx, fd + 6), 1, name="Linen Closet")
    p.room("bed2", "bedroom", R(10, fd + 6, lx, d), 1, name="Bedroom 2")
    p.room("mbath", "bathroom", R(lx, fd, w, d), 1, name="Main Bath", tags={"q:nice"})
    p.door("uphall", "bed3", 1)
    p.door("uphall", "master", 1)
    p.door("uphall", "linen", 1)
    p.door("uphall", "bed2", 1)
    p.door("bed3", "bath2", 1)
    p.door("bed2", "bath2", 1)
    p.door("master", "mbath", 1)
    p.extras.append(back_patio(lx + 2, w - 2, 10.0))
    if c.chance(0.5):
        p.extras.append(porch(gx + 0.5, w - 1, 6.0, p.roof.mat, p.facade.trim, z_roof=10.6))
    p.exterior_props += [("ac_condenser", w + 2.2, d * 0.7, -0.6, 0.0, None),
                         ("gas_meter", w, d * 0.3, 0.0, -math.pi / 2, None),
                         ("garbage_cans", -2.6, 10.0, -0.6, math.pi / 2, None),
                         ("basketball_hoop", 6.0, -1.0, -0.6, math.pi, None)]
    p.tags.add("house")
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("house_old", (26, 32), (34, 40), "LOW_INCOME", "RESIDENTIAL", front_setback=10,
           rear_clear=14, side_gap=6, yard="residential")
def house_old(c: Ctx) -> Plan:
    w, d = c.w, c.d
    basement = c.chance(0.6)
    p = Plan(w, d, [12.0], basement=10.0 if basement else None, quality=c.quality,
             detail=c.detail, name=c.name)
    p.facade = _house_facade(c, old=True)
    p.roof = Roof("gable", c.pick(["roof_shingle_dark", "roof_shingle_brown", "roof_metal",
                                   "roof_shingle_green"]),
                  pitch=c.pick([0.6, 0.7, 0.8]), ridge="x", overhang=1.0, chimney=c.chance(0.6))
    la = round(w * 0.55 * 2) / 2
    fy, my = 14.0, 22.0
    p.room("living", "living", R(0, 0, la, fy), name="Front Room")
    p.room("bed1", "bedroom", R(la, 0, w, fy), name="Bedroom")
    p.room("dining", "dining", R(0, fy, la, my), name="Dining Nook")
    p.room("bath", "bathroom", R(la, fy, w, my), name="Bathroom")
    p.room("kitchen", "kitchen", R(0, my, la, d), name="Kitchen")
    p.room("bed2", "bedroom", R(la, my, w, d), name="Back Bedroom")
    p.door("living", None, kind="exterior", side="front", role="main")
    p.door("kitchen", None, kind="exterior", side="back", role="secondary")
    p.door("living", "dining", kind="arch")
    p.door("dining", "kitchen", kind="opening")
    p.door("living", "bed1")
    p.door("dining", "bath")
    p.door("kitchen", "bed2")
    if basement:
        p.room("cellar", "basement", R(0, fy, la, d), -1, name="Basement", light="bare_bulb")
        p.stair(R(0.6, d - 13.6, 4.6, d - 1.4), -1, "straight", "-y")
    p.extras.append(porch(0.5, w - 0.5, 6.0, p.roof.mat, p.facade.trim, z_roof=10.0))
    p.exterior_props += [("ac_window_unit", la + 3.0, 0.0, 4.0, 0.0, None)] if c.chance(0.6) \
        else []
    p.exterior_props += [("garbage_cans", w + 2.0, d - 4.0, -0.6, -math.pi / 2, None)]
    p.tags.add("house")
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("house_nice", (56, 70), (52, 64), "RESIDENTIAL", "RESIDENTIAL", front_setback=26,
           rear_clear=30, side_gap=16, yard="residential")
def house_nice(c: Ctx) -> Plan:
    """Larger two-storey house; used for upscale streets and (scaled up) the hilltop estate."""
    w, d = c.w, c.d
    p = Plan(w, d, [13.0, 12.0], quality="nice", detail=c.detail, name=c.name)
    p.facade = Facade(mat=c.pick(["stucco_white", "stucco_cream", "brick_cream", "siding_white",
                                  "limestone"]), trim="trim_white", frame="trim_dark",
                      base="stone_base", band=True, bay=10.0)
    p.roof = Roof("gable", c.pick(["roof_tile", "roof_shingle_dark", "roof_shingle_blue"]),
                  pitch=0.55, ridge="x", overhang=2.0, chimney=True)
    gx = 24.0
    fd = 26.0
    p.room("garage", "garage", R(0, 0, gx, fd), name="Garage", tags={"q:nice"})
    p.room("foyer", "foyer", R(gx, 0, gx + 14, fd), name="Entry Hall")
    p.room("living", "living", R(gx + 14, 0, w, fd), name="Living Room")
    p.room("mud", "laundry", R(0, fd, 12, fd + 12), name="Laundry")
    p.room("office", "study", R(0, fd + 12, 12, d), name="Study")
    p.room("kitchen", "kitchen", R(12, fd, gx + 14, d), name="Kitchen")
    p.room("dining", "dining", R(gx + 14, fd, w, d), name="Dining Room")
    p.stair(R(gx + 0.6, 4.0, gx + 5.2, 20.5), 0, "straight", "+y")
    p.door("garage", None, kind="garage2", side="front", role="garage")
    p.door("garage", "mud")
    p.door("mud", "kitchen")
    p.door("office", "kitchen")
    p.door("mud", None, kind="exterior", side="left", role="side")
    p.door("kitchen", "foyer", kind="opening")
    p.door("kitchen", "dining", kind="arch")
    p.door("foyer", "living", kind="arch")
    p.door("living", "dining", kind="opening")
    p.door("foyer", None, kind="glass_double", side="front", role="main", at=gx + 9.5)
    p.door("dining", None, kind="sliding", side="back", role="secondary")
    p.door("kitchen", None, kind="exterior", side="back", role="service")
    p.room("bed3", "bedroom", R(0, 0, gx, fd), 1, name="Guest Room")
    p.room("uphall", "hall", R(gx, 0, gx + 14, fd + 8), 1, name="Gallery")
    p.room("master", "master", R(gx + 14, 0, w, fd), 1, name="Main Suite")
    p.room("bath2", "bathroom", R(0, fd, 12, d), 1, name="Bathroom")
    p.room("bed2", "kids", R(12, fd + 8, gx + 14, d), 1, name="Kids Room")
    p.room("closet", "closet", R(12, fd, gx, fd + 8), 1, name="Linen")
    p.room("mbath", "bathroom", R(gx + 14, fd, w, d), 1, name="Main Bath")
    p.door("uphall", "bed3", 1)
    p.door("uphall", "master", 1)
    p.door("uphall", "bed2", 1)
    p.door("uphall", "closet", 1)
    p.door("bed3", "bath2", 1)
    p.door("bed2", "bath2", 1)
    p.door("master", "mbath", 1)
    p.extras.append(back_patio(gx + 2, w - 2, 12.0))
    p.exterior_props += [("ac_condenser", w + 2.4, d * 0.6, -0.6, 0.0, None),
                         ("ac_condenser", w + 2.4, d * 0.75, -0.6, 0.0, None)]
    p.tags |= {"house", "pool"}
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("trailer", (16, 18), (56, 64), "OUTSKIRTS", "RESIDENTIAL", front_setback=10,
           rear_clear=10, side_gap=12, yard="residential")
def trailer(c: Ctx) -> Plan:
    """Single-wide mobile home: long and narrow, entered from the long side."""
    w, d = c.w, c.d
    p = Plan(w, d, [10.5], quality="cheap" if c.quality != "abandoned" else "abandoned",
             detail=c.detail, name=c.name)
    p.facade = Facade(mat=c.pick(["metal_wall_white", "metal_wall_tan", "siding_faded",
                                  "metal_wall_rust"]), trim="trim_white", frame="frame_alu",
                      base="metal_wall_gray", bay=8.0)
    p.roof = Roof("flat", "roof_metal", parapet=0.6, coping="metal_white", equipment="none")
    p.room("bed1", "bedroom", R(0, 0, w, 14), name="Bedroom")
    p.room("bath", "bathroom", R(0, 14, w * 0.55, 21), name="Bathroom")
    p.room("hall", "hall", R(w * 0.55, 14, w, 21), name="Hall")
    p.room("living", "living", R(0, 21, w, 38), name="Living")
    p.room("kitchen", "kitchen", R(0, 38, w, 50), name="Kitchen")
    p.room("bed2", "bedroom", R(0, 50, w, d), name="Back Bedroom")
    p.door("bed1", "hall")
    p.door("hall", "bath")
    p.door("hall", "living", kind="opening")
    p.door("living", "kitchen", kind="opening")
    p.door("kitchen", "bed2")
    p.door("living", None, kind="exterior", side="right", role="main", at=30.0)
    p.door("kitchen", None, kind="exterior", side="right", role="secondary", at=44.0)

    def skirt(B):
        s = B.out.ext
        s.box("wood_weathered", w + 1.0, 26.0, -1.0, w + 7.0, 34.0, 0.0)
        s.box("wood_weathered", w + 7.0, 28.0, -1.2, w + 9.0, 32.0, -0.5)
    p.extras.append(skirt)
    p.exterior_props += [("propane_cage", w + 3.0, 8.0, -0.6, -math.pi / 2, None),
                         ("lawn_chair", w + 4.0, 24.0, -0.6, -1.2, {"$fabric": "fabric_green"}),
                         ("bbq_grill", w + 5.0, 40.0, -0.6, 0.0, None)]
    p.tags.add("house")
    finishes(p, c.rng)
    return p


@archetype("apartment_lowrise", (60, 84), (50, 64), "RESIDENTIAL", "RESIDENTIAL",
           front_setback=8, rear_clear=14, side_gap=10, yard="parking")
def apartment_lowrise(c: Ctx) -> Plan:
    """Three-to-four storey walk-up: double-loaded corridor, lobby, laundry, basement storage,
    rooftop access, an exterior fire escape."""
    w, d = c.w, c.d
    floors = c.opts.get("floors") or c.pick([3, 3, 4])
    q = c.quality
    p = Plan(w, d, [12.0] * floors, basement=10.0, quality=q, detail=c.detail, name=c.name)
    mat = c.pick(BRICK + ["stucco_cream", "stucco_peach", "stucco_mint"]) if q != "cheap" \
        else c.pick(["brick_dark", "brick_brown", "stucco_gray", "block_painted", "brick_red"])
    p.facade = Facade(mat=mat, trim=c.pick(["trim_white", "trim_cream", "concrete_light"]),
                      frame=c.pick(["trim_white", "frame_alu", "trim_dark"]), base="concrete",
                      cornice=c.chance(0.6), band=c.chance(0.5), bay=10.0)
    p.roof = Roof("flat", c.pick(["roof_gravel", "roof_membrane", "roof_tar"]), parapet=3.0,
                  access=True)
    cd = 6.0
    ya = round((d - cd) / 2 * 2) / 2
    yb = ya + cd
    sw = 12.0
    sx = round((w - sw) / 2 * 2) / 2
    # stairwell spans every level at the back centre
    for L in range(-1, floors):
        p.room(f"stair{L}", "stair", R(sx, yb, sx + sw, d), L, name="Stairwell",
               tags={"always_lit"})
    sr = R(sx + 1.0, yb + 4.5, sx + sw - 1.0, min(d - 1.5, yb + 20.5))
    for L in range(-1, floors - 1):
        p.stair(sr, L, "u", "+y")
    p.stair(sr, floors - 1, "u", "+y", to_roof=True)
    # basement
    p.room("base_hall", "corridor", R(0, ya, w, yb), -1, name="Basement Corridor")
    p.room("storage_a", "storage", R(0, 0, w / 2, ya), -1, name="Tenant Storage")
    p.room("boiler", "mechanical", R(w / 2, 0, w, ya), -1, name="Boiler Room")
    p.room("storage_b", "storage", R(0, yb, sx, d), -1, name="Tenant Storage B")
    p.room("electric", "electrical", R(sx + sw, yb, w, d), -1, name="Electrical")
    for r in ("storage_a", "boiler", "storage_b", "electric", "stair-1"):
        p.door("base_hall", r, -1)
    for L in range(floors):
        cid = f"corr{L}"
        p.room(cid, "corridor", R(0, ya, w, yb), L, name=f"Corridor {L + 1}F")
        p.door(cid, f"stair{L}", L, kind="interior")
        units_front = 3 if w >= 72 else 2
        units_back = 2
        rng = c.rng
        if L == 0:
            lw = 14.0
            lx = round((w - lw) / 2 * 2) / 2
            p.room("lobby", "lobby", R(lx, 0, lx + lw, ya), 0, name="Lobby")
            p.door("lobby", cid, 0, kind="glass")
            p.door("lobby", None, 0, kind="glass_double", side="front", role="main")
            spans = [(0, lx), (lx + lw, w)]
            for i, (a, b) in enumerate(spans):
                apartment_unit(p, f"1{chr(65 + i)}", R(a, 0, b, ya), 0, "back", rng, cid, q)
            p.room("laundry", "laundry", R(0, yb, sx, d), 0, name="Laundry Room",
                   tags={"shared"})
            p.door("laundry", cid, 0)
            apartment_unit(p, "1C", R(sx + sw, yb, w, d), 0, "front", rng, cid, q)
            p.door(cid, None, 0, kind="metal", side="left", role="secondary")
            p.door(cid, None, 0, kind="metal", side="right", role="service")
        else:
            uw = w / units_front
            for i in range(units_front):
                apartment_unit(p, f"{L + 1}{chr(65 + i)}", R(i * uw, 0, (i + 1) * uw, ya), L,
                               "back", rng, cid, q)
            apartment_unit(p, f"{L + 1}{chr(65 + units_front)}", R(0, yb, sx, d), L, "front",
                           rng, cid, q)
            apartment_unit(p, f"{L + 1}{chr(66 + units_front)}", R(sx + sw, yb, w, d), L,
                           "front", rng, cid, q)
    p.extras.append(fire_escape("back", list(range(1, floors)), w - 26.0, w - 6.0, w, d))
    p.tags |= {"apartments"}
    if c.chance(0.35):
        p.tags.add("water_tank")
    p.lighting = "res"
    p.signs.append(Sign(c.name or "Apartments", "front", 0, "letters", bg="sign_black",
                        fg="sign_white"))
    p.exterior_props += [("dumpster", w - 6.0, d + 5.0, -0.6, 0.0, {"$metal": "metal_green"}),
                         ("mailbox_public", w / 2 + 10.0, -2.5, -0.6, 0.0, None),
                         ("bike_rack", w / 2 - 12.0, -2.5, -0.6, 0.0, None)]
    finishes(p, c.rng)
    return p
