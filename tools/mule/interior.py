"""Interior: a plain, mass-produced pickup cabin with four Roblox seats.

Seat geometry is laid out around seated R15 characters at 4 studs/metre:
hips 0.125 m above the cushion, head top about 0.93 m above it, knees about
0.56 m ahead of the seat back. See dims.py for the shared stations.
"""

import math

import numpy as np

import body
from dims import *  # noqa: F401,F403
from sdf import (F, box, box2, capsule, cyl_axis, ellipsoid, fillet_polygon, inter, inter_round,
                 poly2, sphere, sub, sub_round, union, union_round)
from spec import Part

DEPS = ("body", "interior")
SX = SEAT_X


def rot(a, b, ca, cb, ang):
    """Rotate the (a, b) plane by -ang around (ca, cb): returns local coordinates."""
    c, s = F(math.cos(ang)), F(math.sin(ang))
    da, db = a - F(ca), b - F(cb)
    return da * c + db * s, -da * s + db * c


# ------------------------------------------------------------------ seats

REC = math.radians(8)   # front seat back recline


def front_seat(x, y, z):
    # cushion, tilted up 4 degrees at the front, with side bolsters
    zz = z - F(0.035) * (y + F(0.33)) / F(0.54)
    cush = box(x, y, zz, (SX, -0.060, 0.712), (0.250, 0.272, 0.062), 0.045)
    bol = np.minimum(capsule(x, y, zz, (SX - 0.216, -0.30, 0.770), (SX - 0.216, 0.15, 0.770), 0.034),
                     capsule(x, y, zz, (SX + 0.216, -0.30, 0.770), (SX + 0.216, 0.15, 0.770), 0.034))
    cush = union_round(cush, bol, 0.03)
    # seat back reclined around its lower front edge
    yl, zl = rot(y, z, -0.270, 0.790, -REC)
    back = box(x, yl, zl, (SX, -0.052, 0.335), (0.245, 0.050, 0.335), 0.045)
    sbol = np.minimum(capsule(x, yl, zl, (SX - 0.205, -0.020, 0.06), (SX - 0.213, -0.020, 0.56), 0.040),
                      capsule(x, yl, zl, (SX + 0.205, -0.020, 0.06), (SX + 0.213, -0.020, 0.56), 0.040))
    back = union_round(back, sbol, 0.035)
    head = box(x, yl, zl, (SX, -0.072, 0.795), (0.130, 0.046, 0.088), 0.040)
    posts = np.minimum(capsule(x, yl, zl, (SX - 0.07, -0.072, 0.64), (SX - 0.07, -0.072, 0.72), 0.009),
                       capsule(x, yl, zl, (SX + 0.07, -0.072, 0.64), (SX + 0.07, -0.072, 0.72), 0.009))
    return union(union_round(cush, back, 0.04), head, posts)


def front_seat_base(x, y, z):
    base = box(x, y, z, (SX, -0.06, 0.600), (0.190, 0.235, 0.075), 0.02)
    cover = box(x, y, z, (SX + 0.262, -0.255, 0.705), (0.014, 0.095, 0.058), 0.012)
    return union(base, cover)


REAR_REC = math.radians(5)


def rear_bench(x, y, z):
    ax = np.abs(x)
    cush = box(x, y, z, (0.0, -0.760, 0.690), (0.775, 0.262, 0.075), 0.045)
    # two contoured seat pans with a flatter centre section
    pan = box(ax, y, z, (SX, -0.70, 0.778), (0.20, 0.17, 0.025), 0.02)
    cush = sub_round(cush, pan, 0.03)
    riser = box(x, y, z, (0.0, -0.80, 0.580), (0.76, 0.22, 0.060), 0.015)
    yl, zl = rot(y, z, -0.950, 0.770, -REAR_REC)
    back = box(x, yl, zl, (0.0, -0.045, 0.300), (0.775, 0.045, 0.310), 0.040)
    pad = box(ax, yl, zl, (SX, 0.0, 0.29), (0.20, 0.012, 0.24), 0.012)
    back = union_round(back, pad, 0.02)
    heads = box(ax, y, z, (SX, -1.002, 1.470), (0.118, 0.021, 0.072), 0.020)
    return union(union_round(cush, back, 0.04), riser, heads)


