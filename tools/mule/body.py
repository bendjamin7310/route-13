"""Body shell of the Mule: cab (with fenders and greenhouse) and the bed.

Everything is an SDF built from smooth profiles. Panels (hood, doors,
tailgate, fuel door) are cut out of the same solid with real gaps, so
they line up exactly with the surrounding body.
"""

import numpy as np

from dims import *  # noqa: F401,F403
from sdf import (F, box, box2, fillet_polygon, inter, inter_round, poly2, smooth_interp,
                 smoothstep, sub, sub_round, union, union_round)

GAP = 0.005            # panel gap width
WALL_GH = 0.045        # greenhouse (pillar / roof) wall thickness
WALL_DOOR = 0.085      # door thickness at the trim panel

# ------------------------------------------------------------------ profiles

# Lower body half width against height (front view section). The side is
# the smooth minimum of a lower panel and an inward-leaning shoulder band,
# which leaves a soft character line at Z_CREASE (door handle height).
Z_CREASE = 1.125
_WZ = [0.40, 0.47, 0.53, 0.60, 0.72, 0.90, 1.05, 1.20, 1.40]
_WV = [0.822, 0.842, 0.866, 0.884, 0.897, 0.904, 0.906, 0.907, 0.908]


def w_base(z):
    low = smooth_interp(z, _WZ, _WV)
    shoulder = F(0.9065) - (z - F(Z_CREASE)) * F(0.20) - F(0.25) * np.maximum(z - F(1.24), 0) ** 2
    k = F(0.0035)
    h = np.clip(0.5 + 0.5 * (shoulder - low) / k, 0, 1)
    return shoulder + (low - shoulder) * h - k * h * (1 - h)


ARCH_A = 0.515      # half width of the wheel arch opening
ARCH_B = 0.505      # height of the opening above the axle
ARCH_N = 2.35       # superellipse exponent (squarer than a circle)
FLARE = 0.024       # how far the flare lip stands proud of the side
FLARE_W = 0.085     # width of the flare band


def arch_rho(y, z, yc):
    dy = np.abs(y - F(yc)) / F(ARCH_A)
    dz = np.maximum(z - F(AXLE_Z), 0) / F(ARCH_B)
    return (dy ** ARCH_N + dz ** ARCH_N) ** (1.0 / ARCH_N)


def flare(y, z, yc):
    e = (arch_rho(y, z, yc) - 1.0) * ARCH_A
    band = 1.0 - smoothstep(FLARE_W * 0.45, FLARE_W, e)
    fade = smoothstep(0.44, 0.60, z)  # flares die out at the very bottom
    return F(FLARE) * band * fade


def arch_cut(x, y, z, yc, inner=0.53):
    """Wheel-arch opening plus the wheel well behind it."""
    d2 = (arch_rho(y, z, yc) - 1.0) * F(ARCH_A)
    return np.maximum(d2, F(inner) - np.abs(x))


# Front of the cab body in top view: how far each |x| sits behind the nose
_FX = [0.0, 0.30, 0.50, 0.62, 0.72, 0.80, 0.86, 0.92]
_FD = [0.0, 0.010, 0.030, 0.058, 0.100, 0.150, 0.205, 0.290]


def front_y(x, z):
    ax = np.abs(x)
    back = smooth_interp(ax, _FX, _FD)
    y0 = F(Y_HOOD_FRONT + 0.012) - F(0.030) * smoothstep(1.02, 1.13, z)
    bt = bumper_top(x)
    y0 = y0 - F(0.24) * (1 - np.clip((z - (bt - F(0.07))) / F(0.074), 0, 1) ** 2 * (3 - 2 * np.clip((z - (bt - F(0.07))) / F(0.074), 0, 1)))
    return y0 - back


