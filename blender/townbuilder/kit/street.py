"""Street furniture, utilities, signage, fences and yard props."""

from __future__ import annotations

import math

from . import prop, SODIUM, WARM, NEUTRAL, COOL
from .shapes import legs4, table, cone
from ..geom import rot_x, rot_y, rot_z, mat_mul


@prop("streetlight", "street", collide=[(-0.5, -0.5, 0, 0.5, 0.5, 18.0)],
      light={"at": (0, -6.2, 17.0), "color": SODIUM, "range": 44, "brightness": 1.6,
             "kind": "spot", "schedule": "night"})
def streetlight(k):
    k.cyl("metal_gray", 0, 0, 0, 0.7, 0.6, 8)
    k.cyl("metal_gray", 0, 0, 0.6, 0.3, 17.6, 8)
    k.box("metal_gray", -0.15, -6.4, 17.6, 0.15, 0.0, 17.9)
    k.box("metal_gray", -0.7, -7.6, 17.2, 0.7, -5.4, 17.9)
    k.box("lamp_amber", -0.55, -7.4, 17.05, 0.55, -5.6, 17.2)


@prop("streetlight_double", "street", collide=[(-0.5, -0.5, 0, 0.5, 0.5, 18.0)],
      light={"at": (0, -6.2, 17.0), "color": SODIUM, "range": 44, "brightness": 1.6,
             "kind": "spot", "schedule": "night"})
def streetlight_double(k):
    streetlight(k)
    k.box("metal_gray", -0.15, 0.0, 17.6, 0.15, 6.4, 17.9)
    k.box("metal_gray", -0.7, 5.4, 17.2, 0.7, 7.6, 17.9)
    k.box("lamp_amber", -0.55, 5.6, 17.05, 0.55, 7.4, 17.2)


@prop("lamppost_classic", "street", collide=[(-0.5, -0.5, 0, 0.5, 0.5, 12.0)],
      light={"at": (0, 0, 11.0), "color": WARM, "range": 30, "brightness": 1.2,
             "schedule": "night"})
def lamppost_classic(k):
    k.cyl("trim_dark", 0, 0, 0, 0.8, 1.2, 8)
    k.cyl("trim_dark", 0, 0, 1.2, 0.25, 9.0, 8)
    cone(k, "trim_dark", 0, 0, 10.0, 0.3, 0.9, 0.6, 8)
    k.cyl("lamp_warm", 0, 0, 10.6, 0.75, 1.4, 8)
    cone(k, "trim_dark", 0, 0, 12.0, 1.0, 0.1, 0.8, 8)


@prop("parking_light", "street", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 24.0)],
      light={"at": (0, 0, 22.5), "color": (1.0, 0.94, 0.86), "range": 60, "brightness": 1.8,
             "kind": "spot", "schedule": "night"})
def parking_light(k):
    k.cyl("concrete", 0, 0, 0, 1.0, 2.0, 8)
    k.cyl("metal_gray", 0, 0, 2.0, 0.3, 21.0, 8)
    for dy in (-2.2, 2.2):
        k.box("metal_gray", -0.12, min(0, dy), 22.6, 0.12, max(0, dy), 22.9)
        k.box("metal_dark", -1.2, dy - 1.0, 22.3, 1.2, dy + 1.0, 23.0)
        k.box("lamp_cool", -1.0, dy - 0.8, 22.2, 1.0, dy + 0.8, 22.3)


@prop("traffic_signal", "street", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 20.0)])
def traffic_signal(k):
    # pole at origin, mast arm reaching over the road toward -Y
    k.cyl("metal_yellow", 0, 0, 0, 0.45, 19.0, 8)
    k.box("metal_yellow", -0.2, -16.0, 18.2, 0.2, 0.0, 18.7)
    for y in (-6.0, -13.0):
        k.box("metal_dark", -0.8, y - 0.8, 14.8, 0.8, y + 0.8, 18.2)
        k.hcyl("traffic_red", -0.85, y, 17.4, 0.4, 0.1, axis="x", sides=8)
        k.hcyl("traffic_amber", -0.85, y, 16.5, 0.4, 0.1, axis="x", sides=8)
        k.hcyl("traffic_green", -0.85, y, 15.6, 0.4, 0.1, axis="x", sides=8)
    k.box("metal_dark", -0.6, 0.3, 8.5, 0.6, 1.3, 11.0)
    k.box("sign_white", -0.1, -9.0, 19.0, 0.1, -6.0, 20.0, collide=False)


