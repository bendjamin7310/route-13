"""Material palette for the whole town.

Every surface references one of these keys. Each entry carries:

* ``rgb``   - base colour (sRGB, 0-255)
* ``rbx``   - the Roblox ``Enum.Material`` it maps to (the importer/assembler
              sets ``MeshPart.Material`` and ``Color`` from this table)
* ``rough`` - roughness for Blender preview shading
* ``alpha`` - <1 for glass / water
* ``emit``  - emission strength for neon signs, lit fixtures and screens

Palette rules (from the art brief): warm beige / cream / muted white / brown /
warm gray / concrete gray / faded green / muted tan as primaries; faded red,
muted blue, mustard, muted orange, turquoise and dark green as accents.
District quality is expressed by which keys a building draws from.
"""

from __future__ import annotations

P = {}


def _m(name, rgb, rbx="SmoothPlastic", rough=0.75, alpha=1.0, emit=0.0, metal=0.0):
    P[name] = {"rgb": rgb, "rbx": rbx, "rough": rough, "alpha": alpha, "emit": emit,
               "metal": metal}


# --- Facades -----------------------------------------------------------------
_m("brick_red", (152, 80, 62), "Brick")
_m("brick_brown", (124, 84, 64), "Brick")
_m("brick_tan", (184, 146, 108), "Brick")
_m("brick_dark", (96, 66, 58), "Brick")
_m("brick_cream", (214, 200, 170), "Brick")
_m("brick_painted_green", (110, 132, 104), "Brick")
_m("stucco_cream", (228, 214, 184), "Plaster")
_m("stucco_peach", (226, 180, 146), "Plaster")
_m("stucco_mint", (172, 196, 166), "Plaster")
_m("stucco_sky", (150, 178, 196), "Plaster")
_m("stucco_mustard", (214, 176, 96), "Plaster")
_m("stucco_white", (232, 228, 214), "Plaster")
_m("stucco_terracotta", (190, 112, 84), "Plaster")
_m("stucco_gray", (168, 164, 154), "Plaster")
_m("siding_white", (226, 222, 208), "WoodPlanks")
_m("siding_blue", (128, 158, 178), "WoodPlanks")
_m("siding_green", (132, 158, 120), "WoodPlanks")
_m("siding_yellow", (222, 196, 128), "WoodPlanks")
_m("siding_gray", (156, 158, 154), "WoodPlanks")
_m("siding_red", (166, 86, 70), "WoodPlanks")
_m("siding_tan", (196, 172, 134), "WoodPlanks")
_m("siding_teal", (98, 148, 146), "WoodPlanks")
_m("siding_faded", (176, 168, 150), "WoodPlanks")
_m("shingle_wall", (150, 128, 102), "WoodPlanks")
_m("concrete_light", (186, 182, 172), "Concrete")
_m("concrete", (160, 158, 150), "Concrete")
_m("concrete_dark", (112, 112, 108), "Concrete")
_m("concrete_tan", (190, 176, 150), "Concrete")
_m("block_gray", (150, 150, 144), "Concrete")
_m("block_painted", (196, 190, 168), "Concrete")
_m("metal_wall_gray", (150, 154, 156), "Metal", 0.6, metal=0.4)
_m("metal_wall_blue", (92, 120, 146), "Metal", 0.6, metal=0.4)
_m("metal_wall_green", (98, 128, 104), "Metal", 0.6, metal=0.4)
_m("metal_wall_tan", (186, 170, 140), "Metal", 0.6, metal=0.4)
_m("metal_wall_rust", (142, 96, 72), "CorrodedMetal", 0.9, metal=0.3)
_m("metal_wall_white", (214, 214, 206), "Metal", 0.6, metal=0.3)
_m("stone_base", (128, 122, 112), "Slate")
_m("granite", (110, 108, 106), "Granite")
_m("marble", (220, 216, 206), "Marble", 0.3)
_m("sandstone", (198, 170, 128), "Sandstone")
_m("limestone", (206, 196, 172), "Limestone")