def hood_z(x, y):
    ax = np.abs(x)
    base = smooth_interp(y, [Y_COWL - 0.3, Y_COWL, 1.45, 2.05, Y_HOOD_FRONT], [1.236, 1.236, 1.208, 1.170, 1.128])
    # raised centre panel with crisp creases that narrow towards the windshield
    t = np.clip((y - F(Y_COWL)) / F(Y_HOOD_FRONT - Y_COWL), 0, 1)
    half = F(0.30) + F(0.11) * t
    bulge = F(0.026) * (1 - smoothstep(0.0, 0.035, ax - half)) * smoothstep(Y_HOOD_FRONT - 0.01, Y_HOOD_FRONT - 0.20, y)
    edge = -F(0.020) * smoothstep(0.48, 0.86, ax)
    return base + bulge + edge


def top_z(x, y):
    belt = F(Z_BELT_F) + F(Z_BELT_R - Z_BELT_F) * np.clip((F(Y_DOOR_F_FRONT) - y) / F(Y_DOOR_F_FRONT - Y_DOOR_R_BACK), 0, 1)
    t = smoothstep(Y_COWL - 0.10, Y_COWL + 0.03, y)
    return belt + (hood_z(x, y) - belt) * t


# ------------------------------------------------------------------ greenhouse

WS_RUN = Y_WS_BASE - Y_WS_TOP
WS_RISE = Z_WS_TOP - Z_WS_BASE
WS_L = float(np.hypot(WS_RUN, WS_RISE))
WS_WRAP = 0.16       # windshield wrap: corners sit further back by c * x^2
GH_BELT_W = 0.849    # greenhouse half width at the belt
GH_TUMBLE = 0.285    # inward lean per metre of height


def gh_w(z):
    return F(GH_BELT_W) - (z - F(Z_BELT_F)) * F(GH_TUMBLE)


def ws_plane(x, y, z):
    yb = F(Y_WS_BASE) - F(WS_WRAP) * x * x
    return ((y - yb) * F(WS_RISE) + (z - F(Z_WS_BASE)) * F(WS_RUN)) / F(WS_L)


def ws_v(x, y, z):
    """Distance along the windshield from its base towards the roof."""
    yb = F(Y_WS_BASE) - F(WS_WRAP) * x * x
    return ((yb - y) * F(WS_RUN) + (z - F(Z_WS_BASE)) * F(WS_RISE)) / F(WS_L)


RW_DY = Y_RW_TOP - Y_RW_BOT
RW_DZ = 1.765 - 1.300
RW_L = float(np.hypot(RW_DY, RW_DZ))


def rw_plane(x, y, z):
    yb = F(Y_RW_BOT) + F(0.035) * (x / F(0.7)) ** 2
    return (-(y - yb) * F(RW_DZ) + (z - F(1.300)) * F(RW_DY)) / F(RW_L)


def roof_z(x, y):
    return F(ROOF_Z) - F(0.026) * (x / F(0.72)) ** 2 - F(0.012) * ((y + F(0.50)) / F(0.62)) ** 2


def greenhouse(x, y, z):
    ax = np.abs(x)
    side = ax - gh_w(z)
    roof = z - roof_z(x, y)
    g = inter_round(side, roof, 0.065)
    g = inter_round(g, ws_plane(x, y, z), 0.055)
    g = inter_round(g, rw_plane(x, y, z), 0.045)
    return np.maximum(g, F(1.0) - z)


# ------------------------------------------------------------------ cab solid

def cab_outer(x, y, z):
    ax = np.abs(x)
    w = w_base(z) + flare(y, z, Y_FRONT_AXLE) + flare(y, z, Y_REAR_AXLE)
    side = ax - w
    top = z - top_z(x, y)
    d = inter_round(side, top, 0.042)
    fy = front_y(x, z)
    front = (y - fy) * F(0.8)
    d = inter_round(d, front, 0.045)
    d = inter_round(d, F(Z_SILL) - z, 0.025)
    d = inter_round(d, F(Y_CAB_BACK) - y, 0.045)
    d = union_round(d, greenhouse(x, y, z), 0.010)
    d = sub_round(d, arch_cut(x, y, z, Y_FRONT_AXLE), 0.010)
    d = sub_round(d, arch_cut(x, y, z, Y_REAR_AXLE, inner=0.55), 0.010)
    return d


