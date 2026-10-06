"""Face classifiers: decide which material each face of a body part gets.

Roblox MeshParts carry one colour/material each, so parts are split by
these labels into separate objects (Body_Cab_Paint, Body_Cab_WheelWell...).
"""

import numpy as np

import body
from dims import *  # noqa: F401,F403


def _xyz(c):
    c = c.astype(np.float32)
    return c[:, 0], c[:, 1], c[:, 2]


def cab(c, n):
    x, y, z = _xyz(c)
    lab = np.full(len(c), "Paint", dtype=object)
    under = (n[:, 2] < -0.75) & (z < Z_SILL + 0.02)
    lab[under] = "Underbody"
    arch = np.minimum(body.arch_cut(x, y, z, Y_FRONT_AXLE), body.arch_cut(x, y, z, Y_REAR_AXLE, inner=0.55))
    well = (arch < 0.008) & (np.abs(x) < body.w_base(z) - 0.016)
    lab[well] = "WheelWell"
    lamp = np.abs(body.headlight_region(x, y, z)) < 0.006
    lab[lamp & (body.headlight_region(x, y, z) > -0.02)] = "TrimDark"
    gr = body.grille_region(x, y, z)
    lab[np.abs(gr) < 0.006] = "TrimBlack"
    win = (np.abs(body.window_openings(x, y, z)) < 0.006) & (body.cab_outer(x, y, z) < -0.003)
    lab[win] = "TrimBlack"
    cav = np.abs(body.cabin_cavity(x, y, z)) < 0.010
    lab[cav] = "InteriorTrim"
    lab[cav & (n[:, 2] > 0.6) & (z < 0.78)] = "FloorRubber"
    lab[cav & (n[:, 2] < -0.5) & (z > 1.55)] = "Headliner"
    return lab


def door(c, n):
    x, y, z = _xyz(c)
    lab = np.full(len(c), "Paint", dtype=object)
    belt = Z_BELT_F + (Z_BELT_R - Z_BELT_F) * np.clip((Y_DOOR_F_FRONT - y) / (Y_DOOR_F_FRONT - Y_DOOR_R_BACK), 0, 1)
    out = n[:, 0] * np.sign(x) > 0.25
    sash = (z > belt + 0.006) & out
    lab[sash] = "TrimBlack"
    win = (np.abs(body.window_openings(x, y, z)) < 0.006) & (body.cab_outer(x, y, z) < -0.003)
    lab[win] = "TrimBlack"
    cav = np.abs(body.cabin_cavity(x, y, z)) < 0.010
    lab[cav] = "DoorTrim"
    return lab


def bed(c, n):
    x, y, z = _xyz(c)
    lab = np.full(len(c), "Paint", dtype=object)
    under = (n[:, 2] < -0.75) & (z < body.Z_BED_BOTTOM + 0.02)
    lab[under] = "Underbody"
    arch = body.arch_cut(x, y, z, Y_REAR_AXLE, inner=body.BED_WELL_INNER)
    well = (arch < 0.008) & (np.abs(x) < body.w_base(z) - 0.016)
    lab[well] = "WheelWell"
    tail = np.abs(body.tail_light_region(x, y, z)) < 0.006
    lab[tail] = "TrimBlack"
    cav = np.abs(body.bed_cavity(x, y, z)) < 0.008
    lab[cav] = "Bedliner"
    return lab


def tailgate(c, n):
    x, y, z = _xyz(c)
    lab = np.full(len(c), "Paint", dtype=object)
    cav = np.abs(body.bed_cavity(x, y, z)) < 0.008
    lab[cav] = "Bedliner"
    pocket = body.tailgate_handle_pocket(x, y, z) < 0.004
    lab[pocket] = "TrimBlack"
    return lab
