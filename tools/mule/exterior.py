"""Exterior detail parts: bumpers, grille, lights, mirrors, handles, wipers,
mud flaps. Parts that come in pairs are built for the right side (+X) and
mirrored by the builder.
"""

import numpy as np

import body
from body import GRILLE_POLY, HANDLES, HEAD_POLY, arch_cut, flare, front_y, panel_piece, w_base
from dims import *  # noqa: F401,F403
from sdf import (F, box, box2, capsule, circle2, fillet_polygon, inter, inter_round, poly2,
                 smooth_interp, smoothstep, sphere, sub, sub_round, union, union_round)
from spec import Part

DEPS = ("body", "exterior")

# ------------------------------------------------------------------ front bumper

_BX = [0.0, 0.30, 0.50, 0.62, 0.72, 0.80, 0.86, 0.92]
_BD = [0.0, 0.008, 0.026, 0.052, 0.092, 0.142, 0.198, 0.285]


def bumper_face_y(x, z):
    back = smooth_interp(np.abs(x), _BX, _BD)
    under = F(0.018) * smoothstep(0.60, 0.50, z) + F(0.055) * smoothstep(0.455, 0.405, z)
    return F(Y_NOSE) - back - under


def bumper_outer(x, y, z):
    ax = np.abs(x)
    front = (y - bumper_face_y(x, z)) * F(0.8)
    side = ax - (w_base(z) + flare(y, z, Y_FRONT_AXLE) + F(0.004))
    top = z - body.bumper_top(x)
    bot = F(0.405) + F(0.06) * smoothstep(0.55, 0.92, ax) - z
    d = inter_round(front, side, 0.045)
    d = inter_round(d, top, 0.022)
    d = inter_round(d, bot, 0.03)
    d = np.maximum(d, F(Y_FRONT_AXLE + 0.30) - y)
    d = sub_round(d, arch_cut(x, y, z, Y_FRONT_AXLE, inner=0.45), 0.008)
    return d


INTAKE_POLY = fillet_polygon([(-0.40, 0.605), (0.40, 0.605), (0.33, 0.462), (-0.33, 0.462)], 0.03)
FOG_POLY = fillet_polygon([(0.590, 0.505), (0.652, 0.862), (0.800, 0.886), (0.890, 0.846),
                           (0.890, 0.545), (0.700, 0.482)], [0.03, 0.05, 0.04, 0.04, 0.04, 0.04])
FOG_C = (0.752, 0.640)
FOG_R = 0.040


def fog_region(x, y, z):
    d2 = poly2(np.abs(x), z, FOG_POLY)
    return np.maximum(d2, (bumper_face_y(x, z) - F(0.035)) - y)


def bumper_solid(x, y, z):
    o = bumper_outer(x, y, z)
    d = np.maximum(o, F(2.06) - y - F(0.25) * smoothstep(0.55, 0.90, np.abs(x)))
    d = sub_round(d, body.grille_region(x, y, z), 0.004)
    intake = np.maximum(poly2(x, z, INTAKE_POLY), F(2.2) - y)
    d = sub_round(d, intake, 0.006)
    d = sub(d, fog_region(x, y, z))
    return d


def _lower_region(x, y, z):
    return z - F(0.618)


_bl_piece, _bl_hole = panel_piece(bumper_solid, _lower_region, 0.6, gap=0.004)


def bumper_upper(x, y, z):
    s = bumper_solid(x, y, z)
    return np.maximum(s, -_bl_hole(x, y, z, s))


def bumper_lower(x, y, z):
    return _bl_piece(x, y, z)


def fog_bezel(x, y, z):
    ax = np.abs(x)
    d = inter(bumper_outer(x, y, z) + F(0.007), poly2(ax, z, FOG_POLY) + F(0.002),
              (bumper_face_y(x, z) - F(0.06)) - y)
    pocket = circle2(ax, z, FOG_C, FOG_R + 0.006)
    d = np.maximum(d, -np.maximum(pocket, (bumper_face_y(x, z) - F(0.03)) - y))
    return d


def fog_lamp(x, y, z):
    ax = np.abs(x)
    yf = bumper_face_y(F(FOG_C[0]), F(FOG_C[1]))
    disc = np.maximum(circle2(ax, z, FOG_C, FOG_R), np.abs(y - (yf - F(0.026))) - F(0.010))
    return disc


