"""Residential furniture, lighting fixtures and household clutter."""

from __future__ import annotations

from . import prop, WARM, NEUTRAL, COOL
from .shapes import legs4, table, cabinet, shelf_unit, cone
from ..geom import rot_z

import math


# --- Seating -----------------------------------------------------------------

def _sofa(k, w, mat="$fabric", legs="wood_dark"):
    d, h = 3.2, 3.0
    k.box(mat, -w / 2, -d / 2, 0.45, w / 2, d / 2, 1.5)                    # base
    k.box(mat, -w / 2, d / 2 - 0.9, 1.5, w / 2, d / 2, h, collide=False)    # back
    k.box(mat, -w / 2, -d / 2, 1.5, -w / 2 + 0.6, d / 2, 2.2, collide=False)
    k.box(mat, w / 2 - 0.6, -d / 2, 1.5, w / 2, d / 2, 2.2, collide=False)
    n = max(1, int((w - 1.2) / 2.2))
    cw = (w - 1.2) / n
    for i in range(n):
        x0 = -w / 2 + 0.6 + i * cw
        k.box(mat, x0 + 0.04, -d / 2 + 0.05, 1.5, x0 + cw - 0.04, d / 2 - 0.9, 1.85, collide=False)
    legs4(k, legs, w, d, 0.45, 0.2, 0.2)


@prop("sofa_3", "furniture")
def sofa_3(k):
    _sofa(k, 7.6)


@prop("sofa_2", "furniture")
def sofa_2(k):
    _sofa(k, 5.4)


@prop("sofa_leather", "furniture")
def sofa_leather(k):
    _sofa(k, 7.2, "leather_brown")


@prop("armchair", "furniture")
def armchair(k):
    _sofa(k, 3.3)


@prop("recliner", "furniture")
def recliner(k):
    k.box("$fabric", -1.7, -1.8, 0.3, 1.7, 1.6, 1.6)
    k.box("$fabric", -1.7, 0.8, 1.6, 1.7, 1.6, 3.4, collide=False)
    k.box("$fabric", -1.7, -1.8, 1.6, -1.1, 0.8, 2.3, collide=False)
    k.box("$fabric", 1.1, -1.8, 1.6, 1.7, 0.8, 2.3, collide=False)
    k.box("$fabric", -1.0, -2.6, 0.7, 1.0, -1.8, 1.3, collide=False)


@prop("dining_chair", "furniture", collide="none")
def dining_chair(k):
    k.box("$wood", -0.8, -0.8, 1.45, 0.8, 0.8, 1.65)
    legs4(k, "$wood", 1.6, 1.6, 1.45, 0.18, 0.05)
    k.box("$wood", -0.8, 0.62, 1.65, 0.8, 0.8, 3.6, collide=False)


@prop("kitchen_chair_vinyl", "furniture", collide="none")
def kitchen_chair_vinyl(k):
    k.box("vinyl_red", -0.8, -0.8, 1.4, 0.8, 0.8, 1.7)
    legs4(k, "metal_chrome", 1.6, 1.6, 1.4, 0.12, 0.08)
    k.box("vinyl_red", -0.75, 0.6, 1.9, 0.75, 0.8, 3.3, collide=False)
    k.box("metal_chrome", -0.7, 0.66, 1.7, -0.6, 0.76, 1.9, collide=False)
    k.box("metal_chrome", 0.6, 0.66, 1.7, 0.7, 0.76, 1.9, collide=False)


@prop("stool", "furniture", collide="none")
def stool(k):
    k.cyl("$fabric", 0, 0, 2.3, 0.75, 0.3, 10)
    k.cyl("metal_chrome", 0, 0, 0, 0.15, 2.3, 6)
    k.cyl("metal_chrome", 0, 0, 0, 0.6, 0.12, 8)
    k.cyl("metal_chrome", 0, 0, 0.9, 0.55, 0.08, 8)


@prop("bar_stool", "furniture", collide="none")
def bar_stool(k):
    k.cyl("vinyl_red", 0, 0, 2.9, 0.8, 0.35, 10)
    k.cyl("metal_chrome", 0, 0, 0, 0.15, 2.9, 6)
    k.cyl("metal_chrome", 0, 0, 0, 0.7, 0.12, 8)
    k.cyl("metal_chrome", 0, 0, 1.0, 0.6, 0.08, 8)


@prop("bench_wood", "furniture")
def bench_wood(k):
    k.box("$wood", -3, -0.75, 1.3, 3, 0.75, 1.55)
    legs4(k, "$wood", 6, 1.5, 1.3, 0.25, 0.3)


