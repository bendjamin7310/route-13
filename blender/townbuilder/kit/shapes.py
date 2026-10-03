"""Small shape helpers shared by kit builders."""

from __future__ import annotations

import math

from ..geom import rot_x, rot_z, mat_mul


def legs4(k, mat, w, d, h, t=0.25, inset=0.15, z0=0.0):
    hx, hy = w / 2 - inset - t / 2, d / 2 - inset - t / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * hx, sy * hy
            k.box(mat, cx - t / 2, cy - t / 2, z0, cx + t / 2, cy + t / 2, z0 + h, collide=False)


def table(k, top, legs, w, d, h, thick=0.25, leg=0.25):
    k.box(top, -w / 2, -d / 2, h - thick, w / 2, d / 2, h)
    legs4(k, legs, w, d, h - thick, leg)


def cabinet(k, body, front, w, d, h, doors=2, handle="metal_chrome", y_front=None, z0=0.0,
            drawers=0):
    """Box cabinet with door panels and handles on its -Y face."""
    k.box(body, -w / 2, -d / 2 + 0.06, z0, w / 2, d / 2, z0 + h)
    yf = -d / 2 if y_front is None else y_front
    n = max(1, doors)
    gap = 0.06
    pw = (w - gap * (n + 1)) / n
    rows = max(1, drawers) if drawers else 1
    ph = (h - gap * (rows + 1)) / rows
    for i in range(n):
        x0 = -w / 2 + gap + i * (pw + gap)
        for r in range(rows):
            z = z0 + gap + r * (ph + gap)
            k.box(front, x0, yf, z, x0 + pw, yf + 0.08, z + ph, collide=False)
            if drawers:
                k.box(handle, x0 + pw / 2 - 0.3, yf - 0.08, z + ph * 0.6, x0 + pw / 2 + 0.3,
                      yf, z + ph * 0.6 + 0.08, collide=False)
            else:
                hx = x0 + (pw - 0.25 if i % 2 == 0 else 0.15)
                k.box(handle, hx, yf - 0.08, z + ph * 0.45, hx + 0.08, yf, z + ph * 0.75,
                      collide=False)


def shelf_unit(k, frame, w, d, h, levels, goods=None, rng_seed=0, back=True, goods_fill=0.8):
    """Open shelving with optional goods blocks on each level."""
    t = 0.15
    k.box(frame, -w / 2, -d / 2, 0, -w / 2 + t, d / 2, h)
    k.box(frame, w / 2 - t, -d / 2, 0, w / 2, d / 2, h)
    if back:
        k.box(frame, -w / 2, d / 2 - 0.1, 0, w / 2, d / 2, h, collide=False)
    step = (h - 0.3) / levels
    for i in range(levels + 1):
        z = 0.2 + i * step
        k.box(frame, -w / 2 + t, -d / 2, z - 0.1, w / 2 - t, d / 2, z, collide=False)
        if goods and i < levels:
            _goods_row(k, goods, -w / 2 + t + 0.1, w / 2 - t - 0.1, -d / 2 + 0.1,
                       d / 2 - 0.2, z, z + step * goods_fill - 0.1, rng_seed + i)


def _goods_row(k, mats, x0, x1, y0, y1, z0, zmax, seed):
    import random
    r = random.Random(seed)
    x = x0
    while x < x1 - 0.3:
        bw = r.uniform(0.5, 1.4)
        if x + bw > x1:
            bw = x1 - x
        bh = r.uniform(0.5, 1.0) * (zmax - z0)
        mat = mats[r.randrange(len(mats))]
        k.box(mat, x, y0 + r.uniform(0, 0.2), z0, x + bw - 0.05, y1, z0 + max(0.3, bh),
              collide=False)
        x += bw


def pitched(k, mat, cx, cy, cz, sx, sy, sz, pitch, yaw=0.0, collide=True):
    """Box tilted about its local X axis by ``pitch`` radians, then yawed."""
    k.obox(mat, cx, cy, cz, sx, sy, sz, mat_mul(rot_z(yaw), rot_x(pitch)), collide)


def cone(k, mat, cx, cy, z0, r0, r1, h, sides=8):
    """Truncated cone as a free mesh (r1 may be 0)."""
    verts, faces = [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        verts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0))
    if r1 > 1e-4:
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), z0 + h))
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((i, j, sides + j, sides + i))
        faces.append(tuple(range(sides - 1, -1, -1)))
        faces.append(tuple(range(sides, 2 * sides)))
    else:
        verts.append((cx, cy, z0 + h))
        top = sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((i, j, top))
        faces.append(tuple(range(sides - 1, -1, -1)))
    k.mesh(mat, verts, faces)


def blob(k, mat, cx, cy, cz, rx, ry, rz, seed=0, rings=4, segs=7, jitter=0.12):
    """Low-poly lumpy ellipsoid (foliage)."""
    import random
    r = random.Random(seed)
    verts, faces = [], []
    verts.append((cx, cy, cz - rz))
    for i in range(1, rings):
        phi = math.pi * i / rings
        for j in range(segs):
            th = 2 * math.pi * j / segs + (i % 2) * math.pi / segs
            f = 1.0 + r.uniform(-jitter, jitter)
            verts.append((cx + rx * f * math.sin(phi) * math.cos(th),
                          cy + ry * f * math.sin(phi) * math.sin(th),
                          cz - rz * f * math.cos(phi)))
    verts.append((cx, cy, cz + rz))
    top = len(verts) - 1
    for j in range(segs):
        faces.append((0, 1 + (j + 1) % segs, 1 + j))
    for i in range(rings - 2):
        a0 = 1 + i * segs
        b0 = 1 + (i + 1) * segs
        for j in range(segs):
            j1 = (j + 1) % segs
            faces.append((a0 + j, a0 + j1, b0 + j1, b0 + j))
    last = 1 + (rings - 2) * segs
    for j in range(segs):
        faces.append((last + j, last + (j + 1) % segs, top))
    k.mesh(mat, verts, faces)


def car_wheel(k, x, y, r=1.15, w=0.9, hub="metal"):
    k.hcyl("rubber", x, y, r, r, w, axis="x", sides=12, collide=False)
    k.hcyl(hub, x + (0.05 if x > 0 else -0.05), y, r, r * 0.55, w, axis="x", sides=8,
           collide=False)
