"""Door leaves, garage doors, roll-up doors and window dressings.

Doors are kit props so every one in town shares a few meshes, and so Roblox
can make them interactive.  Each is modelled at a nominal size and stretched
to the real opening (placement scale).  Origin: bottom centre of the opening,
leaf centred on the wall plane; hinge side is local -X.
"""

from __future__ import annotations

from . import prop

NOMINAL = {  # name: (width, height)
    "door_interior": (4.0, 7.5),
    "door_exterior": (4.0, 7.5),
    "door_metal": (4.0, 7.5),
    "door_glass": (4.0, 7.5),
    "door_glass_double": (7.0, 7.5),
    "door_sliding_glass": (8.0, 7.5),
    "door_garage": (10.0, 8.0),
    "door_rollup": (12.0, 12.0),
    "door_bay": (14.0, 14.0),
    "door_cell": (4.0, 7.5),
    "door_bifold": (4.0, 7.5),
}


@prop("door_interior", "door", tags=("door", "hinged"), collide="box")
def door_interior(k):
    k.box("$paint", -2.0, -0.15, 0, 2.0, 0.15, 7.5)
    for z0, z1 in ((0.6, 3.4), (4.0, 6.9)):
        k.box("$paint", -1.6, -0.2, z0, 1.6, -0.15, z1, collide=False)
    k.ball("metal_brass", 1.5, -0.3, 3.6, 0.15)
    k.ball("metal_brass", 1.5, 0.3, 3.6, 0.15)


@prop("door_exterior", "door", tags=("door", "hinged"), collide="box")
def door_exterior(k):
    k.box("$paint", -2.0, -0.2, 0, 2.0, 0.2, 7.5)
    k.box("glass_frosted", -1.2, -0.22, 4.6, 1.2, 0.22, 6.8, collide=False)
    k.box("$paint", -1.5, -0.25, 0.6, 1.5, -0.2, 3.8, collide=False)
    k.box("metal_brass", 1.3, -0.4, 3.4, 1.6, 0.4, 3.9, collide=False)


@prop("door_metal", "door", tags=("door", "hinged"), collide="box")
def door_metal(k):
    k.box("$metal", -2.0, -0.2, 0, 2.0, 0.2, 7.5)
    k.box("metal_chrome", -1.6, -0.45, 3.4, 1.6, -0.2, 3.7, collide=False)
    k.box("metal_chrome", 1.3, 0.2, 3.4, 1.6, 0.4, 4.0, collide=False)


@prop("door_glass", "door", tags=("door", "hinged"), collide="box")
def door_glass(k):
    k.box("frame_alu", -2.0, -0.15, 0, 2.0, 0.15, 0.6)
    k.box("frame_alu", -2.0, -0.15, 6.9, 2.0, 0.15, 7.5)
    k.box("frame_alu", -2.0, -0.15, 0.6, -1.6, 0.15, 6.9)
    k.box("frame_alu", 1.6, -0.15, 0.6, 2.0, 0.15, 6.9)
    k.box("glass_store", -1.6, -0.05, 0.6, 1.6, 0.05, 6.9)
    k.box("metal_chrome", 1.1, -0.45, 2.2, 1.25, -0.15, 5.4, collide=False)
    k.box("metal_chrome", 1.1, 0.15, 2.2, 1.25, 0.45, 5.4, collide=False)


@prop("door_glass_double", "door", tags=("door", "double"), collide="box")
def door_glass_double(k):
    for sx in (-1, 1):
        x0, x1 = (-3.5, 0.0) if sx < 0 else (0.0, 3.5)
        k.box("frame_alu", x0, -0.15, 0, x1, 0.15, 0.6)
        k.box("frame_alu", x0, -0.15, 6.9, x1, 0.15, 7.5)
        k.box("frame_alu", x0, -0.15, 0.6, x0 + 0.35, 0.15, 6.9)
        k.box("frame_alu", x1 - 0.35, -0.15, 0.6, x1, 0.15, 6.9)
        k.box("glass_store", x0 + 0.35, -0.05, 0.6, x1 - 0.35, 0.05, 6.9)
        hx = -0.6 if sx < 0 else 0.45
        k.box("metal_chrome", hx, -0.45, 2.2, hx + 0.15, -0.15, 5.4, collide=False)


