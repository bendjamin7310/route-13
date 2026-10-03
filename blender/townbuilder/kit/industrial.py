"""Warehouse, garage, factory, storage and waterfront working props."""

from __future__ import annotations

import math

from . import prop, COOL
from .shapes import cabinet, legs4, shelf_unit, table, cone, car_wheel
from ..geom import rot_z, rot_x, mat_mul


@prop("pallet", "industrial")
def pallet(k):
    for x in (-1.8, -0.1, 1.6):
        k.box("wood_raw", x, -2.0, 0, x + 0.3, 2.0, 0.35)
    for i in range(6):
        y = -2.0 + i * 0.75
        k.box("wood_raw", -2.0, y, 0.35, 2.0, y + 0.45, 0.5, collide=False)


def _pallet_load(k, h, mat="cardboard", wrap=False):
    pallet(k)
    k.box(mat, -1.9, -1.9, 0.5, 1.9, 1.9, 0.5 + h)
    if wrap:
        k.box("glass_frosted", -1.95, -1.95, 0.5, 1.95, 1.95, 0.5 + h * 0.8, collide=False)


@prop("pallet_boxes", "industrial")
def pallet_boxes(k):
    _pallet_load(k, 3.0)


@prop("pallet_boxes_tall", "industrial")
def pallet_boxes_tall(k):
    _pallet_load(k, 4.8, wrap=True)


@prop("pallet_sacks", "industrial")
def pallet_sacks(k):
    pallet(k)
    for z in range(3):
        for x in (-1, 1):
            k.box("fabric_cream", x * 0.95 - 0.9, -1.8, 0.5 + z * 0.8, x * 0.95 + 0.9, 1.8,
                  1.25 + z * 0.8)


@prop("pallet_drums", "industrial")
def pallet_drums(k):
    pallet(k)
    for x in (-0.95, 0.95):
        for y in (-0.95, 0.95):
            k.cyl("plastic_blue", x, y, 0.5, 0.9, 3.0, 10)


@prop("pallet_rack", "industrial", collide=[(-6.5, -2.2, 0, 6.5, 2.2, 0.6), (-6.5, -2.2, 0, -6.2, 2.2, 16.0), (6.2, -2.2, 0, 6.5, 2.2, 16.0), (-6.5, -2.2, 4.5, 6.5, 2.2, 5.0), (-6.5, -2.2, 9.5, 6.5, 2.2, 10.0), (-6.5, -2.2, 14.5, 6.5, 2.2, 15.0)])
def pallet_rack(k):
    # 13 wide x 4.4 deep x 16 tall, 3 load levels
    for x in (-6.5, -0.15, 6.2):
        for y in (-2.2, 1.9):
            k.box("metal_blue", x, y, 0, x + 0.3, y + 0.3, 16.0, collide=False)
    for z in (5.0, 10.0, 15.0):
        for y in (-2.2, 1.9):
            k.box("metal_orange", -6.5, y, z - 0.5, 6.5, y + 0.3, z, collide=False)
    for zi, z in enumerate((0.0, 5.0, 10.0)):
        for bi, x in enumerate((-3.3, 3.2)):
            if (zi + bi) % 4 == 3:
                continue
            k.box("wood_raw", x - 2.6, -2.0, z, x + 2.6, 2.0, z + 0.4, collide=False)
            h = (3.2, 2.5, 3.6)[(zi + bi) % 3]
            m = ("cardboard", "cardboard", "plastic_blue", "fabric_cream")[(zi * 2 + bi) % 4]
            k.box(m, x - 2.5, -1.9, z + 0.4, x + 2.5, 1.9, z + 0.4 + h, collide=False)


@prop("crate", "industrial")
def crate(k):
    k.box("wood_raw", -1.5, -1.5, 0, 1.5, 1.5, 3.0)
    for z in (0.0, 2.7):
        k.box("wood", -1.55, -1.55, z, 1.55, 1.55, z + 0.3, collide=False)


@prop("crate_stack", "industrial")
def crate_stack(k):
    crate(k)
    k.box("wood_raw", -1.4, -1.4, 3.0, 1.4, 1.4, 5.8)
    k.box("wood_raw", 1.7, -1.4, 0, 4.5, 1.4, 2.8)


@prop("barrel", "industrial")
def barrel(k):
    k.cyl("$metal", 0, 0, 0, 1.0, 3.2, 10)
    for z in (0.9, 2.2):
        k.cyl("metal_dark", 0, 0, z, 1.04, 0.12, 10, collide=False)


