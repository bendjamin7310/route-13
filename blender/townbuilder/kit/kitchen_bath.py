"""Kitchens (home + commercial), bathrooms and laundry."""

from __future__ import annotations

from . import prop, WARM, COOL
from .shapes import cabinet, legs4, shelf_unit, cone

# --- Home kitchen modules (all 2.4 deep, 3.0 high to the worktop) -------------

D = 2.4
H = 3.0


def _base(k, w, front="$paint", top="plastic_beige", doors=1, drawers=0):
    cabinet(k, front, front, w, D - 0.1, H - 0.2, doors=doors, drawers=drawers,
            y_front=-D / 2 + 0.05)
    k.box(top, -w / 2, -D / 2, H - 0.2, w / 2, D / 2, H)
    k.box("trim_dark", -w / 2 + 0.05, -D / 2 + 0.2, 0, w / 2 - 0.05, -D / 2 + 0.3, 0.3,
          collide=False)


@prop("counter_base", "kitchen")
def counter_base(k):
    _base(k, 2.0, doors=1)


@prop("counter_base_wide", "kitchen")
def counter_base_wide(k):
    _base(k, 4.0, doors=2)


@prop("counter_drawers", "kitchen")
def counter_drawers(k):
    _base(k, 2.0, doors=1, drawers=3)


@prop("counter_sink", "kitchen")
def counter_sink(k):
    _base(k, 4.0, doors=2)
    k.box("metal_chrome", -1.5, -0.8, H - 0.05, 1.5, 0.6, H + 0.02, collide=False)
    k.box("metal_chrome", -0.1, 0.7, H, 0.1, 0.9, H + 1.2, collide=False)
    k.box("metal_chrome", -0.1, 0.1, H + 1.0, 0.1, 0.9, H + 1.2, collide=False)


@prop("counter_corner", "kitchen")
def counter_corner(k):
    _base(k, 2.4, doors=1)


@prop("stove", "kitchen")
def stove(k):
    k.box("$metal", -1.25, -D / 2, 0, 1.25, D / 2, H)
    k.box("metal_dark", -1.15, -D / 2 - 0.02, 0.4, 1.15, -D / 2, 2.0, collide=False)
    k.box("metal_chrome", -0.9, -D / 2 - 0.15, 2.05, 0.9, -D / 2, 2.15, collide=False)
    for x in (-0.6, 0.6):
        for y in (-0.5, 0.4):
            k.cyl("metal_dark", x, y, H, 0.35, 0.06, 8, collide=False)
    k.box("$metal", -1.25, D / 2 - 0.3, H, 1.25, D / 2, H + 0.9, collide=False)


@prop("stove_old", "kitchen")
def stove_old(k):
    k.box("metal_beige", -1.25, -D / 2, 0, 1.25, D / 2, H)
    k.box("metal_dark", -1.0, -D / 2 - 0.02, 0.5, 1.0, -D / 2, 2.0, collide=False)
    for x in (-0.6, 0.6):
        for y in (-0.5, 0.4):
            k.cyl("metal_dark", x, y, H, 0.35, 0.06, 6, collide=False)
    k.box("metal_beige", -1.25, D / 2 - 0.3, H, 1.25, D / 2, H + 1.3, collide=False)


@prop("fridge", "kitchen")
def fridge(k):
    k.box("$metal", -1.5, -1.3, 0, 1.5, 1.3, 6.2)
    k.box("trim_dark", -1.5, -1.32, 4.0, 1.5, -1.3, 4.06, collide=False)
    k.box("metal_chrome", 1.1, -1.45, 4.3, 1.2, -1.32, 5.6, collide=False)
    k.box("metal_chrome", 1.1, -1.45, 2.4, 1.2, -1.32, 3.7, collide=False)


@prop("fridge_old", "kitchen")
def fridge_old(k):
    k.box("metal_beige", -1.4, -1.3, 0, 1.4, 1.3, 5.6)
    k.box("trim_dark", -1.4, -1.32, 4.1, 1.4, -1.3, 4.15, collide=False)
    k.box("metal_chrome", 1.0, -1.45, 3.3, 1.1, -1.32, 3.9, collide=False)
    k.box("paper", -1.0, -1.33, 2.4, -0.3, -1.31, 3.2, collide=False)
    k.box("sign_yellow", -0.1, -1.33, 2.0, 0.5, -1.31, 2.6, collide=False)