# --- Trim / openings ----------------------------------------------------------
_m("trim_white", (234, 230, 218), "SmoothPlastic", 0.6)
_m("trim_cream", (220, 206, 176), "SmoothPlastic", 0.6)
_m("trim_dark", (60, 58, 56), "SmoothPlastic", 0.6)
_m("trim_green", (56, 86, 64), "SmoothPlastic", 0.6)
_m("trim_brown", (98, 70, 50), "Wood", 0.7)
_m("trim_red", (138, 56, 48), "SmoothPlastic", 0.6)
_m("trim_blue", (60, 84, 112), "SmoothPlastic", 0.6)
_m("trim_teal", (54, 112, 116), "SmoothPlastic", 0.6)
_m("frame_alu", (178, 180, 182), "Metal", 0.4, metal=0.7)
_m("frame_dark", (48, 50, 52), "Metal", 0.5, metal=0.5)
_m("glass", (170, 200, 214), "Glass", 0.05, alpha=0.38)
_m("glass_store", (190, 214, 222), "Glass", 0.05, alpha=0.28)
_m("glass_tint", (90, 112, 124), "Glass", 0.05, alpha=0.62)
_m("glass_dirty", (156, 160, 140), "Glass", 0.4, alpha=0.72)
_m("glass_frosted", (214, 222, 224), "Glass", 0.6, alpha=0.8)
_m("door_wood", (124, 86, 56), "Wood")
_m("door_white", (230, 226, 214), "SmoothPlastic")
_m("door_red", (150, 58, 48), "SmoothPlastic")
_m("door_green", (62, 98, 74), "SmoothPlastic")
_m("door_blue", (66, 98, 132), "SmoothPlastic")
_m("door_mustard", (196, 156, 70), "SmoothPlastic")
_m("door_metal", (128, 132, 134), "Metal", 0.5, metal=0.5)
_m("door_metal_dark", (74, 78, 80), "Metal", 0.5, metal=0.5)
_m("garage_door", (214, 210, 198), "Metal", 0.6, metal=0.3)
_m("rollup_door", (170, 172, 168), "CorrodedMetal", 0.7, metal=0.4)
_m("awning_red", (164, 62, 52), "Fabric")
_m("awning_green", (52, 104, 76), "Fabric")
_m("awning_blue", (56, 92, 136), "Fabric")
_m("awning_mustard", (206, 160, 62), "Fabric")
_m("awning_teal", (48, 126, 128), "Fabric")
_m("awning_cream", (226, 214, 182), "Fabric")
_m("awning_orange", (206, 116, 58), "Fabric")

# --- Roofs -------------------------------------------------------------------
_m("roof_shingle_dark", (72, 70, 70), "RoofShingles")
_m("roof_shingle_brown", (106, 80, 64), "RoofShingles")
_m("roof_shingle_red", (128, 66, 56), "RoofShingles")
_m("roof_shingle_green", (78, 98, 82), "RoofShingles")
_m("roof_shingle_blue", (76, 88, 104), "RoofShingles")
_m("roof_tile", (176, 96, 66), "ClayRoofTiles")
_m("roof_membrane", (150, 150, 146), "Concrete")
_m("roof_gravel", (132, 128, 122), "Pebble")
_m("roof_tar", (66, 66, 66), "Asphalt")
_m("roof_metal", (140, 146, 148), "Metal", 0.5, metal=0.6)
_m("roof_metal_red", (148, 70, 58), "Metal", 0.6, metal=0.4)
_m("roof_metal_green", (80, 114, 92), "Metal", 0.6, metal=0.4)