@prop("beanbag", "furniture", collide="none")
def beanbag(k):
    k.ball("$fabric", 0, 0, 0.9, 1.4, 1.4, 0.9)


@prop("office_chair", "office", collide="none")
def office_chair(k):
    k.box("$fabric", -0.9, -0.9, 1.5, 0.9, 0.9, 1.85)
    k.box("$fabric", -0.85, 0.65, 2.0, 0.85, 0.9, 3.8, collide=False)
    k.cyl("metal_dark", 0, 0, 0.3, 0.12, 1.2, 6)
    for dx, dy in ((0.9, 0), (-0.9, 0), (0, 0.9), (0, -0.9)):
        k.box("plastic_black", min(0, dx) - 0.1, min(0, dy) - 0.1, 0.15, max(0, dx) + 0.1,
              max(0, dy) + 0.1, 0.3, collide=False)


# --- Tables ---------------------------------------------------------------

@prop("coffee_table", "furniture")
def coffee_table(k):
    table(k, "$wood", "$wood", 4.4, 2.4, 1.5, 0.2, 0.2)
    k.box("$wood", -2.0, -1.0, 0.4, 2.0, 1.0, 0.5, collide=False)


@prop("side_table", "furniture")
def side_table(k):
    table(k, "$wood", "$wood", 1.8, 1.8, 2.0, 0.15, 0.15)


@prop("dining_table", "furniture")
def dining_table(k):
    table(k, "$wood", "$wood", 5.6, 3.6, 2.6)


@prop("dining_table_big", "furniture")
def dining_table_big(k):
    table(k, "$wood", "$wood", 8.0, 3.8, 2.6)


@prop("kitchen_table_formica", "furniture")
def kitchen_table_formica(k):
    k.box("plastic_beige", -2.4, -1.6, 2.4, 2.4, 1.6, 2.6)
    k.box("metal_chrome", -2.45, -1.65, 2.35, 2.45, 1.65, 2.42, collide=False)
    legs4(k, "metal_chrome", 4.8, 3.2, 2.35, 0.14, 0.2)


@prop("desk_home", "furniture")
def desk_home(k):
    k.box("$wood", -2.3, -1.1, 2.4, 2.3, 1.1, 2.6)
    k.box("$wood", 0.9, -1.0, 0, 2.2, 1.0, 2.4)
    k.box("$wood", -2.2, -1.0, 0, -2.0, 1.0, 2.4, collide=False)
    k.box("metal_chrome", 1.4, -1.1, 1.6, 1.7, -1.0, 1.7, collide=False)


@prop("vanity_dresser", "furniture")
def vanity_dresser(k):
    cabinet(k, "$paint", "$paint", 4.0, 1.7, 2.6, doors=2, drawers=2)
    k.box("$paint", -1.6, 0.6, 2.6, 1.6, 0.8, 5.6, collide=False)
    k.box("metal_chrome", -1.4, 0.55, 2.9, 1.4, 0.6, 5.4, collide=False)


# --- Beds & bedroom ---------------------------------------------------------

def _bed(k, w, l, frame="$wood", sheet="$sheet", head=3.8):
    k.box(frame, -w / 2, -l / 2, 0.4, w / 2, l / 2, 1.2)
    k.box("mattress", -w / 2 + 0.1, -l / 2 + 0.1, 1.2, w / 2 - 0.1, l / 2 - 0.2, 2.0)
    k.box(sheet, -w / 2 + 0.05, -l / 2 + 0.05, 1.5, w / 2 - 0.05, l / 2 - 1.7, 2.12,
          collide=False)
    n = 2 if w > 4 else 1
    pw = (w - 0.6) / n
    for i in range(n):
        x0 = -w / 2 + 0.3 + i * pw
        k.box("sheet_white", x0 + 0.1, l / 2 - 1.6, 2.0, x0 + pw - 0.1, l / 2 - 0.4, 2.45,
              collide=False)
    k.box(frame, -w / 2, l / 2 - 0.25, 0, w / 2, l / 2, head)
    legs4(k, frame, w, l, 0.4, 0.3, 0.05)


@prop("bed_double", "furniture")
def bed_double(k):
    _bed(k, 5.4, 7.2)


@prop("bed_queen_nice", "furniture")
def bed_queen_nice(k):
    _bed(k, 6.0, 7.4, "fabric_gray", "$sheet", 4.6)


@prop("bed_single", "furniture")
def bed_single(k):
    _bed(k, 3.6, 7.0)


