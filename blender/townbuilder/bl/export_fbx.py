"""Chunked FBX / OBJ export for the Roblox 3D Importer (the MeshPart workflow).

One file per 512-stud chunk containing everything visible in that chunk:

* building shells and interiors (one object per material -> one MeshPart each),
* roads, sidewalks, bridges, rail, landmark structures and other merged infrastructure,
* the terrain surface (4-stud grid tiles) and the sea / creek water,
* every kit prop (furniture, fixtures, vehicles, boats, trees ...) baked into merged
  per-material meshes, with their recolour channels resolved,
* sign boards and their lettering.

Every mesh carries its colour twice: as the material base colour and as a per-corner
vertex colour (sRGB), so the colour survives importers that drop one or the other.

Axis conversion: Blender (+X, +Y fwd, +Z up) -> FBX/OBJ (-Z forward, +Y up), i.e. Roblox
(x, z, -y).  Each file contains a 1-stud cube named ``ANCHOR_<chunk>`` at the chunk's
south-west corner on the ground plane; ``anchors.json`` lists where each anchor belongs in
Roblox (studs) for importers that do not keep scene positions.

Roblox caps a MeshPart at 20k triangles; larger objects are split spatially first.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict

import bpy

from .. import palette as pal
from ..kit import KIT
from ..world import layout as Lay
from ..world.model import chunk_of, chunk_name
from . import materials
from .meshing import _box_uv, prim_geometry

MAX_TRIS = 19000
EXPORT_COLLECTION = "EXPORT_TEMP"


def _tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def _chunk_of_object(o):
    c = o.get("chunk")
    if c is None and o.parent is not None:
        c = o.parent.get("chunk")
    if c is None:
        # unparented world objects (water tiles, signs): chunk of their bounds centre
        mw = o.matrix_world
        pts = [mw @ v.co for v in o.data.vertices] if o.type == "MESH" and o.data.vertices \
            else [o.matrix_world.translation]
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        c = chunk_name(chunk_of(cx, cy))
    return c


def _exportable(o):
    if o.type != "MESH" or o.get("kit_prop"):
        return False
    cols = {c.name for c in o.users_collection}
    if "KIT" in cols or EXPORT_COLLECTION in cols:
        return False
    return True


def _split(o, log):
    """Split a mesh object into spatial pieces of at most MAX_TRIS triangles."""
    me = o.data
    tris = _tris(me)
    if tris <= MAX_TRIS:
        return [o]
    k = tris // MAX_TRIS + 1
    mw = o.matrix_world
    verts = [v.co.copy() for v in me.vertices]
    polys = [(tuple(p.vertices), p.material_index) for p in me.polygons]
    cents = []
    for (vs, _) in polys:
        c = sum((verts[i] for i in vs), verts[vs[0]] * 0) / len(vs)
        cents.append(c)
    xs = [c.x for c in cents]
    ys = [c.y for c in cents]
    axis = 0 if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else 1
    order = sorted(range(len(polys)), key=lambda i: cents[i][axis])
    # a piece is cut on triangles, not polygons, so allow some slack per piece
    per = len(order) // k + 1
    pieces = []
    for n in range(k):
        sel = order[n * per:(n + 1) * per]
        if not sel:
            continue
        used = {}
        faces = []
        for i in sel:
            faces.append(tuple(used.setdefault(v, len(used)) for v in polys[i][0]))
        nv = [None] * len(used)
        for v, j in used.items():
            nv[j] = tuple(verts[v])
        nm = bpy.data.meshes.new(f"{me.name}.p{n}")
        nm.from_pydata(nv, [], faces)
        for m in me.materials:
            nm.materials.append(m)
        nm.polygons.foreach_set("material_index", [polys[i][1] for i in sel])
        _box_uv(nm, nv)
        nm.validate(clean_customdata=False)
        no = bpy.data.objects.new(f"{o.name}.p{n}", nm)
        no.matrix_world = mw
        for key in o.keys():
            no[key] = o[key]
        for c in o.users_collection:
            c.objects.link(no)
        pieces.append(no)
    log(f"export: split {o.name} ({tris} tris) into {len(pieces)}")
    bpy.data.objects.remove(o)
    out = []
    for p in pieces:                      # a piece can still be over the cap: split again
        out.extend(_split(p, log))
    return out


def _material_srgb(mat):
    if mat is None:
        return (0.64, 0.64, 0.65, 1.0)
    c = mat.get("roblox_color")
    if c is not None:
        return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0)
    return tuple(mat.diffuse_color)


def _paint_vertex_colors(o):
    """Per-corner sRGB colour from each polygon's material (object or data slots)."""
    me = o.data
    if not me.polygons:
        return
    slot_cols = []
    for i in range(max(1, len(o.material_slots))):
        mat = o.material_slots[i].material if i < len(o.material_slots) else None
        slot_cols.append(_material_srgb(mat))
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR",
                                                                     "CORNER")
    mi = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", mi)
    flat = []
    for poly, m in zip(me.polygons, mi):
        col = slot_cols[m] if m < len(slot_cols) else slot_cols[0]
        flat.extend(col * poly.loop_total)
    if hasattr(attr.data[0], "color_srgb"):
        attr.data.foreach_set("color_srgb", flat)
    else:
        attr.data.foreach_set("color", flat)
    me.color_attributes.active_color = attr