# --- Ground / roads ------------------------------------------------------------
_m("asphalt", (62, 62, 66), "Asphalt", 0.9)
_m("asphalt_old", (78, 76, 74), "Asphalt", 0.95)
_m("asphalt_patch", (54, 54, 56), "Asphalt", 0.9)
_m("sidewalk", (184, 180, 170), "Pavement", 0.9)
_m("sidewalk_old", (166, 160, 148), "Pavement", 0.95)
_m("curb", (168, 166, 158), "Concrete", 0.9)
_m("brick_paver", (162, 102, 80), "Brick")
_m("cobble", (132, 126, 118), "Cobblestone")
_m("paint_line_white", (232, 232, 226), "SmoothPlastic", 0.6)
_m("paint_line_yellow", (226, 186, 62), "SmoothPlastic", 0.6)
_m("paint_curb_red", (180, 60, 50), "SmoothPlastic", 0.6)
_m("grass", (104, 132, 70), "Grass", 1.0)
_m("grass_lush", (88, 128, 64), "Grass", 1.0)
_m("grass_dry", (150, 146, 88), "Grass", 1.0)
_m("lawn", (96, 138, 70), "LeafyGrass", 1.0)
_m("dirt", (132, 108, 80), "Ground", 1.0)
_m("mud", (96, 82, 66), "Mud", 1.0)
_m("sand", (214, 196, 154), "Sand", 1.0)
_m("sand_wet", (170, 154, 122), "Sand", 1.0)
_m("rock", (120, 116, 108), "Rock", 1.0)
_m("rock_dark", (88, 86, 82), "Basalt", 1.0)
_m("gravel", (142, 136, 124), "Pebble", 1.0)
_m("water", (52, 102, 118), "Glass", 0.05, alpha=0.7)
_m("water_river", (66, 106, 98), "Glass", 0.05, alpha=0.72)
_m("rail_steel", (112, 104, 96), "Metal", 0.5, metal=0.7)
_m("rail_tie", (92, 74, 58), "Wood", 1.0)
_m("ballast", (118, 112, 104), "Pebble", 1.0)

# --- Interior paint ----------------------------------------------------------
_m("paint_cream", (232, 222, 196), "SmoothPlastic", 0.85)
_m("paint_beige", (214, 196, 164), "SmoothPlastic", 0.85)
_m("paint_white", (236, 234, 226), "SmoothPlastic", 0.85)
_m("paint_warmgray", (186, 178, 166), "SmoothPlastic", 0.85)
_m("paint_sage", (176, 190, 160), "SmoothPlastic", 0.85)
_m("paint_tan", (200, 176, 140), "SmoothPlastic", 0.85)
_m("paint_blue", (164, 184, 200), "SmoothPlastic", 0.85)
_m("paint_mustard", (220, 186, 112), "SmoothPlastic", 0.85)
_m("paint_terracotta", (196, 128, 102), "SmoothPlastic", 0.85)
_m("paint_turquoise", (130, 186, 180), "SmoothPlastic", 0.85)
_m("paint_darkgreen", (78, 110, 88), "SmoothPlastic", 0.85)
_m("paint_mint", (196, 220, 196), "SmoothPlastic", 0.85)
_m("paint_pink", (220, 180, 170), "SmoothPlastic", 0.85)
_m("paint_lavender", (190, 182, 204), "SmoothPlastic", 0.85)
_m("paint_institutional", (198, 204, 188), "SmoothPlastic", 0.85)
_m("paint_navy", (68, 82, 108), "SmoothPlastic", 0.85)
_m("paint_oxblood", (122, 58, 52), "SmoothPlastic", 0.85)
_m("paint_faded", (194, 186, 160), "SmoothPlastic", 0.95)
_m("paint_nicotine", (206, 188, 140), "SmoothPlastic", 0.95)
_m("paint_dirty", (170, 160, 136), "SmoothPlastic", 1.0)
_m("wood_panel", (132, 94, 62), "Wood", 0.7)
_m("wainscot", (120, 86, 58), "Wood", 0.7)