@prop("bed_metal_cheap", "furniture")
def bed_metal_cheap(k):
    _bed(k, 4.8, 7.0, "metal_dark", "$sheet", 3.2)


@prop("mattress_floor", "furniture")
def mattress_floor(k):
    k.box("mattress", -2.4, -3.4, 0, 2.4, 3.4, 0.7)
    k.box("$sheet", -2.4, -3.5, 0.2, 1.8, 1.4, 0.8, collide=False)
    k.box("sheet_white", -1.8, 2.0, 0.7, 0.6, 3.2, 1.0, collide=False)


@prop("bunk_bed", "furniture")
def bunk_bed(k):
    for z in (0.5, 4.2):
        k.box("mattress", -1.7, -3.4, z + 0.5, 1.7, 3.4, z + 1.2)
        k.box("$sheet", -1.75, -3.45, z + 0.9, 1.75, 1.8, z + 1.3, collide=False)
        k.box("metal_dark", -1.8, -3.5, z + 0.3, 1.8, 3.5, z + 0.5, collide=False)
    for sx in (-1.7, 1.7):
        for sy in (-3.4, 3.4):
            k.box("metal_dark", sx - 0.1, sy - 0.1, 0, sx + 0.1, sy + 0.1, 7.2, collide=False)
    for z in (1.5, 2.7, 3.9):
        k.box("metal_dark", 1.6, -3.0, z, 1.8, -2.2, z + 0.12, collide=False)


@prop("nightstand", "furniture")
def nightstand(k):
    cabinet(k, "$wood", "$wood", 1.8, 1.6, 2.0, doors=1, drawers=2)


@prop("dresser", "furniture")
def dresser(k):
    cabinet(k, "$wood", "$wood", 4.6, 1.8, 3.2, doors=2, drawers=3)


@prop("wardrobe", "furniture")
def wardrobe(k):
    cabinet(k, "$wood", "$wood", 4.4, 2.0, 7.2, doors=2)


@prop("crib", "furniture")
def crib(k):
    k.box("wood_white", -1.6, -2.6, 1.0, 1.6, 2.6, 1.3)
    k.box("mattress", -1.5, -2.5, 1.3, 1.5, 2.5, 1.7, collide=False)
    for x in (-1.6, 1.6):
        k.box("wood_white", x - 0.1, -2.6, 0, x + 0.1, 2.6, 3.4, collide=False)
    for y in (-2.6, 2.6):
        k.box("wood_white", -1.6, y - 0.1, 0, 1.6, y + 0.1, 3.4, collide=False)


@prop("toy_box", "furniture")
def toy_box(k):
    k.box("$paint", -1.5, -1.0, 0, 1.5, 1.0, 1.8)
    k.ball("plastic_red", -0.6, -0.2, 2.0, 0.4)
    k.box("plastic_yellow", 0.1, -0.5, 1.8, 0.7, 0.1, 2.3, collide=False)


@prop("toys_floor", "furniture", collide="none", detail=3)
def toys_floor(k):
    k.box("plastic_red", -1.0, -0.6, 0, -0.4, 0, 0.5)
    k.box("plastic_blue", -0.2, -0.2, 0, 0.4, 0.4, 0.4)
    k.box("plastic_yellow", 0.3, -0.8, 0, 1.0, -0.3, 0.3)
    k.ball("plastic_green", 0.8, 0.6, 0.4, 0.4)


@prop("laundry_basket", "furniture", collide="none", detail=3)
def laundry_basket(k):
    k.box("plastic_white", -0.9, -0.7, 0, 0.9, 0.7, 1.4)
    k.box("$fabric", -0.8, -0.6, 1.0, 0.8, 0.6, 1.6, collide=False)


@prop("shoes_mat", "furniture", collide="none", detail=3)
def shoes_mat(k):
    k.box("fabric_brown", -1.5, -0.8, 0, 1.5, 0.8, 0.05)
    for i, m in enumerate(("leather_black", "fabric_white", "leather_brown")):
        x = -1.1 + i * 0.9
        k.box(m, x, -0.5, 0.05, x + 0.4, 0.4, 0.4)


@prop("coat_rack", "furniture", collide="none", detail=2)
def coat_rack(k):
    k.cyl("wood_dark", 0, 0, 0, 0.7, 0.15, 8)
    k.cyl("wood_dark", 0, 0, 0, 0.12, 6.0, 6)
    k.box("$fabric", -0.5, -0.4, 3.6, 0.4, 0.3, 5.6, collide=False)


# --- Storage / living ---------------------------------------------------------

