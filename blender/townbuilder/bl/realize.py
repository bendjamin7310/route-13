"""Realise a generated ``World`` as a Blender scene (collections per the brief)."""

from __future__ import annotations

import math
import time
from collections import defaultdict

import bpy
from mathutils import Matrix

from ..geom import Prim
from ..world import layout as Lay
from ..world.model import chunk_of, chunk_name
from .scene import SceneBuilder
from . import materials
from .meshing import build_mesh

SWEEP_COLLECTION = {
    "ROADS": ("TOWN", "ROADS"), "SIDEWALKS": ("TOWN", "SIDEWALKS"),
    "BRIDGES": ("TOWN", "ROADS", "BRIDGES"), "RAIL": ("TOWN", "ROADS", "RAIL"),
    "PROPS": ("TOWN", "PROPS"), "LANDMARKS": ("TOWN", "LANDMARKS"),
    "WATERFRONT": ("TOWN", "WATERFRONT"), "PARKS": ("TOWN", "PARKS"),
    "OUTSKIRTS": ("TOWN", "OUTSKIRTS"), "VEGETATION": ("TOWN", "VEGETATION"),
    "VEHICLES": ("TOWN", "VEHICLES"),
}


def _col(cat):
    return SWEEP_COLLECTION.get(cat, ("TOWN", cat))


