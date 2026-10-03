"""Landmark archetypes: lighthouse + keeper's house (radio studio), water tower with pump
house, multi-level parking structure, hilltop estate."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import finishes, _pp, back_patio
from .residential import house_nice
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect, Sink, rot_x, rot_z, mat_mul, subtract_many
from ..records import LightRec, Marker, SignRec


@archetype("lighthouse", (44, 44), (32, 32), "LANDMARKS", "CIVIC", front_setback=20,
           rear_clear=10, side_gap=10, yard="none")
def lighthouse(c: Ctx) -> Plan:
    """Solace Point Light: a square stone tower (stacked switchback stairs, slit windows,
    glazed lantern room with gallery) joined to the keeper's house, which now holds the
    town's late-night radio studio."""
    w, d = 44.0, 32.0
    nt = 6
    p = Plan(w, d, [12.0] * nt + [10.0], quality="normal", detail=c.detail,
             name=c.name or "Solace Point Lighthouse")
    p.facade = Facade(mat="stucco_white", trim="trim_red", frame="trim_dark", base="stone_base",
                      bay=7.0, window_w=3.0)
    p.facade.side_mats = {}
    p.roof = Roof("gable", "roof_shingle_red", pitch=0.6, ridge="y", overhang=1.2,
                  chimney=True)
    hx = 28.0
    tx0, ty0, tx1, ty1 = hx, 9.0, w, d - 9.0
    p.roof.masses = [(Rect(0, 0, hx, d), "y")]
    # keeper's house (ground: studio, hall, kitchen, stair, bath; upper: bedroom, records)
    p.room("studio", "radio_studio", R(0, 0, hx, 14), name="Dust FM Studio")
    p.room("hall", "hall", R(0, 14, hx, 19), name="Hall")
    p.room("kitchen", "kitchen_dining", R(0, 19, 14, d), name="Keeper's Kitchen")
    p.room("hst0", "stair", R(14, 19, 20, d), name="House Stair")
    p.room("bath", "bathroom", R(20, 19, hx, d), name="Bath")
    p.room("bed", "bedroom", R(0, 0, 14, d), 1, name="Keeper's Bedroom")
    p.room("uhall", "hall", R(14, 0, 20, d), 1, name="Upper Hall")
    p.room("record", "storage", R(20, 0, hx, d), 1, name="Record Library")
    p.stair(R(14.6, 19.6, 19.4, d - 0.6), 0, "straight", "-y")
    p.door("studio", None, kind="exterior", side="front", role="main")
    p.door("studio", "hall", kind="opening")
    p.door("hall", "kitchen")
    p.door("hall", "bath")
    p.door("kitchen", "hst0", at=d - 3.0)
    p.door("kitchen", None, kind="exterior", side="left", role="secondary")
    p.door("uhall", "bed", 1)
    p.door("uhall", "record", 1)
    # tower: one room per level, stacked switchback stairs, slit windows, lantern on top
    for L in range(nt):
        p.room(f"t{L}", "stair", R(tx0, ty0, tx1, ty1), L, name=f"Tower Level {L + 1}",
               window="tall")
    srect = R(tx0 + 1.0, ty0 + 5.0, tx1 - 1.0, ty1 - 0.8)
    for L in range(nt):
        p.stair(srect, L, "u", "+y")
    p.room("lantern", "lantern", R(tx0, ty0, tx1, ty1), nt, name="Lantern Room",
           window="lantern", light="none")
    p.door("hall", "t0")
    p.door("t0", None, kind="exterior", side="right", role="tower")
    p.door("record", "t1", 1)

    def gallery(B):
        s = B.out.ext
        zg = B.z(nt)
        s.box("concrete_light", tx0 - 3.0, ty0 - 3.0, zg - 1.0, tx1 + 3.0, ty1 + 3.0, zg, True)
        for (x0, y0, x1, y1) in ((tx0 - 3, ty0 - 3, tx1 + 3, ty0 - 2.8),
                                 (tx0 - 3, ty1 + 2.8, tx1 + 3, ty1 + 3),
                                 (tx0 - 3, ty0 - 3, tx0 - 2.8, ty1 + 3),
                                 (tx1 + 2.8, ty0 - 3, tx1 + 3, ty1 + 3)):
            s.box("metal_dark", x0, y0, zg + 3.2, x1, y1, zg + 3.5, True)
        for i in range(9):
            for (x, y) in ((tx0 - 3 + i * (tx1 - tx0 + 6) / 8, ty0 - 2.9),
                           (tx0 - 3 + i * (tx1 - tx0 + 6) / 8, ty1 + 2.9)):
                s.box("metal_dark", x - 0.08, y - 0.08, zg, x + 0.08, y + 0.08, zg + 3.2, False)
        top = zg + 10.0
        s.box("metal_dark", tx0 - 0.5, ty0 - 0.5, top, tx1 + 0.5, ty1 + 0.5, top + 0.8, True)
        cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
        from ..kit.shapes import cone
        cone(s, "roof_metal_red", cx, cy, top + 0.8, 9.5, 0.6, 5.5, 8)
        s.ball("metal_dark", cx, cy, top + 6.8, 0.9)
        s.cyl("metal_dark", cx, cy, top + 7.4, 0.15, 4.0, 6, collide=False)
        # the light itself
        s.cyl("metal_brass", cx, cy, zg, 1.2, 3.0, 10, collide=True)
        s.cyl("lamp_warm", cx, cy, zg + 3.0, 2.2, 3.6, 12, collide=False)
        B.out.lights.append(LightRec(cx, cy, zg + 5.0, (1.0, 0.92, 0.75), 160, 3.0, "spot",
                                     "night", dir_=(0.0, -1.0, -0.08)))
        B.out.markers.append(Marker("lighthouse_beam", cx, cy, zg + 5.0, 0.0, "Rotating beam",
                                    {"rpm": 4}))
        B.out.markers.append(Marker("landmark", cx, cy, 0.0, 0.0, "Solace Point Lighthouse"))
        # stripe bands on the tower
        for k in (2, 4):
            z = B.z(k)
            s.box("trim_red", tx0 - 0.15, ty0 - 0.15, z - 1.5, tx1 + 0.15, ty1 + 0.15, z + 1.5,
                  False)
        # radio aerial on the house
        s.cyl("metal", 4.0, d - 4.0, B.z(2), 0.2, 26.0, 6, collide=False)
        for zz in (12.0, 18.0, 24.0):
            s.box("metal", 1.5, d - 4.1, B.z(2) + zz, 6.5, d - 3.9, B.z(2) + zz + 0.2, False)
    p.extras.append(gallery)
    p.signs.append(Sign("DUST FM 13.0", "front", 0, "board", bg="sign_black", fg="sign_orange",
                        neon=True, at=hx / 2, width=18.0))
    p.lighting = "late"
    p.tags |= {"lighthouse"}
    finishes(p, c.rng)
    return p