@prop("door_sliding_glass", "door", tags=("door", "sliding"), collide="box")
def door_sliding_glass(k):
    k.box("frame_alu", -4.0, -0.15, 0, 4.0, 0.15, 0.4)
    k.box("frame_alu", -4.0, -0.15, 7.1, 4.0, 0.15, 7.5)
    for x in (-4.0, -0.1, 3.7):
        k.box("frame_alu", x, -0.15, 0.4, x + 0.3, 0.15, 7.1)
    k.box("glass", -3.7, -0.05, 0.4, -0.1, 0.05, 7.1)
    k.box("glass", 0.2, -0.05, 0.4, 3.7, 0.05, 7.1)


@prop("door_garage", "door", tags=("door", "garage"), collide="box")
def door_garage(k):
    k.box("$paint", -5.0, -0.2, 0, 5.0, 0.2, 8.0)
    for i in range(4):
        z = 0.1 + i * 2.0
        k.box("$paint", -4.8, -0.28, z + 0.15, 4.8, -0.2, z + 1.85, collide=False)
    for x in (-3.6, -1.2, 1.2, 3.6):
        k.box("glass", x - 0.9, -0.3, 6.3, x + 0.9, -0.2, 7.5, collide=False)


@prop("door_rollup", "door", tags=("door", "rollup"), collide="box")
def door_rollup(k):
    k.box("rollup_door", -6.0, -0.25, 0, 6.0, 0.25, 12.0)
    for i in range(15):
        z = 0.4 + i * 0.78
        k.box("metal_gray", -6.0, -0.3, z, 6.0, -0.25, z + 0.12, collide=False)
    k.box("metal_dark", -6.0, -0.6, 11.4, 6.0, 0.6, 12.0, collide=False)
    k.box("hazard_yellow", -6.0, -0.32, 0, 6.0, -0.25, 0.4, collide=False)


@prop("door_bay", "door", tags=("door", "rollup"), collide="box")
def door_bay(k):
    k.box("$paint", -7.0, -0.25, 0, 7.0, 0.25, 14.0)
    for r in range(5):
        z = 0.2 + r * 2.8
        k.box("$paint", -6.8, -0.32, z + 0.2, 6.8, -0.25, z + 2.6, collide=False)
        if r == 3:
            for c in range(5):
                x = -6.0 + c * 2.6
                k.box("glass", x, -0.34, z + 0.6, x + 2.0, -0.25, z + 2.2, collide=False)


@prop("door_cell", "door", tags=("door", "hinged"), collide="box")
def door_cell(k):
    k.box("metal_dark", -2.0, -0.15, 0, 2.0, 0.15, 0.3)
    k.box("metal_dark", -2.0, -0.15, 7.2, 2.0, 0.15, 7.5)
    k.box("metal_dark", -2.0, -0.15, 3.6, 2.0, 0.15, 3.9)
    for i in range(8):
        x = -1.85 + i * 0.53
        k.box("metal_dark", x - 0.06, -0.06, 0.3, x + 0.06, 0.06, 7.2)


@prop("door_bifold", "door", tags=("door", "hinged"), collide="box")
def door_bifold(k):
    for i in range(4):
        x = -2.0 + i * 1.0
        k.box("$paint", x + 0.02, -0.1, 0, x + 0.98, 0.1, 7.5)
        for z in range(10):
            k.box("$paint", x + 0.1, -0.15, 0.5 + z * 0.65, x + 0.9, -0.1, 0.6 + z * 0.65,
                  collide=False)