def _mesh_obj(sb, name, verts, faces, mats, col_path, props=None):
    """mats: list of material keys, one per face."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    slots = []
    idx = {}
    for m in mats:
        if m not in idx:
            idx[m] = len(slots)
            slots.append(m)
    me.polygons.foreach_set("material_index", [idx[m] for m in mats])
    for m in slots:
        me.materials.append(materials.get(m))
    from .meshing import _box_uv
    _box_uv(me, verts)
    me.validate(clean_customdata=False)
    o = bpy.data.objects.new(name, me)
    if props:
        for k, v in props.items():
            o[k] = v
    sb.collection(col_path).objects.link(o)
    sb.stats["objects"] += 1
    sb.stats["tris"] += sum(len(p.vertices) - 2 for p in me.polygons)
    return o


def realize(W, lights_mode="all", log=print, include_interiors=True):
    t0 = time.time()
    sb = SceneBuilder(lights_mode=lights_mode)
    for sub in (("TOWN", "ROADS", "BRIDGES"), ("TOWN", "ROADS", "RAIL"),
                ("TOWN", "TERRAIN", "WATER")):
        sb.collection(sub)

    # ---- terrain tiles -------------------------------------------------------------
    T = W.terrain
    for ti, tj, org, verts, per in T.tile_meshes():
        faces, mats = [], []
        for m, fl in per.items():
            faces.extend(fl)
            mats.extend([m] * len(fl))
        o = _mesh_obj(sb, f"Terrain_{ti}_{tj}", verts, faces, mats, ("TOWN", "TERRAIN"),
                      {"chunk": chunk_name(chunk_of(org[0] + 128, org[1] + 128))})
    for (name, mat, verts, faces) in W.water:
        _mesh_obj(sb, name, verts, faces, [mat] * len(faces), ("TOWN", "TERRAIN", "WATER"))
    log(f"terrain + water objects ({time.time() - t0:.1f}s)")

    # ---- sweeps + patches + boxes, merged per (category, chunk, material) -------------
    groups = defaultdict(lambda: ([], [], []))   # key -> (verts, faces, mats)

    def add(cat, chunk, mat, verts, faces):
        g = groups[(cat, chunk)]
        base = len(g[0])
        g[0].extend(verts)
        for f in faces:
            g[1].append(tuple(base + i for i in f))
            g[2].append(mat)

    for sw in W.sweeps:
        v, f = sw.mesh()
        cx, cy = sw.center()
        add(sw.cat, chunk_of(cx, cy), sw.mat, v, f)
    for patch in W.patches:
        cat, mat, verts, faces, c = patch[:5]
        add(cat, chunk_of(*c), mat, verts, faces)
    from .meshing import prim_geometry
    for (cat, p) in W.boxes:
        v, f = prim_geometry(p)
        add(cat, chunk_of(p.pos[0], p.pos[1]), p.mat, v, f)
    for (cat, chunk), (verts, faces, mats) in groups.items():
        # one object per material so each maps to a single Roblox MeshPart
        by_mat = defaultdict(list)
        for i, m in enumerate(mats):
            by_mat[m].append(i)
        for m, fis in by_mat.items():
            used = {}
            nv, nf = [], []
            for fi in fis:
                nf.append(tuple(used.setdefault(vi, len(used)) for vi in faces[fi]))
            inv = sorted(used.items(), key=lambda kv: kv[1])
            nv = [verts[vi] for vi, _ in inv]
            _mesh_obj(sb, f"{cat.title()}_{chunk_name(chunk)}.{m}", nv, nf, [m] * len(nf),
                      _col(cat), {"chunk": chunk_name(chunk), "material_key": m})
    log(f"infrastructure objects ({time.time() - t0:.1f}s)")

    # ---- world props, lights, markers, signs ------------------------------------------
    for (pp, cat) in W.props:
        o = sb.prop(pp, _col(cat))
        if o is not None:
            o["chunk"] = chunk_name(chunk_of(pp.x, pp.y))
    for lr in W.lights:
        sb.light(lr, ("TOWN", "LIGHTING"))
    for mk in W.markers:
        sb.marker(mk, ("TOWN", "GAMEPLAY"))
    log(f"world props/lights ({time.time() - t0:.1f}s)")

    # ---- buildings --------------------------------------------------------------------
    for k, b in enumerate(W.buildings):
        xf = b.xf
        mw = Matrix.Translation((xf.x, xf.y, xf.z)) @ Matrix.Rotation(xf.yaw, 4, "Z")
        root = sb.empty(f"{b.id}_{b.name}"[:60], b.ext_path, mw, kind="CUBE", size=3.0)
        root["building_id"] = b.id
        root["archetype"] = b.arch
        root["district"] = b.district
        root["display_name"] = b.name
        root["levels"] = len(b.plan.levels)
        root["detail"] = b.plan.detail
        root["landmark"] = bool(b.landmark)
        root["chunk"] = chunk_name(b.chunk)
        base = b.id
        for o in sb.prims_objects(f"{base}.ext", b.built.ext.prims, b.ext_path, root,
                                  props={"building_id": b.id, "part": "exterior"}):
            o.matrix_parent_inverse = Matrix()
        if include_interiors:
            for o in sb.prims_objects(f"{base}.int", b.built.int.prims, b.int_path, root,
                                      props={"building_id": b.id, "part": "interior"}):
                o.matrix_parent_inverse = Matrix()
        for pp in b.built.props:
            if pp.interior and not include_interiors:
                continue
            o = sb.prop(pp, b.int_path if pp.interior else b.ext_path, root)
            if o is not None:
                o.matrix_parent_inverse = Matrix()
                o["building_id"] = b.id
        for lr in b.built.lights:
            lw = lr.moved(xf)
            sb.light(lw, ("TOWN", "LIGHTING"))
        for mk in b.built.markers:
            mw_ = mk.moved(xf)
            mw_.meta = dict(mw_.meta or {})
            mw_.meta["building"] = b.id
            sb.marker(mw_, ("TOWN", "GAMEPLAY"), prefix=f"{b.id}.")
        for i, sg in enumerate(b.built.signs):
            sw_ = sg.moved(xf)
            sb.sign(sw_, b.ext_path, name=f"{b.id}.sign{i}")
        if (k + 1) % 50 == 0:
            log(f"buildings {k + 1}/{len(W.buildings)} ({time.time() - t0:.1f}s, "
                f"{sb.stats['objects']} objects)")
    for s in W.signs:
        sb.sign(s[0], _col(s[1]))
    _lighting_rig()
    log(f"realised: {sb.stats} ({time.time() - t0:.1f}s)")
    return sb


def _lighting_rig():
    """Late-afternoon sun + Nishita sky + Roblox Lighting presets stored on an empty."""
    sc = bpy.context.scene
    col = bpy.data.collections.get("LIGHTING")
    sun = bpy.data.lights.new("Sun_LateAfternoon", "SUN")
    sun.energy = 3.4
    sun.color = (1.0, 0.86, 0.68)
    sun.angle = math.radians(2.0)
    so = bpy.data.objects.new("Sun_LateAfternoon", sun)
    # sun low in the west-south-west
    so.rotation_euler = (math.radians(68), 0.0, math.radians(-118))
    (col or sc.collection).objects.link(so)
    w = bpy.data.worlds.get("TownSky") or bpy.data.worlds.new("TownSky")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(22)
        sky.sun_rotation = math.radians(208)
        sky.altitude = 40
        sky.air_density = 1.4
        sky.dust_density = 2.2
        sky.sun_disc = False
    except Exception:
        pass
    bg.inputs[1].default_value = 0.55
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    sc.world = w
    e = bpy.data.objects.new("RobloxLighting", None)
    e["ClockTime"] = 17.6
    e["GeographicLatitude"] = 34.0
    e["Brightness"] = 2.4
    e["EnvironmentDiffuseScale"] = 0.6
    e["EnvironmentSpecularScale"] = 0.5
    e["Ambient"] = [90, 82, 96]
    e["OutdoorAmbient"] = [128, 118, 132]
    e["ColorShift_Top"] = [255, 222, 186]
    e["Atmosphere_Density"] = 0.32
    e["Atmosphere_Haze"] = 1.6
    e["Atmosphere_Color"] = [214, 186, 160]
    e["Atmosphere_Decay"] = [120, 96, 110]
    e["Bloom_Intensity"] = 0.35
    e["ColorCorrection_Saturation"] = 0.05
    e["ColorCorrection_TintColor"] = [255, 244, 232]
    (col or sc.collection).objects.link(e)