def _prop_meshes(W, coll, log, exterior_only=False):
    """Bake every kit prop (world + building props) into merged per (chunk, material)
    meshes in world space (``exterior_only``: skip props inside buildings)."""
    groups = defaultdict(lambda: ([], []))          # (chunk, mat) -> (verts, faces)
    geo_cache = {}

    def add(pp):
        d = KIT.get(pp.name)
        if d is None:
            return
        if pp.name not in geo_cache:
            geo_cache[pp.name] = [(p.mat, *prim_geometry(p)) for p in d.prims]
        c, s = math.cos(pp.yaw), math.sin(pp.yaw)
        sx, sy, sz = pp.scale
        ch = chunk_name(chunk_of(pp.x, pp.y))
        for (mat, vs, fs) in geo_cache[pp.name]:
            m = pal.resolve(mat, pp.channels) if mat.startswith("$") else mat
            if m == "invisible":
                continue
            verts, faces = groups[(ch, m)]
            base = len(verts)
            for (x, y, z) in vs:
                x, y, z = x * sx, y * sy, z * sz
                verts.append((pp.x + c * x - s * y, pp.y + s * x + c * y, pp.z + z))
            for f in fs:
                faces.append(tuple(base + i for i in f))

    n = 0
    for (pp, _cat) in W.props:
        add(pp)
        n += 1
    for b in W.buildings:
        for pp in b.built.props:
            if exterior_only and pp.interior:
                continue
            add(pp.moved(b.xf))
            n += 1
    objs = []
    for (ch, m), (verts, faces) in groups.items():
        me = bpy.data.meshes.new(f"Props_{ch}.{m}")
        me.from_pydata(verts, [], faces)
        me.materials.append(materials.get(m))
        _box_uv(me, verts)
        me.validate(clean_customdata=False)
        o = bpy.data.objects.new(f"Props_{ch}.{m}", me)
        o["chunk"] = ch
        o["material_key"] = m
        coll.objects.link(o)
        objs.append(o)
    log(f"export: baked {n} props into {len(objs)} merged meshes")
    return objs