def cabin_cavity(x, y, z):
    ax = np.abs(x)
    side = ax - (w_base(z) - F(WALL_DOOR))
    low = inter(side, F(Z_FLOOR_FRONT) - z, y - F(0.83), F(Y_CAB_BACK + 0.042) - y, z - F(1.18))
    gh = np.maximum(greenhouse(x, y, z) + F(WALL_GH), y - F(0.84))
    cav = union_round(low, gh, 0.03)
    # keep a wall around the rear wheel well that pokes into the cab corner
    cav = np.maximum(cav, F(0.03) - arch_cut(x, y, z, Y_REAR_AXLE, inner=0.52))
    # transmission tunnel and a raised rear floor step under the bench
    tunnel = box(x, y, z, (0, 0.30, 0.50), (0.15, 0.55, 0.16), 0.06)
    cav = sub_round(cav, tunnel, 0.03)
    # door trim: armrests and map pockets stand proud of the trim panel,
    # interior handles sit in shallow recesses
    cav = np.maximum(cav, -door_trim_features(x, y, z))
    cav = np.minimum(cav, np.maximum(inner_handle_recesses(x, y, z), F(0.70) - np.abs(x)))
    return cav


INNER_HANDLES = ((0.560, 1.045), (-0.440, 1.055))   # (y, z) front door, rear door


def door_trim_features(x, y, z):
    ax = np.abs(x)
    arm_f = box(ax, y, z, (0.800, 0.170, 0.928), (0.048, 0.390, 0.026), 0.022)
    arm_r = box(ax, y, z, (0.800, -0.715, 0.940), (0.048, 0.250, 0.024), 0.020)
    pocket_f = box(ax, y, z, (0.805, 0.250, 0.650), (0.045, 0.330, 0.065), 0.025)
    pocket_r = box(ax, y, z, (0.805, -0.700, 0.660), (0.040, 0.220, 0.055), 0.022)
    return np.minimum(np.minimum(arm_f, arm_r), np.minimum(pocket_f, pocket_r))


def inner_handle_recesses(x, y, z):
    ax = np.abs(x)
    d = None
    for yc, zc in INNER_HANDLES:
        r = box(ax, y, z, (0.832, yc, zc), (0.030, 0.060, 0.022), 0.012)
        d = r if d is None else np.minimum(d, r)
    return d


# ------------------------------------------------------------------ openings

def _a_pillar_y(z):
    """Y of the A pillar's rear edge seen from the side."""
    w = GH_BELT_W - (z - Z_BELT_F) * GH_TUMBLE
    return Y_WS_BASE - WS_WRAP * w * w - (z - Z_WS_BASE) * WS_RUN / WS_RISE


Z_WIN_TOP = 1.712


def front_window_poly():
    zb = Z_BELT_F + 0.012
    pts = [
        (_a_pillar_y(zb) - 0.070, zb),
        (_a_pillar_y(Z_WIN_TOP) - 0.072, Z_WIN_TOP),
        (Y_B_PILLAR + 0.048, Z_WIN_TOP),
        (Y_B_PILLAR + 0.048, zb),
    ]
    return fillet_polygon(pts, [0.02, 0.07, 0.035, 0.012])


def rear_window_side_poly():
    zb = Z_BELT_R + 0.012
    pts = [
        (Y_B_PILLAR - 0.048, zb),
        (Y_B_PILLAR - 0.048, Z_WIN_TOP),
        (-0.948, Z_WIN_TOP),
        (-0.960, zb),
    ]
    return fillet_polygon(pts, [0.012, 0.035, 0.05, 0.02])