@prop("dishwasher", "kitchen")
def dishwasher(k):
    k.box("$metal", -1.0, -D / 2, 0, 1.0, D / 2, H - 0.2)
    k.box("plastic_beige", -1.0, -D / 2, H - 0.2, 1.0, D / 2, H)
    k.box("metal_chrome", -0.7, -D / 2 - 0.1, 2.3, 0.7, -D / 2, 2.4, collide=False)


@prop("upper_cabinet", "kitchen", mount="wall", collide="none")
def upper_cabinet(k):
    cabinet(k, "$paint", "$paint", 4.0, 1.3, 2.6, doors=2, y_front=-0.65)


@prop("range_hood", "kitchen", mount="wall", collide="none")
def range_hood(k):
    k.box("metal_chrome", -1.3, -1.1, 0, 1.3, 0.0, 0.6)
    k.box("metal_chrome", -0.5, -0.6, 0.6, 0.5, 0.0, 2.6)


@prop("microwave", "kitchen", mount="surface", collide="none", detail=2)
def microwave(k):
    k.box("$metal", -0.9, -0.6, 0, 0.9, 0.6, 1.0)
    k.box("screen", -0.75, -0.62, 0.15, 0.3, -0.6, 0.85)


@prop("coffee_maker", "kitchen", mount="surface", collide="none", detail=3)
def coffee_maker(k):
    k.box("plastic_black", -0.4, -0.3, 0, 0.4, 0.4, 1.2)
    k.cyl("glass_tint", 0, -0.1, 0.1, 0.25, 0.5, 6)


@prop("toaster", "kitchen", mount="surface", collide="none", detail=3)
def toaster(k):
    k.box("metal_chrome", -0.5, -0.3, 0, 0.5, 0.3, 0.6)


@prop("dish_rack", "kitchen", mount="surface", collide="none", detail=3)
def dish_rack(k):
    k.box("metal_chrome", -0.8, -0.5, 0, 0.8, 0.5, 0.5)
    for i in range(4):
        k.box("ceramic", -0.6 + i * 0.35, -0.3, 0.1, -0.5 + i * 0.35, 0.3, 0.8)


@prop("fruit_bowl", "kitchen", mount="surface", collide="none", detail=3)
def fruit_bowl(k):
    k.cyl("ceramic", 0, 0, 0, 0.6, 0.25, 8)
    k.ball("food_red", -0.2, 0, 0.35, 0.22)
    k.ball("food_yellow", 0.2, 0.1, 0.35, 0.22)
    k.ball("food_orange", 0, -0.2, 0.4, 0.22)


@prop("kitchen_island", "kitchen")
def kitchen_island(k):
    cabinet(k, "$paint", "$paint", 6.0, 3.0, 2.8, doors=3, y_front=-1.5)
    k.box("marble", -3.3, -1.7, 2.8, 3.3, 1.7, 3.0)


@prop("pantry_shelf", "kitchen")
def pantry_shelf(k):
    shelf_unit(k, "wood_light", 4.0, 1.8, 7.0, 5,
               goods=["food_red", "food_yellow", "goods_mix2", "cardboard", "food_brown"],
               rng_seed=11)


# --- Commercial kitchen ---------------------------------------------------------

@prop("steel_counter", "kitchen_pro")
def steel_counter(k):
    k.box("metal", -2.5, -1.25, 2.85, 2.5, 1.25, 3.0)
    k.box("metal", -2.4, -1.15, 0.6, 2.4, 1.15, 0.7, collide=False)
    legs4(k, "metal", 5, 2.5, 2.85, 0.15, 0.1)
    k.box("metal_chrome", -1.0, -0.8, 3.0, 1.0, 0.5, 3.15, collide=False)


@prop("commercial_range", "kitchen_pro")
def commercial_range(k):
    k.box("metal", -2.5, -1.5, 0, 2.5, 1.5, 3.0)
    k.box("metal_dark", -2.3, -1.52, 0.4, 2.3, -1.5, 2.2, collide=False)
    for x in (-1.6, -0.5, 0.6, 1.7):
        for y in (-0.6, 0.6):
            k.box("metal_dark", x - 0.4, y - 0.4, 3.0, x + 0.4, y + 0.4, 3.12, collide=False)
    k.box("metal", -2.5, 1.2, 3.0, 2.5, 1.5, 4.0, collide=False)


@prop("fryer", "kitchen_pro")
def fryer(k):
    k.box("metal", -1.0, -1.4, 0, 1.0, 1.4, 3.2)
    k.box("metal_dark", -0.8, -1.0, 3.0, 0.8, 0.9, 3.25, collide=False)
    k.box("metal_chrome", -0.6, -1.6, 3.2, 0.6, -0.4, 3.5, collide=False)