@prop("barrels_group", "industrial")
def barrels_group(k):
    for (x, y, m) in ((-1.1, -1.0, "metal_blue"), (1.0, -1.1, "metal_red"),
                      (0.0, 0.9, "metal_rust")):
        k.cyl(m, x, y, 0, 1.0, 3.2, 10)


@prop("ibc_tote", "industrial")
def ibc_tote(k):
    pallet(k)
    k.box("plastic_white", -1.9, -1.9, 0.5, 1.9, 1.9, 4.2)
    for x in (-1.95, 1.95):
        k.box("metal", x - 0.05, -1.95, 0.5, x + 0.05, 1.95, 4.3, collide=False)


@prop("forklift", "industrial", tags=("vehicle",))
def forklift(k):
    k.box("metal_yellow", -1.8, -1.0, 0.8, 1.8, 4.0, 3.6)
    k.box("metal_dark", -1.8, 2.6, 0.8, 1.8, 4.2, 4.4)
    k.box("leather_black", -1.0, 0.8, 3.6, 1.0, 2.2, 4.3, collide=False)
    for x in (-1.6, 1.6):
        k.box("metal_dark", x - 0.15, 0.4, 3.6, x + 0.15, 0.7, 7.6, collide=False)
        k.box("metal_dark", x - 0.15, 3.4, 3.6, x + 0.15, 3.7, 7.6, collide=False)
    k.box("metal_dark", -1.6, 0.4, 7.4, 1.6, 3.7, 7.6, collide=False)
    k.box("metal_dark", -1.6, -1.6, 0.4, 1.6, -1.2, 5.6)
    for x in (-1.0, 1.0):
        k.box("metal_dark", x - 0.3, -5.2, 0.4, x + 0.3, -1.6, 0.6, collide=False)
    for (x, y) in ((-1.9, -0.2), (1.9, -0.2), (-1.9, 3.2), (1.9, 3.2)):
        k.hcyl("rubber", x, y, 0.8, 0.8, 0.6, axis="x", sides=10, collide=False)


@prop("pallet_jack", "industrial", collide="none", detail=2)
def pallet_jack(k):
    for x in (-0.8, 0.8):
        k.box("metal_red", x - 0.35, -3.6, 0.1, x + 0.35, 0.0, 0.4)
    k.box("metal_red", -1.0, 0.0, 0.1, 1.0, 0.8, 1.2)
    k.box("metal_dark", -0.08, 0.5, 1.2, 0.08, 1.4, 4.4)


@prop("workbench", "garage")
def workbench(k):
    k.box("wood_raw", -3.2, -1.3, 3.0, 3.2, 1.3, 3.3)
    k.box("metal_gray", -3.1, -1.2, 0.8, 3.1, 1.2, 0.9, collide=False)
    legs4(k, "metal_gray", 6.4, 2.6, 3.0, 0.25, 0.1)
    k.box("plywood", -3.2, 1.2, 3.3, 3.2, 1.3, 6.6, collide=False)
    k.box("metal_dark", -2.6, -0.4, 3.3, -1.6, 0.4, 3.9, collide=False)
    k.box("metal_red", 1.0, -0.6, 3.3, 2.4, 0.2, 3.7, collide=False)
    for i in range(5):
        k.box(("metal_dark", "metal_red", "metal_yellow")[i % 3], -2.6 + i * 1.2, 1.0, 4.5,
              -2.4 + i * 1.2, 1.2, 5.8, collide=False)


@prop("tool_cabinet", "garage")
def tool_cabinet(k):
    cabinet(k, "$metal", "$metal", 4.4, 2.2, 4.2, doors=1, drawers=6)
    k.box("metal_dark", -2.2, -1.1, 4.2, 2.2, 1.1, 4.4)
    k.box("$metal", -2.2, -1.0, 4.4, 2.2, 1.1, 6.6, collide=False)


@prop("tool_chest_roll", "garage", detail=2)
def tool_chest_roll(k):
    cabinet(k, "metal_red", "metal_red", 2.6, 1.8, 3.4, doors=1, drawers=5, z0=0.4)
    for x in (-1.1, 1.1):
        for y in (-0.7, 0.7):
            k.cyl("rubber", x, y, 0, 0.2, 0.4, 6, collide=False)