@prop("bookshelf", "furniture")
def bookshelf(k):
    shelf_unit(k, "$wood", 4.2, 1.3, 7.2, 5,
               goods=["book_red", "book_blue", "book_green", "book_tan", "paper"], rng_seed=3)


@prop("shelf_low", "furniture")
def shelf_low(k):
    shelf_unit(k, "$wood", 4.2, 1.3, 3.0, 2, goods=["book_red", "book_tan", "book_blue"],
               rng_seed=7)


@prop("tv_stand", "furniture")
def tv_stand(k):
    cabinet(k, "$wood", "$wood", 5.2, 1.7, 2.0, doors=3)


@prop("tv_flat", "electronics", mount="surface", collide="none")
def tv_flat(k):
    k.box("plastic_black", -2.3, -0.12, 0.6, 2.3, 0.12, 3.3)
    k.box("screen", -2.2, -0.14, 0.7, 2.2, -0.1, 3.2)
    k.box("plastic_black", -0.6, -0.4, 0, 0.6, 0.4, 0.1)
    k.box("plastic_black", -0.1, -0.05, 0.1, 0.1, 0.1, 0.6)


@prop("tv_wall", "electronics", mount="wall", collide="none")
def tv_wall(k):
    k.box("plastic_black", -2.8, -0.2, 0, 2.8, 0.2, 3.3)
    k.box("screen", -2.7, -0.22, 0.1, 2.7, -0.18, 3.2)


@prop("tv_crt", "electronics", mount="surface")
def tv_crt(k):
    k.box("plastic_gray", -1.3, -1.0, 0, 1.3, 1.1, 2.1)
    k.box("screen", -1.0, -1.04, 0.35, 0.8, -0.98, 1.8)
    k.box("plastic_black", 0.9, -1.04, 0.4, 1.15, -0.98, 1.6)
    k.box("plastic_black", -0.1, 0.0, 2.1, 0.1, 0.2, 2.9, collide=False)


@prop("game_console", "electronics", mount="surface", collide="none", detail=3)
def game_console(k):
    k.box("plastic_black", -0.6, -0.5, 0, 0.6, 0.5, 0.3)
    k.box("plastic_gray", 0.8, -0.6, 0, 1.2, -0.3, 0.1)


@prop("radio", "electronics", mount="surface", collide="none", detail=3)
def radio(k):
    k.box("wood_dark", -0.8, -0.35, 0, 0.8, 0.35, 0.9)
    k.box("fabric_brown", -0.7, -0.37, 0.15, 0.1, -0.33, 0.75)
    k.cyl("metal_brass", 0.45, -0.38, 0.35, 0.15, 0.1, 6)


@prop("fireplace", "furniture")
def fireplace(k):
    k.box("brick_red", -3.0, -0.6, 0, 3.0, 1.0, 5.0)
    k.box("rock_dark", -1.6, -0.62, 0.3, 1.6, 0.6, 2.8, collide=False)
    k.box("wood_dark", -3.3, -0.9, 5.0, 3.3, 1.0, 5.35)
    k.box("brick_red", -1.6, 0.0, 5.35, 1.6, 1.0, 12.0, collide=False)


@prop("piano_upright", "furniture")
def piano_upright(k):
    k.box("wood_dark", -2.6, -0.3, 0, 2.6, 1.1, 4.3)
    k.box("wood_dark", -2.6, -1.1, 2.0, 2.6, -0.3, 2.5)
    k.box("plastic_white", -2.4, -1.1, 2.5, 2.4, -0.4, 2.6, collide=False)


@prop("rug_rect", "decor", collide="none")
def rug_rect(k):
    k.box("$fabric2", -4.0, -2.8, 0, 4.0, 2.8, 0.06)
    k.box("$fabric", -3.4, -2.2, 0.02, 3.4, 2.2, 0.08)


@prop("rug_runner", "decor", collide="none")
def rug_runner(k):
    k.box("$fabric", -1.4, -5.0, 0, 1.4, 5.0, 0.06)


@prop("rug_round", "decor", collide="none")
def rug_round(k):
    k.cyl("$fabric", 0, 0, 0, 3.0, 0.06, 16)


@prop("plant_pot", "decor", collide="none")
def plant_pot(k):
    k.cyl("stucco_terracotta", 0, 0, 0, 0.7, 1.2, 8)
    k.ball("leaf", 0, 0, 2.3, 1.0, 1.0, 1.3)
    k.ball("leaf_dark", 0.3, 0.2, 3.1, 0.6)