# ------------------------------------------------------------------ dashboard

DASH_PROFILE = fillet_polygon(
    [(0.95, 1.32), (0.50, 1.150), (0.455, 1.128), (0.445, 1.080), (0.470, 0.960),
     (0.530, 0.840), (0.630, 0.700), (0.95, 0.600)],
    [0.0, 0.06, 0.02, 0.03, 0.08, 0.06, 0.06, 0.0])

GLOVE = ((0.20, 0.62), (0.860, 1.000))
CLUSTER = (-SX, 1.078)


def _dash_raw(x, y, z):
    d2 = poly2(y, z, DASH_PROFILE)
    d = inter_round(d2, np.abs(x) - F(0.80), 0.02)
    bin_ = box(x, y, z, (-SX, 0.545, 1.168), (0.205, 0.100, 0.056), 0.050)
    d = union_round(d, bin_, 0.025)
    stack = box(x, y, z, (0.0, 0.505, 0.910), (0.150, 0.085, 0.205), 0.040)
    d = union_round(d, stack, 0.03)
    # the dash fills the front of the cabin cavity and stops at its walls
    d = np.maximum(d, body.cabin_cavity(x, y, z) - F(0.012))
    return d


def _dash_cuts(x, y, z):
    ax = np.abs(x)
    cluster = box(x, y, z, (CLUSTER[0], 0.440, CLUSTER[1]), (0.168, 0.085, 0.060), 0.030)
    screen = box(x, y, z, (0.0, 0.422, 1.075), (0.112, 0.012, 0.060), 0.010)
    cvent = box(ax, y, z, (0.075, 0.420, 0.965), (0.055, 0.030, 0.024), 0.010)
    ovent = cyl_axis(ax, z, y, 0.690, 1.060, 0.046, 0.30, 0.56, 0.004)
    return union(cluster, screen, cvent, ovent)


def glove_region(x, y, z):
    d2 = box2(x, z, ((GLOVE[0][0] + GLOVE[0][1]) / 2, (GLOVE[1][0] + GLOVE[1][1]) / 2),
              ((GLOVE[0][1] - GLOVE[0][0]) / 2, (GLOVE[1][1] - GLOVE[1][0]) / 2), 0.03)
    return np.maximum(d2, y - F(0.60))


def dash(x, y, z):
    d = sub_round(_dash_raw(x, y, z), _dash_cuts(x, y, z), 0.005)
    gl = np.maximum(glove_region(x, y, z) - F(0.002), -(_dash_raw(x, y, z) + F(0.05)))
    return np.maximum(d, -gl)


def glovebox(x, y, z):
    d = sub_round(_dash_raw(x, y, z), _dash_cuts(x, y, z), 0.005)
    return inter(d, glove_region(x, y, z) + F(0.002), -(_dash_raw(x, y, z) + F(0.045)))


def dash_vents(x, y, z):
    ax = np.abs(x)
    u = np.mod(z - F(0.9445), F(0.0205)) - F(0.01025)
    slats = inter(box2(u, y - F(0.432), (0.0, 0.0), (0.0040, 0.012), 0.003),
                  box(ax, y, z, (0.075, 0.432, 0.965), (0.052, 0.02, 0.022), 0.0))
    ring = np.maximum(np.abs(np.sqrt((ax - F(0.69)) ** 2 + (z - F(1.06)) ** 2) - F(0.039)) - F(0.006),
                      np.abs(y - F(0.468)) - F(0.010))
    bar = box(ax, y, z, (0.69, 0.470, 1.06), (0.040, 0.006, 0.006), 0.003)
    hub = cyl_axis(ax, z, y, 0.69, 1.06, 0.014, 0.455, 0.478, 0.003)
    latch = box(x, y, z, (0.41, 0.462, 0.978), (0.045, 0.008, 0.008), 0.004)
    return union(slats, ring, bar, hub, latch)