@archetype("water_tower", (26, 26), (20, 20), "LANDMARKS", "SERVICE", front_setback=14,
           rear_clear=60, side_gap=24, yard="gated")
def water_tower(c: Ctx) -> Plan:
    """Pump house (enterable: pumps, control panel, tool room) with the town's water tower
    standing behind it; a ladder and catwalk give rooftop-style access high above town."""
    w, d = 26.0, 20.0
    p = Plan(w, d, [12.0], quality="normal", detail=c.detail, name="Port Solace Water Tower")
    p.facade = Facade(mat="block_painted", trim="trim_blue", frame="frame_dark", base="concrete",
                      bay=8.0)
    p.roof = Roof("flat", "roof_metal", parapet=1.0, coping="metal_white")
    p.room("pumps", "mechanical", R(0, 0, 16, d), name="Pump Room")
    p.room("ctrl", "control_room", R(16, 0, w, 11), name="Control")
    p.room("tools", "storage", R(16, 11, w, d), name="Tool Room")
    p.door("pumps", None, kind="metal", side="front", role="main")
    p.door("pumps", "ctrl")
    p.door("ctrl", "tools")
    p.door("tools", None, kind="metal", side="back", role="tower")

    def tower(B):
        s = B.out.ext
        cx, cy = w / 2, d + 34.0
        R0 = 14.0
        zt = 72.0
        for a in range(4):
            ang = math.pi / 4 + a * math.pi / 2
            lx, ly = cx + R0 * math.cos(ang), cy + R0 * math.sin(ang)
            s.box("concrete", lx - 2.0, ly - 2.0, -1.0, lx + 2.0, ly + 2.0, 1.0)
            s.cyl("metal_white", lx, ly, 1.0, 0.9, zt - 1.0, 10)
        for z in (18.0, 36.0, 54.0):
            for a in range(4):
                a0 = math.pi / 4 + a * math.pi / 2
                a1 = a0 + math.pi / 2
                x0, y0 = cx + R0 * math.cos(a0), cy + R0 * math.sin(a0)
                x1, y1 = cx + R0 * math.cos(a1), cy + R0 * math.sin(a1)
                L = math.hypot(x1 - x0, y1 - y0)
                yaw = math.atan2(y1 - y0, x1 - x0)
                s.obox("metal_white", (x0 + x1) / 2, (y0 + y1) / 2, z, L, 0.4, 0.4,
                       rot_z(yaw))
        s.cyl("metal_white", cx, cy, zt, 17.0, 24.0, 24)
        from ..kit.shapes import cone
        cone(s, "metal_white", cx, cy, zt + 24.0, 17.6, 1.0, 7.0, 24)
        cone(s, "metal_white", cx, cy, zt - 6.0, 4.0, 17.0, 6.0, 24)
        s.cyl("metal_white", cx, cy, 0.0, 1.6, zt - 6.0, 10)
        # catwalk ring
        for k in range(24):
            ang = 2 * math.pi * k / 24
            x, y = cx + 19.2 * math.cos(ang), cy + 19.2 * math.sin(ang)
            s.obox("diamond_plate", x, y, zt - 0.3, 5.2, 2.6, 0.3, rot_z(ang + math.pi / 2), True)
            x2, y2 = cx + 20.4 * math.cos(ang), cy + 20.4 * math.sin(ang)
            s.obox("metal_dark", x2, y2, zt + 3.2, 5.4, 0.2, 0.2, rot_z(ang + math.pi / 2), True)
            s.box("metal_dark", x2 - 0.1, y2 - 0.1, zt, x2 + 0.1, y2 + 0.1, zt + 3.2, False)
        # ladder up the south-west leg
        lx, ly = cx - R0 * 0.72, cy - R0 * 0.72
        n = int(zt / 1.0)
        s.box("metal_dark", lx - 0.9, ly - 1.6, 0.0, lx - 0.7, ly - 1.4, zt, True)
        s.box("metal_dark", lx + 0.7, ly - 1.6, 0.0, lx + 0.9, ly - 1.4, zt, True)
        for i in range(n):
            s.box("metal_dark", lx - 0.8, ly - 1.55, i * 1.0 + 0.5, lx + 0.8, ly - 1.45,
                  i * 1.0 + 0.6, False)
        B.out.markers.append(Marker("ladder", lx, ly - 2.0, 0.0, 0.0, "Water tower ladder",
                                    {"top": zt}))
        B.out.markers.append(Marker("landmark", cx, cy, 0.0, 0.0, "Water Tower"))
        B.out.markers.append(Marker("vantage", cx, cy - 19.0, zt, 0.0, "Catwalk lookout"))
        B.out.signs.append(SignRec(
            "PORT SOLACE", cx, cy - 17.1, zt + 12.0, 0.0, 26.0, 5.5, "sign_blue", "sign_blue",
            False, False))
        for a in range(4):
            ang = a * math.pi / 2
            B.out.lights.append(LightRec(cx + 18 * math.cos(ang), cy + 18 * math.sin(ang),
                                         zt + 2.0, (1.0, 0.9, 0.75), 40, 1.2, "spot", "night",
                                         dir_=(math.cos(ang) * 0.2, math.sin(ang) * 0.2, 1.0)))
        B.out.lights.append(LightRec(cx, cy, zt + 31.5, (1.0, 0.2, 0.2), 20, 1.0, "point",
                                     "night"))
    p.extras.append(tower)
    p.lighting = "work"
    finishes(p, c.rng)
    return p


