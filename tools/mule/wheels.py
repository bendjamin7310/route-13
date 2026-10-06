"""Wheels: parametric tyres, an SDF six-spoke rim, brakes and the spare.

Wheel-local axes: X = axle (positive = outboard), Y/Z = wheel plane.
Every wheel object has its origin at the wheel centre so it can spin in
Roblox. Rim, tyre and disc rotate with the wheel; calipers do not.
"""

import math

import numpy as np

import mesher
import spec
from dims import *  # noqa: F401,F403
from sdf import F, inter_round, torus_axis, union, union_round
from spec import MeshPart

NSEG = 56

# Tyre cross-section (radius, axial offset) from bead to shoulder, outboard side.
OUTER_PROFILE = [
    (0.218, 0.097), (0.230, 0.107), (0.244, 0.1175), (0.256, 0.1215),
    (0.280, 0.1245), (0.306, 0.1262), (0.330, 0.1242),
    (0.350, 0.1192), (0.364, 0.1110), (0.373, 0.1000),
]
INNER_PROFILE = [(0.218, 0.097), (0.250, 0.1205), (0.300, 0.1260),
                 (0.346, 0.1205), (0.373, 0.1000)]
R_GROOVE = 0.3735
R_TREAD = 0.3860


def _revolve(prof, nseg, side, v0, v1):
    """Revolve (r, w) points; side=+1 outboard, -1 inboard. Returns verts, quads, uvs."""
    prof = [(r, w * side) for r, w in prof]
    n = len(prof)
    th = np.arange(nseg) * 2 * math.pi / nseg
    verts = []
    for r, w in prof:
        verts.append(np.stack([np.full(nseg, w), r * np.cos(th), r * np.sin(th)], 1))
    verts = np.concatenate(verts)
    quads, uvs = [], []
    for i in range(n - 1):
        for j in range(nseg):
            j2 = (j + 1) % nseg
            a, b = i * nseg + j, i * nseg + j2
            c, d = (i + 1) * nseg + j2, (i + 1) * nseg + j
            quads.append([a, b, c, d])
            u0, u1 = j / nseg, (j + 1) / nseg
            va = v0 + (v1 - v0) * i / (n - 1)
            vb = v0 + (v1 - v0) * (i + 1) / (n - 1)
            uvs.append([(u0, va), (u1, va), (u1, vb), (u0, vb)])
    return verts, quads, uvs


def _block(t0, t1, w0, w1, rt0, rt1, rb0, rb1, skew=0.0):
    """Hexahedral tread block. rt*/rb* = top/bottom radius at w0/w1."""
    corners = []
    for rr in ((rb0, rb1), (rt0, rt1)):
        for (t, w, r) in ((t0, w0, rr[0]), (t1, w0, rr[0]), (t1, w1, rr[1]), (t0, w1, rr[1])):
            tt = t + skew * w
            corners.append((w, r * math.cos(tt), r * math.sin(tt)))
    c = np.array(corners)
    b0, b1, b2, b3, t0_, t1_, t2_, t3_ = range(8)
    quads = [[t0_, t1_, t2_, t3_], [b0, b1, t1_, t0_], [b1, b2, t2_, t1_], [b2, b3, t3_, t2_], [b3, b0, t0_, t3_]]
    centre = c.mean(axis=0)
    out = []
    for q in quads:
        p0, p1, p2 = c[q[0]], c[q[1]], c[q[2]]
        n = np.cross(p1 - p0, p2 - p0)
        if np.dot(n, c[q].mean(axis=0) - centre) < 0:
            q = q[::-1]
        out.append(q)
    return c, out


