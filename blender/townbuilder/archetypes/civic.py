"""Civic and emergency-service archetypes: police station, fire station, town hall."""

from __future__ import annotations

import math

from . import archetype, Ctx
from .common import finishes, _pp
from ..archi.plan import Plan, R, Facade, Roof, Sign
from ..geom import Rect, Sink, rot_z
from ..records import LightRec, Marker


@archetype("police_station", (96, 110), (104, 120), "POLICE", "CIVIC", front_setback=24,
           rear_clear=10, side_gap=16, yard="police")
def police_station(c: Ctx) -> Plan:
    """Municipal police station.  Public lobby + front desk, secure corridor, bullpen,
    interview rooms, briefing, evidence, lockers, holding cells, sally-port garage and an
    admin floor upstairs (chief, dispatch, offices, break room)."""
    w, d = c.w, c.d
    p = Plan(w, d, [14.0, 13.0], quality="normal", detail=c.detail,
             name=c.name or "Port Solace Police Department")
    p.facade = Facade(mat=c.pick(["brick_tan", "brick_cream", "concrete_light", "brick_brown"]),
                      ground=None, trim="concrete_light", frame="frame_dark", glass="glass_tint",
                      base="granite", cornice=True, band=True, bay=10.0)
    p.roof = Roof("flat", "roof_gravel", parapet=3.0, access=True)
    D = 82.0          # main block depth; garage behind it
    cy = 24.0
    # ---- ground floor, front band (public / interview)
    p.room("records", "records", R(0, 0, 24, cy), name="Records & Admin")
    p.room("lobby", "lobby", R(24, 0, 50, cy), name="Public Lobby", tags={"always_lit"})
    p.room("desk", "reception", R(50, 0, 62, cy), name="Front Desk")
    p.room("int1", "interview", R(62, 0, 74, cy), name="Interview Room 1", light="fluor_panel")
    p.room("int2", "interview", R(74, 0, 86, cy), name="Interview Room 2", light="fluor_panel")
    p.room("obs", "office", R(86, 0, w, cy), name="Detectives' Office")
    # secure corridor
    p.room("corr", "corridor", R(0, cy, w, cy + 6), name="Secure Corridor", tags={"always_lit"})
    # back band
    by = cy + 6
    p.room("stair0", "stair", R(0, by, 14, by + 18), name="Staff Stair")
    p.room("bull", "bullpen", R(14, by, 44, D), name="Patrol Bullpen")
    p.room("wc0", "restroom", R(0, by + 18, 14, D), name="Staff Restrooms")
    p.room("brief", "briefing", R(44, by, 64, by + 26), name="Briefing Room")
    p.room("evid", "evidence", R(44, by + 26, 64, D), name="Evidence Room")
    p.room("lock_m", "locker", R(64, by, 78, by + 26), name="Men's Lockers")
    p.room("lock_w", "locker", R(64, by + 26, 78, D), name="Women's Lockers")
    p.room("cellcorr", "corridor", R(78, by, 84, D), name="Cell Block",
           tags={"always_lit"})
    ncell = 4
    ch = (D - by) / ncell
    for i in range(ncell):
        p.room(f"cell{i}", "cell", R(84, by + i * ch, w, by + (i + 1) * ch),
               name=f"Holding Cell {i + 1}")
        p.door("cellcorr", f"cell{i}", kind="cell", locked=True)
    # sally port + vehicle storage behind the main block
    p.room("sally", "sallyport", R(40, D, w, d), name="Sally Port & Garage")
    p.room("armory", "storage", R(0, D, 40, d), name="Equipment Storage", tags={"secure"})
    p.stair(R(1.0, by + 4.5, 13.0, by + 17.5), 0, "u", "+y")
    # doors (ground)
    p.door("lobby", None, kind="glass_double", side="front", role="main")
    p.door("lobby", "desk", kind="opening")
    p.door("desk", "corr", kind="metal", locked=True)
    p.door("records", "lobby")
    p.door("records", "corr")
    p.door("corr", "int1")
    p.door("corr", "int2")
    p.door("corr", "obs")
    p.door("corr", "stair0", kind="opening")
    p.door("corr", "bull", kind="double")
    p.door("corr", "brief")
    p.door("corr", "lock_m")
    p.door("brief", "evid", locked=True)
    p.door("corr", "cellcorr", kind="metal", locked=True)
    p.door("stair0", "wc0")
    p.door("evid", "lock_w")
    p.door("cellcorr", "sally", kind="metal", locked=True, role="prisoner transfer")
    p.door("armory", "sally")
    p.door("bull", "armory", locked=True)
    p.door("sally", None, kind="garage2", side="right", role="vehicle", width=14.0)
    p.door("sally", None, kind="garage2", side="back", role="vehicle", at=(40 + w) / 2,
           width=14.0)
    p.door("armory", None, kind="metal", side="left", role="secondary")
    p.door("obs", None, kind="metal", side="right", role="staff")
    # ---- admin floor
    p.room("stair1", "stair", R(0, by, 14, by + 18), 1, name="Staff Stair")
    p.room("chief", "office", R(0, 0, 26, cy), 1, name="Chief's Office", tags={"chief"})
    p.room("admin", "office_open", R(26, 0, 64, cy), 1, name="Administration")
    p.room("meet", "meeting", R(64, 0, w, cy), 1, name="Command Conference")
    p.room("ucorr", "corridor", R(0, cy, w, by), 1, name="Upper Corridor")
    p.room("disp", "dispatch", R(14, by, 44, D), 1, name="Dispatch Center",
           tags={"always_lit"})
    p.room("break", "breakroom", R(44, by, 70, D), 1, name="Break Room")
    p.room("wc1", "restroom", R(0, by + 18, 14, D), 1, name="Restrooms")
    p.room("it", "electrical", R(70, by, 84, D), 1, name="Server Room")
    p.room("dets", "office_open", R(84, by, w, D), 1, name="Investigations")
    p.stair(R(1.0, by + 4.5, 13.0, by + 17.5), 1, "u", "+y", to_roof=True)
    for r in ("chief", "admin", "meet", "disp", "break", "it", "dets", "stair1"):
        p.door("ucorr", r, 1, kind="opening" if r == "stair1" else "interior")
    p.door("stair1", "wc1", 1)
    # exterior / gameplay
    p.signs.append(Sign("POLICE", "front", 0, "board", bg="police_blue", fg="sign_white",
                        neon=True, width=22.0, at=37.0))
    p.signs.append(Sign(p.name.upper(), "front", 1, "letters", bg="sign_black",
                        fg="sign_white"))
    p.lighting = "always"
    p.tags |= {"police", "civic"}
    p.exterior_props += [("flagpole", 20.0, -12.0, -0.6, 0.0, None),
                         ("bench_park", 46.0, -6.0, -0.6, math.pi, None),
                         ("bollard", 36.0, -3.0, -0.6, 0.0, None),
                         ("bollard", 56.0, -3.0, -0.6, 0.0, None),
                         ("generator", 10.0, d + 6.0, -0.6, 0.0, None)]

    def lights(B):
        for x in (8.0, w - 8.0):
            for y in (8.0, d - 8.0):
                B.out.lights.append(LightRec(x, y, p.height + 3.5, (0.95, 0.97, 1.0), 40, 1.4,
                                             "spot", "night"))
        B.out.markers.append(Marker("poi", 46.0, -8.0, 0.0, 0.0, "Police Station",
                                    {"type": "police"}))
    p.extras.append(lights)
    finishes(p, c.rng)
    return p


