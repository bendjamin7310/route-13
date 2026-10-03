"""Preview renders of the generated town (Cycles, headless)."""

from __future__ import annotations

import math
import os

import bpy
from mathutils import Vector

from ..world import layout as Lay

VIEWS = {
    # name: (camera location, target, lens or ("ortho", scale), resolution, mode)
    "overview": ((0.0, 0.0, 1800.0), (0.0, 0.001, 0.0), ("ortho", 2600.0), (2048, 2048), "day"),
    "aerial": ((1150.0, -1100.0, 620.0), (60.0, -60.0, 0.0), 30.0, (1920, 1080), "day"),
    "downtown": ((560.0, -520.0, 230.0), (150.0, -90.0, 10.0), 28.0, (1920, 1080), "day"),
    "harbor": ((1020.0, -260.0, 160.0), (640.0, -560.0, 0.0), 30.0, (1920, 1080), "day"),
    "motel": ((-760.0, -660.0, 70.0), (-980.0, -560.0, 8.0), 26.0, (1920, 1080), "dusk"),
    "industrial": ((180.0, 260.0, 220.0), (520.0, 640.0, 10.0), 28.0, (1920, 1080), "day"),
    "civic": ((420.0, -200.0, 120.0), (560.0, 60.0, 10.0), 28.0, (1920, 1080), "day"),
    "street": (None, None, 24.0, (1920, 1080), "dusk"),
    "night": ((560.0, -520.0, 230.0), (150.0, -90.0, 10.0), 28.0, (1920, 1080), "night"),
}


LIGHT_RADIUS = 520.0     # dusk/night renders only light the neighbourhood of the view


def _near(o, loc, target):
    p = o.matrix_world.translation
    for c in (target, loc):
        if (p.x - c[0]) ** 2 + (p.y - c[1]) ** 2 < LIGHT_RADIUS ** 2:
            return True
    return False


def _set_mode(mode, loc=(0.0, 0.0, 0.0), target=(0.0, 0.0, 0.0)):
    sc = bpy.context.scene
    sun = bpy.data.objects.get("Sun_LateAfternoon")
    w = sc.world
    sky = w.node_tree.nodes.get("Sky Texture") if w and w.use_nodes else None
    bg = w.node_tree.nodes.get("Background") if w and w.use_nodes else None
    point_lights = [o for o in bpy.data.objects if o.type == "LIGHT" and o.name != sun.name]
    if mode == "day":
        sun.data.energy = 3.4
        sun.data.color = (1.0, 0.86, 0.68)
        sun.rotation_euler = (math.radians(66), 0.0, math.radians(-118))
        if sky:
            sky.sun_elevation = math.radians(24)
        if bg:
            bg.inputs[1].default_value = 0.55
        for o in point_lights:
            o.hide_render = True
    elif mode == "dusk":
        sun.data.energy = 1.6
        sun.data.color = (1.0, 0.62, 0.42)
        sun.rotation_euler = (math.radians(84), 0.0, math.radians(-115))
        if sky:
            sky.sun_elevation = math.radians(5)
        if bg:
            bg.inputs[1].default_value = 0.35
        for o in point_lights:
            o.hide_render = (o.get("schedule") not in ("night", "late", "always", "res", "biz")
                             or not _near(o, loc, target))
    else:  # night
        sun.data.energy = 0.05
        sun.data.color = (0.6, 0.7, 1.0)
        if sky:
            sky.sun_elevation = math.radians(-4)
        if bg:
            bg.inputs[1].default_value = 0.04
        for o in point_lights:
            o.hide_render = (o.get("schedule") == "dark") or not _near(o, loc, target)


def _camera(loc, target, lens):
    cd = bpy.data.cameras.get("PreviewCam") or bpy.data.cameras.new("PreviewCam")
    cd.clip_start = 0.5
    cd.clip_end = 8000.0
    if isinstance(lens, tuple):
        cd.type = "ORTHO"
        cd.ortho_scale = lens[1]
    else:
        cd.type = "PERSP"
        cd.lens = lens
    co = bpy.data.objects.get("PreviewCam")
    if co is None:
        co = bpy.data.objects.new("PreviewCam", cd)
        bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return co


def render_views(W, names, out, samples=32, log=print):
    os.makedirs(out, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.transparent_max_bounces = 6
    sc.cycles.use_light_tree = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast" if hasattr(sc.view_settings, "look") \
        else "None"
    if "all" in names:
        names = list(VIEWS)
    for n in names:
        if n not in VIEWS:
            continue
        loc, target, lens, res, mode = VIEWS[n]
        if n == "motel":
            # aim at the motel itself: from the front-left, over the parking lot
            mb = next((b for b in W.buildings if b.arch == "motel"), None)
            if mb is not None:
                xf = mb.xf
                cx, cy, cz = xf.point((mb.plan.w / 2, mb.plan.d / 2, 0.0))
                fx, fy, _ = xf.vec((0.0, -1.0, 0.0))
                sx, sy, _ = xf.vec((1.0, 0.0, 0.0))
                loc = (cx + fx * 150 - sx * 70, cy + fy * 150 - sy * 70, cz + 48.0)
                target = (cx, cy, cz + 6.0)
        if n == "street":
            r = W.net.by_name.get("Market Street")
            x, y, z, tx, ty = r.at(r.length * 0.55)
            nx, ny = -ty, tx
            loc = (x - tx * 40 + nx * 6, y - ty * 40 + ny * 6, z + 6.5)
            target = (x + tx * 60, y + ty * 60, z + 6.0)
        _set_mode(mode, loc, target)
        _camera(loc, target, lens)
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(out, f"{n}.png")
        bpy.ops.render.render(write_still=True)
        log(f"rendered {n}")
