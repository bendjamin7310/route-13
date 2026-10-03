"""Industrial archetypes: warehouses, fish warehouse, self-storage and a cannery/factory."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import finishes, loading_dock, canopy, _pp
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect, Sink

IND_WALLS = ["metal_wall_gray", "metal_wall_blue", "metal_wall_green", "metal_wall_tan",
             "metal_wall_white", "block_gray", "block_painted", "brick_brown"]


def _ind_facade(c: Ctx):
    mat = c.pick(IND_WALLS)
    if c.quality == "cheap" or c.chance(0.2):
        mat = c.pick(["metal_wall_rust", "block_gray", "metal_wall_gray"])
    return Facade(mat=mat, ground=None, trim=c.pick(["trim_dark", "metal_gray", "trim_red",
                                                     "trim_blue"]),
                  frame="frame_dark", glass="glass" if c.quality != "cheap" else "glass_dirty",
                  base="concrete", bay=14.0, blind=set(c.blind))


def _warehouse(c: Ctx, fish=False) -> Plan:
    w, d = c.w, c.d
    p = Plan(w, d, [12.0, 12.0, 11.0], quality=c.quality, detail=c.detail,
             name=c.name or c.pick_name(["Bayline Logistics", "Coastal Freight Co.",
                                    "Gulfstream Distribution", "Pacific Rim Storage",
                                    "Harbor Supply Depot", "Keel & Co. Warehouse"]))
    if fish:
        p.name = c.name or c.pick_name(["Solace Fish Co.", "Northbay Seafood Packers",
                                   "Breaker Fisheries"])
    p.facade = _ind_facade(c)
    p.roof = Roof("flat", "roof_metal", parapet=1.6, coping="metal_gray")
    ow = 36.0
    od = 26.0
    hall_cells_low = [R(ow, 0, w, od), R(0, od, w, d)]
    hall = p.room("hall", "fish_processing" if fish else "warehouse",
                  R(0, 0, 1, 1), name="Warehouse Floor" if not fish else "Processing Floor",
                  window={0: "none", 1: "none", 2: "high"})
    hall.cells = {0: list(hall_cells_low), 1: list(hall_cells_low), 2: [R(0, 0, w, d)]}
    # two-storey office block at the front-left
    p.room("recep", "reception", R(0, 0, 18, 14), name="Front Office")
    p.room("ofc_wc", "restroom", R(18, 0, ow, 8), name="Restroom")
    p.room("ofc_hall", "corridor", R(18, 8, ow, 14), name="Office Hall")
    p.room("break", "breakroom", R(0, 14, 18, od), name="Break Room")
    p.room("ofc_stair", "stair", R(18, 14, ow, od), name="Office Stair")
    p.stair(R(19.0, 15.0, ow - 1.0, 19.5), 0, "straight", "+x")
    p.room("mgr", "office", R(0, 0, 18, od), 1, name="Manager's Office", tags={"safe"})
    p.room("records", "records", R(18, 0, ow, 14), 1, name="Records")
    p.room("up_stair", "stair", R(18, 14, ow, od), 1, name="Upper Landing")
    p.door("recep", None, kind="glass", side="front", role="main", at=9.0)
    p.door("recep", "ofc_hall")
    p.door("ofc_hall", "ofc_wc")
    p.door("ofc_hall", "ofc_stair", kind="opening")
    p.door("recep", "break")
    p.door("break", "hall")
    p.door("ofc_stair", "hall", kind="metal")
    p.door("up_stair", "mgr", 1)
    p.door("up_stair", "records", 1)
    # loading: drive-in doors on the front, dock doors on the back, personnel doors
    nf = 2 if w < 140 else 3
    for i in range(nf):
        p.door("hall", None, kind="rollup", side="front", role="loading",
               at=ow + (i + 0.5) * (w - ow) / nf)
    nb = max(2, int(w / 40))
    for i in range(nb):
        p.door("hall", None, kind="rollup", side="back", role="loading", at=(i + 0.5) * w / nb)
    p.door("hall", None, kind="metal", side="left", role="secondary", at=d * 0.7)
    p.door("hall", None, kind="metal", side="right", role="secondary", at=d * 0.5)
    if fish:
        p.room("cold", "cold_storage", R(w - 40, d - 30, w, d), name="Cold Storage")
        p.get("hall").cells[0] = [R(ow, 0, w, od), R(0, od, w - 40, d), R(w - 40, od, w, d - 30)]
        p.get("hall").cells[1] = [R(ow, 0, w, od), R(0, od, w - 40, d), R(w - 40, od, w, d - 30)]
        p.room("cold_up", "storage", R(w - 40, d - 30, w, d), 1, name="Cold Storage Loft",
               light="bare_bulb")
        p.door("hall", "cold", kind="metal")
        p.door("cold", None, kind="rollup_small", side="back", role="loading")
        p.tags.add("fish")
    p.extras.append(loading_dock(0, w, 14.0))
    p.signs.append(Sign(p.name.upper(), "front", 0, "board", bg="sign_blue", fg="sign_white",
                        at=ow + (w - ow) / 2, width=min(48.0, (w - ow) * 0.6)))
    p.lighting = "work"
    p.exterior_props += [("dumpster", 6.0, d + 18.0, -0.6, 0.0, {"$metal": "metal_blue"}),
                         ("pallet_boxes", w * 0.5, d + 20.0, -0.6, 0.0, None),
                         ("pallet", w * 0.5 + 6.0, d + 20.0, -0.6, 0.3, None),
                         ("generator", w - 8.0, -6.0, -0.6, 0.0, None)]
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("warehouse", (88, 150), (68, 120), "INDUSTRIAL", "INDUSTRIAL", front_setback=26,
           rear_clear=18, side_gap=14, yard="loading")
def warehouse(c: Ctx) -> Plan:
    return _warehouse(c)


@archetype("fish_warehouse", (90, 130), (70, 100), "WATERFRONT", "INDUSTRIAL",
           front_setback=24, rear_clear=24, side_gap=12, yard="loading")
def fish_warehouse(c: Ctx) -> Plan:
    return _warehouse(c, fish=True)


@archetype("warehouse_small", (60, 90), (50, 70), "INDUSTRIAL", "INDUSTRIAL",
           front_setback=24, rear_clear=20, side_gap=10, yard="loading")
def warehouse_small(c: Ctx) -> Plan:
    """Single-height workshop/warehouse: one big room plus an office corner."""
    w, d = c.w, c.d
    p = Plan(w, d, [20.0], quality=c.quality, detail=c.detail,
             name=c.name or c.pick_name(["Delgado Fabrication", "Seawall Construction Yard",
                                    "Tri-County Plumbing Supply", "Marlow Metalworks",
                                    "Harbor Electric Supply", "Breakwater Boatworks",
                                    "Pacific Pallet Co.", "Gull Wing Welding",
                                    "Hartwell Cabinetry", "Coastal Tile & Stone",
                                    "Anchor Sign Shop", "Stillwater Machine Works",
                                    "Ironside Fabricators", "Baywater Refrigeration"]))
    p.facade = _ind_facade(c)
    p.roof = Roof("shed" if c.chance(0.4) else "flat", "roof_metal", pitch=0.12, parapet=1.2,
                  coping="metal_gray")
    p.room("hall", "workshop" if c.chance(0.5) else "warehouse", R(0, 0, w, d),
           name="Shop Floor", window="high")
    p.get("hall").cells[0] = [R(20, 0, w, d), R(0, 18, 20, d)]
    p.room("office", "office", R(0, 0, 20, 10), name="Office")
    p.room("wc", "restroom", R(0, 10, 10, 18), name="Restroom")
    p.room("store", "storage", R(10, 10, 20, 18), name="Tool Crib")
    p.door("office", None, kind="exterior", side="front", role="main")
    p.door("office", "hall")
    p.door("office", "wc")
    p.door("hall", "store")
    p.door("hall", None, kind="rollup", side="front", role="loading", at=20 + (w - 20) * 0.5)
    p.door("hall", None, kind="rollup_small", side="back", role="loading")
    p.door("hall", None, kind="metal", side="right", role="secondary")
    p.signs.append(Sign(p.name.upper(), "front", 0, "board", bg="sign_yellow", fg="sign_black",
                        at=20 + (w - 20) * 0.5, width=min(36.0, w * 0.5)))
    p.lighting = "work"
    finishes(p, c.rng)
    if c.chance(0.5):
        p.mirror()
    return p


@archetype("storage_facility", (110, 160), (62, 84), "INDUSTRIAL", "SERVICE",
           front_setback=34, rear_clear=24, side_gap=12, yard="gated")
def storage_facility(c: Ctx) -> Plan:
    """Self-storage: management office, security room, interior unit corridor, drive-up units
    on the back facade and a loading entrance."""
    w, d = c.w, c.d
    p = Plan(w, d, [12.0], quality="normal", detail=c.detail,
             name=c.name or c.pick_name(["SafeHarbor Self Storage", "Lockbox Storage",
                                    "Bay Storage Center"]))
    p.facade = Facade(mat=c.pick(["block_painted", "metal_wall_white", "stucco_cream"]),
                      trim="trim_red" if c.chance(0.5) else "trim_blue", frame="frame_alu",
                      base="concrete", bay=12.0)
    p.roof = Roof("flat", "roof_metal", parapet=1.4, coping="metal_white")
    ox = 26.0
    cy0 = round((d - 8) / 2 * 2) / 2
    cy1 = cy0 + 8
    p.room("office", "reception", R(0, 0, ox, cy0), name="Rental Office")
    p.room("security", "security", R(0, cy0, 12, d - 10), name="Security Room")
    p.room("wc", "restroom", R(0, d - 10, 12, d), name="Restroom")
    p.room("load", "loading", R(12, cy1, ox, d), name="Loading Bay")
    p.room("corr", "storage_corridor", R(12, cy0, w, cy1), name="Unit Corridor")
    p.door("office", None, kind="glass", side="front", role="main")
    p.door("office", "security")
    p.door("security", "corr", kind="metal")
    p.door("security", "wc")
    p.door("office", "corr", kind="glass")
    p.door("load", "corr", kind="double")
    p.door("load", None, kind="rollup_small", side="back", role="loading", at=19.0)
    p.door("corr", None, kind="metal", side="right", role="emergency")
    uw = 10.0
    n = int((w - ox) / uw)
    uw = (w - ox) / n
    k = 0
    for i in range(n):
        x0 = ox + i * uw
        x1 = x0 + uw
        # front-row units open onto the corridor
        k += 1
        rid = f"u{k:03d}"
        tags = {"empty"} if c.chance(0.3) else set()
        p.room(rid, "storage_unit", R(x0, 0, x1, cy0), name=f"Unit {k:03d}", tags=tags)
        p.door("corr", rid, kind="rollup_small", width=uw - 2.4, height=8.0)
        # back-row units: split depth into interior-access and drive-up halves
        dd = d - cy1
        k += 1
        rid2 = f"u{k:03d}"
        p.room(rid2, "storage_unit", R(x0, cy1, x1, cy1 + dd / 2), name=f"Unit {k:03d}",
               tags={"empty"} if c.chance(0.3) else set())
        p.door("corr", rid2, kind="rollup_small", width=uw - 2.4, height=8.0)
        k += 1
        rid3 = f"u{k:03d}"
        p.room(rid3, "storage_unit", R(x0, cy1 + dd / 2, x1, d), name=f"Drive-up {k:03d}",
               tags={"empty"} if c.chance(0.3) else set())
        p.door(rid3, None, kind="rollup_small", side="back", role="unit", width=uw - 2.4,
               height=8.0)
    p.signs.append(Sign(p.name.upper(), "front", 0, "roof", bg="sign_red", fg="sign_white",
                        neon=True, width=min(50.0, w * 0.4), at=w * 0.5))
    p.lighting = "always"
    p.tags.add("storage")
    finishes(p, c.rng)
    return p


@archetype("factory", (116, 170), (96, 130), "INDUSTRIAL", "INDUSTRIAL", front_setback=40,
           rear_clear=40, side_gap=28, yard="loading")
def factory(c: Ctx) -> Plan:
    """Processing plant (the town cannery): production hall, control room, lockers,
    maintenance shop, plus smokestack, silos and pipe racks outside."""
    w, d = c.w, c.d
    p = Plan(w, d, [14.0, 12.0, 8.0], quality=c.quality, detail=c.detail,
             name=c.name or "Solace Cannery")
    p.facade = Facade(mat=c.pick(["brick_red", "brick_brown", "brick_dark"]), trim="concrete_light",
                      frame="frame_dark", glass="glass_dirty" if c.quality == "cheap" else "glass",
                      base="concrete", cornice=True, bay=12.0)
    p.roof = Roof("flat", "roof_tar", parapet=2.5, access=True)
    ob = 44.0
    od = 30.0
    mx = w - 34.0
    my = d - 26.0
    low = [R(ob, 0, mx, my), R(mx, 0, w, my), R(0, od, ob, d), R(ob, my, mx, d)]
    hall = p.room("hall", "factory_floor", R(0, 0, 1, 1), name="Production Hall",
                  window={0: "none", 1: "high", 2: "high"})
    hall.cells = {0: list(low), 1: list(low), 2: [R(0, 0, w, d)]}
    p.room("workshop", "workshop", R(mx, my, w, d), name="Maintenance Shop")
    p.room("ws_up", "storage", R(mx, my, w, d), 1, name="Parts Loft", light="bare_bulb")
    # front office block
    p.room("lobby", "lobby", R(0, 0, 16, 16), name="Plant Lobby")
    p.room("lock_m", "locker", R(16, 0, 30, 16), name="Men's Lockers")
    p.room("lock_w", "locker", R(30, 0, ob, 16), name="Women's Lockers")
    p.room("ocorr", "corridor", R(0, 16, ob, 22), name="Office Corridor")
    p.room("canteen", "breakroom", R(0, 22, 28, od), name="Canteen")
    p.room("ostair", "stair", R(28, 22, ob, od), name="Stair")
    p.stair(R(29.0, 23.0, ob - 1.0, 27.5), 0, "straight", "+x")
    p.room("control", "control_room", R(0, 0, 28, od), 1, name="Control Room")
    p.room("plantmgr", "office", R(28, 0, ob, 16), 1, name="Plant Manager", tags={"chief"})
    p.room("ustair", "stair", R(28, 16, ob, od), 1, name="Upper Landing")
    p.door("lobby", None, kind="glass_double", side="front", role="main", at=8.0)
    p.door("lobby", "ocorr", kind="opening")
    p.door("ocorr", "lock_m")
    p.door("ocorr", "lock_w")
    p.door("ocorr", "canteen")
    p.door("ocorr", "ostair", kind="opening")
    p.door("canteen", "hall", kind="metal")
    p.door("ostair", "hall", kind="metal")
    p.door("ustair", "control", 1)
    p.door("ustair", "plantmgr", 1)
    p.door("workshop", "hall", kind="rollup_small")
    p.door("workshop", None, kind="metal", side="back", role="service")
    p.door("workshop", None, kind="rollup_small", side="right", role="loading", at=d - 13.0)
    for i in range(3):
        p.door("hall", None, kind="rollup", side="back", role="loading", at=8.0 + i * 18.0)
    p.door("hall", None, kind="rollup", side="front", role="loading", at=(ob + mx) / 2)
    p.door("hall", None, kind="metal", side="left", role="secondary", at=d * 0.6)
    p.door("hall", None, kind="metal", side="right", role="secondary", at=my * 0.5)

    def stack(B):
        s = B.out.ext
        sx, sy = w + 12.0, d * 0.35
        s.box("concrete", sx - 6, sy - 6, -1.0, sx + 6, sy + 6, 2.0)
        s.cyl("brick_red", sx, sy, 2.0, 4.5, 86.0, 16)
        for z in (30.0, 60.0, 84.0):
            s.cyl("brick_dark", sx, sy, z, 4.9, 2.0, 16)
        s.cyl("metal_dark", sx, sy, 88.0, 4.0, 1.0, 16, collide=False)
        s.box("metal_dark", w, sy - 1.2, 20.0, sx - 4.4, sy + 1.2, 22.4)
        for k in range(3):
            tx, ty = -14.0, 24.0 + k * 16.0
            s.box("concrete", tx - 7, ty - 7, -1.0, tx + 7, ty + 7, 0.5)
            s.cyl("metal_white", tx, ty, 6.0, 6.0, 30.0, 14)
            for a in range(4):
                ang = a * math.pi / 2 + 0.5
                s.box("metal_gray", tx + 5 * math.cos(ang) - 0.4, ty + 5 * math.sin(ang) - 0.4,
                      0.5, tx + 5 * math.cos(ang) + 0.4, ty + 5 * math.sin(ang) + 0.4, 6.0)
            s.cyl("metal_white", tx, ty, 36.0, 3.0, 3.0, 10)
        s.box("metal_yellow", -14.0, 22.0, 26.0, 0.0, 24.0, 27.0)
        from ..records import LightRec, Marker
        B.out.lights.append(LightRec(sx, sy, 90.0, (1.0, 0.2, 0.2), 30, 1.0, "point", "night"))
        B.out.markers.append(Marker("landmark", sx, sy, 0.0, 0.0, "Cannery Smokestack"))
    p.extras.append(stack)
    p.extras.append(loading_dock(0, 60, 14.0))
    p.signs.append(Sign(p.name.upper(), "front", 0, "roof", bg="sign_cream", fg="sign_red",
                        neon=True, width=60.0, at=w * 0.55))
    p.lighting = "work"
    p.tags |= {"cannery", "skylights"}
    finishes(p, c.rng)
    return p