def windshield_poly():
    """Glass outline in (x, v) windshield coordinates."""
    v1 = WS_L - 0.058
    z0 = Z_WS_BASE + 0.03 * WS_RISE / WS_L
    z1 = Z_WS_BASE + v1 * WS_RISE / WS_L
    w0 = GH_BELT_W - (z0 - Z_BELT_F) * GH_TUMBLE - 0.078
    w1 = GH_BELT_W - (z1 - Z_BELT_F) * GH_TUMBLE - 0.085
    pts = [(-w0, 0.03), (w0, 0.03), (w1, v1), (-w1, v1)]
    return fillet_polygon(pts, [0.03, 0.03, 0.06, 0.06])


def rear_window_poly():
    pts = [(-0.565, 1.372), (0.565, 1.372), (0.545, 1.700), (-0.545, 1.700)]
    return fillet_polygon(pts, [0.045, 0.045, 0.05, 0.05])


_FW = front_window_poly()
_RWS = rear_window_side_poly()
_WS = windshield_poly()
_RW = rear_window_poly()


def window_openings(x, y, z):
    ax = np.abs(x)
    side_cut = np.minimum(poly2(y, z, _FW), poly2(y, z, _RWS))
    side_cut = np.maximum(side_cut, F(0.62) - ax)
    v = ws_v(x, y, z)
    ws = np.maximum(poly2(x, v, _WS), np.abs(ws_plane(x, y, z) + F(0.02)) - F(0.10))
    rw = np.maximum(poly2(x, z, _RW), np.maximum(y - F(Y_RW_BOT + 0.12), F(-1.45) - y))
    return union(side_cut, ws, rw)


# ------------------------------------------------------------------ details carved into the cab

HANDLES = ((-0.215, 1.118), (-0.905, 1.122))   # (y, z) of the door handle centres


def door_handle_pockets(x, y, z):
    ax = np.abs(x)
    out = None
    for yc, zc in HANDLES:
        d = box(ax, y, z, (0.915, yc, zc), (0.030, 0.085, 0.026), 0.02)
        out = d if out is None else np.minimum(out, d)
    return out


Z_HOOD_SEAM = 1.0835   # top of the headlights and grille = hood shut line
HEAD_POLY = fillet_polygon(
    [(0.478, 0.925), (0.484, Z_HOOD_SEAM), (0.700, Z_HOOD_SEAM), (0.850, Z_HOOD_SEAM),
     (0.915, 1.050), (0.910, 0.995), (0.780, 0.962), (0.620, 0.935)],
    [0.012, 0.0, 0.0, 0.03, 0.03, 0.03, 0.05, 0.05])

# Bumper top line: follows the underside of the headlights
_BTX = [0.0, 0.48, 0.62, 0.78, 0.91, 1.0]
_BTZ = [0.919, 0.919, 0.929, 0.956, 0.989, 0.995]


def bumper_top(x):
    return smooth_interp(np.abs(x), _BTX, _BTZ)
HEAD_DEPTH = 0.075


def headlight_region(x, y, z):
    """Front-view outline of the headlight cluster, pushed into the nose."""
    ax = np.abs(x)
    d2 = poly2(ax, z, HEAD_POLY)
    depth = y - (front_y(x, z) - F(HEAD_DEPTH))
    return np.maximum(d2, -depth)


_GP = [(0.0, 0.680), (0.392, 0.680), (0.456, 0.930), (0.474, Z_HOOD_SEAM), (0.0, Z_HOOD_SEAM)]
_GP = _GP + [(-p[0], p[1]) for p in reversed(_GP[1:4])]
GRILLE_POLY = fillet_polygon(_GP, [0, 0.05, 0.03, 0.0, 0, 0.0, 0.03, 0.05])
Y_GRILLE_BACK = Y_HOOD_FRONT - 0.09


def grille_region(x, y, z):
    d2 = poly2(x, z, GRILLE_POLY)
    return np.maximum(d2, F(Y_GRILLE_BACK) - y)


def cab_solid(x, y, z):
    d = cab_outer(x, y, z)
    d = sub_round(d, cabin_cavity(x, y, z), 0.008)
    d = sub_round(d, window_openings(x, y, z), 0.004)
    d = sub_round(d, door_handle_pockets(x, y, z), 0.004)
    d = sub(d, headlight_region(x, y, z))
    d = sub(d, grille_region(x, y, z))
    return d


