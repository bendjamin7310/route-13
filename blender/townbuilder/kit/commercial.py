"""Office, retail, food service, nightlife, civic and emergency-service props."""

from __future__ import annotations

import math

from . import prop, NEUTRAL, COOL, WARM
from .shapes import cabinet, legs4, shelf_unit, table, cone
from ..geom import rot_z

GOODS = ["goods_mix1", "goods_mix2", "goods_mix3", "goods_mix4", "goods_mix5", "cardboard",
         "food_red", "food_yellow"]

# --- Office -------------------------------------------------------------------


@prop("desk_office", "office")
def desk_office(k):
    k.box("$wood", -2.6, -1.3, 2.4, 2.6, 1.3, 2.6)
    k.box("metal_gray", -2.5, -1.2, 0, -2.3, 1.2, 2.4, collide=False)
    cabinet(k, "metal_gray", "metal_gray", 1.6, 2.3, 2.4, doors=1, drawers=3, y_front=-1.15)


@prop("desk_workstation", "office")
def desk_workstation(k):
    desk_office(k)
    k.box("plastic_black", -0.9, 0.4, 2.6, 0.9, 0.6, 2.7, collide=False)
    k.box("plastic_black", -0.1, 0.45, 2.7, 0.1, 0.55, 3.2, collide=False)
    k.box("plastic_black", -1.2, 0.35, 3.2, 1.2, 0.55, 4.6, collide=False)
    k.box("screen_on", -1.1, 0.33, 3.3, 1.1, 0.35, 4.5, collide=False)
    k.box("plastic_gray", -0.9, -0.6, 2.6, 0.7, -0.1, 2.7, collide=False)
    k.box("paper", 1.2, -0.8, 2.6, 2.2, 0.2, 2.75, collide=False)


@prop("desk_cop", "office")
def desk_cop(k):
    k.box("metal_gray", -2.6, -1.3, 2.4, 2.6, 1.3, 2.6)
    cabinet(k, "metal_gray", "metal_gray", 1.6, 2.3, 2.4, doors=1, drawers=3, y_front=-1.15)
    k.box("metal_gray", -2.5, -1.2, 0, -2.3, 1.2, 2.4, collide=False)
    k.box("plastic_beige", -1.0, 0.0, 2.6, 0.6, 1.2, 4.0, collide=False)
    k.box("screen_on", -0.8, -0.02, 2.9, 0.4, 0.0, 3.8, collide=False)
    k.box("paper", 0.9, -0.9, 2.6, 2.3, 0.4, 3.0, collide=False)
    k.box("plastic_black", -2.2, -0.6, 2.6, -1.6, 0.0, 2.9, collide=False)


@prop("file_cabinet", "office")
def file_cabinet(k):
    cabinet(k, "$metal", "$metal", 1.6, 2.3, 4.6, doors=1, drawers=4)


@prop("printer_copier", "office")
def printer_copier(k):
    k.box("plastic_beige", -1.6, -1.2, 0, 1.6, 1.2, 3.4)
    k.box("plastic_gray", -1.6, -1.2, 3.4, 1.6, 1.2, 3.9)
    k.box("screen_on", 0.6, -1.0, 3.9, 1.3, -0.4, 4.0, collide=False)


@prop("water_cooler", "office", collide="none", detail=2)
def water_cooler(k):
    k.box("plastic_white", -0.6, -0.6, 0, 0.6, 0.6, 3.4)
    k.cyl("plastic_blue", 0, 0, 3.4, 0.5, 1.4, 8)


@prop("conference_table", "office")
def conference_table(k):
    table(k, "$wood", "metal_dark", 12.0, 4.6, 2.6, 0.25, 0.4)


@prop("reception_desk", "office")
def reception_desk(k):
    k.box("$wood", -4.0, -1.6, 0, 4.0, 1.6, 3.6)
    k.box("marble", -4.2, -1.8, 3.6, 4.2, -0.8, 3.8, collide=False)
    k.box("plastic_black", -1.0, 0.0, 3.0, 1.0, 0.2, 4.2, collide=False)
    k.box("screen_on", -0.9, -0.02, 3.1, 0.9, 0.0, 4.1, collide=False)


@prop("waiting_chairs", "office")
def waiting_chairs(k):
    for i in range(4):
        x = -3.3 + i * 2.2
        k.box("$fabric", x - 1.0, -0.9, 1.4, x + 1.0, 0.9, 1.8)
        k.box("$fabric", x - 1.0, 0.6, 1.8, x + 1.0, 0.9, 3.6, collide=False)
    k.box("metal_chrome", -4.4, -0.8, 0, 4.4, 0.8, 1.4)


@prop("cubicle", "office")
def cubicle(k):
    # 7x7 cubicle opening toward -Y, includes workstation
    for (x0, y0, x1, y1) in ((-3.5, -3.5, -3.3, 3.5), (3.3, -3.5, 3.5, 3.5), (-3.5, 3.3, 3.5, 3.5)):
        k.box("fabric_gray", x0, y0, 0, x1, y1, 5.0)
    k.box("$wood", -3.3, 1.2, 2.4, 3.3, 3.3, 2.6, collide=False)
    k.box("plastic_black", -1.0, 2.2, 2.6, 1.0, 2.5, 4.0, collide=False)
    k.box("screen_on", -0.9, 2.18, 2.7, 0.9, 2.2, 3.9, collide=False)
    k.box("paper", 1.5, 1.6, 2.6, 2.8, 2.8, 2.8, collide=False)