def skid_plate(x, y, z):
    yb = bumper_face_y(x, F(0.43))
    plate = box(x, y, z, (0.0, 2.25, 0.418), (0.40, 0.20, 0.012), 0.008)
    plate = np.maximum(plate, y - (yb + F(0.004)))
    front = box(x, y, z, (0.0, 0.0, 0.448), (0.34, 1.0, 0.034), 0.01)
    lip = np.maximum(front, np.abs(y - (bumper_face_y(x, F(0.45)) + F(0.002))) - F(0.008))
    return np.minimum(plate, lip)


def bumper_classes(c, n):
    x, y, z = c[:, 0].astype(np.float32), c[:, 1].astype(np.float32), c[:, 2].astype(np.float32)
    lab = np.full(len(c), "Paint", dtype=object)
    arch = arch_cut(x, y, z, Y_FRONT_AXLE, inner=0.45)
    lab[(arch < 0.008) & (np.abs(x) < w_base(z) - 0.012)] = "WheelWell"
    return lab


# ------------------------------------------------------------------ grille

def grille_front_y(x):
    return F(Y_HOOD_FRONT + 0.014) - smooth_interp(np.abs(x), body._FX, body._FD)


def grille(x, y, z):
    d2 = poly2(x, z, GRILLE_POLY)
    yf = grille_front_y(x)
    dy = y - yf
    # thick surround
    ring = np.maximum(d2, -(d2 + F(0.048)))
    frame = inter_round(ring, dy, 0.012)
    frame = np.maximum(frame, -(dy + F(0.075)))
    inner = d2 + F(0.040)
    # horizontal slats with a downward rake
    u = np.mod(z - F(0.690), F(0.044)) - F(0.022)
    slats = box2(u + dy * F(0.35), dy, (0.0, -0.034), (0.0085, 0.020), 0.005)
    # vertical struts
    u2 = np.mod(x + F(0.0875), F(0.175)) - F(0.0875)
    struts = box2(u2, dy, (0.0, -0.040), (0.007, 0.022), 0.004)
    midbar = box2(z, dy, (0.915, -0.016), (0.024, 0.014), 0.010)
    fill = np.maximum(union(slats, struts, midbar), inner)
    back = np.maximum(d2 + F(0.01), np.abs(dy + F(0.068)) - F(0.006))
    return union(frame, fill, back)


def badge(x, y, z):
    yf = grille_front_y(F(0.0))
    e = np.sqrt((x / F(0.068)) ** 2 + ((z - F(0.915)) / F(0.044)) ** 2) - F(1.0)
    e = e * F(0.05)
    dy = y - (yf + F(0.004))
    disc = inter_round(e, np.abs(dy) - F(0.006), 0.003)
    ring = np.abs(e + F(0.009)) - F(0.0035)
    ring = np.maximum(ring, np.abs(dy - F(0.004)) - F(0.004))
    return union(disc, ring)


# ------------------------------------------------------------------ headlights

def _dd(x, y, z):
    """Depth below the nose surface (0 at the surface, negative inwards)."""
    return y - front_y(x, z)


LAMP_A = (0.585, 1.010, 0.037)  # (|x|, z, r) projector
LAMP_B = (0.706, 1.024, 0.035)  # high beam reflector


def head_lens(x, y, z):
    o = body.cab_outer(x, y, z)
    lens = inter(o + F(0.0015), -(o + F(0.0065)), poly2(np.abs(x), z, HEAD_POLY) + F(0.002))
    ax = np.abs(x)
    dd = _dd(x, y, z)
    proj = np.sqrt((ax - F(LAMP_A[0])) ** 2 + (dd + F(0.052)) ** 2 + (z - F(LAMP_A[1])) ** 2) - F(0.019)
    return union(lens, proj)


def _cups(ax, dd, z, extra=0.0):
    a = np.sqrt((ax - F(LAMP_A[0])) ** 2 + (dd + F(0.040)) ** 2 + (z - F(LAMP_A[1])) ** 2) - F(LAMP_A[2] + extra)
    b = np.sqrt((ax - F(LAMP_B[0])) ** 2 + (dd + F(0.040)) ** 2 + (z - F(LAMP_B[1])) ** 2) - F(LAMP_B[2] + extra)
    return np.minimum(a, b)


def head_housing(x, y, z):
    ax = np.abs(x)
    dd = _dd(x, y, z)
    d = inter(poly2(ax, z, HEAD_POLY) + F(0.001), dd + F(0.040), -(dd + F(0.080)))
    return np.maximum(d, -_cups(ax, dd, z, 0.004))


