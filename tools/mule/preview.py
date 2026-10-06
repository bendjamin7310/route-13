"""Studio scene and preview renders (Cycles, CPU)."""

import math
import os

import bpy
from mathutils import Vector

VIEWS = {
    # name: (location, target, lens_mm or ortho scale, ortho?)
    "front34": ((-5.2, 7.6, 1.55), (0.0, 0.05, 0.86), 58, False),
    "rear34": ((5.0, -7.6, 2.3), (0.0, -0.4, 0.86), 58, False),
    "side": ((-12.0, -0.19, 0.95), (0.0, -0.19, 0.95), 5.9, True),
    "front": ((0.0, 12.0, 0.95), (0.0, 0.0, 0.95), 4.0, True),
    "rear": ((0.0, -12.0, 0.95), (0.0, 0.0, 0.95), 4.0, True),
    "top": ((0.0, -0.19, 12.0), (0.0, -0.19, 0.0), 5.9, True),
    "low34": ((-3.8, 4.6, 0.55), (0.0, 0.2, 0.75), 35, False),
    "interior": ((0.0, -0.80, 1.60), (-0.12, 0.60, 1.00), 20, False),
    "driver": ((-0.395, -0.16, 1.58), (-0.33, 0.60, 1.02), 17, False),
    "cabin": ((-2.9, -0.30, 1.40), (0.10, -0.30, 0.98), 22, False),
    "bed": ((2.4, -4.6, 2.7), (0.0, -1.95, 0.95), 40, False),
}


def setup_scene(res=(1280, 720), samples=48):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 12
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("Studio")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexGradient")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, -math.pi / 2, 0)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], sky.inputs["Vector"])
    nt.links.new(sky.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (0.62, 0.64, 0.68, 1)
    ramp.color_ramp.elements[1].color = (0.92, 0.93, 0.95, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.9
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(6)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(42), math.radians(-18), math.radians(-35))
    sc.collection.objects.link(so)

    key = bpy.data.lights.new("Key", "AREA")
    key.energy = 900
    key.size = 6
    ko = bpy.data.objects.new("Key", key)
    ko.location = (-6, 6, 5)
    ko.rotation_euler = (Vector((0, 0, 0.8)) - ko.location).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ko)

    mat = bpy.data.materials.new("Ground")
    mat.use_nodes = True
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.72, 0.72, 0.72, 1)
    p.inputs["Roughness"].default_value = 0.85
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "PreviewGround"
    g.data.materials.append(mat)
    return sc


VIEW_HIDE = {
    "cabin": ("Door_FL", "Door_RL", "Mirror_L", "Mirror_Glass_L", "DoorHandles_L"),
}
CABIN_VIEWS = ("interior", "driver", "cabin")


def _cabin_light(on):
    ob = bpy.data.objects.get("CabinFill")
    if ob is None and on:
        L = bpy.data.lights.new("CabinFill", "AREA")
        L.energy = 60
        L.size = 0.9
        ob = bpy.data.objects.new("CabinFill", L)
        ob.location = (0.0, -0.25, 1.70)
        bpy.context.scene.collection.objects.link(ob)
    if ob is not None:
        ob.hide_render = not on


def render_view(name, path, hide=()):
    sc = bpy.context.scene
    hide = tuple(hide) + VIEW_HIDE.get(name, ())
    _cabin_light(name in CABIN_VIEWS)
    loc, tgt, lens, ortho = VIEWS[name]
    cam_data = bpy.data.cameras.new("cam_" + name)
    cam = bpy.data.objects.new("cam_" + name, cam_data)
    sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(tgt) - Vector(loc)
    up = "Y" if abs(d.normalized().z) < 0.99 else "Y"
    cam.rotation_euler = d.to_track_quat("-Z", up).to_euler()
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = lens
    else:
        cam_data.lens = lens
    cam_data.clip_start = 0.02
    sc.camera = cam
    hidden = []
    for ob in sc.objects:
        if any(ob.name.startswith(h) for h in hide):
            hidden.append((ob, ob.hide_render))
            ob.hide_render = True
    if path.endswith(".jpg"):
        sc.render.image_settings.file_format = "JPEG"
        sc.render.image_settings.quality = 90
    else:
        sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    for ob, h in hidden:
        ob.hide_render = h
    bpy.data.objects.remove(cam)


def add_r15_proxies(anchors):
    """Blocky R15-sized stand-ins in the default sitting pose, for checking fit.

    anchors: {name: (x, y, cushion_top_z)} in metres. R15 sizes are in studs
    and converted at dims.STUDS_PER_METRE. Arms hang straight down beside the
    torso, the widest the default sit pose gets.
    """
    from dims import STUDS_PER_METRE as S

    mat = bpy.data.materials.new("R15Proxy")
    p = mat.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.95, 0.38, 0.08, 1)
    p.inputs["Roughness"].default_value = 0.6
    made = []

    def block(name, cx, cy, cz, sx, sy, sz):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = (sx, sy, sz)
        ob.data.materials.append(mat)
        made.append(ob)

    for name, (x, y, zc) in anchors.items():
        s = 1.0 / S
        hip_z = zc + 0.5 * s
        tag = name.replace("SeatAnchor_", "R15Proxy_")
        block(tag + "_LowerTorso", x, y, zc + 0.7 * s, 2 * s, 1 * s, 0.4 * s)
        block(tag + "_UpperTorso", x, y, zc + 1.7 * s, 2 * s, 1 * s, 1.6 * s)
        block(tag + "_Head", x, y, zc + 3.1 * s, 1.2 * s, 1.2 * s, 1.2 * s)
        for side in (-1, 1):
            lx = x + side * 0.5 * s
            block(f"{tag}_UpperLeg{side}", lx, y + 0.36 * s, hip_z, 1 * s, 1.72 * s, 1 * s)
            block(f"{tag}_LowerLeg{side}", lx, y + 1.22 * s, hip_z - 0.52 * s, 1 * s, 1 * s, 1.53 * s)
            block(f"{tag}_Arm{side}", x + side * 1.5 * s, y, zc + 1.25 * s, 1 * s, 1 * s, 2.5 * s)
    return made