@prop("tire_stack", "garage")
def tire_stack(k):
    for i in range(4):
        k.cyl("rubber", 0, 0, i * 0.9, 1.3, 0.85, 12)
    k.cyl("metal_dark", 0, 0, 3.55, 0.7, 0.05, 8, collide=False)


@prop("tire_rack", "garage")
def tire_rack(k):
    k.box("metal_gray", -4.0, -1.2, 0, -3.8, 1.2, 7.0)
    k.box("metal_gray", 3.8, -1.2, 0, 4.0, 1.2, 7.0)
    for z in (0.5, 3.8):
        k.box("metal_gray", -4.0, -1.2, z - 0.2, 4.0, 1.2, z, collide=False)
        for i in range(7):
            k.hcyl("rubber", -3.3 + i * 1.1, 0, z + 1.3, 1.3, 0.9, axis="x", sides=10,
                   collide=False)


@prop("car_lift", "garage", collide=[(-6.2, -0.6, 0, -5.4, 0.6, 12.0), (5.4, -0.6, 0, 6.2, 0.6, 12.0)])
def car_lift(k):
    for x in (-5.8, 5.8):
        k.box("metal_blue", x - 0.4, -0.6, 0, x + 0.4, 0.6, 12.0)
        k.box("metal_blue", x - 0.8, -0.9, 0, x + 0.8, 0.9, 0.3)
        k.box("metal_dark", x - 0.2 if x < 0 else x - 4.0, -4.0, 3.0, x + 4.0 if x < 0 else x + 0.2,
              -3.6, 3.3, collide=False)
        k.box("metal_dark", x - 0.2 if x < 0 else x - 4.0, 3.6, 3.0, x + 4.0 if x < 0 else x + 0.2,
              4.0, 3.3, collide=False)
    k.box("metal_blue", -6.2, -0.6, 11.6, 6.2, 0.6, 12.2)


@prop("engine_hoist", "garage", collide="none", detail=2)
def engine_hoist(k):
    k.box("metal_red", -0.2, -0.2, 0, 0.2, 0.2, 7.0)
    k.obox("metal_red", 0, -2.0, 6.2, 0.4, 4.6, 0.4, rot_x(0.3))
    k.box("metal_red", -1.5, -0.4, 0, 1.5, 0.4, 0.4)
    k.box("metal_red", -0.2, -4.4, 0, 0.2, 0.4, 0.4)
    k.cyl("metal_dark", 0, -4.0, 3.6, 0.06, 2.6, 4)


@prop("engine_block", "garage", detail=2)
def engine_block(k):
    k.box("metal_dark", -1.5, -1.2, 0.4, 1.5, 1.2, 2.8)
    k.box("metal_gray", -1.3, -1.0, 2.8, 1.3, 1.0, 3.4)
    k.box("wood_raw", -1.8, -1.5, 0, 1.8, 1.5, 0.4)


@prop("air_compressor", "garage", detail=2)
def air_compressor(k):
    k.hcyl("metal_red", 0, 0, 1.4, 1.2, 4.0, axis="x", sides=10)
    k.box("metal_dark", -1.2, -0.8, 2.4, 0.6, 0.8, 3.4)
    for x in (-1.5, 1.5):
        k.box("metal_dark", x - 0.2, -0.8, 0, x + 0.2, 0.8, 0.4)


@prop("oil_drums_rack", "garage")
def oil_drums_rack(k):
    k.box("metal_dark", -3.0, -1.2, 0, 3.0, 1.2, 0.6)
    for x in (-1.6, 0.0, 1.6):
        k.cyl(("metal_red", "metal_blue", "metal_green")[int(x + 1.6) % 3], x, 0, 0.6, 0.75,
              2.8, 10)


@prop("spare_parts_shelf", "garage")
def spare_parts_shelf(k):
    shelf_unit(k, "metal_gray", 6.0, 2.0, 7.0, 4, back=False,
               goods=["cardboard", "metal_dark", "rubber", "metal_red", "plastic_blue"],
               rng_seed=41)


@prop("parts_counter", "garage")
def parts_counter(k):
    k.box("metal_gray", -5.0, -1.4, 0, 5.0, 1.4, 3.6)
    k.box("plastic_gray", -5.2, -1.6, 3.6, 5.2, 1.6, 3.8)
    k.box("plastic_black", 2.6, 0.0, 3.8, 3.8, 1.0, 4.9, collide=False)
    k.box("screen_on", 2.7, -0.02, 3.9, 3.7, 0.0, 4.8, collide=False)
    k.box("cardboard", -3.6, -0.6, 3.8, -2.0, 0.8, 4.8, collide=False)