@archetype("fire_station", (76, 86), (88, 96), "FIRE", "CIVIC", front_setback=36,
           rear_clear=26, side_gap=14, yard="apron")
def fire_station(c: Ctx) -> Plan:
    w, d = c.w, c.d
    p = Plan(w, d, [16.0, 12.0], quality="normal", detail=c.detail,
             name=c.name or "Port Solace Fire Station No. 1")
    p.facade = Facade(mat=c.pick(["brick_red", "brick_brown"]), trim="trim_white",
                      frame="trim_white", base="concrete", cornice=True, bay=9.0)
    p.roof = Roof("flat", "roof_gravel", parapet=3.0, access=True)
    nb = 3
    bw = 16.0 * nb
    bay = p.room("bay", "apparatus", R(0, 0, bw, d), name="Apparatus Bay",
                 window={0: "none", 1: "high"})
    bay.cells[1] = [R(0, 0, bw, d)]
    lx = bw
    p.room("watch", "office", R(lx, 0, w, 16), name="Watch Office")
    p.room("lcorr", "corridor", R(lx, 16, lx + 6, d), name="Quarters Hall")
    p.room("stair0", "stair", R(lx + 6, 16, w, 34), name="Stair Hall")
    p.room("kitchen", "kitchen", R(lx + 6, 34, w, 52), name="Station Kitchen")
    p.room("day", "dining", R(lx + 6, 52, w, 66), name="Day Room")
    p.room("gear", "gear", R(lx + 6, 66, w, d - 12), name="Turnout Gear")
    p.room("wc", "restroom", R(lx + 6, d - 12, w, d), name="Restroom")
    srect = R(lx + 7, 20.5, lx + 19, 33.0)
    p.stair(srect, 0, "u", "+y")
    for i in range(nb):
        p.door("bay", None, kind="bay", side="front", role="apparatus", at=(i + 0.5) * 16.0)
        p.door("bay", None, kind="bay", side="back", role="apparatus", at=(i + 0.5) * 16.0)
    p.door("watch", None, kind="exterior", side="front", role="main")
    p.door("watch", "bay")
    p.door("watch", "lcorr", kind="opening")
    p.door("lcorr", "stair0", kind="opening")
    p.door("lcorr", "kitchen", kind="opening")
    p.door("lcorr", "day")
    p.door("lcorr", "gear")
    p.door("lcorr", "wc")
    p.door("lcorr", "bay", kind="metal")
    p.door("lcorr", None, kind="exterior", side="back", role="secondary")
    p.door("day", None, kind="sliding", side="right", role="patio")
    # quarters upstairs
    p.room("uphall", "corridor", R(lx, 16, lx + 6, d), 1, name="Upper Hall")
    p.room("dorm", "dorm", R(lx, 0, w, 16), 1, name="Bunk Room")
    p.room("stair1", "stair", R(lx + 6, 16, w, 34), 1, name="Upper Landing")
    p.room("lounge", "lounge", R(lx + 6, 34, w, 54), 1, name="Lounge")
    p.room("capt", "office", R(lx + 6, 54, w, 66), 1, name="Captain's Office")
    p.room("showers", "bathroom", R(lx + 6, 66, w, d), 1, name="Showers")
    for r in ("dorm", "lounge", "capt", "showers"):
        p.door("uphall", r, 1)
    p.door("uphall", "stair1", 1, kind="opening")
    p.stair(srect, 1, "u", "+y", to_roof=True)

    def tower(B):
        s = B.out.ext
        tx0, ty0 = w - 12.0, d - 12.0
        top = p.height + 26.0
        s.box(p.facade.mat, tx0, ty0, p.height, w, d, top)
        s.box("trim_white", tx0 - 0.4, ty0 - 0.4, top, w + 0.4, d + 0.4, top + 1.2)
        for k in range(3):
            z = p.height + 4 + k * 7
            s.box("glass", tx0 + 3, ty0 - 0.1, z, w - 3, ty0, z + 4, False)
        B.out.markers.append(Marker("landmark", w - 6, d - 6, 0, 0, "Hose Tower"))
        for i in range(nb):
            B.out.lights.append(LightRec((i + 0.5) * 16.0, -3.0, 15.5, (1.0, 0.95, 0.85), 30,
                                         1.2, "point", "always"))
        B.out.markers.append(Marker("poi", bw / 2, -10.0, 0.0, 0.0, "Fire Station",
                                    {"type": "fire"}))
    p.extras.append(tower)
    p.signs.append(Sign("FIRE STATION 1", "front", 0, "letters", bg="sign_black",
                        fg="sign_white", at=bw / 2, width=40.0))
    p.lighting = "always"
    p.tags |= {"fire", "civic", "pole"}
    p.exterior_props += [("flagpole", w - 6.0, -12.0, -0.6, 0.0, None),
                         ("fire_hydrant", w + 2.0, -2.0, -0.6, 0.0, None),
                         ("bench_park", w - 14.0, -4.0, -0.6, math.pi, None),
                         ("bbq_grill", w + 4.0, 46.0, -0.6, 0.0, None),
                         ("picnic_table", w + 8.0, 52.0, -0.6, 0.0, None)]
    finishes(p, c.rng)
    return p