def head_reflector(x, y, z):
    ax = np.abs(x)
    dd = _dd(x, y, z)
    cups = np.maximum(np.abs(_cups(ax, dd, z, 0.0025)) - F(0.0015), dd + F(0.041))
    trim = capsule(ax, dd, z, (0.505, -0.036, 1.064), (0.835, -0.036, 1.066), 0.0045)
    bulb = np.sqrt((ax - F(LAMP_B[0])) ** 2 + (dd + F(0.055)) ** 2 + (z - F(LAMP_B[1])) ** 2) - F(0.010)
    return union(cups, trim, bulb)


def head_drl(x, y, z):
    ax = np.abs(x)
    dd = _dd(x, y, z)
    a = capsule(ax, dd, z, (0.520, -0.022, 0.945), (0.770, -0.020, 0.976), 0.0058)
    b = capsule(ax, dd, z, (0.770, -0.020, 0.976), (0.878, -0.020, 1.004), 0.0058)
    return np.minimum(a, b)


def head_indicator(x, y, z):
    ax = np.abs(x)
    dd = _dd(x, y, z)
    return inter(poly2(ax, z, HEAD_POLY) + F(0.004), F(0.835) - ax, dd + F(0.020), -(dd + F(0.042)))


# ------------------------------------------------------------------ tail lights

def _tail_block(x, y, z):
    ax = np.abs(x)
    reg = box2(ax, z, (0.845, 1.045), (0.068, 0.205), 0.03)
    return inter(body.bed_outer(x, y, z) - F(0.002), reg + F(0.0015), y - F(Y_BED_BACK + 0.058))


def tail_band(z0, z1):
    def f(x, y, z):
        return np.maximum(_tail_block(x, y, z), np.maximum(F(z0) - z, z - F(z1)))
    return f


# ------------------------------------------------------------------ rear bumper

RB_Y0 = Y_BED_BACK + 0.10
RB_Z = (0.470, 0.688)
PLATE_REAR_C = (0.0, Y_TAIL, 0.574)
PLATE_HALF = (0.180, 0.090)


def rear_bumper_outer(x, y, z):
    yc = (RB_Y0 + Y_TAIL) / 2
    d2 = box2(x, y, (0.0, yc), (0.862, (RB_Y0 - Y_TAIL) / 2), 0.11)
    zc = (RB_Z[0] + RB_Z[1]) / 2
    return inter_round(d2, np.abs(z - F(zc)) - F((RB_Z[1] - RB_Z[0]) / 2), 0.022)


def rear_bumper_solid(x, y, z):
    d = rear_bumper_outer(x, y, z)
    step = box(x, y, z, (0.0, Y_TAIL + 0.075, RB_Z[1]), (0.33, 0.085, 0.010), 0.006)
    d = sub_round(d, step, 0.004)
    plate = box(x, y, z, (0.0, Y_TAIL, PLATE_REAR_C[2]), (PLATE_HALF[0] + 0.014, 0.014, PLATE_HALF[1] + 0.009), 0.012)
    d = sub_round(d, plate, 0.004)
    return d


def _cap_region(x, y, z):
    return F(0.735) - np.abs(x)


_rc_piece, _rc_hole = panel_piece(rear_bumper_solid, _cap_region, 0.6, gap=0.004)


def rear_bumper_main(x, y, z):
    s = rear_bumper_solid(x, y, z)
    return np.maximum(s, -_rc_hole(x, y, z, s))


def rear_bumper_caps(x, y, z):
    return _rc_piece(x, y, z)


def rear_step_pad(x, y, z):
    pad = box(x, y, z, (0.0, Y_TAIL + 0.075, RB_Z[1] - 0.008), (0.322, 0.078, 0.006), 0.004)
    u = np.mod(y - F(Y_TAIL), F(0.026)) - F(0.013)
    ribs = np.maximum(box2(u, z, (0.0, RB_Z[1] - 0.001), (0.004, 0.004), 0.003), np.abs(x) - F(0.30))
    ribs = np.maximum(ribs, np.abs(y - F(Y_TAIL + 0.075)) - F(0.068))
    return union(pad, ribs)


def plate_lamp(x, y, z):
    return box(x, y, z, (0.0, Y_TAIL + 0.022, RB_Z[1] - 0.030), (0.045, 0.012, 0.010), 0.005)