@prop("welding_cart", "garage", collide="none", detail=2)
def welding_cart(k):
    k.box("metal_blue", -1.0, -1.0, 0.4, 1.0, 1.0, 3.0)
    k.cyl("metal_green", 0.4, 0.6, 3.0, 0.5, 4.0, 8)
    k.cyl("metal_dark", -0.4, 0.6, 3.0, 0.4, 3.0, 8)


@prop("drill_press", "factory")
def drill_press(k):
    k.box("metal_green", -1.4, -1.4, 0, 1.4, 1.4, 0.6)
    k.cyl("metal_green", 0, 0.8, 0.6, 0.3, 6.0, 8)
    k.box("metal_green", -0.9, -1.2, 5.0, 0.9, 1.2, 6.8)
    k.box("metal_gray", -1.0, -1.2, 3.2, 1.0, 0.6, 3.4)


@prop("lathe", "factory")
def lathe(k):
    k.box("metal_green", -4.0, -1.2, 0, 4.0, 1.2, 3.2)
    k.box("metal_green", -4.0, -1.4, 3.2, -1.8, 1.4, 5.2)
    k.box("metal_gray", -1.8, -0.4, 3.2, 3.6, 0.4, 3.6)
    k.box("metal_green", 2.6, -1.0, 3.6, 3.8, 1.0, 4.8)


@prop("cnc_machine", "factory")
def cnc_machine(k):
    k.box("metal_white", -4.0, -3.0, 0, 4.0, 3.0, 7.2)
    k.box("glass_tint", -2.6, -3.02, 2.4, 2.0, -3.0, 6.0, collide=False)
    k.box("metal_blue", 2.4, -3.2, 2.4, 3.8, -3.0, 6.6, collide=False)
    k.box("screen_on", 2.6, -3.22, 4.8, 3.6, -3.2, 6.2, collide=False)
    k.box("neon_green", 3.4, -2.0, 7.2, 3.6, -1.8, 8.2, collide=False)


@prop("conveyor", "factory")
def conveyor(k):
    k.box("metal_gray", -6.0, -1.4, 2.8, 6.0, 1.4, 3.2)
    k.box("rubber", -6.0, -1.2, 3.2, 6.0, 1.2, 3.3, collide=False)
    for x in (-5.5, 0.0, 5.5):
        legs4(k, "metal_gray", 0.8, 2.6, 2.8, 0.2, 0.0)
        k.box("metal_gray", x - 0.2, -1.3, 0, x + 0.2, -1.1, 2.8, collide=False)
        k.box("metal_gray", x - 0.2, 1.1, 0, x + 0.2, 1.3, 2.8, collide=False)
    for i in range(4):
        k.box("cardboard", -5.0 + i * 3.0, -0.9, 3.3, -3.6 + i * 3.0, 0.9, 4.6, collide=False)


@prop("control_panel", "factory")
def control_panel(k):
    k.box("metal_gray", -2.0, -0.8, 0, 2.0, 0.8, 6.4)
    k.box("metal_dark", -1.8, -0.82, 3.0, 1.8, -0.8, 6.0, collide=False)
    for i in range(6):
        m = ("traffic_red", "traffic_green", "traffic_amber")[i % 3]
        k.box(m, -1.5 + i * 0.55, -0.86, 5.3, -1.2 + i * 0.55, -0.82, 5.6, collide=False)
    k.box("screen_on", -1.4, -0.84, 3.6, 0.6, -0.82, 4.8, collide=False)


@prop("tank_vertical", "factory")
def tank_vertical(k):
    k.cyl("metal_white", 0, 0, 1.0, 3.0, 13.0, 14)
    for a in range(4):
        ang = a * math.pi / 2
        k.box("metal_gray", 2.4 * math.cos(ang) - 0.2, 2.4 * math.sin(ang) - 0.2, 0,
              2.4 * math.cos(ang) + 0.2, 2.4 * math.sin(ang) + 0.2, 1.0)
    cone(k, "metal_white", 0, 0, 14.0, 3.0, 0.5, 1.4, 14)