# ------------------------------------------------------------------ bed solid

BED_IN_W = 0.770
BED_WELL_INNER = 0.57
Y_BED_IN_FRONT = Y_BED_FRONT - 0.055
Y_BED_IN_BACK = Y_BED_BACK + 0.055
Z_BED_BOTTOM = 0.600
Z_TAILGATE_BOTTOM = 0.700


def bed_floor_z(x):
    # pressed ribs running front to back
    pitch = F(0.24)
    u = np.mod(x + F(0.12), pitch) - pitch * F(0.5)
    rib = 1 - smoothstep(0.022, 0.034, np.abs(u))
    return F(Z_BED_FLOOR) + F(0.014) * rib * (np.abs(x) < F(0.70))


def wheel_housing(x, y, z):
    ax = np.abs(x)
    # inner face at |x| = 0.53 leaves a 4 cm wall to the wheel well cut at 0.57
    return box(ax, y, z, (0.80, Y_REAR_AXLE, 0.76), (0.270, 0.47, 0.285), 0.07)


def bed_outer(x, y, z):
    ax = np.abs(x)
    w = w_base(z) + flare(y, z, Y_REAR_AXLE)
    side = ax - w
    d = inter_round(side, z - F(Z_BED_RAIL), 0.018)
    d = inter_round(d, y - F(Y_BED_FRONT), 0.035)
    crease = F(0.004) * smoothstep(1.060, 1.072, z)
    d = inter_round(d, F(Y_BED_BACK) - crease - y, 0.05)
    d = inter_round(d, F(Z_BED_BOTTOM) - z, 0.02)
    d = sub_round(d, arch_cut(x, y, z, Y_REAR_AXLE, inner=BED_WELL_INNER), 0.010)
    return d


def bed_cavity(x, y, z):
    ax = np.abs(x)
    c = inter(ax - F(BED_IN_W), F(Y_BED_IN_BACK) - y, y - F(Y_BED_IN_FRONT), bed_floor_z(x) - z)
    c = inter_round(c, ax - F(BED_IN_W), 0.0)
    c = sub_round(c, wheel_housing(x, y, z), 0.02)
    # vertical stiffening ribs pressed into the inner side walls
    rib_pitch = F(0.36)
    u = np.mod(y - F(Y_BED_IN_BACK) - F(0.18), rib_pitch) - rib_pitch * F(0.5)
    rib = (1 - smoothstep(0.018, 0.030, np.abs(u))) * smoothstep(1.06, 1.10, z) * (1 - smoothstep(1.21, 1.25, z))
    c = np.maximum(c, -(F(BED_IN_W) - F(0.010) * rib - ax) - F(0.0))
    return c


def tail_light_region(x, y, z):
    ax = np.abs(x)
    d2 = box2(ax, z, (0.845, 1.045), (0.068, 0.205), 0.03)
    return np.maximum(d2, y - F(Y_BED_BACK + 0.060))


def tailgate_handle_pocket(x, y, z):
    return box(x, y, z, (0.0, Y_BED_BACK, 1.215), (0.112, 0.022, 0.033), 0.012)


def bed_solid(x, y, z):
    d = bed_outer(x, y, z)
    cav = bed_cavity(x, y, z)
    d = np.maximum(d, -cav)
    d = sub(d, tail_light_region(x, y, z))
    d = sub_round(d, tailgate_handle_pocket(x, y, z), 0.004)
    return d


# ------------------------------------------------------------------ panels

def panel_piece(solid, region, depth, gap=GAP):
    """Return (piece_sdf, remainder_cut_sdf) for a panel region.

    depth is either a thickness below the outer surface or a callable
    floor(x, y, z) -> signed distance below a hidden flat underside.
    """
    if callable(depth):
        def layer(x, y, z, s, extra):
            return depth(x, y, z) - F(extra)
    else:
        def layer(x, y, z, s, extra):
            return -(s + F(depth + extra))

    def piece(x, y, z):
        s = solid(x, y, z)
        return inter(s, region(x, y, z) + F(gap * 0.5), layer(x, y, z, s, 0.0))

    def hole(x, y, z, s):
        return inter(region(x, y, z) - F(gap * 0.5), layer(x, y, z, s, gap * 0.5))

    return piece, hole


