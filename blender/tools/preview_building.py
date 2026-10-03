"""Render a single archetype for inspection (exterior + top-down cutaway per level).

    python tools/preview_building.py house_medium 50 50 out_dir [seed]

Environment: LEVELS=0,1 renders only those floors; EXTERIOR=0 skips the exterior shots.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import bpy
from mathutils import Vector

from townbuilder import kit, archetypes
from townbuilder.archi.build import build_plan
from townbuilder.bl.scene import SceneBuilder
from townbuilder.bl import materials
from townbuilder.records import PropPlace


def setup_render(res=(900, 700), samples=24):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.72, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(3)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    sc.collection.objects.link(so)


def camera(loc, target, ortho=None, lens=35):
    cd = bpy.data.cameras.new("Cam")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cd.lens = lens
    cd.clip_end = 5000
    co = bpy.data.objects.new("Cam", cd)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(co)
    bpy.context.scene.camera = co
    return co


def build(name, w, d, seed, cut=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials.reset()
    kit.load_all()
    archetypes.load_all()
    plan = archetypes.make(name, w, d, seed, detail=3)
    b = build_plan(plan, seed)
    sb = SceneBuilder(lights_mode="all")
    keep = lambda p: cut is None or p.pos[2] < cut
    ext = [p for p in b.ext.prims if keep(p)]
    inn = [p for p in b.int.prims if keep(p)]
    # ground plate
    from townbuilder.geom import Sink
    g = Sink()
    g.box("grass", -40, -40, -2.0, w + 40, d + 40, -0.6)
    sb.prims_objects("ground", g.prims, ("TOWN", "TERRAIN"))
    sb.prims_objects("B.ext", ext, ("TOWN", "RESIDENTIAL"))
    sb.prims_objects("B.int", inn, ("TOWN", "INTERIORS", "RESIDENTIAL"))
    for pp in b.props:
        if cut is None or pp.z < cut - 1.0:
            sb.prop(pp, ("TOWN", "PROPS"))
    if cut is not None:
        for lr in b.lights:
            if lr.z < cut + 2:
                sb.light(lr, ("TOWN", "LIGHTING"))
    for sg in b.signs:
        sb.sign(sg, ("TOWN", "COMMERCIAL"))
    return plan, b, sb


def main():
    name, w, d, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    os.makedirs(out, exist_ok=True)
    plan, b, sb = build(name, w, d, seed)
    print("warnings:", b.warnings)
    setup_render()
    span = max(w, d)
    if os.environ.get("EXTERIOR", "1") != "0":       # EXTERIOR=0: floor plans only
        camera((-span * 0.9, -span * 1.3, span * 0.9 + plan.height * 0.5),
               (w / 2, d / 2, plan.height * 0.3))
        bpy.context.scene.render.filepath = os.path.join(out, f"{name}_ext.png")
        bpy.ops.render.render(write_still=True)
        camera((w * 0.5 + span * 0.8, d + span * 1.2, span * 0.9), (w / 2, d / 2, plan.height * 0.3))
        bpy.context.scene.render.filepath = os.path.join(out, f"{name}_ext_back.png")
        bpy.ops.render.render(write_still=True)
    only = os.environ.get("LEVELS")
    for L in plan.all_levels():
        if only is not None and str(L) not in only.split(","):
            continue
        z = plan.level_z(L)
        plan2, b2, sb2 = build(name, w, d, seed, cut=z + 8.0)
        setup_render()
        rx, ry = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
        camera((w / 2, d / 2, z + 200), (w / 2, d / 2, z), ortho=max(w, d * rx / ry) * 1.08)
        # add an interior fill light so the plan reads
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
        bpy.context.scene.render.filepath = os.path.join(out, f"{name}_L{L}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