@prop("mixer_vat", "factory")
def mixer_vat(k):
    k.cyl("metal_chrome", 0, 0, 2.0, 2.6, 5.0, 14)
    k.cyl("metal_gray", 0, 0, 7.0, 0.6, 2.0, 8)
    legs4(k, "metal_gray", 4.4, 4.4, 2.0, 0.4, 0.0)
    k.hcyl("metal", 0, -3.0, 2.6, 0.3, 2.0, axis="y", sides=6, collide=False)


@prop("industrial_boiler", "factory")
def industrial_boiler(k):
    k.hcyl("metal_red", 0, 0, 3.8, 3.2, 12.0, axis="x", sides=14)
    k.box("metal_dark", -5.6, -2.6, 0, 5.6, 2.6, 0.8)
    k.cyl("metal_dark", 4.0, 0, 6.8, 0.8, 10.0, 8, collide=False)


@prop("pipe_rack", "factory", collide="none")
def pipe_rack(k):
    for x in (-6.0, 6.0):
        k.box("metal_yellow", x - 0.25, -0.25, 0, x + 0.25, 0.25, 13.0)
    k.box("metal_yellow", -6.0, -0.3, 12.6, 6.0, 0.3, 13.0)
    for i, (m, r) in enumerate((("metal", 0.5), ("metal_red", 0.35), ("metal_green", 0.4),
                                ("metal_rust", 0.3))):
        k.hcyl(m, 0, -0.9 + i * 0.6, 13.0 + r, r, 12.0, axis="x", sides=8)


@prop("hvac_rooftop", "roof")
def hvac_rooftop(k):
    k.box("metal_beige", -4.0, -3.0, 0, 4.0, 3.0, 4.6)
    k.box("metal_dark", -3.6, -3.02, 0.6, 3.6, -3.0, 3.4, collide=False)
    k.cyl("metal_dark", 1.6, 0.6, 4.6, 1.4, 0.4, 10, collide=False)
    k.box("metal_gray", -4.2, -3.2, 0, 4.2, 3.2, 0.3)


@prop("roof_vent", "roof", collide="none")
def roof_vent(k):
    k.cyl("metal", 0, 0, 0, 0.6, 2.4, 8)
    cone(k, "metal", 0, 0, 2.4, 1.1, 0.2, 0.8, 8)


@prop("exhaust_fan", "roof")
def exhaust_fan(k):
    k.box("metal", -1.6, -1.6, 0, 1.6, 1.6, 1.2)
    cone(k, "metal", 0, 0, 1.2, 1.5, 0.6, 1.2, 10)


@prop("satellite_dish", "roof", collide="none", detail=2)
def satellite_dish(k):
    k.box("metal_gray", -0.1, -0.1, 0, 0.1, 0.1, 2.0)
    k.obox("plastic_white", 0, -0.5, 2.4, 2.6, 0.3, 2.6, rot_x(0.6))


@prop("water_tank_roof", "roof")
def water_tank_roof(k):
    for x in (-2.4, 2.4):
        for y in (-2.4, 2.4):
            k.box("metal_dark", x - 0.3, y - 0.3, 0, x + 0.3, y + 0.3, 6.0)
    k.box("metal_dark", -3.0, -3.0, 6.0, 3.0, 3.0, 6.5)
    k.cyl("wood_weathered", 0, 0, 6.5, 3.2, 9.0, 14)
    for z in (8.0, 11.0, 14.0):
        k.cyl("metal_dark", 0, 0, z, 3.25, 0.2, 14, collide=False)
    cone(k, "roof_tar", 0, 0, 15.5, 3.5, 0.2, 2.4, 14)


@prop("roof_hatch", "roof")
def roof_hatch(k):
    k.box("metal_gray", -1.8, -1.8, 0, 1.8, 1.8, 1.2)
    k.box("metal_dark", -1.6, -1.6, 1.2, 1.6, 1.6, 1.35)


@prop("roof_access", "roof", collide=[(-3.0, -3.0, 0, 3.0, 3.0, 9.0)])
def roof_access(k):
    # stair bulkhead with a door facing -Y
    k.box("block_gray", -3.0, -3.0, 0, 3.0, 3.0, 9.0)
    k.box("roof_membrane", -3.3, -3.3, 9.0, 3.3, 3.3, 9.4)
    k.box("door_metal", -1.8, -3.15, 0, 1.8, -3.0, 7.5)
    k.box("metal_chrome", 1.1, -3.3, 3.4, 1.3, -3.15, 4.0)
    k.box("lamp_warm", -0.4, -3.4, 8.0, 0.4, -3.0, 8.5)