@prop("flat_grill", "kitchen_pro")
def flat_grill(k):
    k.box("metal", -2.0, -1.4, 0, 2.0, 1.4, 3.0)
    k.box("metal_dark", -1.9, -1.2, 3.0, 1.9, 1.1, 3.1, collide=False)
    k.box("metal", -2.0, 1.0, 3.0, 2.0, 1.4, 3.7, collide=False)


@prop("hood_commercial", "kitchen_pro", mount="wall", collide="none")
def hood_commercial(k):
    k.box("metal", -5.0, -3.5, 0, 5.0, 0.0, 2.2)
    k.box("metal_dark", -4.8, -3.3, -0.05, 4.8, -0.2, 0.0)


@prop("prep_sink", "kitchen_pro")
def prep_sink(k):
    k.box("metal", -2.5, -1.3, 0, 2.5, 1.3, 3.0)
    k.box("metal_dark", -2.3, -1.0, 2.9, -0.1, 1.0, 3.02, collide=False)
    k.box("metal_dark", 0.1, -1.0, 2.9, 2.3, 1.0, 3.02, collide=False)
    k.box("metal", -2.5, 1.0, 3.0, 2.5, 1.3, 4.0, collide=False)
    k.box("metal_chrome", -0.1, 0.9, 3.0, 0.1, 1.1, 4.4, collide=False)


@prop("dish_machine", "kitchen_pro")
def dish_machine(k):
    k.box("metal", -1.6, -1.6, 0, 1.6, 1.6, 6.0)
    k.box("metal_dark", -1.5, -1.62, 2.2, 1.5, -1.6, 5.0, collide=False)


@prop("wire_shelf", "kitchen_pro")
def wire_shelf(k):
    shelf_unit(k, "metal_chrome", 4.8, 2.0, 6.5, 4, back=False,
               goods=["cardboard", "food_red", "plastic_white", "food_yellow", "goods_mix5"],
               rng_seed=21)


@prop("reach_in_fridge", "kitchen_pro")
def reach_in_fridge(k):
    k.box("metal", -1.6, -1.4, 0, 1.6, 1.4, 7.0)
    k.box("metal_dark", -0.05, -1.45, 0.4, 0.05, -1.4, 6.6, collide=False)
    k.box("metal_chrome", -0.4, -1.55, 3.4, -0.25, -1.4, 4.6, collide=False)
    k.box("metal_chrome", 0.25, -1.55, 3.4, 0.4, -1.4, 4.6, collide=False)


@prop("ice_machine", "kitchen_pro")
def ice_machine(k):
    k.box("metal", -1.5, -1.4, 0, 1.5, 1.4, 4.0)
    k.box("metal_dark", -1.2, -1.42, 2.6, 1.2, -1.4, 3.6, collide=False)
    k.box("plastic_white", -1.4, -1.3, 4.0, 1.4, 1.3, 5.6, collide=False)


@prop("mop_sink", "kitchen_pro")
def mop_sink(k):
    k.box("plastic_white", -1.2, -1.2, 0, 1.2, 1.2, 1.2)
    k.box("plastic_yellow", 1.4, -0.6, 0, 2.4, 0.6, 1.4)
    k.box("wood_light", 1.8, -0.05, 1.4, 1.9, 0.05, 5.0)


@prop("food_crates", "kitchen_pro", detail=2)
def food_crates(k):
    k.box("plastic_green", -1.2, -1.0, 0, 1.2, 1.0, 1.0)
    k.box("plastic_red", -1.1, -0.9, 1.0, 1.1, 0.9, 2.0)
    k.ball("food_red", -0.4, 0, 2.2, 0.3)
    k.ball("food_orange", 0.4, 0.2, 2.2, 0.3)


@prop("sack_stack", "kitchen_pro", detail=2)
def sack_stack(k):
    k.box("fabric_cream", -1.4, -1.0, 0, 1.4, 1.0, 1.0)
    k.box("fabric_cream", -1.2, -0.9, 1.0, 1.2, 0.8, 1.8)


@prop("pie_case", "food", mount="surface", collide="none")
def pie_case(k):
    k.box("glass_store", -1.4, -0.8, 0, 1.4, 0.8, 1.6)
    for x in (-0.7, 0.7):
        k.cyl("food_brown", x, 0, 0.1, 0.5, 0.25, 10)
        k.cyl("food_yellow", x, 0, 0.85, 0.5, 0.25, 10)


