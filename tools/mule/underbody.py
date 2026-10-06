"""Underbody: only what shows from normal camera angles (frame rails, axles,
diffs, springs, shocks, fuel tank, exhaust, hitch). Kept deliberately simple.
"""

import numpy as np

from dims import *  # noqa: F401,F403
from sdf import box, capsule, ellipsoid, union
from spec import Part

DEPS = ("underbody",)


def chassis(x, y, z):
    ax = np.abs(x)
    rails = box(ax, y, z, (0.440, -0.20, 0.455), (0.035, 2.45, 0.075), 0.012)
    cross = None
    for yc in (2.05, 0.95, -0.30, -1.20, -2.05, -2.62):
        c = box(x, y, z, (0.0, yc, 0.440), (0.41, 0.035, 0.040), 0.010)
        cross = c if cross is None else np.minimum(cross, c)
    # front suspension arms and steering
    arms = None
    for yy in (1.42, 1.66):
        a = capsule(ax, y, z, (0.42, yy, 0.330), (0.66, Y_FRONT_AXLE, 0.330), 0.020)
        arms = a if arms is None else np.minimum(arms, a)
    upper = capsule(ax, y, z, (0.46, 1.50, 0.56), (0.64, Y_FRONT_AXLE, 0.52), 0.016)
    tie = capsule(x, y, z, (-0.66, 1.36, 0.36), (0.66, 1.36, 0.36), 0.013)
    cv = capsule(ax, y, z, (0.12, Y_FRONT_AXLE, 0.37), (0.66, Y_FRONT_AXLE, AXLE_Z), 0.024)
    fdiff = ellipsoid(x, y, z, (0.05, Y_FRONT_AXLE - 0.02, 0.37), (0.14, 0.13, 0.10))
    fshock = capsule(ax, y, z, (0.60, Y_FRONT_AXLE - 0.06, 0.42), (0.55, Y_FRONT_AXLE - 0.02, 0.84), 0.032)
    # rear live axle on leaf springs
    raxle = capsule(x, y, z, (-0.68, Y_REAR_AXLE, AXLE_Z), (0.68, Y_REAR_AXLE, AXLE_Z), 0.042)
    rdiff = ellipsoid(x, y, z, (0.06, Y_REAR_AXLE + 0.02, AXLE_Z), (0.16, 0.15, 0.15))
    leaf = None
    pts = [(-0.95, 0.47), (-1.25, 0.37), (-1.55, 0.345), (-1.85, 0.37), (-2.20, 0.47)]
    for (y0, z0), (y1, z1) in zip(pts[:-1], pts[1:]):
        seg = capsule(ax, y, z, (0.50, y0, z0), (0.50, y1, z1), 0.022)
        leaf = seg if leaf is None else np.minimum(leaf, seg)
    rshock = capsule(ax, y, z, (0.56, Y_REAR_AXLE - 0.12, 0.40), (0.50, Y_REAR_AXLE - 0.30, 0.62), 0.024)
    # drivetrain
    gearbox = box(x, y, z, (0.0, 0.80, 0.470), (0.15, 0.45, 0.085), 0.05)
    sump = box(x, y, z, (0.0, 1.75, 0.470), (0.24, 0.36, 0.075), 0.04)
    rshaft = capsule(x, y, z, (0.02, 0.32, 0.43), (0.06, Y_REAR_AXLE + 0.14, 0.40), 0.034)
    fshaft = capsule(x, y, z, (0.02, 0.62, 0.42), (0.05, Y_FRONT_AXLE - 0.16, 0.37), 0.028)
    tank = box(x, y, z, (-0.640, -0.62, 0.430), (0.150, 0.32, 0.085), 0.03)
    return union(rails, cross, arms, upper, tie, cv, fdiff, fshock, raxle, rdiff, leaf, rshock,
                 gearbox, sump, rshaft, fshaft, tank)


def exhaust(x, y, z):
    pts = [(0.18, 1.05, 0.42), (0.26, 0.30, 0.39), (0.28, -0.20, 0.39)]
    d = None
    for a, b in zip(pts[:-1], pts[1:]):
        c = capsule(x, y, z, a, b, 0.030)
        d = c if d is None else np.minimum(d, c)
    muffler = ellipsoid(x, y, z, (0.28, -0.55, 0.40), (0.11, 0.33, 0.085))
    tail = [(0.28, -0.85, 0.40), (0.30, -1.20, 0.42), (0.36, -1.95, 0.42), (0.58, -2.12, 0.43)]
    for a, b in zip(tail[:-1], tail[1:]):
        d = np.minimum(d, capsule(x, y, z, a, b, 0.027))
    tip = capsule(x, y, z, (0.58, -2.12, 0.43), (0.66, -2.17, 0.43), 0.034)
    hitch = box(x, y, z, (0.0, -2.78, 0.452), (0.032, 0.11, 0.032), 0.006)
    return union(d, muffler, tip, hitch)


def parts():
    a = dict(deps=DEPS, group="Underbody")
    return [
        Part("Underbody_Chassis", chassis, (-0.82, -2.75, 0.22), (0.82, 2.65, 0.92), 0.007, 1800, "Underbody", **a),
        Part("Exhaust", exhaust, (0.10, -2.93, 0.32), (0.72, 1.12, 0.50), 0.004, 500, "Gunmetal", **a),
    ]