@prop("antenna_mast", "roof", collide="none", detail=2)
def antenna_mast(k):
    k.cyl("metal", 0, 0, 0, 0.12, 12.0, 6)
    for z in (6.0, 9.0, 11.0):
        k.box("metal", -1.5, -0.05, z, 1.5, 0.05, z + 0.1)


@prop("skylight", "roof", collide="none", detail=2)
def skylight(k):
    k.box("frame_alu", -3.0, -2.0, 0, 3.0, 2.0, 0.8)
    k.obox("glass", 0, 0, 1.0, 5.6, 3.8, 0.2, rot_x(0.12))


@prop("ac_window_unit", "exterior", mount="wall", collide="none", detail=2)
def ac_window_unit(k):
    k.box("metal_beige", -1.2, -1.6, 0, 1.2, 0.6, 1.6)
    k.box("metal_dark", -1.0, -1.62, 0.2, 1.0, -1.6, 1.4)


@prop("ac_condenser", "exterior")
def ac_condenser(k):
    k.box("metal_beige", -1.4, -1.4, 0, 1.4, 1.4, 3.0)
    k.cyl("metal_dark", 0, 0, 3.0, 1.1, 0.1, 10, collide=False)
    k.box("concrete", -1.6, -1.6, -0.1, 1.6, 1.6, 0.1)


@prop("gas_meter", "exterior", mount="wall", collide="none", detail=3)
def gas_meter(k):
    k.box("metal_gray", -0.6, -0.6, 2.0, 0.6, 0.0, 3.2)
    k.cyl("metal", 0.2, -0.3, 0, 0.12, 2.0, 6)


@prop("dumpster", "exterior")
def dumpster(k):
    k.box("$metal", -3.5, -2.0, 0.4, 3.5, 2.0, 4.6)
    k.obox("plastic_black", 0, -0.1, 4.9, 7.2, 4.2, 0.3, rot_x(0.1), collide=False)
    for x in (-3.0, 3.0):
        for y in (-1.6, 1.6):
            k.cyl("rubber", x, y, 0, 0.3, 0.4, 6, collide=False)
    k.box("metal_dark", -3.6, -2.1, 3.4, 3.6, 2.1, 3.7, collide=False)


@prop("recycling_bin", "exterior")
def recycling_bin(k):
    k.box("metal_blue", -2.5, -1.6, 0.2, 2.5, 1.6, 4.0)
    k.box("metal_dark", -2.5, -1.6, 4.0, 2.5, 1.6, 4.2, collide=False)


@prop("grease_bin", "exterior", detail=2)
def grease_bin(k):
    k.box("metal_rust", -1.3, -1.0, 0, 1.3, 1.0, 3.2)


@prop("propane_cage", "exterior")
def propane_cage(k):
    k.box("metal_gray", -2.4, -1.2, 0, 2.4, 1.2, 0.2)
    for i in range(4):
        k.cyl("metal_white", -1.7 + i * 1.15, 0, 0.2, 0.5, 2.8, 8, collide=False)
    k.box("metal_gray", -2.4, -1.2, 0.2, 2.4, -1.15, 4.6, collide=False)
    k.box("metal_gray", -2.4, -1.2, 4.6, 2.4, 1.2, 4.8)


@prop("fuel_tank_ag", "exterior")
def fuel_tank_ag(k):
    k.hcyl("metal_white", 0, 0, 3.0, 2.4, 10.0, axis="x", sides=12)
    for x in (-3.6, 3.6):
        k.box("concrete", x - 0.6, -2.0, 0, x + 0.6, 2.0, 1.2)


@prop("transformer_box", "exterior")
def transformer_box(k):
    k.box("metal_green", -2.2, -2.0, 0, 2.2, 2.0, 4.2)
    k.box("concrete", -2.6, -2.4, -0.2, 2.6, 2.4, 0.2)


@prop("generator", "exterior")
def generator(k):
    k.box("metal_beige", -4.0, -2.0, 0.4, 4.0, 2.0, 5.0)
    k.box("metal_dark", -3.8, -2.02, 1.0, 1.0, -2.0, 4.4, collide=False)
    k.cyl("metal_dark", 3.0, 1.0, 5.0, 0.3, 2.0, 6, collide=False)
    k.box("concrete", -4.4, -2.4, -0.2, 4.4, 2.4, 0.4)