def _anchor(chunk, coll):
    i, j = (int(v) for v in chunk[1:].split("_"))
    x0 = -Lay.HALF + i * Lay.CHUNK
    y0 = -Lay.HALF + j * Lay.CHUNK
    me = bpy.data.meshes.new(f"ANCHOR_{chunk}")
    h = 0.5
    vs = [(x0 - h, y0 - h, -h), (x0 + h, y0 - h, -h), (x0 + h, y0 + h, -h), (x0 - h, y0 + h, -h),
          (x0 - h, y0 - h, h), (x0 + h, y0 - h, h), (x0 + h, y0 + h, h), (x0 - h, y0 + h, h)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(vs, [], fs)
    o = bpy.data.objects.new(f"ANCHOR_{chunk}", me)
    coll.objects.link(o)
    return o, [x0, 0.0, -y0]


def export_fbx(out, log=print, W=None, obj=False, props=True, single=None,
               exterior_only=False):
    """Write PortSolace_<chunk>.fbx (and .obj/.mtl with ``obj``) for every chunk, or with
    ``single="Name"`` one Name.fbx for the whole town.  ``exterior_only`` leaves out
    interior geometry and the props inside buildings."""
    os.makedirs(out, exist_ok=True)
    tmp = bpy.data.collections.new(EXPORT_COLLECTION)
    bpy.context.scene.collection.children.link(tmp)
    by_chunk = defaultdict(list)
    for o in list(bpy.data.objects):
        if not _exportable(o):
            continue
        if exterior_only and o.get("part") == "interior":
            continue
        by_chunk[_chunk_of_object(o)].append(o)
    if props and W is not None:
        for o in _prop_meshes(W, tmp, log, exterior_only):
            by_chunk[o["chunk"]].append(o)
    if single:
        merged = []
        for ch in sorted(by_chunk):
            merged.extend(by_chunk[ch])
        by_chunk = {single: merged}
    anchors = {}
    for chunk in sorted(by_chunk):
        objs = []
        for o in by_chunk[chunk]:
            objs.extend(_split(o, log))
        for o in objs:
            _paint_vertex_colors(o)
        a, pos = _anchor(chunk if not single else "C0_0", tmp)
        tris = sum(_tris(o.data) for o in objs)
        anchors[chunk] = {"anchor": a.name, "roblox_position": pos, "objects": len(objs),
                          "triangles": tris}
        for ob in bpy.context.view_layer.objects:
            ob.select_set(False)
        sel = 0
        for ob in objs + [a]:
            try:
                ob.select_set(True)
                sel += 1
            except RuntimeError:
                pass  # object not in the view layer (excluded collection)
        stem = single or f"PortSolace_{chunk}"
        path = os.path.join(out, f"{stem}.fbx")
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True, object_types={"MESH"},
            axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_NONE", global_scale=1.0,
            use_mesh_modifiers=False, mesh_smooth_type="FACE", use_tspace=False,
            colors_type="SRGB", add_leaf_bones=False, bake_anim=False, path_mode="STRIP",
            use_custom_props=True)
        anchors[chunk]["file"] = os.path.basename(path)
        anchors[chunk]["bytes"] = os.path.getsize(path)
        msg = f"export: {os.path.basename(path)} ({sel} objects, {tris} tris, " \
              f"{os.path.getsize(path) / 1e6:.1f} MB)"
        if obj:
            opath = os.path.join(out, f"{stem}.obj")
            bpy.ops.wm.obj_export(
                filepath=opath, export_selected_objects=True, forward_axis="NEGATIVE_Z",
                up_axis="Y", global_scale=1.0, apply_modifiers=False, export_uv=True,
                export_normals=True, export_colors=True, export_materials=True,
                export_triangulated_mesh=False, export_object_groups=False,
                path_mode="STRIP")
            anchors[chunk]["obj"] = os.path.basename(opath)
            msg += f", obj {os.path.getsize(opath) / 1e6:.1f} MB"
        log(msg)
    for ob in list(tmp.objects):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(tmp)
    with open(os.path.join(out, f"{single}_anchor.json" if single else "anchors.json"),
              "w") as fh:
        json.dump({"note": "Roblox studs. Files keep world positions (1 unit = 1 stud, Y up). "
                           "If an importer recentres a chunk, move it so its ANCHOR part "
                           "centre is at roblox_position, then delete the anchor.",
                   "chunks": anchors}, fh, indent=1)
    return anchors