@archetype("parking_structure", (84, 140), (84, 104), "LANDMARKS", "SERVICE",
           front_setback=6, rear_clear=8, side_gap=8, yard="none")
def parking_structure(c: Ctx) -> Plan:
    """Four-level public parking garage: stacked vehicle ramps, two stair towers (one
    reaching the roof), pay booth, open bays on every facade."""
    w, d = c.w, c.d
    nl = c.opts.get("levels", 4)
    p = Plan(w, d, [11.0] * nl, quality="normal", detail=c.detail,
             name=c.name or "Harbor Street Parking")
    p.facade = Facade(mat="concrete_light", trim="concrete", frame="concrete", base="concrete",
                      bay=10.0, band=True)
    p.roof = Roof("flat", "asphalt", parapet=3.6, coping="concrete", access=True,
                  equipment="none")
    t1 = R(0, 0, 14, 22)
    t2 = R(w - 14, d - 22, w, d)
    ramp = R(32.0, 24.0, 48.0, d - 16.0)
    for L in range(nl):
        deck = p.room(f"deck{L}", "parking", R(0, 0, 1, 1), L, name=f"Level {L + 1}",
                      window="open", tags={"always_lit"})
        deck.cells[L] = subtract_many([R(0, 0, w, d)], [t1, t2])
        p.room(f"ta{L}", "stair", t1, L, name="Stair A", tags={"always_lit"})
        p.room(f"tb{L}", "stair", t2, L, name="Stair B", tags={"always_lit"})
        p.door(f"ta{L}", f"deck{L}", L, kind="metal")
        p.door(f"tb{L}", f"deck{L}", L, kind="metal")
        if L < nl - 1:
            p.stair(ramp, L, "ramp", "+y")
            p.stair(R(1.0, 5.0, 13.0, 21.2), L, "u", "+y")
            p.stair(R(w - 13.0, d - 17.0, w - 1.0, d - 0.8), L, "u", "+y")
    p.stair(R(1.0, 5.0, 13.0, 21.2), nl - 1, "u", "+y", to_roof=True)
    # ground: vehicle entrance/exit and pedestrian doors
    p.door("deck0", None, kind="opening", side="front", role="vehicle entrance",
           at=w * 0.55, width=16.0, height=9.0)
    p.door("deck0", None, kind="opening", side="front", role="vehicle exit", at=w * 0.8,
           width=16.0, height=9.0)
    p.door("deck0", None, kind="opening", side="back", role="vehicle", at=w * 0.6,
           width=16.0, height=9.0)
    p.door("ta0", None, kind="glass", side="front", role="pedestrian")
    p.door("tb0", None, kind="metal", side="back", role="pedestrian")

    def booth(B):
        B.out.props.append(_pp("guard_booth", w * 0.67, 8.0, 0.0, 0.0))
        B.out.props.append(_pp("gate_arm", w * 0.55 - 7.0, 4.0, 0.0, 0.0))
        B.out.props.append(_pp("gate_arm", w * 0.8 - 7.0, 4.0, 0.0, 0.0))
        B.out.props.append(_pp("ticket_kiosk", w * 0.55 + 9.5, 4.0, 0.0, 0.0))
        B.out.markers.append(Marker("landmark", w / 2, d / 2, 0.0, 0.0, "Parking Structure"))
    p.extras.append(booth)
    p.signs.append(Sign("PUBLIC PARKING", "front", 0, "board", bg="sign_blue", fg="sign_white",
                        neon=True, at=w * 0.67, width=26.0))
    p.lighting = "always"
    p.tags |= {"parking"}
    finishes(p, c.rng)
    return p