@prop("safe_box", "office")
def safe_box(k):
    k.box("metal_dark", -1.2, -1.2, 0, 1.2, 1.2, 3.2)
    k.hcyl("metal_chrome", 0.3, -1.25, 1.9, 0.35, 0.1, axis="y", sides=8)
    k.box("metal_chrome", -0.7, -1.3, 1.2, -0.5, -1.2, 2.4, collide=False)


@prop("server_rack", "office")
def server_rack(k):
    k.box("metal_dark", -1.2, -1.6, 0, 1.2, 1.6, 7.0)
    for i in range(8):
        z = 0.6 + i * 0.75
        k.box("plastic_black", -1.0, -1.62, z, 1.0, -1.6, z + 0.6, collide=False)
        k.box("neon_green", 0.6, -1.64, z + 0.2, 0.7, -1.62, z + 0.3, collide=False)


@prop("coffee_station", "office")
def coffee_station(k):
    cabinet(k, "$paint", "$paint", 4.0, 2.2, 2.8, doors=2, y_front=-1.1)
    k.box("plastic_beige", -2.1, -1.2, 2.8, 2.1, 1.1, 3.0)
    k.box("plastic_black", -1.6, -0.2, 3.0, -0.6, 0.7, 4.2, collide=False)
    k.box("$metal", 0.3, -0.4, 3.0, 1.8, 0.7, 4.0, collide=False)


@prop("vending_machine", "retail")
def vending_machine(k):
    k.box("$plastic", -1.6, -1.3, 0, 1.6, 1.3, 6.4)
    k.box("glass_store", -1.4, -1.32, 1.6, 0.6, -1.3, 6.0, collide=False)
    for i in range(5):
        z = 1.9 + i * 0.8
        k.box("goods_mix%d" % (i % 5 + 1), -1.3, -1.2, z, 0.5, -0.6, z + 0.5, collide=False)
    k.box("plastic_black", 0.8, -1.32, 3.2, 1.4, -1.3, 4.6, collide=False)
    k.box("lamp_cool", -1.5, -1.33, 6.0, 1.5, -1.3, 6.3, collide=False)


@prop("snack_machine", "retail")
def snack_machine(k):
    k.box("plastic_black", -1.6, -1.3, 0, 1.6, 1.3, 6.4)
    k.box("glass_store", -1.5, -1.32, 1.0, 0.7, -1.3, 6.0, collide=False)
    for r in range(5):
        for c in range(3):
            k.box(GOODS[(r + c) % 5], -1.3 + c * 0.7, -1.2, 1.3 + r * 0.9, -0.8 + c * 0.7, -0.4,
                  1.8 + r * 0.9, collide=False)


@prop("atm", "retail")
def atm(k):
    k.box("metal_gray", -1.0, -0.9, 0, 1.0, 0.9, 5.2)
    k.box("screen_on", -0.6, -0.92, 3.4, 0.6, -0.9, 4.2, collide=False)
    k.box("metal_dark", -0.7, -1.3, 2.7, 0.7, -0.9, 3.0, collide=False)


@prop("payphone", "street", collide="none")
def payphone(k):
    k.box("metal_chrome", -0.15, -0.1, 0, 0.15, 0.2, 7.0)
    k.box("metal_gray", -0.9, -0.6, 3.6, 0.9, 0.2, 6.6)
    k.box("plastic_black", -0.5, -0.65, 4.0, 0.5, -0.6, 6.0)
    k.box("metal_gray", -1.0, -0.9, 6.6, 1.0, 0.2, 6.9)


# --- Retail ---------------------------------------------------------------------

@prop("shelf_gondola", "retail")
def shelf_gondola(k):
    # double-sided aisle shelving, 8 long (x) x 3 deep (y)
    k.box("metal_white", -4.0, -0.2, 0, 4.0, 0.2, 5.6)
    for side in (-1, 1):
        for i in range(4):
            z = 0.3 + i * 1.35
            y0, y1 = (-1.5, -0.2) if side < 0 else (0.2, 1.5)
            k.box("metal_white", -4.0, y0, z, 4.0, y1, z + 0.1, collide=False)
            x = -3.9
            j = 0
            while x < 3.6:
                w = 0.6 + ((i * 7 + j * 3 + side) % 4) * 0.2
                m = GOODS[(i * 3 + j + (side > 0)) % len(GOODS)]
                k.box(m, x, y0 + 0.1, z + 0.1, min(3.9, x + w - 0.08), y1 - 0.1,
                      z + 0.6 + ((i + j) % 3) * 0.2, collide=False)
                x += w
                j += 1
    k.box("metal_white", -4.0, -1.5, 0, 4.0, 1.5, 0.3)


