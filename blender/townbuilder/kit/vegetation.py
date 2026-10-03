"""Low-poly trees, shrubs, rocks and shoreline plants (instanced with random yaw/scale)."""

from __future__ import annotations

import math

from . import prop
from .shapes import blob, cone


def _deciduous(k, seed, h=22.0, r=8.0, leaf="$leaf", trunk="bark"):
    k.cyl(trunk, 0, 0, 0, 0.9, h * 0.55, 7)
    blob(k, leaf, 0, 0, h * 0.62, r, r * 0.95, r * 0.75, seed=seed)
    blob(k, leaf, r * 0.45, r * 0.2, h * 0.78, r * 0.62, r * 0.6, r * 0.55, seed=seed + 1)
    blob(k, leaf, -r * 0.4, -r * 0.3, h * 0.74, r * 0.6, r * 0.6, r * 0.5, seed=seed + 2)


@prop("tree_oak", "tree", collide=[(-0.9, -0.9, 0, 0.9, 0.9, 12)])
def tree_oak(k):
    _deciduous(k, 1, 24.0, 9.0)


@prop("tree_oak_b", "tree", collide=[(-0.9, -0.9, 0, 0.9, 0.9, 12)])
def tree_oak_b(k):
    _deciduous(k, 7, 20.0, 7.5)


@prop("tree_maple", "tree", collide=[(-0.8, -0.8, 0, 0.8, 0.8, 12)])
def tree_maple(k):
    _deciduous(k, 13, 22.0, 7.0, leaf="leaf_autumn")


@prop("tree_street", "tree", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 10)])
def tree_street(k):
    k.cyl("bark", 0, 0, 0, 0.55, 9.0, 6)
    blob(k, "$leaf", 0, 0, 13.0, 5.2, 5.2, 5.4, seed=21)
    k.box("metal_dark", -2.0, -2.0, -0.02, 2.0, 2.0, 0.08, collide=False)


@prop("tree_birch", "tree", collide=[(-0.6, -0.6, 0, 0.6, 0.6, 10)])
def tree_birch(k):
    k.cyl("bark_light", 0, 0, 0, 0.5, 16.0, 6)
    blob(k, "leaf_light", 0, 0, 16.0, 4.6, 4.6, 6.4, seed=31)


@prop("tree_pine", "tree", collide=[(-0.8, -0.8, 0, 0.8, 0.8, 12)])
def tree_pine(k):
    k.cyl("bark", 0, 0, 0, 0.8, 6.0, 6)
    for i, (z, r, h) in enumerate(((4.0, 7.0, 10.0), (10.0, 5.6, 9.0), (16.0, 4.0, 8.0),
                                   (21.0, 2.4, 6.0))):
        cone(k, "leaf_pine", 0, 0, z, r, 0.0, h, 8)


@prop("tree_pine_tall", "tree", collide=[(-0.8, -0.8, 0, 0.8, 0.8, 12)])
def tree_pine_tall(k):
    k.cyl("bark", 0, 0, 0, 0.9, 8.0, 6)
    for (z, r, h) in ((6.0, 7.6, 11.0), (13.0, 6.2, 10.0), (20.0, 4.6, 9.0), (27.0, 3.0, 8.0),
                      (33.0, 1.6, 5.0)):
        cone(k, "leaf_pine", 0, 0, z, r, 0.0, h, 8)


@prop("tree_palm", "tree", collide=[(-0.7, -0.7, 0, 0.7, 0.7, 12)])
def tree_palm(k):
    segs = 7
    for i in range(segs):
        lean = i * 0.25
        k.cyl("bark_light", lean, 0, i * 4.0, 0.7 - i * 0.04, 4.1, 6)
    top = (segs * 0.25, 0, segs * 4.0)
    for a in range(7):
        ang = a * 2 * math.pi / 7
        dx, dy = math.cos(ang), math.sin(ang)
        verts = [(top[0], top[1], top[2]),
                 (top[0] + dx * 4 - dy * 1.2, top[1] + dy * 4 + dx * 1.2, top[2] + 1.2),
                 (top[0] + dx * 8.5, top[1] + dy * 8.5, top[2] - 2.4),
                 (top[0] + dx * 4 + dy * 1.2, top[1] + dy * 4 - dx * 1.2, top[2] + 1.2)]
        under = [(x, y, z - 0.15) for (x, y, z) in verts]
        k.mesh("leaf_palm", verts + under, [(0, 1, 2, 3), (7, 6, 5, 4)])
    k.ball("bark", top[0], top[1], top[2], 0.9)