def hood_floor(x, y, z):
    """Hidden flat underside of the hood (a sloped plane)."""
    zb = F(1.236 - 0.045) + (y - F(Y_COWL)) * F((1.128 - 1.236) / (Y_HOOD_FRONT - Y_COWL))
    return zb - z


def hood_region(x, y, z):
    ax = np.abs(x)
    hw = smooth_interp(y, [Y_COWL, 1.70, 2.30, 3.0], [0.762, 0.790, 0.815, 0.815])
    d = inter_round(ax - hw, F(Y_COWL + 0.004) - y, 0.03)
    return np.maximum(d, F(1.086) - z)


def _door_poly_front():
    zb = Z_DOOR_BOTTOM
    zt = 1.756
    pts = [
        (Y_DOOR_F_FRONT, zb),
        (Y_DOOR_F_FRONT, Z_BELT_F - 0.004),
        (_a_pillar_y(Z_BELT_F) - 0.028, Z_BELT_F - 0.004),
        (_a_pillar_y(zt) - 0.040, zt),
        (Y_B_PILLAR, zt),
        (Y_B_PILLAR, zb),
    ]
    return fillet_polygon(pts, [0.03, 0.0, 0.0, 0.05, 0.0, 0.03])


def _door_poly_rear():
    zb = Z_DOOR_BOTTOM
    zt = 1.756
    pts = [
        (Y_B_PILLAR, zb),
        (Y_B_PILLAR, zt),
        (-0.992, zt),
        (-1.000, Z_BELT_R + 0.010),
        (Y_DOOR_R_BACK, Z_BELT_R - 0.006),
        (Y_DOOR_R_BACK, 0.80),
        (-0.935, zb),
    ]
    return fillet_polygon(pts, [0.0, 0.0, 0.04, 0.0, 0.0, 0.05, 0.03])


_DPF = _door_poly_front()
_DPR = _door_poly_rear()


def door_region(front, side):
    poly = _DPF if front else _DPR
    sgn = F(1 if side > 0 else -1)

    def reg(x, y, z):
        d2 = poly2(y, z, poly)
        return np.maximum(d2, F(0.60) - x * sgn)
    return reg


def tailgate_region(x, y, z):
    d2 = box2(x, z, (0.0, (Z_TAILGATE_BOTTOM + 1.283) / 2), (BED_IN_W - 0.004, (1.283 - Z_TAILGATE_BOTTOM) / 2), 0.012)
    return np.maximum(d2, y - F(Y_BED_IN_BACK + 0.002))


def cowl_region(x, y, z):
    """Black plastic cowl strip between the hood and the windshield."""
    ax = np.abs(x)
    yb = F(Y_WS_BASE - 0.042) - F(WS_WRAP) * x * x
    d = inter_round(ax - F(0.735), yb - y, 0.02)
    return inter(d, y - F(Y_COWL + 0.0005), F(1.19) - z)


def fuel_door_region(x, y, z):
    d2 = box2(y, z, (-1.32, 1.100), (0.080, 0.065), 0.025)
    return np.maximum(d2, x + F(0.86))  # left side outer skin only


PANELS = {
    # name: (parent solid, region, depth)
    "Hood": ("cab", hood_region, hood_floor),
    "Door_FL": ("cab", door_region(True, -1), 0.30),
    "Door_FR": ("cab", door_region(True, 1), 0.30),
    "Door_RL": ("cab", door_region(False, -1), 0.30),
    "Door_RR": ("cab", door_region(False, 1), 0.30),
    "Tailgate": ("bed", tailgate_region, 0.30),
    "FuelDoor": ("bed", fuel_door_region, 0.012),
    "Cowl": ("cab", cowl_region, 0.02),
}