@prop("shipping_container", "industrial", tags=("container",))
def shipping_container(k):
    # 40ft box: 8.0 wide x 40 long x 8.6 high (doors on +Y)
    k.box("$metal", -4.0, -20.0, 0, 4.0, 20.0, 8.6)
    for i in range(16):
        y = -19.0 + i * 2.5
        k.box("$metal", -4.15, y, 0.3, 4.15, y + 0.6, 8.3, collide=False)
    k.box("metal_dark", -3.8, 20.0, 0.3, -0.1, 20.15, 8.3, collide=False)
    k.box("metal_dark", 0.1, 20.0, 0.3, 3.8, 20.15, 8.3, collide=False)


@prop("storage_container_20", "industrial", tags=("container",))
def storage_container_20(k):
    k.box("$metal", -4.0, -10.0, 0, 4.0, 10.0, 8.6)
    for i in range(8):
        y = -9.4 + i * 2.5
        k.box("$metal", -4.15, y, 0.3, 4.15, y + 0.6, 8.3, collide=False)


@prop("cage_partition", "industrial", collide=[(-5.0, -0.1, 0, 5.0, 0.1, 9.0)])
def cage_partition(k):
    k.box("metal_gray", -5.0, -0.1, 0, -4.8, 0.1, 9.0)
    k.box("metal_gray", 4.8, -0.1, 0, 5.0, 0.1, 9.0)
    k.box("metal_gray", -5.0, -0.1, 8.8, 5.0, 0.1, 9.0)
    k.box("glass_frosted", -4.8, -0.03, 0.2, 4.8, 0.03, 8.8, collide=False)


@prop("loading_dock_leveler", "industrial", collide="none", detail=2)
def loading_dock_leveler(k):
    k.box("diamond_plate", -3.4, -3.0, -0.1, 3.4, 0.0, 0.05)
    k.box("rubber", -4.5, 0.0, 0.0, -3.6, 0.8, 4.6)
    k.box("rubber", 3.6, 0.0, 0.0, 4.5, 0.8, 4.6)


@prop("dock_bumpers", "industrial", mount="wall", collide="none", detail=2)
def dock_bumpers(k):
    for x in (-3.6, 3.6):
        k.box("rubber", x - 0.5, -0.8, -1.4, x + 0.5, 0.0, -0.2)


@prop("time_clock", "industrial", mount="wall", collide="none", detail=3)
def time_clock(k):
    k.box("plastic_gray", -0.5, -0.4, 4.0, 0.5, 0.0, 5.2)
    k.box("metal_gray", 0.8, -0.3, 3.0, 2.4, 0.0, 5.6)


@prop("first_aid", "safety", mount="wall", collide="none", detail=3)
def first_aid(k):
    k.box("plastic_white", -0.6, -0.3, 4.2, 0.6, 0.0, 5.2)
    k.box("neon_red", -0.15, -0.32, 4.5, 0.15, -0.3, 4.9)


@prop("safety_sign", "safety", mount="wall", collide="none", detail=3)
def safety_sign(k):
    k.box("sign_yellow", -1.0, -0.05, 5.0, 1.0, 0.0, 6.4)
    k.box("hazard_black", -0.7, -0.06, 5.3, 0.7, -0.05, 5.5)


@prop("ladder_wall", "exterior", mount="wall", collide=[(-0.9, -1.0, 0, 0.9, 0.0, 1.0)])
def ladder_wall(k):
    # 1 unit tall; stretched vertically by placement scale
    for x in (-0.8, 0.8):
        k.box("metal_gray", x - 0.1, -0.9, 0, x + 0.1, -0.7, 1.0)
    k.box("metal_gray", -0.8, -0.85, 0.45, 0.8, -0.75, 0.55)


@prop("storage_unit_door", "industrial", mount="wall", collide="none")
def storage_unit_door(k):
    k.box("rollup_door", -4.5, -0.25, 0, 4.5, 0.0, 8.0)
    for i in range(10):
        k.box("metal_gray", -4.5, -0.28, 0.4 + i * 0.75, 4.5, -0.25, 0.5 + i * 0.75)
    k.box("metal_chrome", -0.6, -0.4, 0.4, 0.6, -0.25, 0.8)