@prop("plant_tall", "decor", collide="none")
def plant_tall(k):
    k.cyl("plastic_white", 0, 0, 0, 0.8, 1.6, 8)
    k.cyl("bark", 0, 0, 1.6, 0.1, 2.5, 5)
    k.ball("leaf_dark", 0, 0, 4.4, 1.3, 1.3, 1.6)


@prop("plant_small", "decor", mount="surface", collide="none", detail=3)
def plant_small(k):
    k.cyl("stucco_terracotta", 0, 0, 0, 0.35, 0.5, 6)
    k.ball("leaf", 0, 0, 0.8, 0.45)


# --- Lighting fixtures ------------------------------------------------------

@prop("floor_lamp", "lighting", collide="none",
      light={"at": (0, 0, 5.6), "color": WARM, "range": 14, "brightness": 0.9})
def floor_lamp(k):
    k.cyl("metal_dark", 0, 0, 0, 0.6, 0.15, 8)
    k.cyl("metal_dark", 0, 0, 0.15, 0.08, 5.0, 6)
    cone(k, "fabric_cream", 0, 0, 5.0, 0.9, 0.55, 1.2, 8)


@prop("table_lamp", "lighting", mount="surface", collide="none",
      light={"at": (0, 0, 1.6), "color": WARM, "range": 10, "brightness": 0.7})
def table_lamp(k):
    k.cyl("ceramic", 0, 0, 0, 0.35, 1.0, 8)
    cone(k, "fabric_cream", 0, 0, 1.0, 0.7, 0.45, 0.9, 8)


@prop("desk_lamp", "lighting", mount="surface", collide="none",
      light={"at": (0, -0.4, 1.4), "color": NEUTRAL, "range": 8, "brightness": 0.6})
def desk_lamp(k):
    k.cyl("metal_dark", 0, 0, 0, 0.35, 0.1, 8)
    k.box("metal_dark", -0.05, -0.05, 0.1, 0.05, 0.05, 1.5)
    k.box("metal_green", -0.3, -0.7, 1.3, 0.3, 0.1, 1.6)


@prop("ceiling_light", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -0.8), "color": WARM, "range": 22, "brightness": 1.0})
def ceiling_light(k):
    k.cyl("lamp_warm", 0, 0, -0.5, 0.9, 0.5, 10)
    k.cyl("metal_white", 0, 0, -0.1, 0.4, 0.1, 8)


@prop("ceiling_fan_light", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -1.6), "color": WARM, "range": 22, "brightness": 1.0})
def ceiling_fan_light(k):
    k.cyl("metal_brass", 0, 0, -1.2, 0.12, 1.2, 6)
    k.cyl("wood_dark", 0, 0, -1.4, 0.5, 0.3, 8)
    for i in range(4):
        a = i * math.pi / 2
        k.obox("wood", 1.5 * math.cos(a), 1.5 * math.sin(a), -1.3, 2.2, 0.5, 0.06, rot_z(a),
               collide=False)
    k.ball("lamp_warm", 0, 0, -1.7, 0.4)


@prop("pendant_light", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -3.2), "color": WARM, "range": 14, "brightness": 0.8})
def pendant_light(k):
    k.cyl("metal_dark", 0, 0, -3.0, 0.05, 3.0, 4)
    cone(k, "metal_dark", 0, 0, -3.4, 0.9, 0.2, 0.6, 8)
    k.ball("lamp_warm", 0, 0, -3.3, 0.25)


@prop("bare_bulb", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -1.2), "color": (1.0, 0.78, 0.52), "range": 16, "brightness": 0.8})
def bare_bulb(k):
    k.cyl("plastic_black", 0, 0, -0.9, 0.04, 0.9, 4)
    k.ball("lamp_amber", 0, 0, -1.1, 0.25)


@prop("fluor_panel", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -0.6), "color": COOL, "range": 22, "brightness": 1.0})
def fluor_panel(k):
    k.box("metal_white", -1.2, -2.4, -0.25, 1.2, 2.4, 0)
    k.box("lamp_cool", -1.0, -2.2, -0.3, 1.0, 2.2, -0.25)


@prop("fluor_strip", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -1.6), "color": COOL, "range": 30, "brightness": 1.1})
def fluor_strip(k):
    k.box("metal_white", -0.5, -3.5, -1.4, 0.5, 3.5, -1.1)
    k.box("lamp_cool", -0.35, -3.4, -1.5, 0.35, 3.4, -1.4)
    k.box("metal_dark", -0.03, -3.0, -1.1, 0.03, -2.9, 0)
    k.box("metal_dark", -0.03, 2.9, -1.1, 0.03, 3.0, 0)


