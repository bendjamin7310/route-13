"""Commercial archetypes with complete front-of-house, back-of-house and service routes."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import (BRICK, STUCCO, TRIMS, finishes, apartment_unit, canopy, loading_dock, _pp)
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect, Sink

NAMES = {
    "convenience": ["Quik Stop", "Harbor Mart", "Corner Pantry", "Gull Mart", "Tidewater Market",
                    "Lucky Penny Market", "Night Owl Foods", "Bayside Grocery"],
    "diner": ["Sunrise Diner", "Dockside Diner", "The Lantern Grill", "Mel's Griddle",
              "Starboard Cafe", "Breakwater Diner"],
    "restaurant": ["Pier 9 Seafood", "Mama Lucia's", "Golden Wok", "Taqueria El Faro",
                   "Captain's Table", "Saltwater Grill", "Bluefin Sushi", "Hearth & Hook"],
    "bar": ["The Rusty Anchor", "Tidewater Tavern", "Low Tide", "The Broken Oar",
            "Neptune Lounge", "Driftwood Bar", "The Salty Dog", "Undertow Club"],
    "pawn": ["Second Chance Pawn", "Harbor Pawn & Loan", "Gold & Gear Pawn", "Quick Cash Pawn",
             "Anchor Pawn & Jewelry", "Lucky Seven Pawn", "Dockside Pawn", "Ace Loan & Pawn"],
    "laundromat": ["Suds City", "Spin Cycle", "Bayside Laundry", "Fluff & Fold", "Bubble & Fold",
                   "Tumble Town Laundry", "Clean Getaway Coin-Op", "Harbor Wash & Dry",
                   "Quarter Spin", "Lint Trap Laundry", "Rinse Cycle", "Sea Breeze Laundry",
                   "The Wash Tub", "Soap Opera Laundromat", "Wringer's Wash House",
                   "Twenty-Four Seven Suds"],
    "pharmacy": ["Solace Pharmacy", "Bay Drug", "Coastal Rx", "Main Street Pharmacy",
                 "Harborview Drugs", "Pelican Pharmacy"],
    "hardware": ["Hartley Hardware", "Anchor Hardware", "Nuts & Bolts", "Keel Supply Co.",
                 "Plumb Line Hardware", "Dockyard Tool & Supply"],
    "electronics": ["Static Electronics", "Volt Shop", "Signal Audio & Video", "Byte Bay",
                    "Circuit Cove", "Lowband Radio & TV"],
    "clothing": ["Thread & Tide", "Seaside Apparel", "Second Skin Thrift", "Harbor Outfitters",
                 "Salt & Denim", "Mariner's Closet"],
    "furniture": ["Porter Home Furnishings", "Coastal Living Furniture", "Plank & Pillow",
                  "Driftwood Home", "Bayside Sofa Barn"],
    "office": ["Pelican Insurance", "Tidewater Realty", "Coastline Legal", "Bay Accounting",
               "Harbor Freight Brokers", "Solace Title Co.", "Marlow & Finch Attorneys"],
    "auto": ["Bay Auto Service", "Cliffside Garage", "Gearhead Auto Repair", "Pit Row Motors",
             "Tow & Go Auto", "Rusty Bolt Garage", "Mile Marker Auto", "Bayside Brake & Muffler",
             "Gasket Brothers", "Coastline Collision", "Torque Shop", "Saltwater Auto Body"],
    "dealer": ["Solace Motors", "Bayview Auto Sales", "Coastline Cars"],
    "bank": ["Harbor Savings", "First Coastal Bank"],
    "bakery": ["Harbor Bakery", "Rise & Brine Bakery", "Crumb & Cove", "Morning Tide Bakehouse"],
    "barber": ["Clipper Barbershop", "Sharp Tide Barbers", "Fade Street Barbers",
               "Old Salt Barber Co."],
    "records": ["Low Tide Records", "Groove Harbor Records", "B-Side Vinyl", "Wax & Wire"],
}

SIGN_COLORS = [("sign_red", "sign_white"), ("sign_green", "sign_cream"),
               ("sign_blue", "sign_white"), ("sign_black", "sign_yellow"),
               ("sign_cream", "sign_red"), ("sign_teal", "sign_white"),
               ("sign_brown", "sign_cream"), ("sign_yellow", "sign_black")]


def _name(c: Ctx, kind):
    return c.name or c.pick_name(NAMES[kind])


def biz_facade(c: Ctx, downtown=None, storefront=True):
    downtown = c.district in ("DOWNTOWN", "MIXED_USE") if downtown is None else downtown
    if downtown:
        mat = c.pick(BRICK + ["stucco_cream", "brick_painted_green", "sandstone", "stucco_peach"])
    elif c.quality == "cheap":
        mat = c.pick(["block_painted", "stucco_gray", "brick_dark", "metal_wall_tan",
                      "stucco_cream"])
    else:
        mat = c.pick(STUCCO + ["block_painted", "brick_tan", "brick_red"])
    f = Facade(mat=mat, trim=c.pick(["trim_white", "trim_cream", "trim_dark", "concrete_light",
                                     "trim_green"]),
               frame=c.pick(["frame_alu", "frame_dark", "trim_dark"]), base="concrete",
               storefront=("front",) if storefront else (), cornice=downtown and c.chance(0.7),
               band=downtown and c.chance(0.5), bay=10.0,
               awning=c.pick(["awning_red", "awning_green", "awning_blue", "awning_mustard",
                              "awning_teal", "awning_cream", "awning_orange", None]),
               blind=set(c.blind))
    return f


def _sign(c, text, style="board", side="front", neon=None):
    bg, fg = c.pick(SIGN_COLORS)
    return Sign(text, side, 0, style, bg=bg, fg=fg,
                neon=c.chance(0.35) if neon is None else neon)


def _std_exterior(p, c, w, d):
    p.exterior_props += [("dumpster", w * 0.3, d + 4.5, -0.6, 0.0, {"$metal": c.pick(
        ["metal_green", "metal_blue", "metal_gray"])}),
        ("ac_condenser", w * 0.7, d + 3.0, -0.6, 0.0, None)]


# -----------------------------------------------------------------------------

@archetype("convenience_store", (44, 60), (42, 56), "COMMERCIAL", "COMMERCIAL",
           front_setback=6, rear_clear=10, side_gap=6, yard="parking")
def convenience_store(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "convenience")
    p = Plan(w, d, [15.0], quality=c.quality, detail=c.detail, name=name)
    p.facade = biz_facade(c)
    p.roof = Roof("flat", "roof_membrane", parapet=3.0)
    by = d - 14
    p.room("floor", "retail", R(0, 0, w, by), name="Sales Floor")
    a1 = round(w * 0.42 * 2) / 2
    p.room("stock", "stockroom", R(0, by, a1, d), name="Stockroom")
    p.room("cooler", "walkin", R(a1, by, a1 + 10, d), name="Walk-in Cooler")
    p.room("wc", "restroom", R(a1 + 10, by, a1 + 19, d), name="Restroom")
    p.room("staff", "employee", R(a1 + 19, by, w, d), name="Staff Room")
    p.door("floor", None, kind="glass_double", side="front", role="main", at=w * 0.62)
    p.door("floor", "stock", kind="interior")
    p.door("stock", "cooler")
    p.door("floor", "staff")
    p.door("floor", "wc")
    p.door("stock", None, kind="metal", side="back", role="service")
    if "right" not in c.blind:
        p.door("staff", None, kind="metal", side="right", role="secondary")
    else:
        p.door("staff", None, kind="metal", side="back", role="secondary")
    p.tags |= {"convenience", "kitchen"}
    p.signs.append(_sign(c, name.upper(), "board"))
    p.lighting = "late"
    p.exterior_props += [("ice_merchandiser", 4.0, -2.4, -0.6, 0.0, None),
                         ("propane_cage", w - 4.5, -2.0, -0.6, 0.0, None),
                         ("newspaper_box", w * 0.62 + 5.0, -2.0, -0.6, 0.0,
                          {"$plastic": "plastic_red"}),
                         ("payphone", w * 0.62 - 5.5, -1.2, -0.6, 0.0, None),
                         ("trash_bin_street", w * 0.62 + 7.5, -2.0, -0.6, 0.0, None)]
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    return p


def _restaurant(c: Ctx, kind="restaurant") -> Plan:
    w, d = c.w, c.d
    name = _name(c, "diner" if kind == "diner" else "restaurant")
    basement = c.chance(0.4) and kind != "diner"
    p = Plan(w, d, [14.0], basement=10.0 if basement else None, quality=c.quality,
             detail=c.detail, name=name)
    p.facade = biz_facade(c, storefront=False)
    p.facade.window_w = 7.0
    if kind == "diner":
        p.facade.mat = c.pick(["metal_wall_white", "stucco_white", "metal_wall_blue",
                               "stucco_sky"])
        p.facade.trim = "metal_chrome"
        p.facade.frame = "frame_alu"
    p.roof = Roof("flat", "roof_membrane", parapet=2.5)
    dy = round(d * 0.55 * 2) / 2
    kx = round(w * 0.55 * 2) / 2
    p.room("dining", "dining_room", R(0, 0, w, dy), name="Dining Room")
    p.room("kitchen", "kitchen_pro", R(0, dy, kx, d - 12), name="Kitchen")
    p.room("walkin", "walkin", R(0, d - 12, 10, d), name="Walk-in")
    p.room("dry", "storage", R(10, d - 12, kx, d), name="Dry Storage")
    p.room("corr", "corridor", R(kx, dy, kx + 6, d), name="Back Corridor")
    rx = kx + 6
    ry = (d - dy) / 3
    p.room("wc_m", "restroom", R(rx, dy, w, dy + ry), name="Men's Room", tags={"mens"})
    p.room("wc_w", "restroom", R(rx, dy + ry, w, dy + 2 * ry), name="Women's Room")
    p.room("office", "employee", R(rx, dy + 2 * ry, w, d), name="Office & Staff")
    p.door("dining", None, kind="glass" if kind != "diner" else "glass_double", side="front",
           role="main")
    p.door("dining", "kitchen", kind="interior", role="swing")
    p.door("dining", "corr", kind="opening")
    p.door("corr", "wc_m")
    p.door("corr", "wc_w")
    p.door("corr", "office")
    p.door("corr", "kitchen", kind="opening")
    p.door("kitchen", "walkin", kind="metal")
    p.door("kitchen", "dry")
    p.door("corr", None, kind="metal", side="back", role="service")
    if "left" not in c.blind:
        p.door("kitchen", None, kind="metal", side="left", role="secondary")
    if basement:
        p.room("cellar", "storage", R(0, dy, kx, d), -1, name="Cellar Storage",
               light="bare_bulb")
        p.stair(R(11.0, d - 2.0 - 11.0, 15.0, d - 1.5), -1, "straight", "+y")
        p.get("dry").cells[0] = [R(10, d - 12, kx, d)]
    p.tags |= {"kitchen", kind}
    p.signs.append(_sign(c, name.upper() if kind != "diner" else name, "board",
                         neon=kind == "diner"))
    if kind == "diner":
        p.signs.append(Sign("OPEN 24 HRS", "front", 0, "blade", bg="sign_red",
                            fg="sign_white", neon=True, at=w - 3.0))
    p.lighting = "late"
    p.exterior_props += [("grease_bin", w - 4.0, d + 3.0, -0.6, 0.0, None)]
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("restaurant", (46, 64), (44, 62), "COMMERCIAL", "COMMERCIAL", front_setback=4,
           rear_clear=8, side_gap=6, yard="parking")
def restaurant(c: Ctx) -> Plan:
    return _restaurant(c, "restaurant")


@archetype("diner", (48, 62), (48, 60), "COMMERCIAL", "COMMERCIAL", front_setback=10,
           rear_clear=10, side_gap=8, yard="parking")
def diner(c: Ctx) -> Plan:
    return _restaurant(c, "diner")


@archetype("bar", (36, 50), (42, 60), "DOWNTOWN", "COMMERCIAL", front_setback=0,
           rear_clear=6, side_gap=0, yard="none")
def bar(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "bar")
    p = Plan(w, d, [14.0], basement=10.0, quality=c.quality, detail=c.detail, name=name)
    p.facade = biz_facade(c, storefront=False)
    p.facade.mat = c.pick(["brick_dark", "brick_red", "wood_panel", "stucco_terracotta",
                           "brick_brown", "paint_navy"]) if c.chance(0.7) else p.facade.mat
    if p.facade.mat in ("wood_panel", "paint_navy"):
        p.facade.mat = "brick_dark"
    p.facade.awning = None
    p.roof = Roof("flat", "roof_tar", parapet=2.5)
    my = round(d * 0.62 * 2) / 2
    p.room("bar", "bar_main", R(0, 0, w, my), name="Bar Room", window="small")
    sx = round(w * 0.4 * 2) / 2
    p.room("store", "storage", R(0, my, sx, d), name="Bar Storage")
    p.room("corr", "corridor", R(sx, my, sx + 6, d), name="Back Hall")
    ry = (d - my) / 3
    p.room("wc_m", "restroom", R(sx + 6, my, w, my + ry), name="Men's", tags={"mens"})
    p.room("wc_w", "restroom", R(sx + 6, my + ry, w, my + 2 * ry), name="Women's")
    p.room("office", "office", R(sx + 6, my + 2 * ry, w, d), name="Manager's Office",
           tags={"safe"})
    p.room("cellar", "storage", R(0, my, w, d), -1, name="Keg Cellar", light="bare_bulb")
    p.room("cellar2", "mechanical", R(0, 0, w, my), -1, name="Basement", light="bare_bulb")
    p.stair(R(1.0, d - 12.5, 5.0, d - 1.5), -1, "straight", "+y")
    p.door("bar", None, kind="exterior", side="front", role="main")
    p.door("bar", "corr", kind="opening")
    p.door("corr", "store")
    p.door("corr", "wc_m")
    p.door("corr", "wc_w")
    p.door("corr", "office")
    p.door("corr", None, kind="metal", side="back", role="service")
    p.door("cellar", "cellar2", -1)
    p.tags |= {"bar", "kitchen"}
    p.signs.append(Sign(name, "front", 0, "blade", bg="sign_black", fg="sign_red", neon=True,
                        at=w - 4.0))
    p.signs.append(_sign(c, name.upper(), "board", neon=True))
    p.lighting = "late"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("pawn_shop", (30, 42), (40, 54), "DOWNTOWN", "COMMERCIAL", front_setback=0,
           rear_clear=6, side_gap=0, yard="none")
def pawn_shop(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "pawn")
    p = Plan(w, d, [14.0], quality="cheap" if c.quality != "nice" else "normal",
             detail=c.detail, name=name)
    p.facade = biz_facade(c)
    p.facade.awning = None
    p.roof = Roof("flat", "roof_tar", parapet=2.5)
    by = d - 16
    hx = round(w * 0.5 * 2) / 2
    p.room("floor", "pawn_floor", R(0, 0, w, by), name="Sales Floor")
    p.room("office", "office", R(0, by, hx, d), name="Back Office", tags={"safe"})
    p.room("wc", "restroom", R(hx, by, w, by + 7), name="Restroom")
    p.room("store", "storage", R(hx, by + 7, w, d), name="Intake Storage")
    p.door("floor", None, kind="glass", side="front", role="main")
    p.door("floor", "office", locked=True)
    p.door("office", "store")
    p.door("store", "wc")
    p.door("store", None, kind="metal", side="back", role="service")
    p.tags |= {"pawn"}
    p.signs.append(_sign(c, name.upper(), "board", neon=True))

    def grille(B):
        # security grille over the shopfront glazing
        for run in B.runs.get(0, []):
            if run.exterior and run.side == "front":
                for op in run.openings:
                    if op.kind == "storefront":
                        n = int((op.u1 - op.u0) / 0.9)
                        for i in range(n + 1):
                            u = op.u0 + i * (op.u1 - op.u0) / max(1, n)
                            B.out.ext.box("metal_dark", u - 0.06, -0.35, op.z0, u + 0.06, -0.25,
                                          op.z1, False)
                        B.out.ext.box("metal_dark", op.u0, -0.4, op.z1 - 0.2, op.u1, -0.25,
                                      op.z1, False)
    p.extras.append(grille)
    p.lighting = "biz"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    return p


@archetype("laundromat", (36, 50), (40, 54), "MIXED_USE", "COMMERCIAL", front_setback=0,
           rear_clear=6, side_gap=0, yard="none")
def laundromat(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "laundromat")
    p = Plan(w, d, [14.0], quality=c.quality, detail=c.detail, name=name)
    p.facade = biz_facade(c)
    p.roof = Roof("flat", "roof_membrane", parapet=2.5)
    by = d - 12
    hx = round(w * 0.45 * 2) / 2
    p.room("floor", "laundromat", R(0, 0, w, by), name="Laundry Floor")
    p.room("util", "mechanical", R(0, by, hx, d), name="Utility Room")
    p.room("wc", "restroom", R(hx, by, hx + 8, d), name="Restroom")
    p.room("attendant", "office", R(hx + 8, by, w, d), name="Attendant Office")
    p.door("floor", None, kind="glass", side="front", role="main")
    p.door("floor", "util", locked=True)
    p.door("floor", "wc")
    p.door("floor", "attendant")
    p.door("util", None, kind="metal", side="back", role="service")
    p.signs.append(_sign(c, name.upper(), "board", neon=c.chance(0.6)))
    p.lighting = "late"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    return p


@archetype("shop", (34, 60), (40, 58), "COMMERCIAL", "COMMERCIAL", front_setback=4,
           rear_clear=6, side_gap=4, yard="parking")
def shop(c: Ctx) -> Plan:
    """Generic single-storey store: pharmacy / hardware / electronics / clothing / furniture."""
    w, d = c.w, c.d
    stype = c.opts.get("type") or c.pick(["pharmacy", "hardware", "electronics", "clothing",
                                          "furniture"])
    name = _name(c, stype)
    p = Plan(w, d, [15.0], quality=c.quality, detail=c.detail, name=name)
    p.facade = biz_facade(c)
    p.roof = Roof("flat", "roof_membrane", parapet=3.0)
    by = d - 14
    sx = round(w * 0.55 * 2) / 2
    p.room("floor", "retail", R(0, 0, w, by), name="Sales Floor")
    p.room("stock", "stockroom", R(0, by, sx, d), name="Stockroom")
    p.room("office", "office", R(sx, by, w - 9, d), name="Office")
    p.room("wc", "restroom", R(w - 9, by, w, d), name="Restroom")
    if stype == "clothing" and w >= 40:
        # fitting room in the back corner so the stockroom still reaches the office
        p.get("stock").cells[0] = [R(8, by, sx, d)]
        p.room("fit", "closet", R(0, by, 8, d), name="Fitting Room")
        p.door("floor", "fit", kind="opening")
    p.door("floor", None, kind="glass_double", side="front", role="main")
    p.door("floor", "stock")
    p.door("stock", "office")
    p.door("floor", "wc")
    p.door("stock", None, kind="rollup_small" if stype in ("hardware", "furniture") else "metal",
           side="back", role="service")
    p.tags |= {stype}
    p.signs.append(_sign(c, name.upper(), "board"))
    p.lighting = "biz"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("office_small", (44, 60), (44, 54), "COMMERCIAL", "COMMERCIAL", front_setback=8,
           rear_clear=10, side_gap=8, yard="parking")
def office_small(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "office")
    p = Plan(w, d, [13.0, 12.0], quality=c.quality, detail=c.detail, name=name)
    p.facade = biz_facade(c, storefront=False)
    p.facade.awning = None
    p.facade.window_w = 6.0
    p.facade.band = True
    p.roof = Roof("flat", "roof_gravel", parapet=2.5)
    rx = round(w * 0.4 * 2) / 2
    by = d - 20
    p.room("recep", "reception", R(0, 0, rx, 18), name="Reception")
    p.room("meet", "meeting", R(0, 18, rx, by), name="Conference Room")
    p.room("open", "office_open", R(rx, 0, w, by), name="Open Office")
    p.room("stairh", "stair", R(0, by, 12, d), name="Stair Hall")
    p.room("kitch", "breakroom", R(12, by, rx + 8, d), name="Kitchenette")
    p.room("wc", "restroom", R(rx + 8, by, rx + 17, d), name="Restroom")
    p.room("store", "storage", R(rx + 17, by, w, d), name="Files & Storage")
    p.stair(R(0.8, by + 4.5, 11.2, d - 0.8), 0, "u", "+y")
    p.door("recep", None, kind="glass_double", side="front", role="main")
    p.door("recep", "meet")
    p.door("recep", "open", kind="glass")
    p.door("open", "kitch")
    p.door("open", "wc")
    p.door("open", "store")
    p.door("stairh", "kitch", kind="opening")
    p.door("stairh", "meet")
    p.door("stairh", None, kind="metal", side="back", role="service")
    # upper floor
    p.room("upstair", "stair", R(0, by, 12, d), 1, name="Upper Landing")
    n = 3
    ow = (w - 0) / n
    for i in range(n):
        p.room(f"po{i}", "office_private", R(i * ow, 0, (i + 1) * ow, 16), 1,
               name=f"Office {201 + i}", tags={"chief"} if i == 0 else set())
    p.room("uphall", "corridor", R(0, 16, w, 22), 1, name="Upper Corridor")
    p.room("upopen", "office_open", R(12, 22, w - 10, d), 1, name="Bullpen")
    p.room("upwc", "restroom", R(w - 10, 22, w, d), 1, name="Restroom")
    p.room("upstore", "records", R(0, 22, 12, by), 1, name="Records")
    p.roof.access = True
    for i in range(n):
        p.door("uphall", f"po{i}", 1)
    p.door("uphall", "upopen", 1, kind="glass")
    p.door("uphall", "upwc", 1)
    p.door("uphall", "upstore", 1)
    p.door("upstair", "upopen", 1)
    p.door("upstair", "upstore", 1)
    p.signs.append(Sign(name.upper(), "front", 1, "letters", bg="sign_black", fg="sign_white"))
    p.lighting = "biz"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("mixed_use", (40, 58), (40, 56), "MIXED_USE", "COMMERCIAL", front_setback=0,
           rear_clear=6, side_gap=0, yard="none")
def mixed_use(c: Ctx) -> Plan:
    """Shop on the ground floor, apartments above with their own street door and stair."""
    w, d = c.w, c.d
    floors = c.opts.get("floors") or c.pick([2, 3, 3, 4])
    stype = c.pick(["clothing", "electronics", "pharmacy", "convenience", "furniture",
                    "hardware", "bakery", "barber", "records"])
    sname = c.pick_name(NAMES[stype]) if stype in NAMES else "Shop"
    p = Plan(w, d, [15.0] + [12.0] * (floors - 1), quality=c.quality, detail=c.detail,
             name=c.name or f"{sname} Building")
    p.facade = biz_facade(c, downtown=True)
    p.facade.band = True
    p.roof = Roof("flat", c.pick(["roof_tar", "roof_gravel"]), parapet=3.0, access=True)
    sw = 12.0
    cw = w - sw
    by = d - 12
    p.room("shop", "retail", R(0, 0, cw, by), name=sname)
    p.room("stock", "stockroom", R(0, by, cw, d), name="Back Room")
    for L in range(floors):
        p.room(f"st{L}", "stair", R(cw, 0, w, d), L, name="Residents' Stair",
               tags={"always_lit"})
    for L in range(floors - 1):
        p.stair(R(cw + 1.0, 10.0, w - 1.0, 26.0), L, "u", "+y")
    p.stair(R(cw + 1.0, 10.0, w - 1.0, 26.0), floors - 1, "u", "+y", to_roof=True)
    p.door("shop", None, kind="glass", side="front", role="main")
    p.door("shop", "stock")
    p.door("stock", None, kind="metal", side="back", role="service")
    p.door("st0", None, kind="exterior", side="front", role="residents")
    p.door("st0", None, kind="metal", side="back", role="secondary")
    p.door("st0", "stock", locked=True)
    for L in range(1, floors):
        cid = f"corr{L}"
        p.room(cid, "corridor", R(0, d - 8, cw, d), L, name=f"Hall {L + 1}F")
        p.door(cid, f"st{L}", L, kind="interior")
        half = round(cw / 2 * 2) / 2
        if cw >= 34:
            apartment_unit(p, f"{L + 1}A", R(0, 0, half, d - 8), L, "back", c.rng, cid,
                           c.quality)
            apartment_unit(p, f"{L + 1}B", R(half, 0, cw, d - 8), L, "back", c.rng, cid,
                           c.quality)
        else:
            apartment_unit(p, f"{L + 1}A", R(0, 0, cw, d - 8), L, "back", c.rng, cid,
                           c.quality)
    p.tags |= {stype if stype in ("clothing", "electronics", "pharmacy", "furniture",
                                  "hardware", "convenience") else "general", "apartments"}
    p.signs.append(_sign(c, sname.upper(), "board"))
    p.lighting = "biz"
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("office_tower", (60, 80), (52, 70), "DOWNTOWN", "COMMERCIAL", front_setback=4,
           rear_clear=10, side_gap=6, yard="plaza")
def office_tower(c: Ctx) -> Plan:
    w, d = c.w, c.d
    floors = c.opts.get("floors") or c.pick([5, 6, 7])
    name = c.name or c.pick_name(["Harbor Trust Building", "Meridian Tower", "Gullwing Plaza",
                             "Tidewater Center"])
    p = Plan(w, d, [16.0] + [12.0] * (floors - 1), quality="nice", detail=c.detail, name=name)
    p.facade = Facade(mat=c.pick(["concrete_light", "limestone", "sandstone", "brick_tan",
                                  "granite"]),
                      ground=c.pick(["granite", "marble", "stone_base"]), trim="concrete_light",
                      frame="frame_dark", glass="glass_tint", base="granite",
                      storefront=("front",), cornice=True, band=True, bay=8.0, window_w=6.0)
    p.roof = Roof("flat", "roof_gravel", parapet=4.0, access=True)
    cx0 = round((w - 26) / 2 * 2) / 2
    cx1 = cx0 + 26
    cy0 = d - 22
    lx0 = round(w * 0.3 * 2) / 2
    lx1 = w - lx0
    # ground floor
    p.room("lobby", "lobby", R(lx0, 0, lx1, cy0), name="Lobby")
    p.room("shop_l", "retail", R(0, 0, lx0, cy0), name="Corner Cafe")
    p.room("shop_r", "retail", R(lx1, 0, w, cy0), name="Newsstand")
    p.room("svc_l", "storage", R(0, cy0, cx0, d), name="Loading & Mail")
    p.room("svc_r", "security", R(cx1, cy0, w, d), name="Security Office")
    p.door("lobby", None, kind="glass_double", side="front", role="main")
    p.door("shop_l", None, kind="glass", side="front", role="shop")
    p.door("shop_r", None, kind="glass", side="front", role="shop")
    p.door("lobby", "shop_l", kind="glass")
    p.door("lobby", "shop_r", kind="glass")
    p.door("svc_l", None, kind="rollup_small", side="back", role="service")
    p.door("svc_r", None, kind="metal", side="right" if "right" not in c.blind else "back",
           role="secondary")
    p.tags |= {"general", "skylights"}
    for L in range(floors):
        # core: stairwell + restrooms + elevator, stacked on every floor
        p.room(f"stair{L}", "stair", R(cx0, cy0, cx0 + 12, d), L, name="Stairwell",
               tags={"always_lit"})
        p.room(f"elev{L}", "mechanical", R(cx0 + 12, cy0 + 8, cx1, d), L, name="Elevator Shaft",
               furnish=False, light="none")
        p.room(f"core{L}", "corridor", R(cx0 + 12, cy0, cx1, cy0 + 8), L, name="Elevator Lobby")
        p.door(f"core{L}", f"stair{L}", L)
        p.door(f"core{L}", f"elev{L}", L, kind="metal", locked=True)
        if L < floors - 1:
            p.stair(R(cx0 + 1.0, cy0 + 4.0, cx0 + 11.0, d - 1.5), L, "u", "+y")
        else:
            p.stair(R(cx0 + 1.0, cy0 + 4.0, cx0 + 11.0, d - 1.5), L, "u", "+y", to_roof=True)
        if L == 0:
            p.door("core0", "lobby", kind="opening")
            p.door("stair0", "svc_l")
            continue
        det = c.detail if L <= 2 else max(1, c.detail - 1)
        p.room(f"open{L}", "office_open", R(0, 18, w, cy0), L, name=f"Floor {L + 1} Open Plan")
        n = 4
        ow = w / n
        for i in range(n):
            p.room(f"po{L}_{i}", "office_private" if i % 3 else "meeting",
                   R(i * ow, 0, (i + 1) * ow, 18), L, name=f"Suite {L + 1}0{i + 1}",
                   tags={"chief"} if (i == 0 and L == floors - 1) else set())
            p.door(f"open{L}", f"po{L}_{i}", L, kind="glass")
        p.room(f"wc{L}", "restroom", R(0, cy0, cx0, d), L, name="Restrooms")
        p.room(f"kit{L}", "breakroom", R(cx1, cy0, w, d), L, name="Break Room")
        p.door(f"core{L}", f"open{L}", L, kind="glass_double")
        p.door(f"open{L}", f"wc{L}", L)
        p.door(f"open{L}", f"kit{L}", L)
    p.signs.append(Sign(name.upper(), "front", 0, "roof", bg="sign_black", fg="sign_white",
                        neon=True))
    p.lighting = "biz"
    p.exterior_props += [("planter_box", lx0 - 4.0, -4.0, -0.6, 0.0, None),
                         ("planter_box", lx1 + 4.0, -4.0, -0.6, 0.0, None),
                         ("bike_rack", w / 2 + 14.0, -3.0, -0.6, 0.0, None)]
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    return p


@archetype("supermarket", (120, 150), (92, 116), "COMMERCIAL", "COMMERCIAL", front_setback=70,
           rear_clear=24, side_gap=14, yard="parking")
def supermarket(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = c.name or "Harbor Fresh Market"
    p = Plan(w, d, [22.0], quality="normal", detail=c.detail, name=name)
    p.facade = Facade(mat=c.pick(["block_painted", "stucco_cream", "brick_tan"]),
                      trim="trim_green", frame="frame_alu", base="concrete", storefront=("front",),
                      awning="awning_green", bay=12.0)
    p.roof = Roof("flat", "roof_membrane", parapet=4.0)
    by = d - 26
    p.room("floor", "supermarket", R(0, 0, w, by), name="Sales Floor")
    x = [0, w * 0.42, w * 0.58, w * 0.7, w * 0.8, w * 0.9, w]
    x = [round(v * 2) / 2 for v in x]
    p.room("stock", "stockroom", R(x[0], by, x[1], d), name="Receiving & Stockroom")
    p.room("cold", "cold_storage", R(x[1], by, x[2], d), name="Cold Storage")
    p.room("break", "breakroom", R(x[2], by, x[3], d), name="Break Room")
    p.room("office", "office", R(x[3], by, x[4], d), name="Manager's Office", tags={"safe"})
    p.room("wc_m", "restroom", R(x[4], by, x[5], d), name="Men's Room", tags={"mens"})
    p.room("wc_w", "restroom", R(x[5], by, x[6], d), name="Women's Room")
    p.door("floor", None, kind="glass_double", side="front", role="main", at=w * 0.25)
    p.door("floor", None, kind="glass_double", side="front", role="exit", at=w * 0.75)
    p.door("floor", "stock", kind="double")
    p.door("stock", "cold", kind="metal")
    p.door("floor", "break")
    p.door("floor", "office", locked=True)
    p.door("floor", "wc_m")
    p.door("floor", "wc_w")
    for i, f in enumerate((0.15, 0.32)):
        p.door("stock", None, kind="rollup", side="back", role="loading", at=w * f)
    p.door("stock", None, kind="metal", side="left", role="service")
    p.extras.append(loading_dock(w * 0.05, w * 0.42, 14.0))
    p.tags |= {"grocery", "kitchen"}
    p.signs.append(Sign(name.upper(), "front", 0, "board", bg="sign_green", fg="sign_cream",
                        neon=True, width=min(60, w * 0.5)))
    p.lighting = "late"
    p.exterior_props += [("shopping_carts", w * 0.25 - 8.0, -3.0, -0.6, math.pi / 2, None),
                         ("shopping_carts", w * 0.75 + 8.0, -3.0, -0.6, math.pi / 2, None),
                         ("ice_merchandiser", w * 0.5, -2.6, -0.6, 0.0, None),
                         ("atm", w * 0.5 + 6.0, -1.5, -0.6, 0.0, None)]
    _std_exterior(p, c, w, d)
    finishes(p, c.rng)
    return p


@archetype("car_dealership", (76, 96), (60, 76), "COMMERCIAL", "COMMERCIAL",
           front_setback=60, rear_clear=16, side_gap=12, yard="carlot")
def car_dealership(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = c.name or c.pick_name(NAMES["dealer"])
    p = Plan(w, d, [18.0], quality="nice", detail=c.detail, name=name)
    p.facade = Facade(mat=c.pick(["metal_wall_white", "concrete_light", "stucco_white"]),
                      trim="frame_dark", frame="frame_dark", glass="glass_store",
                      base="concrete", storefront=("front", "left"), bay=10.0)
    p.roof = Roof("flat", "roof_metal", parapet=2.0, coping="metal_white")
    sx = round(w * 0.58 * 2) / 2
    sy = round(d * 0.6 * 2) / 2
    p.room("show", "showroom", R(0, 0, sx, sy), name="Showroom")
    p.room("sales", "office_open", R(0, sy, sx * 0.5, d), name="Sales Offices")
    p.room("parts", "parts", R(sx * 0.5, sy, sx, d - 10), name="Service Desk & Parts")
    p.room("wc", "restroom", R(sx * 0.5, d - 10, sx * 0.5 + 9, d), name="Restroom")
    p.room("break", "breakroom", R(sx * 0.5 + 9, d - 10, sx, d), name="Lounge")
    p.room("bays", "garage_bay", R(sx, 0, w, d), name="Service Bays")
    p.door("show", None, kind="glass_double", side="front", role="main", at=sx * 0.5)
    p.door("show", "sales", kind="glass")
    p.door("show", "parts", kind="opening")
    p.door("parts", "wc")
    p.door("parts", "break")
    p.door("parts", "bays")
    p.door("show", "bays", kind="rollup_small", role="showroom")
    p.door("bays", None, kind="rollup", side="front", role="service", at=sx + (w - sx) * 0.5)
    p.door("bays", None, kind="rollup", side="back", role="service")
    p.door("sales", None, kind="metal", side="back", role="secondary")
    p.signs.append(Sign(name.upper(), "front", 0, "roof", bg="sign_blue", fg="sign_white",
                        neon=True))
    p.signs.append(Sign("SERVICE", "front", 0, "board", bg="sign_blue", fg="sign_white",
                        at=sx + (w - sx) * 0.5, width=16))
    p.lighting = "biz"
    p.tags |= {"dealer"}
    finishes(p, c.rng)
    return p


@archetype("auto_shop", (52, 70), (44, 58), "INDUSTRIAL", "INDUSTRIAL", front_setback=24,
           rear_clear=14, side_gap=10, yard="lot")
def auto_shop(c: Ctx) -> Plan:
    w, d = c.w, c.d
    name = _name(c, "auto")
    p = Plan(w, d, [17.0], quality="cheap" if c.chance(0.6) else "normal", detail=c.detail,
             name=name)
    p.facade = Facade(mat=c.pick(["block_painted", "metal_wall_blue", "metal_wall_gray",
                                  "brick_brown", "stucco_gray"]),
                      trim=c.pick(["trim_red", "trim_dark", "trim_blue"]), frame="frame_dark",
                      base="concrete", bay=10.0)
    p.roof = Roof("flat", "roof_metal", parapet=1.5, coping="metal_gray")
    bx = round(w * 0.66 * 2) / 2
    p.room("bays", "garage_bay", R(0, 0, bx, d), name="Repair Bays")
    p.room("front", "parts", R(bx, 0, w, d * 0.45), name="Customer Counter")
    p.room("office", "office", R(bx, d * 0.45, w, d * 0.7), name="Shop Office", tags={"safe"})
    p.room("wc", "restroom", R(bx, d * 0.7, w, d * 0.85), name="Restroom")
    p.room("store", "storage", R(bx, d * 0.85, w, d), name="Parts Storage")
    nb = 3 if bx >= 42 else 2
    for i in range(nb):
        p.door("bays", None, kind="rollup_small", side="front", role="service",
               at=(i + 0.5) * bx / nb)
    p.door("bays", None, kind="rollup_small", side="back", role="service", at=bx * 0.5)
    p.door("front", None, kind="glass", side="front", role="main")
    p.door("front", "bays")
    p.door("front", "office")
    p.door("office", "wc")
    p.door("store", "bays")
    p.door("store", None, kind="metal", side="back", role="secondary")
    p.signs.append(_sign(c, name.upper(), "board", neon=False))
    p.lighting = "work"
    p.tags |= {"garage"}
    p.exterior_props += [("tire_stack", bx + 3.0, -3.0, -0.6, 0.0, None),
                         ("tire_stack", bx + 6.0, -3.0, -0.6, 0.0, None),
                         ("oil_drums_rack", w * 0.3, d + 3.0, -0.6, 0.0, None),
                         ("car_wreck", w * 0.6, d + 10.0, -0.6, 1.3, None),
                         ("air_pump", w - 3.0, -3.0, -0.6, 0.0, None)]
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p