SOLIDS = {"cab": cab_solid, "bed": bed_solid}


def make_piece(name):
    parent, region, depth = PANELS[name]
    solid = SOLIDS[parent]
    piece, _ = panel_piece(solid, region, depth)
    return piece


def make_remainder(parent):
    solid = SOLIDS[parent]
    holes = [(panel_piece(solid, reg, dep)[1]) for n, (p, reg, dep) in PANELS.items() if p == parent]

    def rem(x, y, z):
        s = solid(x, y, z)
        d = s
        for h in holes:
            d = np.maximum(d, -h(x, y, z, s))
        return d
    return rem


BOUNDS = {
    "cab": ((-1.00, -1.15, 0.40), (1.00, 2.50, 1.86)),
    "bed": ((-0.98, -2.84, 0.55), (0.98, -1.07, 1.34)),
    "Hood": ((-0.86, 0.80, 1.00), (0.86, 2.48, 1.30)),
    "Door_FL": ((-0.98, -0.40, 0.48), (-0.55, 0.86, 1.82)),
    "Door_FR": ((0.55, -0.40, 0.48), (0.98, 0.86, 1.82)),
    "Door_RL": ((-0.98, -1.10, 0.48), (-0.55, -0.29, 1.82)),
    "Door_RR": ((0.55, -1.10, 0.48), (0.98, -0.29, 1.82)),
    "Tailgate": ((-0.80, -2.82, 0.65), (0.80, -2.60, 1.33)),
    "FuelDoor": ((-0.98, -1.44, 0.98), (-0.80, -1.20, 1.21)),
    "Cowl": ((-0.78, 0.62, 1.17), (0.78, 0.90, 1.32)),
}


# ------------------------------------------------------------------ part list

def parts():
    import classify
    from spec import Part
    a = dict(deps=("body",))
    door_x = 0.90
    P = [
        Part("Body_Cab", make_remainder("cab"), *BOUNDS["cab"], 0.005, 13500, classify.cab, group="Body", **a),
        Part("Hood", make_piece("Hood"), *BOUNDS["Hood"], 0.004, 1500, "Paint", group="Body",
             origin=(0.0, Y_COWL, 1.236), **a),
        Part("Door_FL", make_piece("Door_FL"), *BOUNDS["Door_FL"], 0.004, 2400, classify.door, group="Doors",
             origin=(-door_x, Y_DOOR_F_FRONT - 0.01, 1.0), **a),
        Part("Door_FR", make_piece("Door_FR"), *BOUNDS["Door_FR"], 0.004, 2400, classify.door, group="Doors",
             origin=(door_x, Y_DOOR_F_FRONT - 0.01, 1.0), **a),
        Part("Door_RL", make_piece("Door_RL"), *BOUNDS["Door_RL"], 0.004, 2000, classify.door, group="Doors",
             origin=(-door_x, Y_B_PILLAR - 0.005, 1.0), **a),
        Part("Door_RR", make_piece("Door_RR"), *BOUNDS["Door_RR"], 0.004, 2000, classify.door, group="Doors",
             origin=(door_x, Y_B_PILLAR - 0.005, 1.0), **a),
        Part("Body_Bed", make_remainder("bed"), *BOUNDS["bed"], 0.005, 6000, classify.bed, group="Body", **a),
        Part("Tailgate", make_piece("Tailgate"), *BOUNDS["Tailgate"], 0.004, 1500, classify.tailgate, group="Body",
             origin=(0.0, Y_BED_BACK + 0.03, Z_TAILGATE_BOTTOM), **a),
        Part("FuelDoor", make_piece("FuelDoor"), *BOUNDS["FuelDoor"], 0.002, 150, "Paint", group="Body", **a),
        Part("Cowl", make_piece("Cowl"), *BOUNDS["Cowl"], 0.003, 500, "TrimBlack", group="Body", **a),
    ]
    return P
