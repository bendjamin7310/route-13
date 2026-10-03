"""Roadside archetypes: the two-storey motel with exterior walkways, and the gas station."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import finishes, canopy, _pp
from .commercial import convenience_store
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect, Sink, rot_x
from ..records import LightRec, Marker

ROOM_W = 15.0
ROOM_D = 20.0
BATH_D = 8.0
WING_D = ROOM_D + BATH_D


@archetype("motel", (140, 180), (90, 120), "MOTEL", "RESIDENTIAL", front_setback=60,
           rear_clear=12, side_gap=14, yard="motel")
def motel(c: Ctx) -> Plan:
    """L-shaped two-storey motor inn: office + manager's flat in the corner block, rooms
    off exterior walkways, exterior stairs, ice/vending alcove, housekeeping, pool."""
    w, d = c.w, c.d
    name = c.name or c.pick_name(["SEABREEZE MOTOR INN", "HARBOR LIGHT MOTEL", "DRIFTWOOD INN"])
    p = Plan(w, d, [12.0, 12.0], quality="cheap", detail=c.detail, name=name)
    p.facade = Facade(mat=c.pick(["stucco_peach", "stucco_mint", "stucco_sky", "stucco_cream",
                                  "stucco_mustard"]), trim="trim_white", frame="frame_alu",
                      base="concrete", bay=ROOM_W, window_w=5.0)
    p.roof = Roof("flat", "roof_tar", parapet=1.5, coping="trim_white", equipment="auto")
    cw = WING_D
    # corner block: office / housekeeping / manager's flat
    p.room("office", "motel_office", R(0, 0, cw, 14), name="Front Office",
           tags={"always_lit"})
    p.room("staff", "employee", R(0, 14, 12, cw), name="Staff Room")
    p.room("laundry", "laundry", R(12, 14, cw, cw), name="Housekeeping Laundry")
    p.door("office", None, kind="glass", side="front", role="main", at=cw * 0.5)
    p.door("office", "staff")
    p.door("staff", "laundry")
    p.door("staff", None, kind="metal", side="left", role="service")
    p.room("mgr_liv", "living", R(0, 0, cw, 16), 1, name="Manager's Flat",
           unit="MGR", tags={"q:normal"})
    p.room("mgr_bed", "bedroom", R(0, 16, 16, cw), 1, unit="MGR", name="Manager's Bedroom")
    p.room("mgr_bath", "bathroom", R(16, 16, cw, cw), 1, unit="MGR", name="Manager's Bath")
    p.door("mgr_liv", "mgr_bed", 1)
    p.door("mgr_bed", "mgr_bath", 1)
    p.door("mgr_liv", None, 1, kind="exterior", side="front", role="flat", at=cw - 3.0)
    # main wing along the front (doors face the lot, y < 0)
    n = int((w - cw - 8) / ROOM_W)
    num = {0: 101, 1: 201}
    vend_at = n // 2
    for L in (0, 1):
        x = cw
        for i in range(n):
            if L == 0 and i == vend_at:
                p.room("vend", "vending", R(x, 0, x + 8, ROOM_D), name="Ice & Vending")
                p.room("vend_store", "storage", R(x, ROOM_D, x + 8, WING_D),
                       name="Linen Closet")
                p.door("vend", None, kind="opening", side="front", role="vending", width=5.0)
                p.door("vend", "vend_store", locked=True)
                x += 8
            rid = f"r{num[L]}"
            worn = c.chance(0.4)
            tags = {"worn", "q:cheap"} if worn else {"q:normal"}
            p.room(rid, "motel_room", R(x, 0, x + ROOM_W, ROOM_D), L, name=f"Room {num[L]}",
                   unit=str(num[L]), tags=tags)
            p.room(rid + "b", "motel_bath", R(x, ROOM_D, x + ROOM_W, WING_D), L,
                   name=f"Room {num[L]} Bath", unit=str(num[L]), tags=tags)
            p.door(rid, None, L, kind="exterior", side="front", role="room",
                   at=x + 3.5)
            p.door(rid, rid + "b", L)
            num[L] += 1
            x += ROOM_W
        if L == 1:
            p.room("vend_up", "storage", R(cw + vend_at * ROOM_W, 0, cw + vend_at * ROOM_W + 8,
                                           WING_D), 1, name="Maintenance Closet")
            p.door("vend_up", None, 1, kind="metal", side="front", role="maintenance")
    wing_end = x
    # side wing along the left edge, doors face +x (the courtyard)
    m = int((d - cw - 6) / ROOM_W)
    for L in (0, 1):
        y = cw
        for i in range(m):
            rid = f"r{num[L]}"
            tags = {"worn", "q:cheap"} if c.chance(0.4) else {"q:normal"}
            p.room(rid, "motel_room", R(BATH_D, y, cw, y + ROOM_W), L, name=f"Room {num[L]}",
                   unit=str(num[L]), tags=tags)
            p.room(rid + "b", "motel_bath", R(0, y, BATH_D, y + ROOM_W), L,
                   name=f"Room {num[L]} Bath", unit=str(num[L]), tags=tags)
            p.door(rid, None, L, kind="exterior", side="right", role="room", at=y + 3.5)
            p.door(rid, rid + "b", L)
            num[L] += 1
            y += ROOM_W
    side_end = y

    def walkways(B):
        s = B.out.ext
        zw = B.z(1)
        # main wing walkway + covered balcony
        x0, x1 = cw, wing_end
        s.box("concrete_light", x0 - 6, -7.0, -1.0, x1 + 7, 0.0, -0.4)
        s.box("concrete", x0, -6.5, zw - 1.0, x1, 0.0, zw, True)
        s.box("trim_white", x0, -6.5, zw - 1.0, x1, -6.2, zw + 3.4, False)
        s.box("trim_white", x0, -6.7, zw + 3.2, x1, -6.2, zw + 3.5, True)
        for k in range(int((x1 - x0) / 0.9)):
            xx = x0 + 0.4 + k * 0.9
            s.box("trim_white", xx, -6.5, zw, xx + 0.12, -6.38, zw + 3.2, False)
        for xx in range(int(x0), int(x1) + 1, int(ROOM_W)):
            s.box("trim_white", xx - 0.4, -6.4, -0.4, xx + 0.4, -5.6, zw + 12.0, True)
        s.box("roof_tar", x0 - 0.5, -7.5, zw + 12.0, x1 + 0.5, 0.0, zw + 12.6, True)
        s.box("trim_white", x0 - 0.5, -7.6, zw + 11.4, x1 + 0.5, -7.3, zw + 12.6, False)
        # side wing walkway
        y0, y1 = cw, side_end
        s.box("concrete_light", cw, y0, -1.0, cw + 7.0, y1 + 6, -0.4)
        s.box("concrete", cw, y0 - 6.5, zw - 1.0, cw + 6.5, y1, zw, True)
        s.box("trim_white", cw + 6.2, y0, zw - 1.0, cw + 6.5, y1, zw + 3.4, False)
        s.box("trim_white", cw + 6.2, y0, zw + 3.2, cw + 6.7, y1, zw + 3.5, True)
        for yy in range(int(y0), int(y1) + 1, int(ROOM_W)):
            s.box("trim_white", cw + 5.6, yy - 0.4, -0.4, cw + 6.4, yy + 0.4, zw + 12.0, True)
        s.box("roof_tar", cw, y0 - 7.0, zw + 12.0, cw + 7.5, y1 + 0.5, zw + 12.6, True)
        # exterior stairs at the far end of the main wing and next to the office
        for (sx, sdir) in ((x1 + 1.0, 1), (cw - 0.5 - 4.4, -1)):
            nst = 13
            for k in range(nst):
                zt = (k + 1) * zw / nst
                yy0 = -7.0 - 15.6 + k * 1.2
                s.box("concrete", sx, yy0, max(-0.6, zt - 1.6), sx + 4.4, yy0 + 1.2, zt, True)
            s.box("concrete", sx, -7.0, zw - 1.0, sx + 4.4, 0.0, zw, True)
            s.box("metal_dark", sx - 0.15, -22.6, 0, sx, -7.0, zw + 3.4, False)
            s.box("metal_dark", sx + 4.4, -22.6, 0, sx + 4.55, -7.0, zw + 3.4, False)
        # pool in the courtyard
        px0, py0 = cw + 26.0, cw + 18.0
        px1, py1 = min(wing_end - 10.0, px0 + 50.0), py0 + 26.0
        s.box("concrete_light", px0 - 6, py0 - 6, -1.0, px1 + 6, py1 + 6, 0.0, True)
        s.box("tile_bath_blue", px0, py0, -0.6, px1, py1, 0.05, False)
        s.box("water", px0 + 0.4, py0 + 0.4, -0.3, px1 - 0.4, py1 - 0.4, -0.05, False)
        for k in range(4):
            B.out.props.append(_pp("pool_lounger", px0 - 3.5, py0 + 3 + k * 6, 0.0,
                                   math.pi / 2))
        B.out.props.append(_pp("pool_ladder", px1 - 4.0, py0 + 0.4, 0.0, 0.0))
        B.out.props.append(_pp("fence_iron", (px0 + px1) / 2, py0 - 6.2, 0.0, 0.0))
        B.out.lights.append(LightRec((px0 + px1) / 2, (py0 + py1) / 2, 0.5, (0.5, 0.9, 1.0),
                                     30, 0.8, "point", "night"))
        B.out.markers.append(Marker("poi", (px0 + px1) / 2, py1 + 4.0, 0, 0, "Motel Pool"))
        # walkway lights
        for xx in range(int(x0) + 7, int(x1), int(ROOM_W)):
            for zz in (0.0, zw):
                B.out.lights.append(LightRec(xx, -3.0, zz + 10.5, (1.0, 0.85, 0.6), 14, 0.7,
                                             "point", "night"))
    p.extras.append(walkways)
    p.signs.append(Sign(name, "front", 0, "pole", bg="sign_teal", fg="sign_white", neon=True,
                        at=w - 12.0, width=26.0, offset=46.0))
    p.signs.append(Sign("VACANCY", "front", 0, "pole", bg="sign_black", fg="sign_red",
                        neon=True, at=w - 12.0, width=14.0, offset=46.5, z=14.0))
    p.signs.append(Sign("OFFICE", "front", 0, "board", bg="sign_red", fg="sign_white",
                        neon=True, at=cw * 0.5, width=12.0))
    p.lighting = "res"
    p.tags |= {"motel"}
    p.exterior_props += [("ice_merchandiser", cw + vend_at * ROOM_W + 4.0, -9.0, -0.6, 0.0,
                          None),
                         ("dumpster", w - 10.0, WING_D + 6.0, -0.6, 0.0, {"$metal": "metal_blue"}),
                         ("payphone_stand", cw - 3.0, -9.0, -0.6, 0.0, None),
                         ("laundry_cart", cw + 2.0, -3.0, 0.0, 0.0, {"$fabric": "fabric_white"})]
    finishes(p, c.rng)
    return p


@archetype("gas_station", (46, 56), (40, 50), "COMMERCIAL", "COMMERCIAL", front_setback=46,
           rear_clear=10, side_gap=12, yard="fuel")
def gas_station(c: Ctx) -> Plan:
    c.name = c.name or c.pick_name(["SOLACE FUEL", "HARBOR GAS & GO", "TIDEWATER FUEL STOP",
                               "COASTLINE GAS", "BAYSIDE FUEL", "LAST CHANCE GAS",
                               "ROUTE 13 FUEL"])
    p = convenience_store(c)
    p.name = c.name
    w, d = p.w, p.d
    p.extras.append(canopy(-6.0, -40.0, w + 6.0, -12.0, 16.0, mat="metal_white",
                           post="metal_white", band="sign_red",
                           posts=[(6.0, -26.0), (w - 6.0, -26.0)]))
    for x in (w * 0.25, w * 0.75):
        p.exterior_props.append(("gas_pump", x, -26.0, -0.6, math.pi / 2,
                                 {"$sign": "sign_red"}))
    p.exterior_props += [("air_pump", w + 4.0, -6.0, -0.6, 0.0, None),
                         ("trash_bin_street", w * 0.25, -20.0, -0.6, 0.0, None),
                         ("trash_bin_street", w * 0.75, -32.0, -0.6, 0.0, None)]
    p.signs.append(Sign(c.name, "front", 0, "pole", bg="sign_red", fg="sign_white", neon=True,
                        at=w + 4.0, width=16.0, offset=44.0))
    p.tags.add("fuel")
    p.lighting = "always"
    return p