@prop("stop_sign", "sign", collide="none")
def stop_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 9.0)
    pts = []
    for i in range(8):
        a = math.pi / 8 + i * math.pi / 4
        pts.append((1.2 * math.cos(a), -0.15, 8.0 + 1.2 * math.sin(a)))
    verts = pts + [(x, -0.05, z) for (x, _, z) in pts]
    faces = [tuple(range(8)), tuple(range(15, 7, -1))] + \
        [(i, 8 + i, 8 + (i + 1) % 8, (i + 1) % 8) for i in range(8)]
    k.mesh("sign_red", verts, faces)
    k.box("sign_white", -0.8, -0.17, 7.8, 0.8, -0.15, 8.2)


@prop("yield_sign", "sign", collide="none", detail=2)
def yield_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 8.6)
    k.mesh("sign_red", [(-1.3, -0.15, 9.2), (1.3, -0.15, 9.2), (0, -0.15, 7.0),
                        (-1.3, -0.05, 9.2), (1.3, -0.05, 9.2), (0, -0.05, 7.0)],
           [(2, 1, 0), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)])


@prop("street_sign", "sign", collide="none")
def street_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 10.0)
    k.box("sign_green", -2.4, -0.06, 9.0, 2.4, 0.06, 9.9)
    k.box("sign_green", -0.06, -2.4, 9.95, 0.06, 2.4, 10.85)


@prop("speed_sign", "sign", collide="none", detail=2)
def speed_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 8.0)
    k.box("sign_white", -1.0, -0.15, 6.0, 1.0, -0.05, 8.6)
    k.box("sign_black", -0.6, -0.17, 6.6, 0.6, -0.15, 7.6)


@prop("parking_sign", "sign", collide="none", detail=2)
def parking_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 7.6)
    k.box("sign_white", -0.8, -0.15, 6.0, 0.8, -0.05, 7.8)
    k.box("sign_red", -0.6, -0.17, 7.0, 0.6, -0.15, 7.5)


@prop("route_shield_sign", "sign", collide="none", detail=2)
def route_shield_sign(k):
    for x in (-1.0, 1.0):
        k.box("metal_gray", x - 0.1, -0.1, 0, x + 0.1, 0.1, 9.0)
    k.box("sign_white", -1.6, -0.15, 6.4, 1.6, -0.05, 9.4)
    k.box("sign_black", -1.4, -0.17, 6.6, 1.4, -0.15, 9.2)


@prop("big_green_sign", "sign", collide=[(-0.4, -0.4, 0, 0.4, 0.4, 18.0)])
def big_green_sign(k):
    for x in (-5.0, 5.0):
        k.box("metal_gray", x - 0.3, -0.3, 0, x + 0.3, 0.3, 19.0)
    k.box("sign_green", -7.0, -0.25, 12.0, 7.0, 0.0, 18.0)
    k.box("sign_white", -6.6, -0.27, 12.3, 6.6, -0.25, 12.5)


@prop("utility_pole", "street", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 30.0)])
def utility_pole(k):
    k.cyl("wood_weathered", 0, 0, 0, 0.6, 30.0, 8)
    k.box("wood_weathered", -4.0, -0.3, 27.0, 4.0, 0.3, 27.6)
    for x in (-3.4, -1.2, 1.2, 3.4):
        k.cyl("plastic_white", x, 0, 27.6, 0.18, 0.6, 6)
    k.box("wood_weathered", -2.6, -0.3, 23.5, 2.6, 0.3, 24.0)


@prop("utility_pole_transformer", "street", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 30.0)])
def utility_pole_transformer(k):
    utility_pole(k)
    k.cyl("metal_gray", 0, -1.4, 19.0, 1.0, 3.2, 10)
    k.box("metal_gray", -0.2, -0.8, 21.0, 0.2, -0.3, 21.4)


@prop("power_tower", "street", collide=[(-4, -4, 0, 4, 4, 70)])
def power_tower(k):
    # lattice transmission tower (utility corridor landmark)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.obox("metal_gray", sx * 3.0, sy * 3.0, 30.0, 0.6, 0.6, 62.0,
                   mat_mul(rot_x(-sy * 0.06), rot_y(sx * 0.06)))
    for z in (10.0, 22.0, 34.0, 46.0, 58.0):
        w = 6.0 - z * 0.075
        for (a, b) in ((0, 1), (1, 0)):
            k.box("metal_gray", -w if a else -0.15, -w if b else -0.15, z, w if a else 0.15,
                  w if b else 0.15, z + 0.4)
        k.box("metal_gray", -w, -w, z, w, -w + 0.3, z + 0.4)
        k.box("metal_gray", -w, w - 0.3, z, w, w, z + 0.4)
        k.box("metal_gray", -w, -w, z, -w + 0.3, w, z + 0.4)
        k.box("metal_gray", w - 0.3, -w, z, w, w, z + 0.4)
    k.box("metal_gray", -12.0, -0.4, 60.0, 12.0, 0.4, 61.0)
    k.box("metal_gray", -8.0, -0.4, 68.0, 8.0, 0.4, 69.0)
    k.box("metal_gray", -1.2, -1.2, 61.0, 1.2, 1.2, 70.0)
    for x in (-11.0, -7.0, 7.0, 11.0):
        z = 61.0 if abs(x) > 9 else 69.0
        k.cyl("plastic_white", x, 0, z - 3.0, 0.3, 3.0, 6)