# --- Interior floors / ceilings / tile ----------------------------------------
_m("floor_wood_light", (196, 160, 112), "WoodPlanks", 0.6)
_m("floor_wood", (156, 112, 74), "WoodPlanks", 0.6)
_m("floor_wood_dark", (104, 74, 52), "WoodPlanks", 0.6)
_m("floor_wood_worn", (150, 122, 92), "WoodPlanks", 0.9)
_m("floor_laminate", (178, 150, 116), "WoodPlanks", 0.5)
_m("floor_tile_white", (222, 220, 210), "CeramicTiles", 0.4)
_m("floor_tile_check", (196, 192, 178), "CeramicTiles", 0.4)
_m("floor_tile_terracotta", (178, 106, 76), "CeramicTiles", 0.5)
_m("floor_tile_blue", (140, 168, 182), "CeramicTiles", 0.4)
_m("floor_tile_green", (136, 160, 132), "CeramicTiles", 0.4)
_m("floor_vinyl", (200, 190, 166), "Plastic", 0.5)
_m("floor_vinyl_green", (150, 166, 140), "Plastic", 0.5)
_m("floor_vinyl_gray", (166, 166, 160), "Plastic", 0.5)
_m("floor_vinyl_worn", (178, 166, 140), "Plastic", 0.8)
_m("floor_linoleum_red", (156, 92, 76), "Plastic", 0.6)
_m("carpet_blue", (88, 100, 126), "Carpet", 1.0)
_m("carpet_gray", (132, 130, 126), "Carpet", 1.0)
_m("carpet_brown", (124, 100, 80), "Carpet", 1.0)
_m("carpet_red", (130, 64, 58), "Carpet", 1.0)
_m("carpet_green", (88, 112, 86), "Carpet", 1.0)
_m("carpet_beige", (190, 176, 150), "Carpet", 1.0)
_m("carpet_stained", (150, 132, 108), "Carpet", 1.0)
_m("floor_concrete", (150, 148, 142), "Concrete", 0.9)
_m("floor_concrete_sealed", (164, 162, 156), "SmoothPlastic", 0.35)
_m("floor_epoxy_gray", (146, 152, 150), "SmoothPlastic", 0.3)
_m("floor_terrazzo", (204, 198, 186), "Marble", 0.35)
_m("floor_rubber", (64, 66, 68), "Rubber", 0.9)
_m("floor_diamond", (150, 152, 154), "DiamondPlate", 0.5, metal=0.6)
_m("ceiling_white", (236, 234, 226), "Plaster", 0.95)
_m("ceiling_tile", (222, 220, 212), "Plaster", 0.95)
_m("ceiling_stained", (210, 200, 176), "Plaster", 1.0)
_m("ceiling_wood", (176, 140, 100), "WoodPlanks", 0.8)
_m("ceiling_dark", (54, 52, 52), "SmoothPlastic", 0.9)
_m("tile_bath_white", (228, 230, 226), "CeramicTiles", 0.3)
_m("tile_bath_blue", (150, 186, 200), "CeramicTiles", 0.3)
_m("tile_bath_mint", (176, 210, 190), "CeramicTiles", 0.3)
_m("tile_bath_pink", (222, 180, 176), "CeramicTiles", 0.3)
_m("tile_kitchen", (222, 214, 190), "CeramicTiles", 0.3)
_m("tile_subway", (232, 232, 228), "CeramicTiles", 0.3)
_m("tile_institutional", (200, 206, 194), "CeramicTiles", 0.3)