def gauges(x, y, z):
    out = None
    for dx in (-0.075, 0.075):
        g = cyl_axis(x, z, y, CLUSTER[0] + dx, CLUSTER[1], 0.056, 0.514, 0.528, 0.004)
        out = g if out is None else np.minimum(out, g)
    info = box(x, y, z, (CLUSTER[0], 0.524, CLUSTER[1]), (0.018, 0.004, 0.030), 0.003)
    return np.minimum(out, info)


def needles(x, y, z):
    out = None
    for dx, ang in ((-0.075, 2.2), (0.075, 2.6)):
        cx, cz = CLUSTER[0] + dx, CLUSTER[1]
        tip = (cx + 0.044 * math.cos(ang), 0.512, cz + 0.044 * math.sin(ang))
        n = capsule(x, y, z, (cx, 0.512, cz), tip, 0.0028)
        out = n if out is None else np.minimum(out, n)
    return out


def screen(x, y, z):
    return box(x, y, z, (0.0, 0.425, 1.075), (0.104, 0.006, 0.053), 0.006)


def controls(x, y, z):
    d = None
    for kx in (-0.075, 0.0, 0.075):
        k = cyl_axis(x, z, y, kx, 0.880, 0.022, 0.392, 0.428, 0.004)
        d = k if d is None else np.minimum(d, k)
    for i in range(6):
        b = box(x, y, z, (-0.0875 + i * 0.035, 0.418, 0.918), (0.013, 0.008, 0.008), 0.003)
        d = np.minimum(d, b)
    hazard = box(x, y, z, (0.0, 0.420, 1.005), (0.016, 0.008, 0.010), 0.003)
    return np.minimum(d, hazard)


# ------------------------------------------------------------------ steering

SW_C = (-SX, 0.215, 1.070)
SW_TILT = math.radians(24)
SW_R = 0.185


def _sw_local(x, y, z):
    n = (0.0, -math.cos(SW_TILT), math.sin(SW_TILT))       # towards the driver
    t = (0.0, math.sin(SW_TILT), math.cos(SW_TILT))        # wheel "up"
    px, py, pz = x - F(SW_C[0]), y - F(SW_C[1]), z - F(SW_C[2])
    u = px
    v = py * F(t[1]) + pz * F(t[2])
    w = py * F(n[1]) + pz * F(n[2])
    return u, v, w


def steering_wheel(x, y, z):
    u, v, w = _sw_local(x, y, z)
    q = np.sqrt(u * u + v * v) - F(SW_R)
    # slightly oval grip section
    rim = np.sqrt(q * q + (w * F(1.15)) ** 2) - F(0.0165)
    spoke_h = inter_round(np.abs(v + F(0.012)) - F(0.020), np.abs(w + F(0.010)) - F(0.011), 0.008)
    spoke_h = np.maximum(spoke_h, np.abs(u) - F(SW_R))
    spoke_v = inter_round(np.abs(u) - F(0.024), np.abs(w + F(0.010)) - F(0.011), 0.008)
    spoke_v = np.maximum(spoke_v, np.maximum(v + F(0.0), -v - F(SW_R)))
    hub = inter_round(np.sqrt(u * u + (v + F(0.005)) ** 2) - F(0.072), np.abs(w + F(0.006)) - F(0.026), 0.018)
    return union(union_round(union(spoke_h, spoke_v), rim, 0.012), hub)


def steering_column(x, y, z):
    n = np.array([0.0, -math.cos(SW_TILT), math.sin(SW_TILT)])
    a = np.array(SW_C) - n * 0.045
    b = np.array((-SX, 0.50, 0.950))
    col = capsule(x, y, z, a, b, 0.040)
    shroud = capsule(x, y, z, a - n * 0.04, b, 0.052)
    shroud = np.maximum(shroud, -(z - F(0.99)) - F(0.0))
    st1 = capsule(x, y, z, a - n * 0.05 + np.array([0.05, 0, 0]), a - n * 0.05 + np.array([0.16, -0.01, 0.02]), 0.008)
    st2 = capsule(x, y, z, a - n * 0.05 - np.array([0.05, 0, 0]), a - n * 0.05 - np.array([0.16, 0.01, -0.02]), 0.008)
    return union(col, shroud, st1, st2)