@prop("fire_hydrant", "street")
def fire_hydrant(k):
    k.cyl("metal_red", 0, 0, 0, 0.5, 2.2, 8)
    k.ball("metal_red", 0, 0, 2.2, 0.5, 0.5, 0.4)
    k.hcyl("metal_red", 0, 0, 1.5, 0.22, 1.5, axis="x", sides=6)
    k.cyl("metal_red", 0, 0, 0, 0.7, 0.2, 8)


@prop("mailbox_public", "street")
def mailbox_public(k):
    k.box("metal_blue", -1.0, -0.9, 0.6, 1.0, 0.9, 3.6)
    k.hcyl("metal_blue", 0, 0, 3.6, 0.9, 1.8, axis="y", sides=10)
    for x in (-0.8, 0.8):
        k.box("metal_blue", x - 0.15, -0.8, 0, x + 0.15, 0.8, 0.6)


@prop("mailbox_post", "street", collide="none")
def mailbox_post(k):
    k.box("wood", -0.15, -0.15, 0, 0.15, 0.15, 3.6)
    k.box("$metal", -0.5, -1.0, 3.6, 0.5, 1.0, 4.4)
    k.hcyl("$metal", 0, 0, 4.4, 0.5, 2.0, axis="y", sides=8)
    k.box("metal_red", 0.5, 0.2, 4.2, 0.6, 0.4, 5.2)


@prop("bench_park", "street")
def bench_park(k):
    for x in (-2.8, 2.8):
        k.box("metal_dark", x - 0.15, -0.9, 0, x + 0.15, 0.9, 1.6)
        k.box("metal_dark", x - 0.15, 0.6, 1.6, x + 0.15, 0.9, 3.4)
    for i in range(3):
        k.box("wood", -3.2, -0.9 + i * 0.5, 1.5, 3.2, -0.5 + i * 0.5, 1.7)
    for z in (2.2, 2.9):
        k.box("wood", -3.2, 0.7, z, 3.2, 0.9, z + 0.4)


@prop("bus_shelter", "street", collide=[(-6, 1.6, 0, 6, 2.0, 8.5), (-6, -2, 0, -5.7, 2, 8.5),
                                         (5.7, -2, 0, 6, 2, 8.5), (-6, -2.5, 8.3, 6, 2, 8.8)],
      light={"at": (0, 0, 8.0), "color": COOL, "range": 16, "brightness": 0.8,
             "schedule": "night"})
def bus_shelter(k):
    k.box("frame_alu", -6.0, -2.0, 0, -5.7, 2.0, 8.5)
    k.box("frame_alu", 5.7, -2.0, 0, 6.0, 2.0, 8.5)
    k.box("glass", -5.7, 1.7, 0.4, 5.7, 1.9, 8.2)
    k.box("glass", -5.9, -1.6, 0.4, -5.8, 1.7, 8.2, collide=False)
    k.box("roof_metal", -6.3, -2.6, 8.3, 6.3, 2.2, 8.8)
    k.box("sign_white", 1.5, 1.6, 2.0, 5.4, 1.65, 7.6, collide=False)
    k.box("metal_dark", -4.5, 0.5, 1.6, 0.5, 1.6, 1.9)
    k.box("sign_blue", -5.8, -2.0, 9.0, -5.6, -1.4, 11.0, collide=False)
    k.box("metal_gray", -5.8, -2.05, 0, -5.6, -1.85, 9.0, collide=False)


@prop("bus_stop_sign", "sign", collide="none", detail=2)
def bus_stop_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 9.0)
    k.box("sign_blue", -1.0, -0.15, 7.0, 1.0, -0.05, 9.0)


@prop("trash_bin_street", "street")
def trash_bin_street(k):
    k.cyl("trim_green", 0, 0, 0, 1.0, 3.4, 10)
    k.cyl("metal_dark", 0, 0, 3.4, 1.05, 0.3, 10)