# --- Props: wood, fabric, metal, plastic --------------------------------------
_m("wood_light", (196, 162, 116), "Wood", 0.7)
_m("wood", (150, 108, 72), "Wood", 0.7)
_m("wood_dark", (96, 66, 46), "Wood", 0.7)
_m("wood_white", (230, 226, 214), "Wood", 0.7)
_m("wood_green", (90, 120, 96), "Wood", 0.7)
_m("wood_blue", (98, 126, 150), "Wood", 0.7)
_m("wood_raw", (186, 156, 110), "WoodPlanks", 0.9)
_m("wood_weathered", (148, 136, 118), "WoodPlanks", 1.0)
_m("plywood", (200, 172, 124), "WoodPlanks", 0.9)
_m("fabric_red", (156, 64, 56), "Fabric")
_m("fabric_blue", (74, 98, 136), "Fabric")
_m("fabric_green", (88, 116, 84), "Fabric")
_m("fabric_brown", (128, 96, 72), "Fabric")
_m("fabric_gray", (128, 128, 124), "Fabric")
_m("fabric_mustard", (198, 160, 74), "Fabric")
_m("fabric_cream", (222, 210, 182), "Fabric")
_m("fabric_teal", (64, 128, 128), "Fabric")
_m("fabric_orange", (198, 112, 64), "Fabric")
_m("fabric_purple", (112, 88, 128), "Fabric")
_m("fabric_pink", (206, 150, 150), "Fabric")
_m("fabric_dark", (60, 60, 62), "Fabric")
_m("fabric_white", (236, 234, 228), "Fabric")
_m("fabric_plaid", (140, 78, 64), "Fabric")
_m("leather_brown", (110, 70, 48), "Leather", 0.5)
_m("leather_black", (44, 42, 42), "Leather", 0.5)
_m("leather_red", (140, 46, 42), "Leather", 0.5)
_m("leather_cream", (218, 202, 170), "Leather", 0.5)
_m("vinyl_red", (176, 52, 48), "Leather", 0.35)
_m("vinyl_teal", (60, 138, 136), "Leather", 0.35)
_m("metal", (160, 164, 166), "Metal", 0.4, metal=0.8)
_m("metal_dark", (70, 72, 74), "Metal", 0.5, metal=0.7)
_m("metal_chrome", (206, 210, 214), "Foil", 0.15, metal=1.0)
_m("metal_brass", (186, 150, 82), "Foil", 0.3, metal=1.0)
_m("metal_rust", (134, 86, 60), "CorrodedMetal", 0.9, metal=0.3)
_m("metal_red", (172, 52, 44), "Metal", 0.5, metal=0.3)
_m("metal_yellow", (220, 176, 48), "Metal", 0.5, metal=0.3)
_m("metal_blue", (62, 98, 150), "Metal", 0.5, metal=0.3)
_m("metal_green", (70, 116, 84), "Metal", 0.5, metal=0.3)
_m("metal_orange", (210, 110, 48), "Metal", 0.5, metal=0.3)
_m("metal_white", (222, 222, 216), "Metal", 0.5, metal=0.3)
_m("metal_gray", (124, 128, 130), "Metal", 0.5, metal=0.5)
_m("metal_beige", (200, 190, 168), "Metal", 0.6, metal=0.3)
_m("diamond_plate", (160, 162, 164), "DiamondPlate", 0.4, metal=0.8)
_m("plastic_white", (232, 232, 228), "SmoothPlastic", 0.4)
_m("plastic_black", (40, 40, 42), "SmoothPlastic", 0.4)
_m("plastic_gray", (130, 132, 134), "SmoothPlastic", 0.5)
_m("plastic_beige", (210, 200, 176), "SmoothPlastic", 0.5)
_m("plastic_red", (190, 58, 50), "SmoothPlastic", 0.4)
_m("plastic_blue", (60, 108, 170), "SmoothPlastic", 0.4)
_m("plastic_green", (70, 140, 84), "SmoothPlastic", 0.4)
_m("plastic_yellow", (230, 190, 60), "SmoothPlastic", 0.4)
_m("plastic_orange", (226, 120, 50), "SmoothPlastic", 0.4)
_m("plastic_teal", (60, 150, 150), "SmoothPlastic", 0.4)
_m("plastic_pink", (220, 130, 150), "SmoothPlastic", 0.4)
_m("ceramic", (238, 238, 234), "SmoothPlastic", 0.15)
_m("rubber", (36, 36, 38), "Rubber", 0.9)
_m("cardboard", (176, 140, 98), "Cardboard", 0.9)
_m("paper", (236, 232, 220), "SmoothPlastic", 0.9)
_m("screen", (30, 34, 40), "SmoothPlastic", 0.15)
_m("screen_on", (120, 170, 200), "Neon", 0.2, emit=1.5)
_m("mattress", (226, 222, 210), "Fabric")
_m("sheet_white", (234, 232, 224), "Fabric")
_m("sheet_blue", (128, 156, 186), "Fabric")
_m("sheet_green", (140, 170, 140), "Fabric")
_m("sheet_red", (180, 92, 84), "Fabric")
_m("sheet_yellow", (226, 200, 130), "Fabric")
_m("sheet_gray", (150, 150, 150), "Fabric")
_m("food_red", (196, 72, 56), "SmoothPlastic", 0.6)
_m("food_green", (110, 160, 70), "SmoothPlastic", 0.6)
_m("food_orange", (226, 140, 50), "SmoothPlastic", 0.6)
_m("food_yellow", (236, 206, 90), "SmoothPlastic", 0.6)
_m("food_brown", (150, 100, 60), "SmoothPlastic", 0.6)
_m("goods_mix1", (200, 80, 70), "SmoothPlastic", 0.5)
_m("goods_mix2", (70, 120, 180), "SmoothPlastic", 0.5)
_m("goods_mix3", (230, 200, 90), "SmoothPlastic", 0.5)
_m("goods_mix4", (90, 160, 100), "SmoothPlastic", 0.5)
_m("goods_mix5", (230, 230, 220), "SmoothPlastic", 0.5)
_m("book_red", (150, 60, 50), "SmoothPlastic", 0.7)
_m("book_blue", (60, 80, 120), "SmoothPlastic", 0.7)
_m("book_green", (60, 100, 70), "SmoothPlastic", 0.7)
_m("book_tan", (190, 160, 110), "SmoothPlastic", 0.7)
_m("felt_green", (46, 110, 70), "Fabric")
_m("felt_blue", (46, 84, 130), "Fabric")
_m("chalkboard", (48, 66, 56), "Slate", 0.9)
_m("whiteboard", (240, 240, 236), "SmoothPlastic", 0.1)
_m("corkboard", (176, 136, 90), "Cardboard", 1.0)
_m("rope", (196, 170, 120), "Fabric")
_m("net", (90, 110, 96), "Fabric")