@prop("highbay_light", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -3.0), "color": (0.95, 0.95, 0.9), "range": 46, "brightness": 1.3})
def highbay_light(k):
    k.cyl("metal_dark", 0, 0, -2.0, 0.06, 2.0, 4)
    cone(k, "metal_gray", 0, 0, -2.9, 1.3, 0.5, 0.9, 10)
    k.cyl("lamp_cool", 0, 0, -3.0, 1.1, 0.1, 10)


@prop("chandelier", "lighting", mount="ceiling", collide="none",
      light={"at": (0, 0, -2.6), "color": WARM, "range": 26, "brightness": 1.2})
def chandelier(k):
    k.cyl("metal_brass", 0, 0, -2.0, 0.06, 2.0, 4)
    k.cyl("metal_brass", 0, 0, -2.6, 1.6, 0.15, 10)
    for i in range(6):
        a = i * math.pi / 3
        k.ball("lamp_warm", 1.5 * math.cos(a), 1.5 * math.sin(a), -2.3, 0.25)


@prop("wall_sconce", "lighting", mount="wall", collide="none",
      light={"at": (0, -0.6, 0.4), "color": WARM, "range": 14, "brightness": 0.8})
def wall_sconce(k):
    k.box("metal_brass", -0.3, 0.1, 0, 0.3, 0.2, 0.8)
    k.cyl("lamp_warm", 0, -0.35, 0.1, 0.35, 0.7, 8)


@prop("exit_sign", "lighting", mount="wall", collide="none", detail=2)
def exit_sign(k):
    k.box("plastic_white", -0.9, 0.0, 0, 0.9, 0.2, 0.7)
    k.box("neon_red", -0.7, -0.02, 0.15, 0.7, 0.0, 0.55)


# --- Wall decor -----------------------------------------------------------

@prop("picture_small", "decor", mount="wall", collide="none", detail=2)
def picture_small(k):
    k.box("wood_dark", -0.9, 0.0, 0, 0.9, 0.12, 1.3)
    k.box("$fabric", -0.75, -0.02, 0.15, 0.75, 0.0, 1.15)


@prop("picture_large", "decor", mount="wall", collide="none", detail=2)
def picture_large(k):
    k.box("$wood", -2.0, 0.0, 0, 2.0, 0.12, 2.6)
    k.box("$fabric", -1.8, -0.02, 0.2, 1.8, 0.0, 2.4)
    k.box("$fabric2", -0.9, -0.03, 0.6, 1.1, -0.01, 1.7)


@prop("photo_frames", "decor", mount="wall", collide="none", detail=3)
def photo_frames(k):
    for i, (x, z) in enumerate(((-1.1, 0.0), (0.0, 0.5), (1.0, 0.1), (-0.4, 1.3))):
        k.box("wood_dark", x - 0.4, 0.0, z, x + 0.4, 0.08, z + 0.55)
        k.box(("paper", "fabric_blue", "fabric_cream", "fabric_green")[i], x - 0.32, -0.02,
              z + 0.07, x + 0.32, 0.0, z + 0.48)


@prop("mirror_wall", "decor", mount="wall", collide="none", detail=2)
def mirror_wall(k):
    k.box("wood_dark", -1.2, 0.0, 0, 1.2, 0.1, 3.0)
    k.box("metal_chrome", -1.05, -0.02, 0.15, 1.05, 0.0, 2.85)


@prop("clock_wall", "decor", mount="wall", collide="none", detail=3)
def clock_wall(k):
    k.hcyl("plastic_white", 0, 0.05, 0.6, 0.6, 0.1, axis="y", sides=12)
    k.box("plastic_black", -0.03, -0.02, 0.6, 0.03, 0.0, 1.0)
    k.box("plastic_black", -0.03, -0.02, 0.57, 0.35, 0.0, 0.63)


@prop("curtains", "decor", mount="wall", collide="none", detail=2)
def curtains(k):
    # spans a 5-stud window; origin at the window's sill-centre on the wall plane
    k.box("metal_dark", -3.2, -0.35, 5.4, 3.2, -0.25, 5.5)
    k.box("$fabric", -3.1, -0.3, -0.4, -2.0, -0.15, 5.4)
    k.box("$fabric", 2.0, -0.3, -0.4, 3.1, -0.15, 5.4)


@prop("blinds", "decor", mount="wall", collide="none", detail=2)
def blinds(k):
    k.box("plastic_white", -2.6, -0.3, 2.4, 2.6, -0.1, 5.4)
    k.box("plastic_gray", -2.6, -0.32, 5.2, 2.6, -0.1, 5.5)