@prop("newspaper_box", "street", detail=2)
def newspaper_box(k):
    k.box("$plastic", -0.9, -0.8, 1.2, 0.9, 0.8, 4.0)
    k.box("glass_store", -0.7, -0.82, 2.6, 0.7, -0.8, 3.6)
    for x in (-0.7, 0.7):
        k.box("metal_dark", x - 0.1, -0.6, 0, x + 0.1, 0.6, 1.2)


@prop("parking_meter", "street", collide="none", detail=2)
def parking_meter(k):
    k.cyl("metal_gray", 0, 0, 0, 0.15, 4.0, 6)
    k.box("metal_gray", -0.4, -0.3, 4.0, 0.4, 0.3, 5.2)
    k.box("glass", -0.3, -0.32, 4.6, 0.3, -0.3, 5.0)


@prop("bollard", "street")
def bollard(k):
    k.cyl("hazard_yellow", 0, 0, 0, 0.5, 3.2, 8)


@prop("planter_box", "street")
def planter_box(k):
    k.box("concrete_light", -2.5, -2.5, 0, 2.5, 2.5, 2.2)
    k.box("dirt", -2.2, -2.2, 2.0, 2.2, 2.2, 2.25, collide=False)
    k.ball("hedge", 0, 0, 3.2, 2.2, 2.2, 1.4)


@prop("picnic_table", "street")
def picnic_table(k):
    table(k, "wood", "wood", 7.0, 3.2, 2.6, 0.3, 0.35)
    for sy in (-1, 1):
        k.box("wood", -3.5, sy * 2.6 - 0.6, 1.4, 3.5, sy * 2.6 + 0.6, 1.65)
        for x in (-2.8, 2.8):
            k.box("wood", x - 0.2, sy * 2.6 - 0.2, 0, x + 0.2, sy * 2.6 + 0.2, 1.4,
                  collide=False)


@prop("bike_rack", "street", detail=2)
def bike_rack(k):
    for i in range(4):
        x = -2.4 + i * 1.6
        k.box("metal_gray", x - 0.1, -0.8, 0, x + 0.1, -0.6, 2.8)
        k.box("metal_gray", x - 0.1, 0.6, 0, x + 0.1, 0.8, 2.8)
        k.box("metal_gray", x - 0.1, -0.8, 2.6, x + 0.1, 0.8, 2.8)


@prop("jersey_barrier", "street")
def jersey_barrier(k):
    k.box("concrete_light", -5.0, -1.0, 0, 5.0, 1.0, 1.0)
    k.box("concrete_light", -5.0, -0.5, 1.0, 5.0, 0.5, 2.8)


@prop("construction_barrier", "street", detail=2)
def construction_barrier(k):
    for x in (-2.0, 2.0):
        k.box("metal_gray", x - 0.1, -0.6, 0, x + 0.1, 0.6, 3.6, collide=False)
    for z in (1.6, 2.8):
        k.box("cone_orange", -2.6, -0.1, z, 2.6, 0.1, z + 0.6)
        k.box("plastic_white", -1.6, -0.12, z, -0.8, 0.12, z + 0.6)
        k.box("plastic_white", 0.4, -0.12, z, 1.2, 0.12, z + 0.6)


@prop("traffic_cone", "street", collide="none")
def traffic_cone(k):
    k.box("rubber", -0.7, -0.7, 0, 0.7, 0.7, 0.15)
    cone(k, "cone_orange", 0, 0, 0.15, 0.5, 0.08, 2.2, 8)


@prop("cones_group", "street", collide="none", detail=2)
def cones_group(k):
    for (x, y) in ((-2.0, 0.0), (0.0, 0.3), (2.0, -0.2)):
        k.box("rubber", x - 0.7, y - 0.7, 0, x + 0.7, y + 0.7, 0.15)
        cone(k, "cone_orange", x, y, 0.15, 0.5, 0.08, 2.2, 8)


@prop("sawhorse", "street", detail=2)
def sawhorse(k):
    k.box("cone_orange", -2.4, -0.15, 2.2, 2.4, 0.15, 3.0)
    for x in (-1.8, 1.8):
        k.box("metal_gray", x - 0.1, -0.8, 0, x + 0.1, 0.8, 2.2, collide=False)


@prop("guardrail", "street")
def guardrail(k):
    k.box("metal", -4.0, -0.3, 1.6, 4.0, 0.0, 2.6)
    for x in (-3.6, 0.0, 3.6):
        k.box("metal_dark", x - 0.2, 0.0, 0, x + 0.2, 0.4, 2.6, collide=False)


@prop("road_work_sign", "sign", collide="none", detail=2)
def road_work_sign(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 5.0)
    k.obox("cone_orange", 0, -0.12, 5.6, 2.0, 0.1, 2.0, rot_y(math.pi / 4))