# --- Vegetation -------------------------------------------------------------
_m("bark", (98, 78, 60), "Wood", 1.0)
_m("bark_light", (150, 134, 110), "Wood", 1.0)
_m("leaf_dark", (66, 100, 58), "Grass", 1.0)
_m("leaf", (92, 126, 64), "Grass", 1.0)
_m("leaf_light", (128, 150, 76), "Grass", 1.0)
_m("leaf_pine", (56, 86, 62), "Grass", 1.0)
_m("leaf_autumn", (190, 122, 60), "Grass", 1.0)
_m("leaf_palm", (96, 136, 70), "Grass", 1.0)
_m("leaf_dry", (150, 140, 84), "Grass", 1.0)
_m("hedge", (72, 108, 60), "LeafyGrass", 1.0)
_m("flower_red", (196, 70, 70), "SmoothPlastic", 0.8)
_m("flower_yellow", (232, 200, 80), "SmoothPlastic", 0.8)
_m("flower_purple", (150, 110, 180), "SmoothPlastic", 0.8)
_m("reed", (150, 150, 92), "Grass", 1.0)

# --- Vehicles -----------------------------------------------------------------
_m("car_red", (166, 48, 44), "SmoothPlastic", 0.3)
_m("car_blue", (54, 88, 142), "SmoothPlastic", 0.3)
_m("car_white", (230, 230, 226), "SmoothPlastic", 0.3)
_m("car_black", (34, 34, 36), "SmoothPlastic", 0.3)
_m("car_silver", (170, 174, 178), "SmoothPlastic", 0.25, metal=0.4)
_m("car_green", (60, 104, 76), "SmoothPlastic", 0.3)
_m("car_beige", (200, 186, 152), "SmoothPlastic", 0.3)
_m("car_teal", (60, 132, 136), "SmoothPlastic", 0.3)
_m("car_maroon", (110, 40, 44), "SmoothPlastic", 0.3)
_m("car_brown", (110, 80, 58), "SmoothPlastic", 0.3)
_m("car_orange", (206, 110, 46), "SmoothPlastic", 0.3)
_m("car_yellow", (230, 186, 46), "SmoothPlastic", 0.3)
_m("car_navy", (40, 52, 82), "SmoothPlastic", 0.3)
_m("car_rust", (140, 92, 66), "CorrodedMetal", 0.8)
_m("car_police", (24, 26, 32), "SmoothPlastic", 0.3)
_m("car_fire", (178, 40, 36), "SmoothPlastic", 0.3)
_m("car_window", (40, 52, 62), "Glass", 0.05, alpha=0.75)
_m("headlight", (250, 244, 220), "Neon", 0.2, emit=0.6)
_m("taillight", (200, 40, 40), "Neon", 0.2, emit=0.4)
_m("lightbar_red", (220, 40, 40), "Neon", 0.2, emit=0.8)
_m("lightbar_blue", (50, 90, 230), "Neon", 0.2, emit=0.8)
_m("hull_white", (232, 232, 226), "SmoothPlastic", 0.3)
_m("hull_blue", (50, 84, 130), "SmoothPlastic", 0.3)
_m("hull_red", (160, 52, 46), "SmoothPlastic", 0.3)
_m("hull_green", (54, 92, 72), "SmoothPlastic", 0.3)
_m("deck_teak", (170, 128, 86), "WoodPlanks", 0.7)