@prop("shelf_wall_retail", "retail")
def shelf_wall_retail(k):
    shelf_unit(k, "metal_white", 8.0, 1.8, 7.0, 5, goods=GOODS, rng_seed=5)


@prop("cooler_display", "retail")
def cooler_display(k):
    k.box("metal_white", -4.0, -1.4, 0, 4.0, 1.4, 7.4)
    for i in range(3):
        x0 = -3.9 + i * 2.62
        k.box("glass_store", x0, -1.45, 0.5, x0 + 2.5, -1.4, 6.8, collide=False)
        for r in range(5):
            z = 0.8 + r * 1.2
            k.box(GOODS[(i + r) % 6], x0 + 0.2, -1.1, z, x0 + 2.3, 0.8, z + 0.8, collide=False)
    k.box("lamp_cool", -3.9, -1.42, 6.9, 3.9, -1.38, 7.2, collide=False)


@prop("checkout_counter", "retail")
def checkout_counter(k):
    k.box("$wood", -3.0, -1.5, 0, 3.0, 1.5, 3.4)
    k.box("plastic_beige", -3.1, -1.6, 3.4, 3.1, 1.6, 3.6)
    k.box("plastic_gray", 0.6, -0.8, 3.6, 2.2, 0.6, 4.1, collide=False)
    k.box("plastic_black", 0.8, -0.2, 4.1, 2.0, 0.4, 5.0, collide=False)
    k.box("screen_on", 0.9, -0.22, 4.2, 1.9, -0.2, 4.9, collide=False)
    k.box("goods_mix3", -2.6, -1.9, 0.4, -0.4, -1.5, 3.2, collide=False)


@prop("checkout_lane", "retail")
def checkout_lane(k):
    k.box("metal_white", -1.5, -5.0, 0, 1.5, 3.0, 3.2)
    k.box("rubber", -1.3, -5.0, 3.2, 1.3, 1.0, 3.3, collide=False)
    k.box("plastic_black", -1.0, 1.4, 3.2, 1.0, 2.6, 4.0, collide=False)
    k.box("metal_gray", -0.1, 2.0, 3.2, 0.1, 2.2, 7.5, collide=False)
    k.box("neon_white", -0.6, 1.95, 7.5, 0.6, 2.25, 8.2, collide=False)


@prop("display_case", "retail")
def display_case(k):
    k.box("$wood", -3.0, -1.2, 0, 3.0, 1.2, 2.0)
    k.box("glass_store", -3.0, -1.2, 2.0, 3.0, 1.2, 3.6)
    k.box("metal_chrome", -2.6, -0.6, 2.1, -1.8, 0.2, 2.3, collide=False)
    k.box("metal_brass", -1.2, -0.5, 2.1, -0.6, 0.3, 2.6, collide=False)
    k.box("plastic_black", 0.0, -0.6, 2.1, 1.0, 0.4, 2.4, collide=False)
    k.box("metal_chrome", 1.6, -0.2, 2.1, 2.6, 0.5, 2.8, collide=False)


@prop("clothing_rack", "retail", collide="none")
def clothing_rack(k):
    k.box("metal_chrome", -2.2, -0.1, 4.8, 2.2, 0.1, 5.0)
    for x in (-2.1, 2.1):
        k.box("metal_chrome", x - 0.1, -0.1, 0, x + 0.1, 0.1, 5.0)
        k.box("metal_chrome", x - 0.1, -0.8, 0, x + 0.1, 0.8, 0.15)
    for i in range(8):
        x = -1.9 + i * 0.5
        k.box(("$fabric", "fabric_cream", "fabric_dark", "$fabric2")[i % 4], x, -0.7, 2.0,
              x + 0.4, 0.7, 4.7)


@prop("mannequin", "retail", collide="none", detail=2)
def mannequin(k):
    k.cyl("metal_chrome", 0, 0, 0, 0.6, 0.1, 8)
    k.cyl("metal_chrome", 0, 0, 0.1, 0.08, 2.4, 4)
    k.box("$fabric", -0.8, -0.4, 2.5, 0.8, 0.4, 4.5)
    k.ball("plastic_white", 0, 0, 5.0, 0.45)