# ------------------------------------------------------------------ mirrors

MIRROR_HEAD = (1.000, 0.645, 1.372)


def mirror_housing(x, y, z):
    head = box(x, y, z, MIRROR_HEAD, (0.108, 0.052, 0.079), 0.034)
    # taper the outboard end and round the front
    head = np.maximum(head, (y - F(MIRROR_HEAD[1])) * F(0.9) + (x - F(1.06)) * F(0.45) - F(0.03))
    arm = box(x, y, z, (0.905, 0.655, 1.338), (0.060, 0.034, 0.026), 0.018)
    base = box(x, y, z, (0.868, 0.660, 1.330), (0.020, 0.075, 0.042), 0.015)
    d = union_round(union_round(head, arm, 0.025), base, 0.015)
    glass_pocket = box(x, y, z, (MIRROR_HEAD[0], MIRROR_HEAD[1] - 0.052, MIRROR_HEAD[2]), (0.090, 0.012, 0.062), 0.016)
    return sub_round(d, glass_pocket, 0.004)


def mirror_glass(x, y, z):
    return box(x, y, z, (MIRROR_HEAD[0], MIRROR_HEAD[1] - 0.052 + 0.006, MIRROR_HEAD[2]), (0.088, 0.003, 0.060), 0.015)


# ------------------------------------------------------------------ small parts

def door_handles(x, y, z):
    d = None
    for yc, zc in HANDLES:
        h = box(x, y, z, (0.906, yc, zc), (0.012, 0.080, 0.0155), 0.0115)
        d = h if d is None else np.minimum(d, h)
    return d


def tailgate_handle(x, y, z):
    return box(x, y, z, (0.0, Y_BED_BACK + 0.004, 1.215), (0.095, 0.012, 0.020), 0.010)


def _ws_point(xx, v, off):
    """A point on the windshield (x, distance v up the glass) pushed out by off."""
    yb = Y_WS_BASE - body.WS_WRAP * xx * xx
    run, rise, L = body.WS_RUN, body.WS_RISE, body.WS_L
    y = yb - v * run / L + off * rise / L
    z = Z_WS_BASE + v * rise / L + off * run / L
    return (xx, y, z)


def wipers(x, y, z):
    d = None
    for x0, x1 in ((-0.56, 0.02), (0.06, 0.62)):
        pivot = _ws_point(x0 + 0.03, -0.035, 0.022)
        tip = _ws_point(x1 - 0.06, 0.050, 0.020)
        arm = capsule(x, y, z, pivot, tip, 0.0075)
        b0 = _ws_point(x0, 0.058, 0.012)
        b1 = _ws_point(x1, 0.048, 0.012)
        blade = capsule(x, y, z, b0, b1, 0.0075)
        cap = sphere(x, y, z, pivot, 0.017)
        w = union(arm, blade, cap)
        d = w if d is None else np.minimum(d, w)
    return d


def mud_flap(yc, z0, z1, x0, x1):
    def f(x, y, z):
        t = np.clip((F(z1) - z) / F(z1 - z0), 0, 1)
        yy = y - (F(yc) - F(0.025) * t * t)
        return box(x, yy, z, ((x0 + x1) / 2, 0.0, (z0 + z1) / 2), ((x1 - x0) / 2, 0.004, (z1 - z0) / 2), 0.004)
    return f


# ------------------------------------------------------------------ part list