@prop("manhole", "street", collide="none", detail=3)
def manhole(k):
    k.cyl("metal_dark", 0, 0, 0, 1.4, 0.06, 12)


@prop("storm_drain", "street", collide="none", detail=3)
def storm_drain(k):
    k.box("metal_dark", -1.5, -0.6, 0, 1.5, 0.6, 0.06)


@prop("billboard", "street", collide=[(-1, -1, 0, 1, 1, 22)])
def billboard(k):
    for x in (-6.0, 6.0):
        k.box("metal_gray", x - 0.5, -0.5, 0, x + 0.5, 0.5, 22.0)
    k.box("metal_gray", -13.0, 0.2, 20.0, 13.0, 1.0, 34.0)
    k.box("$sign", -12.6, -0.05, 20.4, 12.6, 0.2, 33.6)
    k.box("sign_white", -11.0, -0.1, 22.0, 2.0, -0.05, 31.0)
    k.box("metal_gray", -13.0, -2.0, 19.2, 13.0, 1.0, 19.6)


@prop("payphone_stand", "street", collide="none", detail=2)
def payphone_stand(k):
    k.box("metal_gray", -0.15, -0.15, 0, 0.15, 0.15, 7.0)
    k.box("metal_gray", -1.0, -0.6, 3.4, 1.0, 0.2, 6.6)
    k.box("plastic_black", -0.5, -0.65, 4.0, 0.5, -0.6, 6.0)
    k.box("sign_blue", -1.0, -0.4, 6.6, 1.0, 0.2, 7.4)


@prop("ice_merchandiser", "street")
def ice_merchandiser(k):
    k.box("metal_white", -3.0, -1.6, 0, 3.0, 1.6, 6.0)
    k.box("sign_blue", -2.8, -1.62, 3.4, 2.8, -1.6, 5.6, collide=False)


@prop("gas_pump", "street", collide=[(-1.4, -1.0, 0, 1.4, 1.0, 7.0)])
def gas_pump(k):
    k.box("concrete_light", -2.0, -3.0, 0, 2.0, 3.0, 0.8)
    k.box("metal_white", -1.3, -0.9, 0.8, 1.3, 0.9, 6.8)
    k.box("$sign", -1.35, -0.95, 5.6, 1.35, 0.95, 7.2)
    for sy in (-1, 1):
        k.box("screen_on", -0.7, sy * 0.92 - 0.02, 4.2, 0.7, sy * 0.92 + 0.02, 5.2, collide=False)
        k.box("plastic_black", 0.6, sy * 0.95 - 0.1, 2.0, 1.0, sy * 0.95 + 0.1, 3.4,
              collide=False)
    for y in (-2.6, 2.6):
        k.cyl("hazard_yellow", 1.6, y, 0.8, 0.3, 3.0, 6)


@prop("air_pump", "street", detail=2)
def air_pump(k):
    k.box("metal_red", -0.8, -0.6, 0, 0.8, 0.6, 4.4)
    k.box("screen", -0.5, -0.62, 3.0, 0.5, -0.6, 3.8)


# --- Fences, gates, walls (modular, 8 studs long along X) ---------------------------

@prop("fence_chain", "fence", collide=[(-4, -0.1, 0, 4, 0.1, 8)])
def fence_chain(k):
    k.cyl("metal_gray", -4.0, 0, 0, 0.18, 8.0, 6)
    k.box("metal_gray", -4.0, -0.08, 7.8, 4.0, 0.08, 8.0)
    k.box("glass_frosted", -4.0, -0.02, 0.1, 4.0, 0.02, 7.8)


@prop("fence_chain_barbed", "fence", collide=[(-4, -0.1, 0, 4, 0.1, 9)])
def fence_chain_barbed(k):
    fence_chain(k)
    k.box("metal_gray", -0.05, -0.6, 8.0, 0.05, 0.0, 9.0)
    for z in (8.4, 8.8):
        k.box("metal_dark", -4.0, -0.5, z, 4.0, -0.45, z + 0.05)


@prop("fence_wood", "fence", collide=[(-4, -0.2, 0, 4, 0.2, 6.5)])
def fence_wood(k):
    for x in (-4.0, 0.0):
        k.box("wood_weathered", x - 0.25, -0.25, 0, x + 0.25, 0.25, 6.8)
    for z in (1.2, 5.2):
        k.box("wood_weathered", -4.0, 0.05, z, 4.0, 0.25, z + 0.4)
    k.box("$wood", -4.0, -0.2, 0.2, 4.0, 0.05, 6.5)


