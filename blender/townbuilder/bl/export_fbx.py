"""Chunked FBX export for the Roblox 3D Importer (the MeshPart workflow).

One FBX per 512-stud chunk with every static mesh of that chunk: building shells and
interiors (one object per material -> one MeshPart each), roads, sidewalks, bridges, rail,
landmark structures and other merged infrastructure.  Kit props, lights, markers and signs
are not exported: TownBuilder places those from the Roblox data modules.

Axis conversion: Blender (+X, +Y fwd, +Z up) -> FBX (-Z forward, +Y up), i.e. Roblox
(x, z, -y).  Each file contains a 1-stud cube named ``ANCHOR_<chunk>`` at the chunk's
south-west corner on the ground plane: after importing, move the model so that this
part sits at the position recorded in ``fbx/anchors.json`` (Roblox coordinates).

Roblox caps a MeshPart at 20k triangles; larger objects are split spatially first.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

import bpy

from ..world import layout as Lay
from .meshing import _box_uv

MAX_TRIS = 19000
SIGN_RE = re.compile(r"(^|\.)sign\d*\.board|^Sign\.board", re.IGNORECASE)


def _tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def _chunk_of_object(o):
    c = o.get("chunk")
    if c is None and o.parent is not None:
        c = o.parent.get("chunk")
    return c


def _exportable(o, terrain):
    if o.type != "MESH" or o.get("kit_prop") or o.get("sign_text"):
        return False
    if SIGN_RE.search(o.name):
        return False
    cols = {c.name for c in o.users_collection}
    if "KIT" in cols:
        return False
    if not terrain and ("TERRAIN" in cols or "WATER" in cols):
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
        mi = [polys[i][1] for i in sel]
        nm.polygons.foreach_set("material_index", mi)
        _box_uv(nm, nv)
        nm.validate(clean_customdata=False)
        no = bpy.data.objects.new(f"{o.name}.p{n}", nm)
        no.matrix_world = mw
        for key in o.keys():
            no[key] = o[key]
        for c in o.users_collection:
            c.objects.link(no)
        pieces.append(no)
    log(f"fbx: split {o.name} ({tris} tris) into {len(pieces)}")
    bpy.data.objects.remove(o)
    return pieces


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
    # Roblox position of the anchor centre
    return o, [x0, 0.0, -y0]


def export_fbx(out, log=print, terrain=False):
    os.makedirs(out, exist_ok=True)
    by_chunk = defaultdict(list)
    for o in list(bpy.data.objects):
        if not _exportable(o, terrain):
            continue
        c = _chunk_of_object(o)
        if c is None:
            continue
        by_chunk[c].extend(_split(o, log))
    tmp = bpy.data.collections.new("FBX_ANCHORS")
    bpy.context.scene.collection.children.link(tmp)
    anchors = {}
    for chunk in sorted(by_chunk):
        objs = by_chunk[chunk]
        a, pos = _anchor(chunk, tmp)
        anchors[chunk] = {"anchor": a.name, "roblox_position": pos, "objects": len(objs)}
        for ob in bpy.context.view_layer.objects:
            ob.select_set(False)
        sel = 0
        for ob in objs + [a]:
            try:
                ob.select_set(True)
                sel += 1
            except RuntimeError:
                pass  # object not in the view layer (excluded collection)
        path = os.path.join(out, f"PortSolace_{chunk}.fbx")
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True, object_types={"MESH"},
            axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_NONE", global_scale=1.0,
            use_mesh_modifiers=False, mesh_smooth_type="FACE", use_tspace=False,
            add_leaf_bones=False, bake_anim=False, path_mode="STRIP",
            use_custom_props=True)
        anchors[chunk]["file"] = os.path.basename(path)
        anchors[chunk]["bytes"] = os.path.getsize(path)
        log(f"fbx: {os.path.basename(path)} ({sel} objects, "
            f"{os.path.getsize(path) / 1e6:.1f} MB)")
    for ob in list(tmp.objects):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(tmp)
    with open(os.path.join(out, "anchors.json"), "w") as fh:
        json.dump({"note": "Roblox studs. Move each imported chunk so its ANCHOR part centre "
                           "is at roblox_position, then delete the anchor.",
                   "chunks": anchors}, fh, indent=1)
    return anchors