def tyre(side=1, nseg=NSEG, blocks=True):
    vs, qs, uvs = [], [], []
    off = 0

    def add(v, q, uv):
        nonlocal off
        vs.append(v)
        qs.extend([[i + off for i in quad] for quad in q])
        uvs.extend(uv)
        off += len(v)

    add(*_revolve(OUTER_PROFILE, nseg, side, 0.0, 0.42))
    add(*_revolve(INNER_PROFILE, nseg, -side, 0.0, 0.30))
    base = [(R_GROOVE + 0.0015 * (1 - (w / 0.1) ** 2), w) for w in np.linspace(0.1, -0.1, 5)]
    add(*_revolve(base, nseg, side, 0.42, 0.60))
    n_carcass = len(qs)
    if blocks:
        npitch = 30
        dt = 2 * math.pi / npitch
        rows = [  # (w0, w1, theta offset, coverage, top radius at w0, w1)
            (0.060, 0.117, 0.00, 0.60, R_TREAD, R_TREAD - 0.011),
            (0.008, 0.054, 0.45, 0.62, R_TREAD + 0.0005, R_TREAD),
            (-0.054, -0.008, 0.05, 0.62, R_TREAD, R_TREAD + 0.0005),
            (-0.117, -0.060, 0.52, 0.60, R_TREAD - 0.011, R_TREAD),
        ]
        for k in range(npitch):
            for w0, w1, ofs, cov, rt0, rt1 in rows:
                t0 = (k + ofs) * dt
                t1 = t0 + cov * dt
                ww0, ww1 = w0 * side, w1 * side
                r_b0 = R_GROOVE - 0.004 if abs(w0) < 0.1 else 0.356
                r_b1 = R_GROOVE - 0.004 if abs(w1) < 0.1 else 0.356
                if side < 0:
                    ww0, ww1 = ww1, ww0
                    rt0, rt1 = rt1, rt0
                    r_b0, r_b1 = r_b1, r_b0
                c, q = _block(t0, t1, ww0, ww1, rt0, rt1, r_b0, r_b1, skew=0.9 * side)
                u0, u1 = (t0 % (2 * math.pi)) / (2 * math.pi), (t1 % (2 * math.pi)) / (2 * math.pi)
                uv = [[(u0, 0.62), (u1, 0.62), (u1, 0.7), (u0, 0.7)]] + [[(u0, 0.7), (u1, 0.7), (u1, 0.74), (u0, 0.74)]] * 4
                add(c, q, uv)
    v = np.concatenate(vs)
    q = np.array(qs, dtype=np.int32)
    uv = np.array(uvs, dtype=np.float32)
    # orient every quad away from the tyre's core ring (r = 0.30, w = 0)
    a, b, c = v[q[:, 0]], v[q[:, 1]], v[q[:, 2]]
    n = np.cross(b - a, c - a)
    cen = v[q].mean(axis=1)
    rr = np.hypot(cen[:, 1], cen[:, 2])
    core = np.stack([np.zeros(len(cen)), cen[:, 1] / rr * 0.30, cen[:, 2] / rr * 0.30], 1)
    # tread block faces: orient away from the block centre instead
    flip = np.einsum("ij,ij->i", n, cen - core) < 0
    flip[n_carcass:] = False  # tread blocks are already oriented
    q[flip] = q[flip][:, ::-1]
    uv[flip] = uv[flip][:, ::-1]
    return v.astype(np.float32), q, uv


# ----------------------------------------------------------------- rim (SDF)

def rim_sdf(x, y, z):
    w = x
    r = np.sqrt(y * y + z * z)
    th = np.arctan2(z, y)
    barrel = np.maximum(np.abs(r - F(0.2105)) - F(0.0055), np.abs(w) - F(0.101))
    flange = np.minimum(torus_axis(y, z, w, 0, 0, 0.1018, 0.2215, 0.0075), torus_axis(y, z, w, 0, 0, -0.1018, 0.2215, 0.0075))
    d = union_round(barrel, flange, 0.004)
    # dished face with six spokes
    wf = F(0.064) + F(0.020) * np.clip(1 - r / F(0.205), 0, 1)
    face = inter_round(np.abs(w - wf) - F(0.0105), r - F(0.209), 0.004)
    sector = math.pi / 3
    tm = np.mod(th + F(sector / 2), F(sector)) - F(sector / 2)
    perp = r * np.abs(np.sin(tm))
    hw = F(0.027) + F(0.015) * np.clip((F(0.190) - r) / F(0.09), 0, 1)
    spoke = perp - hw
    window = inter_round(inter_round(F(0.102) - r, r - F(0.191), 0.014), -spoke, 0.012)
    face = np.maximum(face, -window)
    d = union_round(d, face, 0.006)
    hub = inter_round(r - F(0.088), np.abs(w - F(0.084)) - F(0.012), 0.008)
    cap = inter_round(r - F(0.036), np.abs(w - F(0.092)) - F(0.011), 0.006)
    d = union_round(d, union(hub, cap), 0.006)
    # lug nuts on a 139.7 mm PCD, between the spokes
    tl = np.mod(th, F(sector)) - F(sector / 2)
    ly = r * np.cos(tl) - F(0.0698)
    lz = r * np.sin(tl)
    lug = inter_round(np.sqrt(ly * ly + lz * lz) - F(0.0105), np.abs(w - F(0.097)) - F(0.008), 0.003)
    return np.minimum(d, lug)


def caliper_sdf(x, y, z):
    w = x
    r = np.sqrt(y * y + z * z)
    th = np.arctan2(z, y)
    ang = np.abs(th - F(math.radians(160)))
    body_ = np.maximum(np.abs(r - F(0.150)) - F(0.030), r * ang - F(0.085))
    body_ = inter_round(body_, np.abs(w + F(0.006)) - F(0.034), 0.012)
    return body_


