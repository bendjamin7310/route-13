"""Convert primitive lists into Blender meshes (flat-shaded, box-projected UVs)."""

from __future__ import annotations

import math

import bpy

from .. import palette as pal
from . import materials

UV_SCALE = 1.0 / 8.0   # one texture repeat every 8 studs

_BOX_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
_BOX_CORNERS = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
# wedge: full height at -Y, zero at +Y
_WEDGE_CORNERS = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1))
_WEDGE_FACES = ((0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4))

_unit_cache = {}


def _cyl_unit(n):
    key = ("cyl", n)
    if key in _unit_cache:
        return _unit_cache[key]
    verts = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        verts.append((math.cos(a), math.sin(a), -1.0))
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        verts.append((math.cos(a), math.sin(a), 1.0))
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    _unit_cache[key] = (verts, faces)
    return verts, faces


def _ball_unit(seg=8, rings=5):
    key = ("ball", seg, rings)
    if key in _unit_cache:
        return _unit_cache[key]
    verts = [(0.0, 0.0, -1.0)]
    for r in range(1, rings):
        phi = math.pi * r / rings
        for s in range(seg):
            th = 2 * math.pi * s / seg
            verts.append((math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th),
                          -math.cos(phi)))
    verts.append((0.0, 0.0, 1.0))
    top = len(verts) - 1
    faces = []
    for s in range(seg):
        faces.append((0, 1 + (s + 1) % seg, 1 + s))
    for r in range(rings - 2):
        a0 = 1 + r * seg
        b0 = 1 + (r + 1) * seg
        for s in range(seg):
            s1 = (s + 1) % seg
            faces.append((a0 + s, a0 + s1, b0 + s1, b0 + s))
    last = 1 + (rings - 2) * seg
    for s in range(seg):
        faces.append((last + s, last + (s + 1) % seg, top))
    _unit_cache[key] = (verts, faces)
    return verts, faces


def prim_geometry(p):
    """Return (verts, faces) for one primitive in its parent's frame."""
    k = p.kind
    if k == "mesh":
        vs, fs = p.data
        px, py, pz = p.pos
        return [(v[0] + px, v[1] + py, v[2] + pz) for v in vs], fs
    hx, hy, hz = p.size[0] * 0.5, p.size[1] * 0.5, p.size[2] * 0.5
    if k == "box":
        unit, faces = _BOX_CORNERS, _BOX_FACES
    elif k == "wedge":
        unit, faces = _WEDGE_CORNERS, _WEDGE_FACES
    elif k == "cyl":
        unit, faces = _cyl_unit(int(p.data or 12))
    else:
        unit, faces = _ball_unit()
    r = p.rot
    px, py, pz = p.pos
    out = []
    for (ux, uy, uz) in unit:
        lx, ly, lz = ux * hx, uy * hy, uz * hz
        out.append((px + r[0] * lx + r[1] * ly + r[2] * lz,
                    py + r[3] * lx + r[4] * ly + r[5] * lz,
                    pz + r[6] * lx + r[7] * ly + r[8] * lz))
    return out, faces


def build_mesh(name, prims, channels=None, mat_slots=None):
    """Build one mesh containing all prims (multi-material).  Returns the mesh."""
    verts = []
    faces = []
    fmat = []
    slot_of = {}
    slots = []
    for p in prims:
        m = pal.resolve(p.mat, channels) if not (mat_slots and p.mat in mat_slots) else p.mat
        if m == "invisible":
            continue
        if m not in slot_of:
            slot_of[m] = len(slots)
            slots.append(m)
        si = slot_of[m]
        vs, fs = prim_geometry(p)
        base = len(verts)
        verts.extend(vs)
        for f in fs:
            faces.append(tuple(base + i for i in f))
            fmat.append(si)
    me = bpy.data.meshes.new(name)
    if not faces:
        return me, []
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("material_index", fmat)
    for m in slots:
        if m.startswith("$"):
            me.materials.append(materials.get(pal.CHANNEL_DEFAULTS.get(m, "plastic_gray")))
        else:
            me.materials.append(materials.get(m))
    _box_uv(me, verts)
    me.validate(clean_customdata=False)
    return me, slots


def _box_uv(me, verts):
    uv = me.uv_layers.new(name="UVMap")
    data = []
    polys = me.polygons
    loops = me.loops
    for poly in polys:
        n = poly.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in poly.loop_indices:
            v = verts[loops[li].vertex_index]
            if az >= ax and az >= ay:
                data.extend((v[0] * UV_SCALE, v[1] * UV_SCALE))
            elif ax >= ay:
                data.extend((v[1] * UV_SCALE, v[2] * UV_SCALE))
            else:
                data.extend((v[0] * UV_SCALE, v[2] * UV_SCALE))
    uv.data.foreach_set("uv", data)


def split_by_material(prims, channels=None):
    out = {}
    for p in prims:
        m = pal.resolve(p.mat, channels)
        out.setdefault(m, []).append(p)
    return out
