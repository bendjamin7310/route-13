"""Roblox export: per-chunk Luau data modules, palette/kit tables, voxel terrain,
manifest.json and an .rbxmx bundle containing everything plus the Luau tools.

All coordinates are converted to Roblox space: (x, y, z)_rbx = (x, z, -y)_blender.
"""

from __future__ import annotations

import base64
import json
import math
import os
from collections import defaultdict

from .. import palette as pal
from ..geom import (Prim, Xform, mat_mul, rot_z, rot_x, to_roblox_rot, to_roblox_pos,
                    to_roblox_size)
from ..kit import KIT, load_all as _load_kit
from ..world import layout as Lay
from ..world.model import chunk_of, chunk_name

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROBLOX = os.path.normpath(os.path.join(HERE, "..", "..", "..", "roblox", "src"))

_load_kit()                                                       # indices need the full kit
PAL_NAMES = list(pal.P.keys())
PAL_INDEX = {n: i + 1 for i, n in enumerate(PAL_NAMES)}          # Lua is 1-based
KIT_NAMES = sorted(KIT.keys())
KIT_INDEX = {n: i + 1 for i, n in enumerate(KIT_NAMES)}
CYL_FIX = (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)            # Rz(90) in Roblox space


def f(v):
    """Compact float formatting."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def quat(m):
    """Rotation matrix (row-major 3x3) -> quaternion (x, y, z, w)."""
    m00, m01, m02, m10, m11, m12, m20, m21, m22 = m
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return (x / n, y / n, z / n, w / n)


def mat_index(name, channels=None):
    name = pal.resolve(name, channels)
    return PAL_INDEX.get(name, PAL_INDEX["plastic_gray"])


def part_line(p: Prim, channels=None, keep_channel=False):
    """One primitive (world/local Blender frame) -> Roblox part record."""
    if p.kind == "mesh":
        return mesh_fallback(p, channels, keep_channel)
    R = to_roblox_rot(p.rot)
    pos = to_roblox_pos(p.pos)
    sx, sy, sz = to_roblox_size(p.size)
    if p.kind == "box":
        k = "B"
    elif p.kind == "wedge":
        k = "W"
    elif p.kind == "cyl":
        k = "C"
        R = mat_mul(R, CYL_FIX)
        sx, sy, sz = sy, sx, sz      # Roblox cylinder: X = axis length, Y/Z = diameter
    else:
        k = "S" if abs(sx - sy) < 1e-3 and abs(sy - sz) < 1e-3 else "E"
    q = quat(R)
    m = p.mat if (keep_channel and p.mat.startswith("$")) else str(mat_index(p.mat, channels))
    return ",".join([k, f(pos[0]), f(pos[1]), f(pos[2]), f(q[0]), f(q[1]), f(q[2]), f(q[3]),
                     f(sx), f(sy), f(sz), m, "1" if p.collide else "0"])


def mesh_fallback(p: Prim, channels=None, keep_channel=False):
    """Free meshes (cones, foliage blobs, hulls) become an ellipsoid/block approximation."""
    vs = p.data[0]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [v[2] for v in vs]
    cx, cy, cz = (min(xs) + max(xs)) / 2 + p.pos[0], (min(ys) + max(ys)) / 2 + p.pos[1], \
        (min(zs) + max(zs)) / 2 + p.pos[2]
    size = (max(0.2, max(xs) - min(xs)), max(0.2, max(ys) - min(ys)), max(0.2, max(zs) - min(zs)))
    q = Prim("ball" if size[2] < max(size[0], size[1]) * 1.6 else "box", p.mat, (cx, cy, cz),
             size, p.rot, p.collide)
    if q.kind == "box":
        q = Prim("ball", p.mat, (cx, cy, cz), (size[0] * 0.7, size[1] * 0.7, size[2]), p.rot,
                 p.collide)
    return part_line(q, channels, keep_channel)


def box_line(p: Prim):
    """Collider record (always a block-ish volume)."""
    R = to_roblox_rot(p.rot)
    pos = to_roblox_pos(p.pos)
    sx, sy, sz = to_roblox_size(p.size)
    k = "W" if p.kind == "wedge" else "B"
    if p.kind == "cyl":
        R = mat_mul(R, CYL_FIX)
        sx, sy, sz = sy, sx, sz
        k = "C"
    q = quat(R)
    return ",".join([k, f(pos[0]), f(pos[1]), f(pos[2]), f(q[0]), f(q[1]), f(q[2]), f(q[3]),
                     f(sx), f(sy), f(sz)])


def cframe_yaw(x, y, z, yaw):
    """Blender position + yaw -> Roblox position + quaternion."""
    pos = to_roblox_pos((x, y, z))
    q = quat(to_roblox_rot(rot_z(yaw)))
    return pos, q


# ---------------------------------------------------------------------------------------
# sweeps / patches -> boxes (native parts path)

def sweep_boxes(sw):
    prof = sw.profile
    lats = [p[0] for p in prof]
    dzs = [p[1] for p in prof]
    lat0, lat1 = min(lats), max(lats)
    z0, z1 = min(dzs), max(dzs)
    if z1 - z0 < 0.08:
        z0 -= 0.5 if sw.cat in ("ROADS",) and lat1 - lat0 > 3 else 0.04
    width = max(0.1, lat1 - lat0)
    height = max(0.06, z1 - z0)
    clat = (lat0 + lat1) / 2
    cz = (z0 + z1) / 2
    smp = sw.samples
    segs = []
    for i in range(len(smp) - 1):
        a, b = smp[i], smp[i + 1]
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.hypot(dx, dy)
        if L < 1e-3:
            continue
        segs.append([a, b, math.atan2(dy, dx), math.atan2(dz, L)])
    merged = []
    for s in segs:
        if merged:
            m = merged[-1]
            if abs(m[2] - s[2]) < 0.004 and abs(m[3] - s[3]) < 0.004:
                m[1] = s[1]
                continue
        merged.append(list(s))
    out = []
    for (a, b, yaw, pitch) in merged:
        nx = (a[3] + b[3]) / 2
        ny = (a[4] + b[4]) / 2
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        Lz = math.hypot(L, b[2] - a[2])
        cx = (a[0] + b[0]) / 2 + nx * clat
        cy = (a[1] + b[1]) / 2 + ny * clat
        czz = (a[2] + b[2]) / 2 + cz
        rot = mat_mul(rot_z(yaw - math.pi / 2), rot_x(pitch))
        out.append(Prim("box", sw.mat, (cx, cy, czz), (width, Lz + 0.6, height), rot,
                        sw.collide))
    return out


def _min_rect(poly):
    """Minimum-area oriented rectangle of a polygon -> (cx, cy, w, h, angle)."""
    best = None
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        ang = math.atan2(y1 - y0, x1 - x0)
        c, s = math.cos(-ang), math.sin(-ang)
        us = [c * x - s * y for (x, y) in poly]
        vs = [s * x + c * y for (x, y) in poly]
        area = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or area < best[0]:
            cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
            cc, ss = math.cos(ang), math.sin(ang)
            best = (area, cc * cu - ss * cv, ss * cu + cc * cv, max(us) - min(us),
                    max(vs) - min(vs), ang)
    return best[1:]


def patch_boxes(patch):
    cat, mat, verts, faces, c = patch[:5]
    info = patch[5] if len(patch) > 5 else None
    out = []
    if info and info["kind"] == "fan":
        cx, cy, w, h, ang = _min_rect(info["poly"])
        out.append(Prim("box", mat, (cx, cy, info["z"] - 0.5), (w, h, 1.0), rot_z(ang), True))
    elif info and info["kind"] == "corner":
        inner, outer, z = info["inner"], info["outer"], info["z"]
        for i in range(len(inner) - 1):
            pts = [inner[i], inner[i + 1], outer[i + 1], outer[i]]
            cx = sum(p[0] for p in pts) / 4
            cy = sum(p[1] for p in pts) / 4
            ma = ((inner[i][0] + outer[i][0]) / 2, (inner[i][1] + outer[i][1]) / 2)
            mb = ((inner[i + 1][0] + outer[i + 1][0]) / 2, (inner[i + 1][1] + outer[i + 1][1]) / 2)
            L = math.hypot(mb[0] - ma[0], mb[1] - ma[1]) + 0.6
            wd = (math.hypot(outer[i][0] - inner[i][0], outer[i][1] - inner[i][1]) +
                  math.hypot(outer[i + 1][0] - inner[i + 1][0],
                             outer[i + 1][1] - inner[i + 1][1])) / 2
            yaw = math.atan2(mb[1] - ma[1], mb[0] - ma[0])
            out.append(Prim("box", mat, (cx, cy, z - 0.55), (L, wd, 2.1), rot_z(yaw), True))
    return out


CARVE_CATS = ("ROADS", "SIDEWALKS", "BRIDGES", "RAIL")


def carve_above(p: Prim, clear=10.0):
    """Box of air standing on top of a (possibly pitched) surface box."""
    R = p.rot
    up = (R[2], R[5], R[8])                      # local +Z column
    k = p.size[2] / 2 + clear / 2 + 0.05
    c = (p.pos[0] + up[0] * k, p.pos[1] + up[1] * k, p.pos[2] + up[2] * k)
    return Prim("box", "invisible", c, (p.size[0] - 0.4, p.size[1], clear), R, False)


def building_carves(plan):
    """Air volumes over each ground-floor / basement room so voxel terrain never pokes
    through floors (local plan coordinates)."""
    out = []
    top = plan.height + 1.0
    for room in plan.rooms:
        for L in (-1, 0):
            for r in room.cells.get(L, []):
                if L == -1:
                    z0 = plan.level_z(-1) + 0.05
                    z1 = 0.0
                else:
                    z0, z1 = 0.05, top
                if r.w < 0.5 or r.d < 0.5 or z1 - z0 < 0.2:
                    continue
                out.append(Prim("box", "invisible", (r.cx, r.cy, (z0 + z1) / 2),
                                (r.w, r.d, z1 - z0), collide=False))
    return out


# ---------------------------------------------------------------------------------------

class ChunkData:
    def __init__(self, name):
        self.name = name
        self.parts = []          # lines, with "#Model|Path" group headers
        self.colliders = []
        self.props = []
        self.lights = []
        self.markers = []
        self.signs = []
        self.carve = []          # terrain volumes to clear (building footprints, above roads)

    def to_lua(self):
        def blk(name, lines):
            body = "\n".join(lines)
            eq = "=" * 3
            while f"]{eq}]" in body:
                eq += "="
            return f"\t{name} = [{eq}[\n{body}\n]{eq}],\n"
        return ("-- Generated by blender/build_town.py - Port Solace chunk " + self.name +
                "\nreturn {\n" + f'\tname = "{self.name}",\n' + blk("parts", self.parts) +
                blk("colliders", self.colliders) + blk("props", self.props) +
                blk("lights", self.lights) + blk("markers", self.markers) +
                blk("signs", self.signs) + blk("carve", self.carve) + "}\n")


def _escape(s):
    return str(s).replace(",", " ").replace("\n", " ").replace("|", "/").replace(";", " ")


def export_roblox(W, out, log=print):
    os.makedirs(out, exist_ok=True)
    chunks = defaultdict(lambda: None)

    def ch(x, y):
        c = chunk_name(chunk_of(x, y))
        if chunks[c] is None:
            chunks[c] = ChunkData(c)
        return chunks[c]

    # -- buildings ---------------------------------------------------------------------
    for b in W.buildings:
        cx, cy = b.lot.center
        cd = ch(cx, cy)
        xf = b.xf
        for part_name, prims in (("Exterior", b.built.ext.prims), ("Interior", b.built.int.prims)):
            cd.parts.append(f"#{b.id}|{part_name}")
            cd.colliders.append(f"#{b.id}|{part_name}")
            for p in prims:
                if p.mat == "invisible":
                    continue
                wp = p.transformed(xf)
                cd.parts.append(part_line(wp))
                if p.collide:
                    cd.colliders.append(box_line(wp))
        cd.props.append(f"#{b.id}")
        for pp in b.built.props:
            cd.props.append(prop_line(pp.moved(xf), pp))
        for lr in b.built.lights:
            cd.lights.append(light_line(lr.moved(xf), b.id))
        for mk in b.built.markers:
            cd.markers.append(marker_line(mk.moved(xf), b.id))
        cd.markers.append(marker_line_raw("building", cx, cy, xf.z, xf.yaw, b.name, b.id,
                                          {"archetype": b.arch, "district": b.district}))
        for sg in b.built.signs:
            cd.signs.append(sign_line(sg.moved(xf), b.id))
        for p in building_carves(b.plan):
            cd.carve.append(box_line(p.transformed(xf)))
    log("roblox: buildings encoded")

    # -- infrastructure -------------------------------------------------------------------
    for sw in W.sweeps:
        cx, cy = sw.center()
        cd = ch(cx, cy)
        cd.parts.append(f"#Infrastructure|{sw.cat.title()}")
        for p in sweep_boxes(sw):
            cd.parts.append(part_line(p))
            if p.collide:
                cd.colliders.append(box_line(p))
            if sw.cat in CARVE_CATS and p.size[0] > 2.5:
                cd.carve.append(box_line(carve_above(p)))
    for patch in W.patches:
        cd = ch(*patch[4])
        cd.parts.append(f"#Infrastructure|{patch[0].title()}")
        for p in patch_boxes(patch):
            cd.parts.append(part_line(p))
            cd.colliders.append(box_line(p))
            cd.carve.append(box_line(carve_above(p)))
    for (cat, p) in W.boxes:
        cd = ch(p.pos[0], p.pos[1])
        cd.parts.append(f"#Infrastructure|{cat.title()}")
        cd.parts.append(part_line(p))
        if p.collide:
            cd.colliders.append(box_line(p))
    for (pp, cat) in W.props:
        cd = ch(pp.x, pp.y)
        cd.props.append(f"#{cat.title()}")
        cd.props.append(prop_line(pp, pp))
    for lr in W.lights:
        ch(lr.x, lr.y).lights.append(light_line(lr, ""))
    for mk in W.markers:
        ch(mk.x, mk.y).markers.append(marker_line(mk, ""))
    log("roblox: infrastructure encoded")

    # -- write chunk modules --------------------------------------------------------------
    data_dir = os.path.join(out, "PortSolace")        # Rojo-syncable module folder
    cdir = os.path.join(data_dir, "Chunks")
    os.makedirs(cdir, exist_ok=True)
    sizes = {}
    for name, cd in sorted(chunks.items()):
        if cd is None:
            continue
        cd.parts = _collapse_headers(cd.parts)
        cd.colliders = _collapse_headers(cd.colliders)
        cd.props = _collapse_headers(cd.props)
        src = cd.to_lua()
        with open(os.path.join(cdir, f"{name}.lua"), "w") as fh:
            fh.write(src)
        sizes[name] = len(src)
    log(f"roblox: {len(sizes)} chunk modules, {sum(sizes.values()) / 1e6:.1f} MB")

    # -- tables, terrain, manifest ----------------------------------------------------------
    with open(os.path.join(data_dir, "Palette.lua"), "w") as fh:
        fh.write(palette_lua())
    with open(os.path.join(data_dir, "Kit.lua"), "w") as fh:
        fh.write(kit_lua())
    with open(os.path.join(data_dir, "TerrainData.lua"), "w") as fh:
        fh.write(terrain_lua(W.terrain))
    manifest = build_manifest(W, sizes)
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    with open(os.path.join(data_dir, "Manifest.lua"), "w") as fh:
        fh.write(manifest_lua(manifest))
    write_rbxmx(out, sorted(sizes), log)
    log("roblox: export complete")
    return manifest


def _collapse_headers(lines):
    """Drop repeated identical group headers."""
    out = []
    last = None
    for ln in lines:
        if ln.startswith("#"):
            if ln == last:
                continue
            last = ln
        out.append(ln)
    return out


def prop_line(pw, plocal):
    pos = to_roblox_pos((pw.x, pw.y, pw.z))
    q = quat(to_roblox_rot(rot_z(pw.yaw)))
    sx, sy, sz = pw.scale
    sr = to_roblox_size((sx, sy, sz))
    chans = ";".join(f"{k[1:]}={mat_index(v)}" for k, v in sorted((pw.channels or {}).items()))
    meta = ""
    if pw.meta:
        meta = ";".join(f"{k}={_escape(v)}" for k, v in sorted(pw.meta.items())
                        if v is not None and k != "rooms")
    d = KIT.get(pw.name)
    flags = (1 if pw.interior else 0) | ((d.detail if d else 1) << 1)
    return ",".join([str(KIT_INDEX.get(pw.name, 0)), f(pos[0]), f(pos[1]), f(pos[2]), f(q[0]),
                     f(q[1]), f(q[2]), f(q[3]), f(sr[0]), f(sr[1]), f(sr[2]), str(flags),
                     chans, meta])


def light_line(lr, owner):
    pos = to_roblox_pos((lr.x, lr.y, lr.z))
    d = to_roblox_pos(lr.dir)
    return ",".join([f(pos[0]), f(pos[1]), f(pos[2]), lr.kind, f(lr.color[0]), f(lr.color[1]),
                     f(lr.color[2]), f(lr.range), f(lr.brightness), lr.schedule, f(d[0]),
                     f(d[1]), f(d[2]), owner])


def marker_line(mk, owner):
    return marker_line_raw(mk.kind, mk.x, mk.y, mk.z, mk.yaw, mk.label, owner, mk.meta)


def marker_line_raw(kind, x, y, z, yaw, label, owner, meta):
    pos = to_roblox_pos((x, y, z))
    meta_s = ";".join(f"{k}={_escape(v)}" for k, v in sorted((meta or {}).items()))
    return ",".join([kind, f(pos[0]), f(pos[1]), f(pos[2]), f(math.degrees(yaw)),
                     _escape(label), owner, meta_s])


def sign_line(sg, owner):
    pos = to_roblox_pos((sg.x, sg.y, sg.z))
    q = quat(to_roblox_rot(rot_z(sg.yaw)))
    fg = sg.fg
    if sg.neon and fg.startswith("sign_") and ("neon_" + fg[5:]) in pal.P:
        fg = "neon_" + fg[5:]
    return ",".join([f(pos[0]), f(pos[1]), f(pos[2]), f(q[0]), f(q[1]), f(q[2]), f(q[3]),
                     f(sg.w), f(sg.h), str(mat_index(sg.bg)), str(mat_index(fg)),
                     "1" if sg.neon else "0", "1" if sg.board else "0", owner,
                     _escape(sg.text)])


def palette_lua():
    lines = ["-- Generated palette: index -> material, colour, transparency, glow",
             "return {"]
    for n in PAL_NAMES:
        e = pal.P[n]
        r, g, b = e["rgb"]
        lines.append(f'\t{{name="{n}", material="{e["rbx"]}", color={{{r},{g},{b}}}, '
                     f'transparency={f(1 - e["alpha"])}, glow={f(e["emit"])}}},')
    lines.append("}")
    lines[1] = "local P = {"
    chans = ", ".join(f'{k[1:]} = {PAL_INDEX[v]}' for k, v in sorted(pal.CHANNEL_DEFAULTS.items()))
    lines.append(f"P.channelDefaults = {{{chans}}}")
    lines.append("P.index = {}")
    lines.append("for i, e in ipairs(P) do P.index[e.name] = i end")
    lines.append("return P")
    return "\n".join(lines) + "\n"


def kit_lua():
    lines = ["-- Generated prop kit: definitions + primitive fallbacks (Roblox local space)",
             "local K = {}", "K.defs = {"]
    for n in KIT_NAMES:
        d = KIT[n]
        bx0, by0, bz0, bx1, by1, bz1 = d.bbox
        # bbox in Roblox local space: x, z(up), -y
        bb = (bx0, bz0, -by1, bx1, bz1, -by0)
        cols = []
        for (x0, y0, z0, x1, y1, z1) in d.collision_boxes():
            cols.append("{" + ",".join(f(v) for v in (x0, z0, -y1, x1, z1, -y0)) + "}")
        light = "nil"
        if d.light:
            lt = d.light
            ax, ay, az = lt["at"]
            c = lt["color"]
            light = (f'{{at={{{f(ax)},{f(az)},{f(-ay)}}}, color={{{f(c[0])},{f(c[1])},{f(c[2])}}},'
                     f' range={f(lt["range"])}, brightness={f(lt["brightness"])}, '
                     f'kind="{lt.get("kind", "point")}", schedule="{lt.get("schedule", "")}"}}')
        chans = ",".join(f'"{c[1:]}"' for c in d.channels)
        tags = ",".join(f'"{t}"' for t in d.tags)
        lines.append(f'\t{{name="{n}", cat="{d.cat}", mount="{d.mount}", detail={d.detail}, '
                     f'bbox={{{",".join(f(v) for v in bb)}}}, colliders={{{",".join(cols)}}}, '
                     f'light={light}, channels={{{chans}}}, tags={{{tags}}}}},')
    lines.append("}")
    lines.append("K.prims = {")
    for n in KIT_NAMES:
        body = "\n".join(part_line(p, keep_channel=True) for p in KIT[n].prims)
        lines.append(f"\t[==[\n{body}\n]==],")
    lines.append("}")
    lines.append("K.index = {}")
    lines.append("for i, d in ipairs(K.defs) do K.index[d.name] = i end")
    lines.append("return K")
    return "\n".join(lines) + "\n"


B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def _enc2(v):
    v = max(0, min(4095, int(v)))
    return B64[v >> 6] + B64[v & 63]


def terrain_lua(T):
    """Heights (0.25-stud steps, offset 512) + material ids + water level, 4-stud grid."""
    import numpy as np
    from ..world.terrain import N, RES, MAT_IDS
    H = T.H
    rows_h, rows_m, rows_w = [], [], []
    lvl = getattr(T, "creek_level_grid", None)
    for i in range(N):
        rh = []
        rm = []
        rw = []
        for j in range(N):
            rh.append(_enc2(round(H[i, j] * 4) + 512))
            rm.append(B64[int(T.mat[i, j])])
            if T.sea[i, j]:
                wl = 0.0
            elif lvl is not None and T.creek_d[i, j] < T.creek_hw_grid[i, j] + 2:
                wl = float(lvl[i, j]) + 0.2
            else:
                wl = None
            rw.append("__" if wl is None or wl <= H[i, j] else _enc2(round(wl * 4) + 512))
        rows_h.append("".join(rh))
        rows_m.append("".join(rm))
        rows_w.append("".join(rw))
    mats = ",".join(f'"{m}"' for m in MAT_IDS)
    rbxm = ",".join(f'"{pal.P[m]["rbx"]}"' for m in MAT_IDS)
    return ("-- Generated terrain: 4-stud grid, row i = Blender Y (Roblox -Z), col j = X\n"
            "return {\n"
            f"\tsize = {N}, res = {RES}, origin = {-Lay.HALF}, offset = 512, scale = 4,\n"
            f"\tmaterials = {{{mats}}},\n\trobloxMaterials = {{{rbxm}}},\n"
            "\talphabet = \"" + B64 + "\",\n"
            "\theights = {\n" + "\n".join(f'\t\t"{r}",' for r in rows_h) + "\n\t},\n"
            "\tmats = {\n" + "\n".join(f'\t\t"{r}",' for r in rows_m) + "\n\t},\n"
            "\twater = {\n" + "\n".join(f'\t\t"{r}",' for r in rows_w) + "\n\t},\n"
            "}\n")


def build_manifest(W, sizes):
    roads = []
    for r in W.net.roads:
        pts = []
        for i in range(0, len(r.P), 4):
            p = to_roblox_pos((r.P[i][0], r.P[i][1], r.Z[i]))
            pts.append([round(p[0], 1), round(p[1], 1), round(p[2], 1)])
        roads.append({"name": r.name, "kind": r.kind, "width": r.w, "sidewalk": r.sw,
                      "length": round(r.length, 1), "points": pts,
                      "bridge": any(r.bridge)})
    junctions = []
    for j in W.net.junctions:
        p = to_roblox_pos((j.x, j.y, j.z))
        junctions.append({"pos": [round(v, 1) for v in p], "signal": j.signal,
                          "roads": sorted({W.net.roads[k].name for k in j.members})})
    landmarks = []
    for mk in W.markers:
        if mk.kind == "landmark":
            p = to_roblox_pos((mk.x, mk.y, mk.z))
            landmarks.append({"name": mk.label, "pos": [round(v, 1) for v in p]})
    for b in W.buildings:
        for mk in b.built.markers:
            if mk.kind == "landmark":
                w = mk.moved(b.xf)
                p = to_roblox_pos((w.x, w.y, w.z))
                landmarks.append({"name": mk.label, "pos": [round(v, 1) for v in p],
                                  "building": b.id})
        if b.landmark:
            cx, cy = b.lot.center
            p = to_roblox_pos((cx, cy, b.xf.z))
            landmarks.append({"name": b.name, "pos": [round(v, 1) for v in p],
                              "building": b.id})
    districts = {k: [[round(x, 1), round(-y, 1)] for (x, y) in poly]
                 for k, poly in Lay.DISTRICTS.items()}
    return {
        "town": Lay.TOWN_NAME,
        "coordinates": "Roblox studs; Blender (x, y, z) -> Roblox (x, z, -y)",
        "map_size": [2 * Lay.HALF, 2 * Lay.HALF], "chunk_size": Lay.CHUNK,
        "chunks": sizes, "stats": W.stats,
        "districts": districts, "roads": roads, "junctions": junctions,
        "landmarks": landmarks,
        "buildings": [b.summary() for b in W.buildings],
    }


def manifest_lua(m):
    """A slim Lua view of the manifest for runtime lookups (buildings + landmarks)."""
    lines = ["-- Generated manifest (slim). Full data: manifest.json", "return {"]
    lines.append(f'\ttown = "{m["town"]}",')
    lines.append("\tlandmarks = {")
    for lm in m["landmarks"]:
        p = lm["pos"]
        lines.append(f'\t\t{{name = "{_escape(lm["name"])}", pos = Vector3.new({p[0]}, {p[1]},'
                     f' {p[2]})}},')
    lines.append("\t},")
    lines.append("\tbuildings = {")
    for b in m["buildings"]:
        c = b["center"]
        cr = to_roblox_pos((c[0], c[1], c[2]))
        ents = ", ".join(
            f'{{role="{e["role"]}", pos=Vector3.new({f(to_roblox_pos(e["pos"])[0])}, '
            f'{f(to_roblox_pos(e["pos"])[1])}, {f(to_roblox_pos(e["pos"])[2])})}}'
            for e in b["entrances"])
        lines.append(f'\t\t{b["id"]} = {{name = "{_escape(b["name"])}", archetype = '
                     f'"{b["archetype"]}", district = "{b["district"]}", center = '
                     f'Vector3.new({f(cr[0])}, {f(cr[1])}, {f(cr[2])}), levels = {b["levels"]},'
                     f' entrances = {{{ents}}}}},')
    lines.append("\t},")
    lines.append("}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------
# rbxmx bundle

def _xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class _Ref:
    n = 0

    @classmethod
    def next(cls):
        cls.n += 1
        return f"RBX{cls.n:08X}"


def _item(cls, name, children="", source=None):
    ref = _Ref.next()
    props = f'<string name="Name">{_xml_escape(name)}</string>'
    if source is not None:
        src = source.replace("]]>", "]]]]><![CDATA[>")
        props += f'<ProtectedString name="Source"><![CDATA[{src}]]></ProtectedString>'
    return (f'<Item class="{cls}" referent="{ref}"><Properties>{props}</Properties>'
            f"{children}</Item>")


def write_rbxmx(out, chunk_names, log=print):
    """PortSolace.rbxmx: Folder with data ModuleScripts + tool scripts, ready to drop into
    ServerStorage.  The runtime script is a disabled copy to move into ServerScriptService."""
    def rd(path):
        with open(path) as fh:
            return fh.read()
    tools = {}
    if os.path.isdir(REPO_ROBLOX):
        for fn in sorted(os.listdir(REPO_ROBLOX)):
            if fn.endswith(".lua") or fn.endswith(".luau"):
                tools[fn] = rd(os.path.join(REPO_ROBLOX, fn))
    data_items = []
    for nm in ("Palette", "Kit", "TerrainData", "Manifest"):
        data_items.append(_item("ModuleScript", nm,
                                source=rd(os.path.join(out, "PortSolace", nm + ".lua"))))
    chunk_items = "".join(_item("ModuleScript", c,
                                source=rd(os.path.join(out, "PortSolace", "Chunks",
                                                       c + ".lua"))))
                          for c in chunk_names)
    data_items.append(_item("Folder", "Chunks", chunk_items))
    tool_items = []
    for fn, src in tools.items():
        base = fn.rsplit(".", 1)[0]
        cls = "ModuleScript"
        if base.endswith(".server"):
            cls = "Script"
            base = base[: -len(".server")]
        elif base.endswith(".client"):
            cls = "LocalScript"
            base = base[: -len(".client")]
        tool_items.append(_item(cls, base, source=src))
    root = _item("Folder", "PortSolace", "".join(data_items) + "".join(tool_items))
    xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">'
           + root + "</roblox>")
    path = os.path.join(out, "PortSolace.rbxmx")
    with open(path, "w") as fh:
        fh.write(xml)
    log(f"roblox: wrote {path} ({len(xml) / 1e6:.1f} MB)")