@archetype("town_hall", (96, 120), (70, 84), "CIVIC", "CIVIC", front_setback=40,
           rear_clear=16, side_gap=16, yard="plaza")
def town_hall(c: Ctx) -> Plan:
    """Town hall: public service hall with counters, clerk & permits, council chamber
    (double height), records, mayor's office, clock tower and front portico."""
    w, d = c.w, c.d
    p = Plan(w, d, [16.0, 14.0], quality="nice", detail=c.detail,
             name=c.name or "Port Solace Town Hall")
    p.facade = Facade(mat=c.pick(["limestone", "sandstone", "brick_cream"]), trim="marble",
                      frame="trim_white", base="granite", cornice=True, band=True, bay=9.0,
                      window_w=4.5)
    p.roof = Roof("flat", "roof_metal_green", parapet=4.0, access=True, coping="limestone")
    cx0 = round(w * 0.32 * 2) / 2
    cx1 = round(w * 0.68 * 2) / 2
    sy = round(d * 0.6 * 2) / 2
    p.room("hall", "service_hall", R(cx0, 0, cx1, sy), name="Public Service Hall",
           tags={"always_lit"})
    p.get("hall").cells[1] = [R(cx0, 0, cx1, sy)]
    p.room("clerk", "office_open", R(0, 0, cx0, 24), name="Town Clerk")
    p.room("permits", "office", R(0, 24, cx0, sy), name="Permits & Licensing")
    cham = p.room("chamber", "chamber", R(cx1, 0, w, sy + 8), name="Council Chamber")
    cham.cells[1] = [R(cx1, 0, w, sy + 8)]
    p.room("bcorr", "corridor", R(0, sy, cx1, sy + 8), name="Rear Hall")
    p.room("records", "records", R(0, sy + 8, cx0, d), name="Records Vault")
    p.room("stair0", "stair", R(cx0, sy + 8, cx0 + 14, d), name="Stair")
    p.room("wc0", "restroom", R(cx0 + 14, sy + 8, cx1, d), name="Restrooms")
    p.room("svc", "mechanical", R(cx1, sy + 8, w, d), name="Building Services")
    srect = R(cx0 + 1, sy + 12.5, cx0 + 13, min(d - 1.0, sy + 28.5))
    p.stair(srect, 0, "u", "+y")
    p.door("hall", None, kind="glass_double", side="front", role="main")
    p.door("hall", "clerk", kind="glass")
    p.door("hall", "permits")
    p.door("hall", "chamber", kind="double")
    p.door("hall", "bcorr", kind="arch")
    p.door("bcorr", "records", locked=True)
    p.door("bcorr", "stair0", kind="opening")
    p.door("bcorr", "wc0")
    p.door("bcorr", "permits")
    p.door("chamber", "svc")
    p.door("svc", None, kind="metal", side="back", role="service")
    p.door("bcorr", None, kind="exterior", side="left", role="secondary")
    p.door("chamber", None, kind="exterior", side="right", role="secondary")
    # upper floor (wings + gallery around the double-height hall)
    p.room("mayor", "office", R(0, 0, cx0, 24), 1, name="Mayor's Office", tags={"chief"})
    p.room("council_ofc", "office_open", R(0, 24, cx0, sy), 1, name="Council Offices")
    p.room("ucorr", "corridor", R(0, sy, cx1, sy + 8), 1, name="Upper Hall")
    p.room("planning", "meeting", R(0, sy + 8, cx0, d), 1, name="Planning Room")
    p.room("stair1", "stair", R(cx0, sy + 8, cx0 + 14, d), 1, name="Stair")
    p.room("ulobby", "corridor", R(cx0 + 14, sy + 8, cx1, d), 1, name="Archive Hall")
    p.room("archive", "records", R(cx1, sy + 8, w, d), 1, name="Archive")
    for r in ("council_ofc", "planning"):
        p.door("ucorr", r, 1)
    p.door("ucorr", "ulobby", 1, kind="opening")
    p.door("ulobby", "archive", 1, locked=True)
    p.door("ucorr", "stair1", 1, kind="opening")
    p.door("mayor", "council_ofc", 1)
    p.stair(srect, 1, "u", "+y", to_roof=True)

    def portico_and_tower(B):
        s = B.out.ext
        # portico with columns and pediment-like beam
        s.box("granite", cx0 - 2, -14.0, -1.0, cx1 + 2, 0.0, 0.0)
        for i in range(3):
            s.box("granite", cx0 + 2, -15.0 - i * 1.2, -1.0 - (i + 1) * 0.4, cx1 - 2,
                  -14.0 - i * 1.2, -1.0 - i * 0.4)
        n = 6
        for i in range(n):
            x = cx0 + 2 + i * (cx1 - cx0 - 4) / (n - 1)
            s.cyl("marble", x, -12.0, 0.0, 1.2, 15.0, 12)
        s.box("marble", cx0 - 1, -14.5, 15.0, cx1 + 1, 0.0, 17.5)
        s.box("limestone", cx0 - 1.5, -15.0, 17.5, cx1 + 1.5, 0.0, 18.5)
        # clock tower rising from the roof over the service hall
        tx, ty = (cx0 + cx1) / 2, sy * 0.45
        base = p.height
        s.box(p.facade.mat, tx - 8, ty - 8, base, tx + 8, ty + 8, base + 22)
        s.box("marble", tx - 8.6, ty - 8.6, base + 22, tx + 8.6, ty + 8.6, base + 23.5)
        s.box(p.facade.mat, tx - 6.5, ty - 6.5, base + 23.5, tx + 6.5, ty + 6.5, base + 36)
        for (fx, fy, yaw) in ((0, -1, 0.0), (0, 1, math.pi), (-1, 0, -math.pi / 2),
                              (1, 0, math.pi / 2)):
            cxp = tx + fx * 6.6
            cyp = ty + fy * 6.6
            from ..geom import mat_mul, rot_x
            rot = mat_mul(rot_z(yaw), rot_x(math.pi / 2))
            s.cyl("plastic_white", cxp, cyp, base + 29.5, 4.2, 0.4, 20, rot=rot, collide=False)
            s.cyl("sign_black", cxp + fx * 0.25, cyp + fy * 0.25, base + 29.5, 0.4, 0.5, 8,
                  rot=rot, collide=False)
            s.obox("sign_black", cxp + fx * 0.3, cyp + fy * 0.3, base + 30.8, 0.4 if fx == 0
                   else 0.15, 0.15 if fx == 0 else 0.4, 2.6, collide=False)
        s.box("roof_metal_green", tx - 7.5, ty - 7.5, base + 36, tx + 7.5, ty + 7.5, base + 37)
        from .common import _pp as pp
        s.wedge("roof_metal_green", tx, ty + 3.6, base + 41, 15, 7.2, 8, yaw=0.0)
        s.wedge("roof_metal_green", tx, ty - 3.6, base + 41, 15, 7.2, 8, yaw=math.pi)
        s.cyl("metal_brass", tx, ty, base + 45, 0.25, 6.0, 6, collide=False)
        B.out.lights.append(LightRec(tx, ty - 9.0, base + 29.5, (1.0, 0.9, 0.7), 24, 1.2,
                                     "point", "night"))
        B.out.markers.append(Marker("landmark", tx, ty, 0, 0, "Town Hall Clock Tower"))
        B.out.markers.append(Marker("poi", tx, -16.0, 0, 0, "Town Hall", {"type": "civic"}))
    p.extras.append(portico_and_tower)
    p.signs.append(Sign("TOWN HALL", "front", 1, "letters", bg="sign_black", fg="sign_brown",
                        width=36.0))
    p.lighting = "biz"
    p.tags |= {"civic"}
    p.exterior_props += [("flagpole", cx0 - 10.0, -20.0, -0.6, 0.0, None),
                         ("flagpole", cx1 + 10.0, -20.0, -0.6, 0.0, None),
                         ("bench_park", cx0 - 16.0, -8.0, -0.6, math.pi, None),
                         ("bench_park", cx1 + 16.0, -8.0, -0.6, math.pi, None)]
    finishes(p, c.rng)
    return p