# ------------------------------------------------------------------ console

def console(x, y, z):
    base = box(x, y, z, (0.0, 0.090, 0.630), (0.105, 0.420, 0.105), 0.035)
    arm = box(x, y, z, (0.0, -0.205, 0.800), (0.098, 0.130, 0.062), 0.035)
    d = union_round(base, arm, 0.03)
    boot = cyl_axis(x, y, z, 0.0, 0.270, 0.060, 0.70, 0.78, 0.02)
    cups = np.minimum(cyl_axis(x, y, z, -0.046, 0.030, 0.034, 0.68, 0.80, 0.008),
                      cyl_axis(x, y, z, 0.046, 0.030, 0.034, 0.68, 0.80, 0.008))
    slot = box(x, y, z, (0.0, -0.005, 0.735), (0.022, 0.09, 0.02), 0.01)
    d = sub_round(d, union(boot, cups, slot), 0.006)
    dial = cyl_axis(x, y, z, 0.062, 0.395, 0.018, 0.728, 0.748, 0.004)
    return np.minimum(d, dial)


def gear_shifter(x, y, z):
    boot = ellipsoid(x, y, z, (0.0, 0.270, 0.722), (0.052, 0.052, 0.034))
    lever = capsule(x, y, z, (0.0, 0.270, 0.73), (0.0, 0.246, 0.925), 0.011)
    knob = sphere(x, y, z, (0.0, 0.243, 0.948), 0.030)
    return union(union_round(boot, lever, 0.01), knob)


def handbrake(x, y, z):
    lever = capsule(x, y, z, (0.0, 0.07, 0.738), (0.0, -0.085, 0.800), 0.017)
    grip = capsule(x, y, z, (0.0, -0.020, 0.775), (0.0, -0.105, 0.810), 0.021)
    button = capsule(x, y, z, (0.0, -0.105, 0.810), (0.0, -0.118, 0.815), 0.010)
    return union(union_round(lever, grip, 0.006), button)


def pedals(x, y, z):
    d = None
    for px, tall in ((-SX - 0.125, False), (-SX - 0.010, False), (-SX + 0.120, True)):
        arm = capsule(x, y, z, (px, 0.700, 0.900), (px, 0.598, 0.690), 0.010)
        if tall:
            pad = box(x, y, z, (px, 0.600, 0.668), (0.026, 0.010, 0.060), 0.008)
        else:
            pad = box(x, y, z, (px, 0.594, 0.672), (0.040, 0.011, 0.034), 0.010)
        p = union(arm, pad)
        d = p if d is None else np.minimum(d, p)
    return d


# ------------------------------------------------------------------ roof items

def rear_view_mirror(x, y, z):
    stem = capsule(x, y, z, (0.0, 0.110, 1.712), (0.0, 0.082, 1.672), 0.008)
    body_ = box(x, y, z, (0.0, 0.075, 1.660), (0.110, 0.018, 0.031), 0.016)
    pocket = box(x, y, z, (0.0, 0.056, 1.660), (0.100, 0.004, 0.023), 0.012)
    return union(stem, sub(body_, pocket))


def rear_view_glass(x, y, z):
    return box(x, y, z, (0.0, 0.059, 1.660), (0.098, 0.0025, 0.021), 0.011)


def sun_visor(x, y, z):
    yl, zl = rot(y, z, -0.04, 1.738, math.radians(-3))
    return box(x, yl, zl, (0.40, 0.0, 0.0), (0.170, 0.078, 0.012), 0.012)


def dome_light(x, y, z):
    return box(x, y, z, (0.0, -0.45, 1.752), (0.085, 0.048, 0.010), 0.008)


def inner_handles(x, y, z):
    d = None
    for yc, zc in body.INNER_HANDLES:
        h = box(x, y, z, (0.818, yc, zc), (0.010, 0.048, 0.010), 0.007)
        d = h if d is None else np.minimum(d, h)
    return d


# ------------------------------------------------------------------ part list