@prop("produce_bin", "retail")
def produce_bin(k):
    k.box("wood", -2.5, -2.0, 0, 2.5, 2.0, 2.4)
    for i, m in enumerate(("food_red", "food_green", "food_orange", "food_yellow")):
        x0 = -2.4 + (i % 2) * 2.45
        y0 = -1.9 + (i // 2) * 1.95
        k.box(m, x0, y0, 2.4, x0 + 2.3, y0 + 1.8, 2.9, collide=False)


@prop("deli_counter", "retail")
def deli_counter(k):
    k.box("metal_white", -4.0, -1.5, 0, 4.0, 1.5, 3.0)
    k.box("glass_store", -4.0, -1.5, 3.0, 4.0, 0.5, 4.6, collide=False)
    for i, m in enumerate(("food_red", "food_brown", "food_yellow", "food_green")):
        k.box(m, -3.6 + i * 1.9, -1.0, 3.05, -2.2 + i * 1.9, 0.2, 3.4, collide=False)
    k.box("plastic_white", -4.0, 0.5, 3.0, 4.0, 1.5, 3.2, collide=False)


@prop("shopping_carts", "retail", collide="none", detail=2)
def shopping_carts(k):
    for i in range(3):
        y = -1.2 + i * 1.0
        k.box("metal_chrome", -1.0, y - 1.4, 1.2, 1.0, y + 1.4, 3.0)
        k.box("plastic_red", -1.0, y + 1.3, 3.0, 1.0, y + 1.5, 3.6)


@prop("magazine_rack", "retail", detail=2)
def magazine_rack(k):
    k.box("metal_chrome", -1.6, -0.6, 0, 1.6, 0.6, 4.4)
    for r in range(4):
        for c in range(4):
            k.box(GOODS[(r * 4 + c) % 8], -1.5 + c * 0.78, -0.65, 0.4 + r * 1.0, -0.8 + c * 0.78,
                  -0.6, 1.2 + r * 1.0, collide=False)


@prop("pegboard_tools", "retail", mount="wall", collide="none")
def pegboard_tools(k):
    k.box("plywood", -4.0, 0.0, 0, 4.0, 0.15, 5.0)
    for r in range(4):
        for c in range(7):
            m = ("metal_red", "metal_yellow", "metal_dark", "metal", "plastic_blue")[(r + c) % 5]
            k.box(m, -3.6 + c * 1.05, -0.4, 0.5 + r * 1.1, -3.0 + c * 1.05, 0.0, 1.2 + r * 1.1)


@prop("paint_shelf", "retail")
def paint_shelf(k):
    shelf_unit(k, "metal_orange", 8.0, 2.2, 7.0, 4, rng_seed=9)
    for r in range(4):
        for c in range(10):
            m = ("paint_cream", "paint_blue", "paint_mustard", "paint_sage", "paint_terracotta",
                 "plastic_white")[(r * 3 + c) % 6]
            k.cyl(m, -3.4 + c * 0.75, -0.2, 0.4 + r * 1.65, 0.33, 0.8, 8, collide=False)


@prop("lumber_rack", "retail")
def lumber_rack(k):
    k.box("metal_orange", -6.0, -0.2, 0, -5.7, 2.4, 9.0)
    k.box("metal_orange", 5.7, -0.2, 0, 6.0, 2.4, 9.0)
    for z in (1.0, 3.5, 6.0):
        k.box("metal_orange", -6.0, -0.2, z - 0.2, 6.0, 2.4, z)
        k.box("wood_raw", -5.6, 0.0, z, 5.6, 2.2, z + 1.4, collide=False)


@prop("tv_display_wall", "retail", mount="wall", collide="none")
def tv_display_wall(k):
    for r in range(2):
        for c in range(3):
            x = -5.0 + c * 3.4
            z = 0.3 + r * 2.4
            k.box("plastic_black", x, -0.2, z, x + 3.2, 0.0, z + 2.0)
            k.box("screen_on", x + 0.1, -0.22, z + 0.1, x + 3.1, -0.2, z + 1.9)


@prop("electronics_table", "retail")
def electronics_table(k):
    table(k, "$wood", "metal_dark", 6.0, 3.0, 3.0)
    for i in range(3):
        x = -2.0 + i * 2.0
        k.box("plastic_black", x - 0.7, -0.4, 3.0, x + 0.7, 0.3, 3.1, collide=False)
        k.box("screen_on", x - 0.6, 0.1, 3.1, x + 0.6, 0.15, 4.0, collide=False)


@prop("pharmacy_counter", "retail")
def pharmacy_counter(k):
    k.box("$wood", -5.0, -1.4, 0, 5.0, 1.4, 3.6)
    k.box("plastic_white", -5.2, -1.6, 3.6, 5.2, 1.6, 3.8)
    k.box("glass_store", -5.0, -0.1, 3.8, 5.0, 0.1, 7.0, collide=False)
    k.box("plastic_black", 2.5, -0.6, 3.8, 3.7, 0.4, 4.8, collide=False)


@prop("pharmacy_shelf", "retail")
def pharmacy_shelf(k):
    shelf_unit(k, "plastic_white", 6.0, 1.6, 7.0, 6, goods=["plastic_white", "plastic_orange",
               "goods_mix5", "plastic_blue"], rng_seed=13, goods_fill=0.6)


@prop("furniture_display_sofa", "retail")
def furniture_display_sofa(k):
    k.box("fabric_gray", -3.8, -1.6, 0.45, 3.8, 1.6, 1.5)
    k.box("fabric_gray", -3.8, 0.7, 1.5, 3.8, 1.6, 3.0, collide=False)
    k.box("sign_white", 2.5, -1.7, 1.5, 3.4, -1.6, 2.2, collide=False)


@prop("price_sign", "retail", mount="surface", collide="none", detail=3)
def price_sign(k):
    k.box("sign_yellow", -0.6, -0.05, 0, 0.6, 0.05, 0.8)


# --- Food service & nightlife ------------------------------------------------------

@prop("booth", "food")
def booth(k):
    # two benches facing a table, 6 wide (x) x 7.6 long (y)
    for sy in (-1, 1):
        y0 = sy * 3.8
        y1 = sy * 2.4
        k.box("$fabric", -3.0, min(y0, y1), 0, 3.0, max(y0, y1), 1.6)
        yb0 = sy * 3.8
        yb1 = sy * 3.2
        k.box("$fabric", -3.0, min(yb0, yb1), 1.6, 3.0, max(yb0, yb1), 4.2, collide=False)
    k.box("plastic_beige", -2.8, -1.6, 2.5, 2.8, 1.6, 2.7)
    k.cyl("metal_chrome", 0, 0, 0, 0.2, 2.5, 6, collide=False)
    k.box("metal_chrome", -0.3, -0.3, 2.7, 0.3, 0.3, 3.2, collide=False)


@prop("restaurant_table_2", "food")
def restaurant_table_2(k):
    table(k, "$wood", "metal_dark", 3.0, 3.0, 2.6)
    for sy in (-1, 1):
        k.box("$fabric", -0.8, sy * 2.0 - 0.8, 1.45, 0.8, sy * 2.0 + 0.8, 1.65, collide=False)
        legs4(k, "metal_dark", 1.6, 1.6, 1.45, 0.12, 0.05)
        k.box("$fabric", -0.8, sy * 2.75 - 0.08, 1.65, 0.8, sy * 2.75 + 0.08, 3.5, collide=False)


@prop("restaurant_table_4", "food")
def restaurant_table_4(k):
    table(k, "$wood", "metal_dark", 4.0, 4.0, 2.6)
    k.cyl("ceramic", 0, 0, 2.6, 0.25, 0.4, 6, collide=False)
    for a in range(4):
        ang = a * math.pi / 2
        cx, cy = 2.6 * math.cos(ang), 2.6 * math.sin(ang)
        r = rot_z(ang + math.pi / 2)
        k.obox("$fabric", cx, cy, 1.55, 1.6, 1.6, 0.2, r, collide=False)
        bx, by = 3.35 * math.cos(ang), 3.35 * math.sin(ang)
        k.obox("$fabric", bx, by, 2.55, 1.6, 0.16, 2.0, r, collide=False)


@prop("high_top", "food")
def high_top(k):
    k.cyl("$wood", 0, 0, 3.6, 1.4, 0.2, 10)
    k.cyl("metal_dark", 0, 0, 0, 0.15, 3.6, 6)
    k.cyl("metal_dark", 0, 0, 0, 0.9, 0.1, 8)


@prop("bar_counter", "bar")
def bar_counter(k):
    # 10 long front bar, customers on -Y side
    k.box("$wood", -5.0, -1.0, 0, 5.0, 1.4, 3.6)
    k.box("wood_dark", -5.2, -1.6, 3.6, 5.2, 1.4, 3.85)
    k.box("metal_brass", -5.0, -1.7, 0.5, 5.0, -1.5, 0.7, collide=False)
    for x in (-3.0, 0.5, 3.4):
        k.box("metal_chrome", x - 0.2, 0.4, 3.85, x + 0.2, 0.8, 5.0, collide=False)


@prop("back_bar", "bar")
def back_bar(k):
    cabinet(k, "wood_dark", "wood_dark", 10.0, 2.0, 3.2, doors=5, y_front=-1.0)
    k.box("wood_dark", -5.0, -1.0, 3.2, 5.0, 1.0, 3.4)
    k.box("metal_chrome", -4.8, 0.85, 3.4, 4.8, 1.0, 8.0, collide=False)
    for z in (4.5, 6.2):
        k.box("glass", -4.8, 0.2, z - 0.1, 4.8, 1.0, z, collide=False)
        for i in range(14):
            x = -4.5 + i * 0.68
            m = ("glass_tint", "food_brown", "glass", "food_yellow", "food_green")[i % 5]
            k.cyl(m, x, 0.6, z, 0.18, 1.0 + (i % 3) * 0.2, 6, collide=False)
    k.box("lamp_amber", -4.8, 0.9, 7.8, 4.8, 1.0, 8.0, collide=False)


@prop("pool_table", "bar")
def pool_table(k):
    k.box("wood_dark", -4.4, -2.4, 2.4, 4.4, 2.4, 3.0)
    k.box("felt_green", -3.9, -1.9, 3.0, 3.9, 1.9, 3.05, collide=False)
    for sx in (-1, 1):
        k.box("wood_dark", sx * 3.9, -2.4, 3.0, sx * 4.4, 2.4, 3.3, collide=False)
    for sy in (-1, 1):
        k.box("wood_dark", -3.9, sy * 1.9, 3.0, 3.9, sy * 2.4, 3.3, collide=False)
    legs4(k, "wood_dark", 8.4, 4.4, 2.4, 0.6, 0.3)
    k.ball("plastic_white", -2.0, 0, 3.25, 0.2)
    k.ball("plastic_red", 1.8, 0.2, 3.25, 0.2)
    k.ball("plastic_yellow", 2.2, -0.3, 3.25, 0.2)


@prop("pool_light", "bar", mount="ceiling", collide="none",
      light={"at": (0, 0, -3.5), "color": WARM, "range": 16, "brightness": 1.0})
def pool_light(k):
    k.cyl("metal_dark", -2.0, 0, -3.0, 0.04, 3.0, 4)
    k.cyl("metal_dark", 2.0, 0, -3.0, 0.04, 3.0, 4)
    k.box("felt_green", -3.0, -0.7, -3.6, 3.0, 0.7, -3.0)
    k.box("lamp_warm", -2.8, -0.5, -3.65, 2.8, 0.5, -3.6)


@prop("jukebox", "bar", light={"at": (0, -1.2, 3.5), "color": (1.0, 0.6, 0.4), "range": 10,
                               "brightness": 0.6})
def jukebox(k):
    k.box("wood_dark", -1.4, -1.0, 0, 1.4, 1.0, 3.6)
    k.hcyl("neon_orange", 0, -0.4, 3.6, 1.4, 1.2, axis="y", sides=12)
    k.box("glass_store", -1.0, -1.02, 1.6, 1.0, -1.0, 3.2, collide=False)
    k.box("metal_chrome", -1.2, -1.05, 0.6, 1.2, -1.0, 1.4, collide=False)


@prop("arcade_cabinet", "bar")
def arcade_cabinet(k):
    k.box("$plastic", -1.2, -1.2, 0, 1.2, 1.4, 6.2)
    k.box("screen_on", -0.9, -1.0, 3.6, 0.9, -0.9, 5.0, collide=False)
    k.box("plastic_black", -1.1, -1.8, 2.8, 1.1, -1.0, 3.2, collide=False)
    k.box("neon_pink", -1.1, -1.25, 5.5, 1.1, -1.2, 6.0, collide=False)


@prop("keg_stack", "bar")
def keg_stack(k):
    for i in range(3):
        x = -1.6 + i * 1.6
        k.cyl("metal", x, 0, 0, 0.75, 2.2, 10)
    k.cyl("metal", -0.8, 0, 2.2, 0.75, 2.2, 10)
    k.cyl("metal", 0.8, 0, 2.2, 0.75, 2.2, 10)


@prop("beer_crates", "bar", detail=2)
def beer_crates(k):
    for i in range(3):
        k.box(("plastic_red", "plastic_green", "plastic_yellow")[i], -1.0, -0.8, i * 1.1, 1.0, 0.8,
              i * 1.1 + 1.0)


@prop("menu_board", "food", mount="wall", collide="none")
def menu_board(k):
    k.box("chalkboard", -4.0, -0.15, 0, 4.0, 0.0, 3.0)
    for r in range(6):
        k.box("paper", -3.6, -0.17, 0.3 + r * 0.45, 0.0 + (r % 3) * 0.6, -0.15, 0.5 + r * 0.45)
        k.box("sign_yellow", 2.4, -0.17, 0.3 + r * 0.45, 3.4, -0.15, 0.5 + r * 0.45)


@prop("drink_fountain", "food", mount="surface", collide="none", detail=2)
def drink_fountain(k):
    k.box("metal_chrome", -1.4, -1.0, 0, 1.4, 1.0, 2.8)
    k.box("$plastic", -1.3, -1.02, 1.6, 1.3, -1.0, 2.6)


@prop("stage_platform", "bar")
def stage_platform(k):
    k.box("wood_dark", -7.0, -4.0, 0, 7.0, 4.0, 1.5)
    k.box("plastic_black", -6.0, 2.5, 1.5, -4.6, 3.8, 5.0)
    k.box("plastic_black", 4.6, 2.5, 1.5, 6.0, 3.8, 5.0)
    k.cyl("metal_chrome", 0, -1.0, 1.5, 0.1, 4.0, 6, collide=False)


@prop("dining_bench_long", "food")
def dining_bench_long(k):
    table(k, "$wood", "$wood", 12.0, 3.6, 2.6)
    for sy in (-1, 1):
        k.box("$wood", -6.0, sy * 2.6 - 0.7, 1.3, 6.0, sy * 2.6 + 0.7, 1.55)
        legs4(k, "$wood", 12.0, 1.4, 1.3, 0.25, 0.3)


# --- Civic / police / fire -----------------------------------------------------

@prop("service_counter", "civic")
def service_counter(k):
    k.box("$wood", -6.0, -1.5, 0, 6.0, 1.5, 3.6)
    k.box("marble", -6.2, -1.7, 3.6, 6.2, 1.7, 3.8)
    k.box("glass", -6.0, -0.1, 3.8, 6.0, 0.1, 7.6, collide=False)
    for x in (-3.0, 3.0):
        k.box("plastic_black", x - 0.7, 0.4, 3.8, x + 0.7, 1.2, 5.0, collide=False)
        k.box("screen_on", x - 0.6, 0.38, 3.9, x + 0.6, 0.4, 4.9, collide=False)


@prop("ticket_kiosk", "civic", detail=2)
def ticket_kiosk(k):
    k.box("metal_gray", -0.9, -0.7, 0, 0.9, 0.7, 4.8)
    k.box("screen_on", -0.7, -0.72, 3.0, 0.7, -0.7, 4.2, collide=False)


@prop("council_dais", "civic")
def council_dais(k):
    k.box("wood_dark", -10.0, -1.5, 0, 10.0, 6.0, 1.5)
    k.box("wood_dark", -9.5, -1.5, 1.5, 9.5, 0.0, 4.6)
    for i in range(5):
        x = -7.6 + i * 3.8
        k.box("leather_black", x - 1.0, 2.0, 1.5, x + 1.0, 4.0, 3.0, collide=False)
        k.box("leather_black", x - 1.0, 3.8, 3.0, x + 1.0, 4.2, 6.0, collide=False)
        k.cyl("metal_dark", x, 0.6, 4.6, 0.05, 1.0, 4, collide=False)


@prop("podium", "civic", detail=2)
def podium(k):
    k.box("wood_dark", -1.4, -1.0, 0, 1.4, 1.0, 3.9)
    k.box("wood_dark", -1.6, -1.2, 3.9, 1.6, 1.0, 4.2)
    k.cyl("metal_dark", 0, -0.6, 4.2, 0.05, 1.0, 4, collide=False)


@prop("chair_row", "civic")
def chair_row(k):
    for i in range(5):
        x = -4.4 + i * 2.2
        k.box("$fabric", x - 0.9, -0.9, 1.45, x + 0.9, 0.9, 1.75)
        k.box("$fabric", x - 0.9, 0.7, 1.75, x + 0.9, 0.9, 3.5, collide=False)
        legs4(k, "metal_dark", 1.8, 1.8, 1.45, 0.12, 0.1)


@prop("flag_pole_indoor", "civic", collide="none", detail=2)
def flag_pole_indoor(k):
    k.cyl("metal_brass", 0, 0, 0, 0.6, 0.3, 8)
    k.cyl("wood_dark", 0, 0, 0.3, 0.08, 8.0, 6)
    k.box("fabric_blue", 0.1, -0.05, 5.0, 2.6, 0.05, 7.6)


@prop("locker_row", "police")
def locker_row(k):
    for i in range(5):
        x = -4.0 + i * 1.6
        k.box("$metal", x - 0.78, -1.0, 0, x + 0.78, 1.0, 7.0)
        for z in (5.6, 5.9, 6.2):
            k.box("metal_dark", x - 0.5, -1.02, z, x + 0.5, -1.0, z + 0.1, collide=False)
        k.box("metal_chrome", x + 0.4, -1.1, 3.4, x + 0.55, -1.0, 4.2, collide=False)


@prop("locker_bench", "police")
def locker_bench(k):
    k.box("wood_light", -3.5, -0.7, 1.4, 3.5, 0.7, 1.7)
    legs4(k, "metal_chrome", 7.0, 1.4, 1.4, 0.15, 0.3)


@prop("cell_bars", "police", collide=[(-4.0, -0.2, 0, 4.0, 0.2, 10.0)])
def cell_bars(k):
    # 8 wide x 10 high bar wall with a door section (bars only - the wall gap is the cell front)
    k.box("metal_dark", -4.0, -0.2, 0, 4.0, 0.2, 0.3)
    k.box("metal_dark", -4.0, -0.2, 9.7, 4.0, 0.2, 10.0)
    k.box("metal_dark", -4.0, -0.2, 4.6, 4.0, 0.2, 4.9)
    for i in range(17):
        x = -3.8 + i * 0.475
        k.cyl("metal_dark", x, 0, 0.3, 0.07, 9.4, 4, collide=False)
    k.box("metal_dark", 1.3, -0.3, 3.0, 1.6, 0.3, 4.0, collide=False)


@prop("cell_bench", "police")
def cell_bench(k):
    k.box("concrete", -3.0, -0.9, 0, 3.0, 0.9, 1.6)


@prop("cell_toilet", "police")
def cell_toilet(k):
    k.box("metal_chrome", -0.8, -1.0, 0, 0.8, 1.0, 1.4)
    k.box("metal_chrome", -0.8, 0.5, 1.4, 0.8, 1.0, 3.0)


@prop("interview_table", "police")
def interview_table(k):
    table(k, "metal_gray", "metal_gray", 5.0, 3.0, 2.6)
    k.box("metal_chrome", -0.3, -0.3, 2.6, 0.3, 0.3, 2.8, collide=False)


@prop("evidence_cage", "police")
def evidence_cage(k):
    shelf_unit(k, "metal_gray", 8.0, 2.4, 7.0, 4, goods=["cardboard", "plastic_white",
               "cardboard", "paper"], rng_seed=31)
    k.box("metal_gray", -4.0, -1.3, 0, 4.0, -1.2, 7.0, collide=False)


@prop("briefing_board", "police", mount="wall", collide="none")
def briefing_board(k):
    k.box("frame_alu", -5.0, 0.0, 0, 5.0, 0.15, 4.0)
    k.box("whiteboard", -4.8, -0.02, 0.2, 0.0, 0.0, 3.8)
    k.box("corkboard", 0.2, -0.02, 0.2, 4.8, 0.0, 3.8)
    for i in range(6):
        x = 0.5 + (i % 3) * 1.4
        z = 0.6 + (i // 3) * 1.6
        k.box("paper", x, -0.04, z, x + 1.0, -0.02, z + 1.2)
    k.box("fabric_blue", -4.0, -0.04, 1.0, -1.0, -0.02, 3.0)


@prop("map_board", "police", mount="wall", collide="none", detail=2)
def map_board(k):
    k.box("frame_dark", -3.0, 0.0, 0, 3.0, 0.1, 3.2)
    k.box("stucco_mint", -2.9, -0.02, 0.1, 2.9, 0.0, 3.1)
    k.box("sign_blue", -2.9, -0.03, 0.1, -0.5, -0.01, 1.4)
    k.box("paint_line_yellow", -2.9, -0.04, 1.8, 2.9, -0.02, 1.95)
    k.box("paint_line_yellow", 0.4, -0.04, 0.1, 0.55, -0.02, 3.1)


@prop("radio_dispatch", "police")
def radio_dispatch(k):
    k.box("metal_gray", -4.0, -1.6, 2.4, 4.0, 1.6, 2.6)
    k.box("metal_gray", -4.0, -1.6, 0, -3.8, 1.6, 2.4, collide=False)
    k.box("metal_gray", 3.8, -1.6, 0, 4.0, 1.6, 2.4, collide=False)
    for x in (-2.4, 0, 2.4):
        k.box("plastic_black", x - 1.0, 0.6, 2.6, x + 1.0, 0.9, 4.2, collide=False)
        k.box("screen_on", x - 0.9, 0.58, 2.7, x + 0.9, 0.6, 4.1, collide=False)


@prop("metal_detector", "police", collide="none", detail=2)
def metal_detector(k):
    k.box("plastic_gray", -2.0, -0.4, 0, -1.6, 0.4, 7.4)
    k.box("plastic_gray", 1.6, -0.4, 0, 2.0, 0.4, 7.4)
    k.box("plastic_gray", -2.0, -0.4, 7.4, 2.0, 0.4, 8.0)


@prop("gear_rack", "fire")
def gear_rack(k):
    for i in range(4):
        x = -4.5 + i * 3.0
        k.box("metal_gray", x - 1.4, -1.2, 0, x - 1.3, 1.2, 7.0, collide=False)
        k.box("fabric_mustard", x - 1.1, -0.6, 2.0, x + 1.1, 0.8, 5.6)
        k.box("fabric_mustard", x - 0.9, -0.5, 0.0, x + 0.9, 0.6, 2.0)
        k.ball("metal_yellow", x, 0, 6.3, 0.7, 0.8, 0.5)
    k.box("metal_gray", -6.0, -1.2, 6.8, 6.0, 1.2, 7.0, collide=False)


@prop("hose_rack", "fire", mount="wall", collide="none")
def hose_rack(k):
    k.box("metal_red", -2.0, -0.6, 3.0, 2.0, 0.0, 3.2)
    for i in range(3):
        k.hcyl("fabric_cream", -1.2 + i * 1.2, -0.6, 2.4, 0.55, 0.9, axis="y", sides=10)


@prop("fire_pole", "fire", collide="none")
def fire_pole(k):
    k.cyl("metal_chrome", 0, 0, 0, 0.18, 24.0, 8)
    k.cyl("rubber", 0, 0, 0, 1.6, 0.4, 12)


@prop("scba_rack", "fire", detail=2)
def scba_rack(k):
    shelf_unit(k, "metal_gray", 6.0, 1.6, 5.0, 2, back=True)
    for i in range(4):
        k.cyl("metal_yellow", -2.2 + i * 1.45, 0, 0.3, 0.45, 2.0, 8, collide=False)
        k.cyl("metal_yellow", -2.2 + i * 1.45, 0, 2.6, 0.45, 2.0, 8, collide=False)


# --- Motel ----------------------------------------------------------------------

@prop("luggage_rack", "motel", detail=2)
def luggage_rack(k):
    table(k, "$wood", "metal_brass", 3.0, 1.8, 1.8, 0.15, 0.12)
    k.box("fabric_brown", -1.2, -0.7, 1.8, 1.2, 0.7, 3.0, collide=False)


@prop("key_board", "motel", mount="wall", collide="none", detail=2)
def key_board(k):
    k.box("wood_dark", -2.5, 0.0, 0, 2.5, 0.15, 2.4)
    for r in range(3):
        for c in range(8):
            k.box("metal_brass", -2.2 + c * 0.6, -0.1, 0.3 + r * 0.7, -2.1 + c * 0.6, 0.0,
                  0.7 + r * 0.7)


@prop("ice_vending_alcove", "motel")
def ice_vending_alcove(k):
    k.box("metal_white", -2.8, -1.4, 0, -0.2, 1.4, 5.4)
    k.box("metal_dark", -2.4, -1.42, 3.6, -0.6, -1.4, 4.6, collide=False)
    k.box("sign_blue", -2.6, -1.43, 4.8, -0.4, -1.41, 5.2, collide=False)
    vend = ((0.2, 2.8),)
    for x0, x1 in vend:
        k.box("plastic_red", x0, -1.3, 0, x1, 1.3, 6.4)
        k.box("glass_store", x0 + 0.2, -1.32, 1.6, x1 - 0.8, -1.3, 6.0, collide=False)