@prop("fence_picket", "fence", collide=[(-4, -0.15, 0, 4, 0.15, 3.4)])
def fence_picket(k):
    k.box("wood_white", -4.0, 0.0, 1.0, 4.0, 0.2, 1.3)
    k.box("wood_white", -4.0, 0.0, 2.6, 4.0, 0.2, 2.9)
    for i in range(12):
        x = -3.85 + i * 0.67
        k.box("wood_white", x, -0.15, 0, x + 0.4, 0.0, 3.4)


@prop("fence_iron", "fence", collide=[(-4, -0.15, 0, 4, 0.15, 6.0)])
def fence_iron(k):
    k.box("trim_dark", -4.0, -0.1, 0.6, 4.0, 0.1, 0.8)
    k.box("trim_dark", -4.0, -0.1, 5.4, 4.0, 0.1, 5.6)
    for i in range(16):
        x = -3.9 + i * 0.5
        k.box("trim_dark", x - 0.05, -0.05, 0, x + 0.05, 0.05, 6.0)
    k.box("brick_red", -4.3, -0.5, 0, -3.7, 0.5, 6.6)


@prop("wall_block", "fence", collide=[(-4, -0.4, 0, 4, 0.4, 6.0)])
def wall_block(k):
    k.box("$paint", -4.0, -0.4, 0, 4.0, 0.4, 6.0)
    k.box("concrete_light", -4.0, -0.5, 6.0, 4.0, 0.5, 6.3)


@prop("hedge_row", "fence", collide=[(-4, -1.3, 0, 4, 1.3, 5.0)])
def hedge_row(k):
    k.box("hedge", -4.0, -1.3, 0, 4.0, 1.3, 4.6)
    k.ball("hedge", -2.0, 0, 4.6, 2.2, 1.3, 0.6)
    k.ball("hedge", 2.0, 0, 4.6, 2.2, 1.3, 0.7)


@prop("gate_chain", "fence", collide="none", tags=("gate",))
def gate_chain(k):
    k.box("metal_gray", -8.0, -0.1, 0.2, 8.0, 0.1, 0.4)
    k.box("metal_gray", -8.0, -0.1, 7.6, 8.0, 0.1, 7.8)
    for x in (-8.0, 0.0, 8.0):
        k.box("metal_gray", x - 0.15, -0.1, 0.2, x + 0.15, 0.1, 7.8)
    k.box("glass_frosted", -8.0, -0.02, 0.4, 8.0, 0.02, 7.6)


@prop("gate_arm", "fence", collide="none", tags=("gate",))
def gate_arm(k):
    k.box("metal_yellow", -0.8, -0.8, 0, 0.8, 0.8, 4.0)
    k.box("hazard_yellow", 0.0, -0.15, 3.4, 16.0, 0.15, 3.8)
    for i in range(6):
        k.box("hazard_black", 1.5 + i * 2.6, -0.17, 3.4, 2.5 + i * 2.6, 0.17, 3.8)


@prop("guard_booth", "fence", collide=[(-3, -3, 0, 3, 3, 9)],
      light={"at": (0, 0, 8), "color": COOL, "range": 14, "brightness": 0.9})
def guard_booth(k):
    k.box("metal_white", -3.0, -3.0, 0, 3.0, 3.0, 3.4)
    k.box("glass", -3.0, -3.0, 3.4, 3.0, 3.0, 8.0)
    for (x, y) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        k.box("metal_white", x - 0.2, y - 0.2, 3.4, x + 0.2, y + 0.2, 8.0, collide=False)
    k.box("roof_metal", -3.6, -3.6, 8.0, 3.6, 3.6, 8.8)
    k.box("plastic_black", -1.0, 1.6, 3.4, 1.0, 2.6, 4.6, collide=False)


# --- Yard / residential exterior -----------------------------------------------------

@prop("bbq_grill", "yard", detail=2)
def bbq_grill(k):
    k.ball("metal_dark", 0, 0, 3.0, 1.2, 1.2, 0.9)
    for (x, y) in ((-0.8, -0.8), (0.8, -0.8), (0, 0.9)):
        k.box("metal_dark", x - 0.08, y - 0.08, 0, x + 0.08, y + 0.08, 2.4)


@prop("patio_set", "yard")
def patio_set(k):
    k.cyl("metal_white", 0, 0, 2.4, 2.2, 0.15, 12)
    k.cyl("metal_white", 0, 0, 0, 0.12, 2.4, 6)
    k.cyl("metal_white", 0, 0, 2.55, 0.08, 4.0, 4, collide=False)
    cone(k, "$fabric", 0, 0, 6.0, 4.5, 0.2, 1.4, 8)
    for a in range(4):
        ang = a * math.pi / 2 + 0.4
        cx, cy = 3.0 * math.cos(ang), 3.0 * math.sin(ang)
        k.obox("metal_white", cx, cy, 1.5, 1.6, 1.6, 0.2, rot_z(ang), collide=False)