# --- Light & signage ----------------------------------------------------------
_m("lamp_warm", (255, 226, 170), "Neon", 0.3, emit=3.0)
_m("lamp_cool", (230, 240, 255), "Neon", 0.3, emit=3.0)
_m("lamp_amber", (255, 180, 90), "Neon", 0.3, emit=3.0)
_m("lamp_off", (226, 222, 210), "SmoothPlastic", 0.4)
_m("neon_red", (255, 70, 60), "Neon", 0.3, emit=4.0)
_m("neon_pink", (255, 110, 170), "Neon", 0.3, emit=4.0)
_m("neon_blue", (80, 160, 255), "Neon", 0.3, emit=4.0)
_m("neon_green", (90, 230, 130), "Neon", 0.3, emit=4.0)
_m("neon_yellow", (255, 214, 90), "Neon", 0.3, emit=4.0)
_m("neon_orange", (255, 140, 60), "Neon", 0.3, emit=4.0)
_m("neon_white", (255, 246, 230), "Neon", 0.3, emit=4.0)
_m("neon_teal", (70, 230, 210), "Neon", 0.3, emit=4.0)
_m("sign_white", (238, 234, 222), "SmoothPlastic", 0.5)
_m("sign_cream", (232, 220, 190), "SmoothPlastic", 0.5)
_m("sign_red", (176, 56, 48), "SmoothPlastic", 0.5)
_m("sign_green", (40, 110, 70), "SmoothPlastic", 0.5)
_m("sign_blue", (46, 82, 140), "SmoothPlastic", 0.5)
_m("sign_yellow", (232, 196, 60), "SmoothPlastic", 0.5)
_m("sign_brown", (100, 70, 50), "SmoothPlastic", 0.5)
_m("sign_black", (36, 36, 38), "SmoothPlastic", 0.5)
_m("sign_orange", (220, 120, 50), "SmoothPlastic", 0.5)
_m("sign_teal", (46, 120, 124), "SmoothPlastic", 0.5)
_m("traffic_red", (220, 50, 40), "Neon", 0.3, emit=2.0)
_m("traffic_green", (60, 220, 120), "Neon", 0.3, emit=2.0)
_m("traffic_amber", (250, 170, 40), "Neon", 0.3, emit=1.0)
_m("hazard_yellow", (232, 190, 40), "SmoothPlastic", 0.5)
_m("hazard_black", (36, 36, 36), "SmoothPlastic", 0.5)
_m("cone_orange", (236, 110, 40), "SmoothPlastic", 0.5)
_m("police_blue", (40, 64, 110), "SmoothPlastic", 0.5)
_m("fire_red", (180, 40, 36), "SmoothPlastic", 0.4)
_m("invisible", (255, 0, 255), "SmoothPlastic", 1.0, alpha=0.0)