@archetype("mansion", (72, 82), (60, 68), "LANDMARKS", "RESIDENTIAL", front_setback=40,
           rear_clear=44, side_gap=24, yard="estate")
def mansion(c: Ctx) -> Plan:
    c.quality = "nice"
    p = house_nice(c)
    p.name = c.name or "Corrigan Estate"
    p.facade.mat = "stucco_white"
    p.roof.mat = "roof_tile"

    def pool(B):
        s = B.out.ext
        d = B.p.d
        x0, x1 = 8.0, B.p.w - 8.0
        y0, y1 = d + 14.0, d + 36.0
        s.box("limestone", x0 - 6, y0 - 6, -1.0, x1 + 6, y1 + 6, 0.0, True)
        s.box("tile_bath_blue", x0, y0, -0.6, x1, y1, 0.05, False)
        s.box("water", x0 + 0.4, y0 + 0.4, -0.3, x1 - 0.4, y1 - 0.4, -0.05, False)
        for k in range(5):
            B.out.props.append(_pp("pool_lounger", x0 + 4 + k * 8, y1 + 3.5, 0.0, math.pi))
        B.out.props.append(_pp("pool_ladder", x1 - 3.0, y0 + 0.4, 0.0, 0.0))
        B.out.lights.append(LightRec((x0 + x1) / 2, (y0 + y1) / 2, 0.5, (0.5, 0.9, 1.0), 40, 1.0,
                                     "point", "night"))
        B.out.markers.append(Marker("landmark", B.p.w / 2, d / 2, 0.0, 0.0, "Hilltop Estate"))
        B.out.markers.append(Marker("safehouse", B.p.w / 2, -6.0, 0.0, 0.0, "Estate (high-end)"))
    p.extras.append(pool)
    p.tags.add("estate")
    return p