@prop("tree_dead", "tree", collide=[(-0.7, -0.7, 0, 0.7, 0.7, 12)])
def tree_dead(k):
    k.cyl("bark_light", 0, 0, 0, 0.7, 14.0, 6)
    from ..geom import rot_y, rot_x
    k.cyl("bark_light", 1.6, 0, 9.0, 0.3, 6.0, 5, rot=rot_y(0.7))
    k.cyl("bark_light", -1.2, 0.4, 11.0, 0.25, 5.0, 5, rot=rot_x(0.6))


@prop("bush_round", "shrub", collide="none")
def bush_round(k):
    blob(k, "$leaf", 0, 0, 1.6, 2.6, 2.4, 1.9, seed=41)


@prop("bush_small", "shrub", collide="none")
def bush_small(k):
    blob(k, "$leaf", 0, 0, 1.0, 1.5, 1.5, 1.2, seed=43, rings=3, segs=6)


@prop("bush_flowering", "shrub", collide="none", detail=2)
def bush_flowering(k):
    blob(k, "leaf", 0, 0, 1.4, 2.2, 2.2, 1.6, seed=45)
    for i in range(5):
        a = i * 1.3
        k.ball("flower_red" if i % 2 else "flower_purple", 1.6 * math.cos(a),
               1.6 * math.sin(a), 2.0 + (i % 2) * 0.6, 0.35)


@prop("hedge_block", "shrub", collide=[(-3, -1.5, 0, 3, 1.5, 4)])
def hedge_block(k):
    k.box("hedge", -3.0, -1.5, 0, 3.0, 1.5, 4.0)


@prop("weeds", "shrub", collide="none", detail=2)
def weeds(k):
    for i in range(6):
        a = i * 1.1
        r = 0.6 + (i % 3) * 0.5
        k.ball("leaf_dry" if i % 2 else "grass_dry", r * math.cos(a), r * math.sin(a), 0.5,
               0.5, 0.5, 0.8)


@prop("tall_grass", "shrub", collide="none", detail=2)
def tall_grass(k):
    for i in range(5):
        a = i * 1.4
        r = 0.3 + (i % 2) * 0.8
        cone(k, "grass_dry", r * math.cos(a), r * math.sin(a), 0, 0.5, 0.0, 2.4 + (i % 3) * 0.5,
             5)


@prop("reeds", "shrub", collide="none")
def reeds(k):
    for i in range(9):
        a = i * 0.9
        r = 0.4 + (i % 3) * 0.9
        cone(k, "reed", r * math.cos(a), r * math.sin(a), -1.0, 0.25, 0.0, 5.0 + (i % 4), 4)


@prop("rock_small", "rock", collide="box")
def rock_small(k):
    blob(k, "rock", 0, 0, 0.6, 1.6, 1.3, 1.0, seed=51, rings=3, segs=6, jitter=0.25)


@prop("rock_med", "rock", collide="box")
def rock_med(k):
    blob(k, "rock", 0, 0, 1.4, 3.6, 3.0, 2.4, seed=53, rings=3, segs=7, jitter=0.25)


@prop("rock_large", "rock", collide="box")
def rock_large(k):
    blob(k, "rock_dark", 0, 0, 3.0, 8.0, 6.5, 5.0, seed=57, rings=4, segs=8, jitter=0.22)


@prop("flower_planter", "shrub", collide="none", detail=2)
def flower_planter(k):
    k.box("wood_dark", -2.0, -0.8, 0, 2.0, 0.8, 1.6)
    for i in range(5):
        k.ball(("flower_red", "flower_yellow", "flower_purple")[i % 3], -1.6 + i * 0.8, 0, 2.0,
               0.45)