def parts():
    P = []
    a = dict(deps=DEPS)
    P += [
        Part("Bumper_Front", bumper_upper, (-0.98, 1.80, 0.36), (0.98, 2.49, 1.03), 0.004, 3200, bumper_classes, group="Body", **a),
        Part("SkidPlate", skid_plate, (-0.44, 2.02, 0.39), (0.44, 2.47, 0.49), 0.003, 500, "Gunmetal", group="Body", **a),
        Part("Bumper_Front_Lower", bumper_lower, (-0.98, 1.80, 0.36), (0.98, 2.49, 0.66), 0.004, 1600, "TrimBlack", group="Body", **a),
        Part("FogBezel_R", fog_bezel, (0.55, 1.95, 0.44), (0.95, 2.45, 0.92), 0.003, 650, "TrimBlack", group="Lights", mirror=True, **a),
        Part("FogLamp_R", fog_lamp, (0.68, 2.20, 0.57), (0.82, 2.45, 0.71), 0.0025, 260, "LensWhite", group="Lights", mirror=True, **a),
        Part("Grille", grille, (-0.52, 2.27, 0.64), (0.52, 2.47, 1.10), 0.0025, 3000, "TrimDark", group="Body", sharp=40, **a),
        Part("Badge_Front", badge, (-0.09, 2.42, 0.86), (0.09, 2.47, 0.97), 0.0015, 500, "Chrome", group="Body", **a),
        Part("Headlight_Lens_R", head_lens, (0.45, 2.10, 0.90), (0.95, 2.46, 1.10), 0.0025, 700, "LensClear", group="Lights", mirror=True, **a),
        Part("Headlight_Housing_R", head_housing, (0.45, 2.05, 0.90), (0.95, 2.44, 1.10), 0.003, 600, "Gunmetal", group="Lights", mirror=True, **a),
        Part("Headlight_Reflector_R", head_reflector, (0.47, 2.05, 0.92), (0.92, 2.44, 1.09), 0.002, 600, "Chrome", group="Lights", mirror=True, **a),
        Part("Headlight_DRL_R", head_drl, (0.49, 2.05, 0.92), (0.92, 2.45, 1.04), 0.002, 300, "LightDRL", group="Lights", mirror=True, **a),
        Part("Headlight_Indicator_R", head_indicator, (0.80, 2.05, 0.95), (0.95, 2.30, 1.10), 0.0025, 200, "LensAmber", group="Lights", mirror=True, **a),
        Part("TailLight_Brake_R", tail_band(1.012, 1.30), (0.74, -2.80, 0.80), (0.95, -2.68, 1.30), 0.003, 420, "LensRed", group="Lights", mirror=True, **a),
        Part("TailLight_Reverse_R", tail_band(0.934, 1.008), (0.74, -2.80, 0.80), (0.95, -2.68, 1.30), 0.003, 160, "LensWhite", group="Lights", mirror=True, **a),
        Part("TailLight_Turn_R", tail_band(0.80, 0.930), (0.74, -2.80, 0.80), (0.95, -2.68, 1.30), 0.003, 260, "LensAmber", group="Lights", mirror=True, **a),
        Part("Bumper_Rear", rear_bumper_main, (-0.92, -2.88, 0.43), (0.92, -2.62, 0.73), 0.004, 1800, "Gunmetal", group="Body", **a),
        Part("Bumper_Rear_Caps", rear_bumper_caps, (-0.92, -2.88, 0.43), (0.92, -2.62, 0.73), 0.004, 700, "TrimBlack", group="Body", **a),
        Part("Bumper_Rear_Step", rear_step_pad, (-0.36, -2.86, 0.66), (0.36, -2.65, 0.70), 0.002, 400, "Rubber", group="Body", **a),
        Part("PlateLamp", plate_lamp, (-0.07, -2.85, 0.63), (0.07, -2.78, 0.68), 0.002, 120, "LensWhite", group="Lights", **a),
        Part("Mirror_R", mirror_housing, (0.82, 0.55, 1.26), (1.14, 0.75, 1.48), 0.003, 800, "TrimBlack", group="Body", mirror=True, **a),
        Part("Mirror_Glass_R", mirror_glass, (0.88, 0.57, 1.29), (1.12, 0.62, 1.45), 0.002, 80, "MirrorGlass", group="Body", mirror=True, **a),
        Part("DoorHandles_R", door_handles, (0.87, -1.02, 1.07), (0.95, -0.11, 1.16), 0.002, 300, "TrimBlack", group="Body", mirror=True, **a),
        Part("Tailgate_Handle", tailgate_handle, (-0.12, -2.80, 1.18), (0.12, -2.75, 1.25), 0.002, 150, "TrimBlack", group="Body", **a),
        Part("Wipers", wipers, (-0.66, 0.70, 1.20), (0.72, 0.90, 1.34), 0.002, 420, "TrimBlack", group="Body", **a),
        Part("MudFlap_FR", mud_flap(Y_FRONT_AXLE - 0.545, 0.30, 0.50, 0.700, 0.890), (0.68, 0.90, 0.27), (0.91, 1.05, 0.53), 0.002, 120, "Rubber", group="Body", mirror=True, **a),
        Part("MudFlap_RR", mud_flap(Y_REAR_AXLE - 0.548, 0.32, 0.615, 0.705, 0.895), (0.68, -2.14, 0.29), (0.92, -2.04, 0.64), 0.002, 120, "Rubber", group="Body", mirror=True, **a),
    ]
    return P