@prop("blinds_closed", "decor", mount="wall", collide="none", detail=2)
def blinds_closed(k):
    k.box("plastic_beige", -2.6, -0.3, -0.2, 2.6, -0.1, 5.4)


@prop("newspaper_cover", "decor", mount="wall", collide="none", detail=2)
def newspaper_cover(k):
    # taped-over window (abandoned / safehouse look)
    k.box("paper", -2.5, -0.2, 0.1, 2.5, -0.15, 5.0)
    k.box("cardboard", -1.5, -0.25, 1.4, 1.0, -0.2, 3.6)


@prop("shelf_wall", "decor", mount="wall", collide="none", detail=2)
def shelf_wall(k):
    k.box("$wood", -2.0, -0.2, 0, 2.0, 0.6, 0.15)
    k.box("book_red", -1.8, -0.1, 0.15, -1.3, 0.5, 1.0)
    k.box("book_blue", -1.25, -0.1, 0.15, -0.9, 0.5, 0.9)
    k.cyl("ceramic", 0.6, 0.2, 0.15, 0.3, 0.6, 6)
    k.box("plastic_green", 1.2, 0.0, 0.15, 1.7, 0.5, 0.5)


@prop("bulletin_board", "decor", mount="wall", collide="none", detail=2)
def bulletin_board(k):
    k.box("wood", -2.2, 0.0, 0, 2.2, 0.12, 2.8)
    k.box("corkboard", -2.0, -0.02, 0.2, 2.0, 0.0, 2.6)
    for i, (x, z) in enumerate(((-1.5, 1.6), (-0.4, 1.9), (0.7, 1.3), (-1.0, 0.6), (1.2, 0.5))):
        k.box("paper" if i % 2 == 0 else "sign_yellow", x, -0.04, z, x + 0.7, -0.02, z + 0.8)


@prop("whiteboard_wall", "office", mount="wall", collide="none")
def whiteboard_wall(k):
    k.box("frame_alu", -3.5, 0.0, 0, 3.5, 0.12, 3.4)
    k.box("whiteboard", -3.4, -0.02, 0.1, 3.4, 0.0, 3.3)
    k.box("frame_alu", -3.4, -0.4, 0.0, 3.4, 0.0, 0.1)


@prop("dartboard", "bar", mount="wall", collide="none", detail=2)
def dartboard(k):
    k.box("wood_dark", -1.3, 0.0, 0, 1.3, 0.1, 2.6)
    k.hcyl("felt_green", 0, -0.05, 1.3, 0.9, 0.12, axis="y", sides=12)
    k.hcyl("fabric_red", 0, -0.08, 1.3, 0.25, 0.12, axis="y", sides=8)


@prop("flag_wall", "civic", mount="wall", collide="none", detail=2)
def flag_wall(k):
    k.box("fabric_blue", -2.4, -0.05, 0, -0.6, 0.0, 1.4)
    for i in range(7):
        m = "fabric_red" if i % 2 == 0 else "fabric_white"
        k.box(m, -2.4 if i >= 3 else -0.6, -0.05, i * 0.2, 2.4, 0.0, i * 0.2 + 0.2)


@prop("fire_extinguisher", "safety", mount="wall", collide="none", detail=2)
def fire_extinguisher(k):
    k.cyl("metal_red", 0, -0.2, 1.0, 0.3, 1.6, 8)
    k.box("plastic_black", -0.1, -0.3, 2.6, 0.1, -0.1, 2.9)


@prop("electrical_panel", "utility", mount="wall", collide="none")
def electrical_panel(k):
    k.box("metal_gray", -1.0, -0.4, 3.0, 1.0, 0.0, 6.0)
    k.box("metal_dark", -0.15, -0.45, 3.2, 0.15, -0.4, 5.8)
    k.box("metal_gray", -0.2, -0.3, 6.0, 0.2, 0.0, 9.5)


@prop("pipes_wall", "utility", mount="wall", collide="none", detail=2)
def pipes_wall(k):
    k.hcyl("metal_rust", 0, -0.4, 8.5, 0.25, 8.0, axis="x", sides=6)
    k.hcyl("metal", 0, -0.9, 8.9, 0.18, 8.0, axis="x", sides=6)
    k.cyl("metal", 3.5, -0.9, 0, 0.18, 8.9, 6)