@prop("cash_register", "retail", mount="surface", collide="none")
def cash_register(k):
    k.box("plastic_gray", -0.8, -0.7, 0, 0.8, 0.7, 0.5)
    k.box("plastic_black", -0.6, -0.4, 0.5, 0.6, 0.4, 0.8)
    k.box("plastic_black", -0.5, 0.2, 0.8, 0.5, 0.4, 1.5)
    k.box("screen_on", -0.4, 0.18, 0.9, 0.4, 0.2, 1.4)


# --- Bathrooms ------------------------------------------------------------------

@prop("toilet", "bath", collide=[(-0.8, -1.3, 0, 0.8, 1.2, 2.6)])
def toilet(k):
    k.box("ceramic", -0.55, -0.6, 0, 0.55, 0.6, 1.2)
    k.cyl("ceramic", 0, -0.55, 1.0, 0.8, 0.45, 10, ry=1.0)
    k.box("ceramic", -0.85, 0.65, 0.9, 0.85, 1.2, 2.6)
    k.cyl("plastic_white", 0, -0.55, 1.45, 0.82, 0.08, 10, ry=1.02, collide=False)


@prop("sink_pedestal", "bath")
def sink_pedestal(k):
    k.cyl("ceramic", 0, 0.2, 0, 0.35, 2.4, 8)
    k.box("ceramic", -1.0, -0.8, 2.4, 1.0, 0.8, 2.9)
    k.box("metal_chrome", -0.08, 0.5, 2.9, 0.08, 0.7, 3.4, collide=False)


@prop("vanity_sink", "bath")
def vanity_sink(k):
    cabinet(k, "$paint", "$paint", 3.2, 1.8, 2.6, doors=2, y_front=-0.9)
    k.box("marble", -1.7, -1.0, 2.6, 1.7, 0.9, 2.8)
    k.box("ceramic", -0.7, -0.6, 2.75, 0.7, 0.3, 2.85, collide=False)
    k.box("metal_chrome", -0.08, 0.4, 2.8, 0.08, 0.6, 3.3, collide=False)


@prop("bathtub", "bath")
def bathtub(k):
    k.box("ceramic", -1.4, -2.8, 0, 1.4, 2.8, 1.9)
    k.box("tile_bath_blue", -1.15, -2.55, 1.0, 1.15, 2.55, 1.91, collide=False)
    k.box("metal_chrome", -0.1, 2.6, 2.4, 0.1, 2.8, 2.6, collide=False)
    k.box("metal_chrome", -0.1, 2.4, 6.8, 0.1, 2.8, 7.0, collide=False)
    k.box("fabric_white", -1.45, -2.0, 1.9, -1.4, 1.5, 7.0, collide=False)


@prop("shower_stall", "bath")
def shower_stall(k):
    k.box("ceramic", -1.6, -1.6, 0, 1.6, 1.6, 0.3)
    k.box("glass_frosted", -1.6, -1.65, 0.3, 1.6, -1.55, 7.2, collide=False)
    k.box("glass_frosted", -1.65, -1.6, 0.3, -1.55, 1.6, 7.2, collide=False)
    k.box("metal_chrome", -0.1, 1.2, 6.2, 0.1, 1.6, 6.5, collide=False)


@prop("towel_rack", "bath", mount="wall", collide="none", detail=3)
def towel_rack(k):
    k.box("metal_chrome", -1.0, -0.2, 4.0, 1.0, 0.0, 4.1)
    k.box("$fabric", -0.8, -0.25, 2.8, 0.8, -0.15, 4.1)


@prop("mirror_bath", "bath", mount="wall", collide="none", detail=2)
def mirror_bath(k):
    k.box("metal_chrome", -1.3, -0.08, 0, 1.3, 0.0, 2.2)
    k.box("lamp_warm", -1.0, -0.3, 2.3, 1.0, 0.0, 2.5)


@prop("urinal", "bath", mount="wall", collide="none")
def urinal(k):
    k.box("ceramic", -0.7, -1.0, 1.6, 0.7, 0.0, 4.2)
    k.box("metal_chrome", -0.08, -0.2, 4.2, 0.08, 0.0, 5.0)