# --- Marina / fishing ---------------------------------------------------------

@prop("fish_crates", "marina")
def fish_crates(k):
    for i in range(3):
        for j in range(2):
            k.box(("plastic_blue", "plastic_white", "plastic_blue")[i], -2.0 + j * 2.1, -1.2,
                  i * 0.9, -0.1 + j * 2.1, 1.2, i * 0.9 + 0.85)
    k.box("plastic_white", -1.8, -1.0, 2.7, -0.3, 1.0, 2.8, collide=False)


@prop("ice_bin_fish", "marina")
def ice_bin_fish(k):
    k.box("plastic_white", -2.5, -2.0, 0, 2.5, 2.0, 3.2)
    k.box("glass_frosted", -2.3, -1.8, 3.0, 2.3, 1.8, 3.25, collide=False)


@prop("net_pile", "marina", collide="none", detail=2)
def net_pile(k):
    k.ball("net", 0, 0, 0.8, 2.6, 1.8, 0.9)
    k.ball("plastic_orange", 1.6, 0.6, 1.2, 0.5)
    k.ball("plastic_orange", -1.4, -0.8, 1.0, 0.45)


@prop("rope_coil", "marina", collide="none", detail=3)
def rope_coil(k):
    k.cyl("rope", 0, 0, 0, 1.2, 0.6, 10)


@prop("buoy_stack", "marina", detail=2)
def buoy_stack(k):
    for i, (x, y) in enumerate(((-0.8, 0), (0.8, 0.1), (0, 0.9))):
        k.ball(("plastic_orange", "plastic_red", "plastic_white")[i], x, y, 0.8, 0.8)


@prop("life_ring", "marina", mount="wall", collide="none", detail=2)
def life_ring(k):
    k.hcyl("plastic_orange", 0, -0.2, 4.6, 1.1, 0.4, axis="y", sides=12)
    k.hcyl("metal_white", 0, -0.25, 4.6, 0.6, 0.45, axis="y", sides=10)


@prop("outboard_stand", "marina", detail=2)
def outboard_stand(k):
    k.box("metal_gray", -1.0, -1.0, 0, 1.0, 1.0, 3.0)
    k.box("plastic_black", -0.7, -0.8, 3.0, 0.7, 0.8, 5.0)
    k.box("metal_gray", -0.2, -0.3, 0.2, 0.2, 0.3, 3.0, collide=False)


@prop("kayak_rack", "marina")
def kayak_rack(k):
    for x in (-4.0, 4.0):
        k.box("wood_raw", x - 0.3, -1.4, 0, x + 0.3, 1.4, 6.0)
    for i, z in enumerate((1.4, 3.2, 5.0)):
        k.box("wood_raw", -4.0, -1.4, z - 0.3, 4.0, 1.4, z)
        k.box(("plastic_red", "plastic_yellow", "plastic_teal")[i], -6.0, -0.8, z, 6.0, 0.8,
              z + 0.9, collide=False)


@prop("bait_fridge", "marina")
def bait_fridge(k):
    k.box("metal_white", -2.0, -1.3, 0, 2.0, 1.3, 3.6)
    k.box("glass_store", -1.8, -1.0, 3.6, 1.8, 1.0, 3.7, collide=False)
    k.box("sign_blue", -1.8, -1.32, 2.4, 1.8, -1.3, 3.2, collide=False)


@prop("dock_cleat", "marina", collide="none", detail=3)
def dock_cleat(k):
    k.box("metal_dark", -0.6, -0.15, 0, 0.6, 0.15, 0.35)


@prop("bollard_dock", "marina")
def bollard_dock(k):
    k.cyl("metal_dark", 0, 0, 0, 0.6, 1.8, 10)
    k.cyl("metal_dark", 0, 0, 1.8, 0.8, 0.3, 10)


@prop("boat_trailer", "marina", collide="none")
def boat_trailer(k):
    k.box("metal_gray", -2.6, -8.0, 1.4, -2.2, 8.0, 1.8)
    k.box("metal_gray", 2.2, -8.0, 1.4, 2.6, 8.0, 1.8)
    k.box("metal_gray", -0.2, -11.0, 1.4, 0.2, -8.0, 1.8)
    for y in (-1.0, 1.4):
        car_wheel(k, -2.9, y, 1.2, 0.7)
        car_wheel(k, 2.9, y, 1.2, 0.7)