def disc(nseg=48):
    """Vented disc as a parametric ring (r 0.095..0.160) with a hat."""
    prof_out = [(0.160, 0.012), (0.095, 0.012), (0.090, 0.040), (0.060, 0.045)]
    prof_edge = [(0.160, -0.014), (0.160, 0.012)]
    vs, qs = [], []
    off = 0
    for prof in (prof_out, prof_edge):
        v, q, _ = _revolve([(r, w) for r, w in prof], nseg, 1, 0, 1)
        vs.append(v)
        qs += [[i + off for i in quad] for quad in q]
        off += len(v)
    v = np.concatenate(vs).astype(np.float32)
    q = np.array(qs, dtype=np.int32)
    a, b, c = v[q[:, 0]], v[q[:, 1]], v[q[:, 2]]
    n = np.cross(b - a, c - a)
    cen = v[q].mean(axis=1)
    want = np.where(np.abs(cen[:, 0] - 0.012) < 1e-3, 1.0, 0.0)[:, None] * np.array([1, 0, 0]) + \
        np.where(np.abs(cen[:, 0] - 0.012) >= 1e-3, 1.0, 0.0)[:, None] * np.stack([np.zeros(len(cen)), cen[:, 1], cen[:, 2]], 1)
    flip = np.einsum("ij,ij->i", n, want) < 0
    q[flip] = q[flip][:, ::-1]
    return v, q


def drum(nseg=40):
    prof = [(0.045, 0.045), (0.150, 0.040), (0.155, 0.030), (0.155, -0.060)]
    v, q, _ = _revolve(prof, nseg, 1, 0, 1)
    v = v.astype(np.float32)
    q = np.array(q, dtype=np.int32)
    a, b, c = v[q[:, 0]], v[q[:, 1]], v[q[:, 2]]
    n = np.cross(b - a, c - a)
    cen = v[q].mean(axis=1)
    want = cen.copy()
    want[:, 0] = 0.5
    flip = np.einsum("ij,ij->i", n, want) < 0
    q[flip] = q[flip][:, ::-1]
    return v, q


# ----------------------------------------------------------------- assembly

WHEELS = {
    "FR": (X_WHEEL_F, Y_FRONT_AXLE, 1),
    "FL": (-X_WHEEL_F, Y_FRONT_AXLE, -1),
    "RR": (X_WHEEL_R, Y_REAR_AXLE, 1),
    "RL": (-X_WHEEL_R, Y_REAR_AXLE, -1),
}


def _place(v, cx, cy, side):
    v = np.asarray(v, dtype=np.float32).copy()
    if side < 0:
        v[:, 0] *= -1
    v[:, 0] += cx
    v[:, 1] += cy
    v[:, 2] += AXLE_Z
    return v


def _flip(q, side):
    q = np.asarray(q)
    return q[:, ::-1].copy() if side < 0 else q


def parts():
    key = (spec.source_hash("wheels"),)
    rim_v, rim_f = mesher.sdf_part("Rim", rim_sdf, (-0.12, -0.235, -0.235), (0.12, 0.235, 0.235), 0.0018, 1600, key_extra=key)
    cal_v, cal_f = mesher.sdf_part("Caliper", caliper_sdf, (-0.05, -0.2, -0.05), (0.04, 0.0, 0.14), 0.002, 260, key_extra=key)
    tv, tq, tuv = tyre(1)
    dv, dq = disc()
    drv, drq = drum()
    P = []
    for name, (cx, cy, side) in WHEELS.items():
        org = (cx, cy, AXLE_Z)
        tv_s, tq_s, tuv_s = (tv, tq, tuv)
        if side < 0:
            tv_s, tq_s, tuv_s = tyre(-1)
            P.append(MeshPart(f"Wheel_{name}_Tire", _place(tv_s, cx, cy, 1), tq_s, "Rubber", group="Wheels",
                              origin=org, sharp=34, uv=tuv_s.reshape(-1, 2)))
        else:
            P.append(MeshPart(f"Wheel_{name}_Tire", _place(tv, cx, cy, 1), tq, "Rubber", group="Wheels",
                              origin=org, sharp=34, uv=tuv.reshape(-1, 2)))
        P.append(MeshPart(f"Wheel_{name}_Rim", _place(rim_v, cx, cy, side), _flip(rim_f, side), "RimPaint",
                          group="Wheels", origin=org, sharp=50))
        if name.startswith("F"):
            P.append(MeshPart(f"Wheel_{name}_Disc", _place(dv, cx, cy, side), _flip(dq, side), "BrakeDisc",
                              group="Wheels", origin=org, sharp=50))
            P.append(MeshPart(f"Wheel_{name}_Caliper", _place(cal_v, cx, cy, side), _flip(cal_f, side), "Gunmetal",
                              group="Wheels", origin=org, sharp=50))
        else:
            P.append(MeshPart(f"Wheel_{name}_Drum", _place(drv, cx, cy, side), _flip(drq, side), "Gunmetal",
                              group="Wheels", origin=org, sharp=50))
    # spare wheel slung under the bed, lying flat
    sv, sq, suv = tyre(1, nseg=32, blocks=False)
    rot = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=np.float32)  # axle X -> Z (face down)
    sv = sv @ rot.T
    sv[:, 1] += -2.27
    sv[:, 2] += 0.465
    P.append(MeshPart("SpareWheel_Tire", sv, sq, "Rubber", group="Underbody", sharp=34, uv=suv.reshape(-1, 2)))
    return P