@prop("thermostat", "utility", mount="wall", collide="none", detail=3)
def thermostat(k):
    k.box("plastic_beige", -0.25, -0.08, 4.8, 0.25, 0.0, 5.3)


@prop("light_switch", "utility", mount="wall", collide="none", detail=3)
def light_switch(k):
    k.box("plastic_white", -0.15, -0.05, 4.0, 0.15, 0.0, 4.5)


@prop("calendar_wall", "decor", mount="wall", collide="none", detail=3)
def calendar_wall(k):
    k.box("paper", -0.6, -0.04, 4.0, 0.6, 0.0, 5.6)
    k.box("sign_red", -0.6, -0.05, 4.9, 0.6, -0.04, 5.6)


# --- Clutter -----------------------------------------------------------------

@prop("boxes_stack", "clutter")
def boxes_stack(k):
    k.box("cardboard", -1.5, -1.2, 0, 0.5, 0.8, 1.6)
    k.box("cardboard", 0.6, -1.0, 0, 1.6, 1.0, 1.2)
    k.box("cardboard", -1.2, -1.0, 1.6, 0.2, 0.5, 2.6)


@prop("boxes_moving", "clutter")
def boxes_moving(k):
    k.box("cardboard", -2.0, -1.4, 0, 0.0, 0.4, 1.8)
    k.box("cardboard", 0.1, -1.0, 0, 1.9, 1.2, 1.6)
    k.box("cardboard", -1.6, -1.0, 1.8, -0.2, 0.3, 3.0)
    k.box("cardboard", 0.4, -0.6, 1.6, 1.6, 0.8, 2.6)
    k.box("paper", 0.6, -1.02, 0.4, 1.4, -1.0, 0.9, collide=False)


@prop("trash_can_small", "clutter", collide="none")
def trash_can_small(k):
    k.cyl("plastic_gray", 0, 0, 0, 0.6, 1.6, 8)


@prop("trash_bags", "clutter", collide="none", detail=2)
def trash_bags(k):
    k.ball("plastic_black", -0.5, 0, 0.8, 0.9, 0.9, 0.8)
    k.ball("plastic_black", 0.6, 0.3, 0.7, 0.8, 0.8, 0.7)


@prop("clutter_pile", "clutter", detail=2)
def clutter_pile(k):
    k.box("cardboard", -1.5, -1.0, 0, -0.1, 0.4, 1.2)
    k.box("paper", -0.2, -0.6, 0, 1.0, 0.5, 0.3)
    k.ball("plastic_black", 0.8, 0.6, 0.6, 0.7, 0.7, 0.6)
    k.box("fabric_plaid", -1.2, 0.4, 0, 0.6, 1.2, 0.5)


@prop("suitcase", "clutter", collide="none", detail=2)
def suitcase(k):
    k.box("$fabric", -1.0, -0.4, 0, 1.0, 0.4, 2.6)
    k.box("metal_dark", -0.4, -0.1, 2.6, 0.4, 0.1, 2.9)


@prop("duffel_bag", "clutter", collide="none", detail=2)
def duffel_bag(k):
    k.hcyl("$fabric", 0, 0, 0.6, 0.6, 2.4, axis="x", sides=8)


@prop("vacuum", "clutter", collide="none", detail=3)
def vacuum(k):
    k.box("plastic_red", -0.5, -0.6, 0, 0.5, 0.6, 0.5)
    k.box("plastic_gray", -0.1, 0.2, 0.5, 0.1, 0.4, 3.6)


@prop("ironing_board", "clutter", collide="none", detail=3)
def ironing_board(k):
    k.box("fabric_blue", -2.0, -0.6, 2.8, 2.0, 0.6, 2.95)
    k.box("metal_gray", -1.0, -0.05, 0, 1.0, 0.05, 2.8)


@prop("bicycle", "vehicle_small", collide="none")
def bicycle(k):
    k.hcyl("rubber", 0, -1.6, 1.1, 1.1, 0.15, axis="y", sides=12)
    k.hcyl("rubber", 0, 1.6, 1.1, 1.1, 0.15, axis="y", sides=12)
    k.box("$plastic", -0.08, -1.6, 1.0, 0.08, 1.6, 1.2)
    k.box("$plastic", -0.08, -0.4, 1.1, 0.08, 0.0, 2.6)
    k.box("plastic_black", -0.3, -0.5, 2.6, 0.3, 0.3, 2.8)
    k.box("metal_dark", -0.9, 1.3, 2.8, 0.9, 1.5, 2.9)
    k.box("$plastic", -0.08, 1.2, 1.2, 0.08, 1.5, 2.8)