@prop("toilet_stall", "bath", collide=[(-1.8, -2.8, 0.5, -1.7, 2.8, 6.5), (1.7, -2.8, 0.5, 1.8, 2.8, 6.5)])
def toilet_stall(k):
    # 3.6 wide x 5.6 deep cubicle with partitions and a door on the -Y side
    for x in (-1.8, 1.7):
        k.box("metal_beige", x, -2.8, 0.5, x + 0.1, 2.8, 6.5)
    k.box("metal_beige", -1.7, -2.8, 0.5, 0.9, -2.7, 6.3, collide=False)
    k.box("metal_chrome", 0.5, -2.95, 3.2, 0.7, -2.8, 3.5, collide=False)
    k.box("ceramic", -0.55, 1.4, 0, 0.55, 2.4, 1.2)
    k.cyl("ceramic", 0, 1.3, 1.0, 0.8, 0.45, 10, ry=1.0)
    k.box("ceramic", -0.85, 2.2, 0.9, 0.85, 2.8, 2.6)


@prop("hand_dryer", "bath", mount="wall", collide="none", detail=3)
def hand_dryer(k):
    k.box("metal_chrome", -0.5, -0.7, 0, 0.5, 0.0, 1.0)


@prop("sink_commercial", "bath")
def sink_commercial(k):
    k.box("marble", -3.0, -1.1, 2.6, 3.0, 1.0, 2.9)
    k.box("trim_dark", -3.0, -0.9, 0.0, 3.0, 1.0, 2.6, collide=False)
    for x in (-1.5, 1.5):
        k.box("ceramic", x - 0.7, -0.7, 2.85, x + 0.7, 0.4, 2.95, collide=False)
        k.box("metal_chrome", x - 0.08, 0.5, 2.9, x + 0.08, 0.7, 3.4, collide=False)


@prop("water_heater", "utility")
def water_heater(k):
    k.cyl("metal_white", 0, 0, 0, 1.0, 5.6, 10)
    k.cyl("metal", 0, 0, 5.6, 0.2, 2.0, 6, collide=False)


@prop("furnace", "utility")
def furnace(k):
    k.box("metal_beige", -1.4, -1.4, 0, 1.4, 1.4, 5.5)
    k.box("metal", -0.8, -0.8, 5.5, 0.8, 0.8, 9.0, collide=False)


@prop("boiler", "utility")
def boiler(k):
    k.box("metal_red", -2.5, -2.0, 0, 2.5, 2.0, 5.5)
    k.cyl("metal", 1.5, 0, 5.5, 0.4, 4.0, 8, collide=False)
    k.hcyl("metal_rust", 0, -2.2, 3.0, 0.3, 4.0, axis="x", sides=6)


# --- Laundry --------------------------------------------------------------

@prop("washer", "laundry")
def washer(k):
    k.box("$metal", -1.3, -1.3, 0, 1.3, 1.3, 3.4)
    k.hcyl("glass_tint", 0, -1.33, 1.7, 0.8, 0.1, axis="y", sides=12)
    k.box("plastic_gray", -1.3, 0.9, 3.4, 1.3, 1.3, 3.9, collide=False)


@prop("dryer_stack", "laundry")
def dryer_stack(k):
    k.box("$metal", -1.3, -1.3, 0, 1.3, 1.3, 6.6)
    k.hcyl("glass_tint", 0, -1.33, 1.6, 0.75, 0.1, axis="y", sides=12)
    k.hcyl("glass_tint", 0, -1.33, 4.9, 0.75, 0.1, axis="y", sides=12)
    k.box("screen_on", -0.6, -1.33, 3.1, 0.6, -1.3, 3.4, collide=False)


@prop("washer_topload", "laundry")
def washer_topload(k):
    k.box("metal_white", -1.3, -1.3, 0, 1.3, 1.3, 3.4)
    k.box("metal_white", -1.3, 0.9, 3.4, 1.3, 1.3, 4.2, collide=False)
    k.box("metal_chrome", -1.0, -1.0, 3.4, 1.0, 0.7, 3.45, collide=False)


@prop("folding_table", "laundry")
def folding_table(k):
    k.box("plastic_beige", -4.0, -1.5, 2.8, 4.0, 1.5, 3.0)
    legs4(k, "metal", 8, 3, 2.8, 0.2, 0.2)
    k.box("$fabric", -2.0, -0.8, 3.0, -0.4, 0.6, 3.3, collide=False)


@prop("laundry_cart", "laundry", collide="none", detail=2)
def laundry_cart(k):
    k.box("metal_chrome", -1.2, -0.9, 1.0, 1.2, 0.9, 3.0)
    k.box("metal_chrome", -1.2, 0.8, 3.0, 1.2, 0.9, 5.0)
    legs4(k, "metal_chrome", 2.4, 1.8, 1.0, 0.1, 0.05)
    k.box("$fabric", -1.0, -0.7, 2.4, 1.0, 0.7, 3.2)