# Channel defaults: props can expose recolourable "$channels".
CHANNEL_DEFAULTS = {
    "$fabric": "fabric_red",
    "$fabric2": "fabric_cream",
    "$wood": "wood",
    "$paint": "wood_white",
    "$metal": "metal_gray",
    "$plastic": "plastic_blue",
    "$car": "car_blue",
    "$sheet": "sheet_white",
    "$leaf": "leaf",
    "$hull": "hull_white",
    "$sign": "sign_red",
    "$goods": "goods_mix1",
    "$goods2": "goods_mix2",
    "$goods3": "goods_mix3",
    "$book": "book_red",
}

# Colour families for random picks.
FABRICS = ["fabric_red", "fabric_blue", "fabric_green", "fabric_brown", "fabric_gray",
           "fabric_mustard", "fabric_cream", "fabric_teal", "fabric_orange", "fabric_plaid",
           "fabric_dark", "fabric_purple"]
FABRICS_CHEAP = ["fabric_brown", "fabric_plaid", "fabric_gray", "fabric_mustard",
                 "fabric_orange", "fabric_green"]
FABRICS_NICE = ["fabric_cream", "fabric_gray", "fabric_blue", "fabric_teal", "leather_brown",
                "fabric_dark", "leather_cream"]
SHEETS = ["sheet_white", "sheet_blue", "sheet_green", "sheet_red", "sheet_yellow", "sheet_gray"]
WOODS = ["wood_light", "wood", "wood_dark"]
CAR_PAINTS = ["car_red", "car_blue", "car_white", "car_black", "car_silver", "car_green",
              "car_beige", "car_teal", "car_maroon", "car_brown", "car_navy", "car_white",
              "car_silver", "car_black", "car_orange"]
CAR_PAINTS_OLD = ["car_rust", "car_beige", "car_brown", "car_maroon", "car_green", "car_silver"]
HULLS = ["hull_white", "hull_white", "hull_blue", "hull_red", "hull_green"]

PAINT_WARM = ["paint_cream", "paint_beige", "paint_white", "paint_warmgray", "paint_tan",
              "paint_sage"]
PAINT_ACCENT = ["paint_blue", "paint_mustard", "paint_terracotta", "paint_turquoise",
                "paint_darkgreen", "paint_mint", "paint_pink", "paint_lavender", "paint_navy",
                "paint_oxblood"]
PAINT_CHEAP = ["paint_faded", "paint_nicotine", "paint_beige", "paint_dirty", "paint_mint",
               "paint_institutional", "paint_warmgray"]


def rgb01(name):
    r, g, b = P[name]["rgb"]
    return (r / 255.0, g / 255.0, b / 255.0)


def resolve(mat, channels=None):
    if mat and mat[0] == "$":
        if channels and mat in channels:
            return channels[mat]
        return CHANNEL_DEFAULTS.get(mat, "plastic_gray")
    return mat


def check(name):
    if name not in P and not (name and name[0] == "$"):
        raise KeyError(f"unknown material {name!r}")
    return name