def parts():
    a = dict(deps=DEPS, group="Interior")
    return [
        Part("Seat_Front_R", front_seat, (0.06, -0.53, 0.60), (0.68, 0.30, 1.72), 0.004, 1600, "SeatFabric", mirror=True, **a),
        Part("Seat_Front_R_Base", front_seat_base, (0.13, -0.38, 0.51), (0.68, 0.21, 0.79), 0.005, 260, "InteriorTrim", mirror=True, **a),
        Part("Seat_Rear", rear_bench, (-0.81, -1.08, 0.50), (0.81, -0.46, 1.58), 0.005, 2300, "SeatFabric", **a),
        Part("Dashboard", dash, (-0.84, 0.36, 0.56), (0.84, 0.92, 1.34), 0.004, 2800, "Dash", **a),
        Part("Glovebox", glovebox, (0.17, 0.42, 0.83), (0.65, 0.62, 1.03), 0.003, 220, "Dash", **a),
        Part("Dash_Vents", dash_vents, (-0.75, 0.40, 0.93), (0.75, 0.50, 1.12), 0.0015, 700, "TrimBlack", **a),
        Part("Dash_Gauges", gauges, (-0.55, 0.49, 1.00), (-0.17, 0.54, 1.15), 0.002, 240, "Gauge", **a),
        Part("Dash_Needles", needles, (-0.49, 0.50, 1.07), (-0.23, 0.53, 1.13), 0.0015, 80, "LensAmber", **a),
        Part("Dash_Screen", screen, (-0.12, 0.41, 1.01), (0.12, 0.44, 1.14), 0.002, 60, "Screen", **a),
        Part("Dash_Controls", controls, (-0.12, 0.38, 0.85), (0.12, 0.44, 1.03), 0.002, 420, "TrimBlack", **a),
        Part("SteeringWheel", steering_wheel, (-0.58, 0.10, 0.84), (-0.14, 0.33, 1.29), 0.0025, 1400, "TrimBlack",
             origin=SW_C, **a),
        Part("SteeringColumn", steering_column, (-0.57, 0.14, 0.88), (-0.14, 0.56, 1.10), 0.003, 420, "TrimBlack", **a),
        Part("Console", console, (-0.14, -0.36, 0.50), (0.14, 0.53, 0.88), 0.004, 1100, "Dash", **a),
        Part("GearShifter", gear_shifter, (-0.07, 0.19, 0.68), (0.07, 0.33, 0.99), 0.002, 320, "TrimBlack", **a),
        Part("Handbrake", handbrake, (-0.04, -0.15, 0.70), (0.04, 0.10, 0.84), 0.002, 260, "TrimBlack", **a),
        Part("Pedals", pedals, (-0.55, 0.56, 0.60), (-0.20, 0.72, 0.92), 0.002, 360, "TrimBlack", **a),
        Part("RearViewMirror", rear_view_mirror, (-0.13, 0.04, 1.62), (0.13, 0.13, 1.73), 0.002, 220, "TrimBlack", **a),
        Part("RearViewMirror_Glass", rear_view_glass, (-0.11, 0.05, 1.63), (0.11, 0.07, 1.69), 0.0015, 60, "MirrorGlass", **a),
        Part("SunVisor_R", sun_visor, (0.21, -0.14, 1.70), (0.59, 0.06, 1.78), 0.003, 140, "DoorTrim", mirror=True, **a),
        Part("DomeLight", dome_light, (-0.11, -0.52, 1.73), (0.11, -0.38, 1.77), 0.002, 60, "LensWhite", **a),
        Part("Door_FR_InnerHandle", lambda x, y, z: np.where(y > -0.345, inner_handles(x, y, z), 1.0).astype(np.float32),
             (0.78, 0.49, 1.01), (0.85, 0.63, 1.08), 0.0015, 70, "MetalAccent", mirror=True, **a),
        Part("Door_RR_InnerHandle", lambda x, y, z: np.where(y < -0.345, inner_handles(x, y, z), 1.0).astype(np.float32),
             (0.78, -0.51, 1.02), (0.85, -0.37, 1.09), 0.0015, 70, "MetalAccent", mirror=True, **a),
    ]