@prop("lawn_chair", "yard", collide="none", detail=2)
def lawn_chair(k):
    k.box("$fabric", -1.0, -1.2, 1.0, 1.0, 1.0, 1.3)
    k.obox("$fabric", 0, 1.1, 2.4, 2.0, 0.2, 2.8, rot_x(-0.25))
    legs4(k, "metal", 2.0, 2.2, 1.0, 0.12, 0.05)


@prop("swing_set", "yard", collide=[(-6, -3, 0, -5.6, 3, 9), (5.6, -3, 0, 6, 3, 9)])
def swing_set(k):
    k.hcyl("metal_red", 0, 0, 9.0, 0.3, 12.0, axis="x", sides=8)
    for x in (-5.8, 5.8):
        for sy in (-1, 1):
            k.obox("metal_red", x, sy * 1.5, 4.5, 0.4, 0.4, 9.4, rot_x(sy * 0.33))
    for x in (-2.0, 2.0):
        for dx in (-0.8, 0.8):
            k.box("metal_gray", x + dx - 0.04, -0.04, 2.2, x + dx + 0.04, 0.04, 9.0,
                  collide=False)
        k.box("rubber", x - 1.0, -0.5, 2.0, x + 1.0, 0.5, 2.3, collide=False)


@prop("trampoline", "yard")
def trampoline(k):
    k.cyl("metal_gray", 0, 0, 2.6, 6.0, 0.3, 16)
    k.cyl("plastic_black", 0, 0, 2.7, 5.4, 0.25, 16, collide=False)
    for a in range(6):
        ang = a * math.pi / 3
        k.box("metal_gray", 5.6 * math.cos(ang) - 0.1, 5.6 * math.sin(ang) - 0.1, 0,
              5.6 * math.cos(ang) + 0.1, 5.6 * math.sin(ang) + 0.1, 2.6, collide=False)


@prop("basketball_hoop", "yard", collide=[(-0.4, -0.4, 0, 0.4, 0.4, 13.0)])
def basketball_hoop(k):
    k.cyl("metal_gray", 0, 0, 0, 0.3, 11.0, 6)
    k.box("metal_gray", -0.1, -2.0, 10.6, 0.1, 0.0, 11.0)
    k.box("plastic_white", -2.4, -2.3, 10.0, 2.4, -2.0, 13.4)
    k.cyl("metal_orange", 0, -3.3, 10.8, 1.0, 0.1, 10, collide=False)


@prop("garbage_cans", "yard", detail=2)
def garbage_cans(k):
    for x, m in ((-1.0, "plastic_gray"), (1.0, "plastic_green")):
        k.box(m, x - 0.9, -0.9, 0, x + 0.9, 0.9, 3.6)
        k.box(m, x - 1.0, -1.0, 3.6, x + 1.0, 1.0, 3.9, collide=False)


@prop("woodpile", "yard", detail=2)
def woodpile(k):
    for z in range(3):
        for i in range(5 - z):
            k.hcyl("bark", 0, -1.4 + i * 0.7 + z * 0.35, 0.35 + z * 0.62, 0.35, 4.0, axis="x",
                   sides=6)


@prop("kiddie_pool", "yard", collide="none", detail=3)
def kiddie_pool(k):
    k.cyl("plastic_blue", 0, 0, 0, 3.0, 1.0, 12)
    k.cyl("water", 0, 0, 0.2, 2.7, 0.7, 12)


@prop("lawn_mower", "yard", collide="none", detail=3)
def lawn_mower(k):
    k.box("metal_red", -1.0, -1.2, 0.4, 1.0, 1.2, 1.4)
    k.obox("metal_dark", 0, 2.0, 2.4, 1.6, 0.15, 3.2, rot_x(-0.6))
    for (x, y) in ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)):
        k.hcyl("rubber", x, y, 0.4, 0.4, 0.3, axis="x", sides=8)


@prop("garden_bed", "yard", collide="none", detail=2)
def garden_bed(k):
    k.box("wood_raw", -4.0, -1.5, 0, 4.0, 1.5, 1.0)
    k.box("dirt", -3.8, -1.3, 0.9, 3.8, 1.3, 1.05)
    for i in range(6):
        k.ball(("leaf", "flower_red", "leaf_light", "flower_yellow")[i % 4], -3.2 + i * 1.3,
               0, 1.5, 0.6)


@prop("doghouse", "yard", detail=2)
def doghouse(k):
    k.box("$wood", -1.8, -1.8, 0, 1.8, 1.8, 3.0)
    k.wedge("roof_shingle_red", 0, 0.95, 3.9, 4.0, 1.9, 1.8, yaw=0.0)
    k.wedge("roof_shingle_red", 0, -0.95, 3.9, 4.0, 1.9, 1.8, yaw=math.pi)
    k.box("plastic_black", -0.8, -1.82, 0.2, 0.8, -1.8, 2.2, collide=False)


@prop("pool_ladder", "yard", collide="none", detail=2)
def pool_ladder(k):
    for x in (-0.9, 0.9):
        k.box("metal_chrome", x - 0.1, -0.1, -4.0, x + 0.1, 0.1, 3.0)
    for z in (-3.0, -2.0, -1.0):
        k.box("metal_chrome", -0.9, -0.3, z, 0.9, 0.1, z + 0.15)


@prop("pool_lounger", "yard", detail=2)
def pool_lounger(k):
    k.box("plastic_white", -1.2, -3.2, 1.0, 1.2, 1.6, 1.3)
    k.obox("plastic_white", 0, 2.3, 2.2, 2.4, 1.8, 0.3, rot_x(-0.8))
    legs4(k, "plastic_white", 2.4, 6.4, 1.0, 0.2, 0.2)


@prop("flagpole", "civic", collide=[(-0.4, -0.4, 0, 0.4, 0.4, 32)])
def flagpole(k):
    k.cyl("concrete_light", 0, 0, 0, 1.6, 1.0, 10)
    k.cyl("metal_chrome", 0, 0, 1.0, 0.25, 31.0, 8)
    k.ball("metal_brass", 0, 0, 32.2, 0.5)
    k.box("fabric_blue", 0.3, -0.05, 26.0, 3.4, 0.05, 30.4)
    for i in range(7):
        k.box("fabric_red" if i % 2 == 0 else "fabric_white", 3.4, -0.05, 26.0 + i * 0.63,
              8.0, 0.05, 26.0 + (i + 1) * 0.63)


@prop("fountain", "civic", collide=[(-8, -8, 0, 8, 8, 2.2)])
def fountain(k):
    k.cyl("limestone", 0, 0, 0, 8.0, 2.2, 20)
    k.cyl("water", 0, 0, 0.4, 7.3, 1.6, 20, collide=False)
    k.cyl("limestone", 0, 0, 2.0, 1.4, 4.0, 10)
    k.cyl("limestone", 0, 0, 6.0, 3.0, 0.6, 14)
    k.cyl("water", 0, 0, 6.2, 2.6, 0.5, 14, collide=False)
    k.cyl("limestone", 0, 0, 6.6, 0.6, 2.4, 8)


@prop("statue", "civic", collide=[(-3, -3, 0, 3, 3, 16)])
def statue(k):
    k.box("granite", -3.0, -3.0, 0, 3.0, 3.0, 6.0)
    k.box("granite", -3.4, -3.4, 0, 3.4, 3.4, 1.0)
    k.box("metal_brass", -0.8, -0.6, 6.0, 0.8, 0.6, 9.4)
    k.box("metal_brass", -1.2, -0.7, 9.4, 1.2, 0.7, 12.6)
    k.ball("metal_brass", 0, 0, 13.6, 0.9)
    k.box("metal_brass", 1.2, -0.4, 10.2, 3.4, 0.4, 10.9)
    k.box("metal_brass", -2.2, -0.3, 11.0, -1.2, 0.3, 14.0)


@prop("playground", "park", collide=[(-8, -6, 0, 8, 6, 12)])
def playground(k):
    for (x, y) in ((-6, -4), (-6, 4), (0, -4), (0, 4)):
        k.box("metal_blue", x - 0.25, y - 0.25, 0, x + 0.25, y + 0.25, 11.0)
    k.box("wood_raw", -6.0, -4.0, 5.0, 0.0, 4.0, 5.4)
    k.wedge("plastic_red", -3.0, 0, 12.0, 6.6, 8.6, 2.0)
    k.obox("plastic_yellow", 4.0, -2.0, 2.6, 3.0, 9.0, 0.3,
           mat_mul(rot_z(math.pi / 2), rot_x(0.55)))
    for z in (1.2, 2.4, 3.6):
        k.box("metal_blue", -6.4, 2.0, z, -6.2, 4.0, z + 0.2)
    k.box("sand", -8.0, -6.0, -0.05, 8.0, 6.0, 0.1, collide=False)
