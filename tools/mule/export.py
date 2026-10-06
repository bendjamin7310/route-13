"""Export: .blend (metres), FBX + GLB (1 unit = 1 stud), a JSON manifest and
the Roblox setup ModuleScript generated from the same data.
"""

import json
import os

import bpy
import numpy as np
from mathutils import Matrix

import materials
import mesher
import seats
from dims import *  # noqa: F401,F403
from mesher import log

S = STUDS_PER_METRE


def to_roblox(p):
    """Blender metres (x right, y forward, z up) -> Roblox studs (X right, Y up, -Z forward)."""
    x, y, z = (float(v) for v in p)
    return (round(x * S, 4), round(z * S, 4), round(-y * S, 4))


def organise_wheels(root):
    """Give each wheel its own empty so it imports as a Model per wheel."""
    wheels = bpy.data.objects.get("Wheels")
    for corner in ("FL", "FR", "RL", "RR"):
        parts = [o for o in bpy.data.objects if o.name.startswith(f"Wheel_{corner}_")]
        if not parts:
            continue
        e = bpy.data.objects.new(f"Wheel_{corner}", None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = wheels
        for o in parts:
            mw = o.matrix_world.copy()
            o.parent = e
            o.matrix_world = mw


def _mesh_objects(root):
    return [o for o in root.children_recursive if o.type == "MESH"]


def scale_scene(root, k):
    for o in root.children_recursive:
        if o.type == "MESH":
            o.data.transform(Matrix.Scale(k, 4))
            o.data.update()
        o.location = o.location * k


def _select_tree(root):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for o in root.children_recursive:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root


def manifest(root, rows):
    parts = []
    for o in _mesh_objects(root):
        key = o.get("mule_material", "Paint")
        mat = o.data.materials[0] if o.data.materials else None
        co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        lo, hi = co.min(axis=0), co.max(axis=0)
        parts.append({
            "name": o.name,
            "group": o.parent.name if o.parent else "",
            "material": key,
            "triangles": mesher.tri_count(o),
            "pivot_studs": to_roblox(o.matrix_world.translation),
            "centre_studs": to_roblox((lo + hi) / 2),
            "size_studs": [round(float(hi[0] - lo[0]) * S, 3), round(float(hi[2] - lo[2]) * S, 3),
                           round(float(hi[1] - lo[1]) * S, 3)],
            "texture_color": mat.get("mule_texture_color") if mat else None,
            "texture_roughness": mat.get("mule_texture_roughness") if mat else None,
        })
    parts.sort(key=lambda p: p["name"])
    seat_list = []
    for name, (x, y, ztop) in seats.ANCHORS.items():
        seat_list.append({"name": name, "top_centre_studs": to_roblox((x, y, ztop)),
                          "size_studs": [round(seats.SIZE[0] * S, 3), round(seats.SIZE[2] * S, 3), round(seats.SIZE[1] * S, 3)]})
    xs = [], [], []
    for o in _mesh_objects(root):
        if o.name.startswith("SeatAnchor") or o.name.startswith("Plate_Front") or o.name.startswith("PlateBracket"):
            continue
        bb = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        for i in range(3):
            xs[i].append((bb[:, i].min(), bb[:, i].max()))
    ext = [(float(min(a for a, _ in v)), float(max(b for _, b in v))) for v in xs]
    return {
        "name": "Mule",
        "description": "Hilux-style 4x4 double-cab pickup for Route 13",
        "studs_per_metre": S,
        "triangles_total": int(sum(p["triangles"] for p in parts
                                   if not p["name"].startswith("SeatAnchor") and p["name"] != "MuleRoot")),
        "size_studs": {
            "length": round((ext[1][1] - ext[1][0]) * S, 2),
            "width_with_mirrors": round((ext[0][1] - ext[0][0]) * S, 2),
            "height": round((ext[2][1] - ext[2][0]) * S, 2),
        },
        "wheels": {
            "radius_studs": round(TIRE_R * S, 3),
            "width_studs": round(TIRE_W * S, 3),
            "centres_studs": {c: to_roblox((x, y, AXLE_Z)) for c, (x, y) in
                              {"FL": (-X_WHEEL_F, Y_FRONT_AXLE), "FR": (X_WHEEL_F, Y_FRONT_AXLE),
                               "RL": (-X_WHEEL_R, Y_REAR_AXLE), "RR": (X_WHEEL_R, Y_REAR_AXLE)}.items()},
        },
        "seats": seat_list,
        "materials": {k: {"color_rgb": list(materials.hex_rgb(v[0])), "roblox_material": v[3],
                          "transparency": v[4], "reflectance": v[5]} for k, v in materials.PALETTE.items()},
        "parts": parts,
    }


def export_all(root, objs, out_dir, rows):
    os.makedirs(out_dir, exist_ok=True)
    organise_wheels(root)
    sc = bpy.context.scene
    # Roblox's documented Blender workflow: metric scene, unit scale 1, FBX
    # "FBX Unit Scale", then import with Scale Unit = Stud. The geometry is
    # scaled to studs right before export, so 1 file unit = 1 stud.
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0

    blend = os.path.join(out_dir, "mule_pickup.blend")
    bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups
    try:
        bpy.ops.file.pack_all()
    except RuntimeError:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True, copy=True)
    log("saved", blend)

    data = manifest(root, rows)
    scale_scene(root, S)
    try:
        _select_tree(root)
        fbx = os.path.join(out_dir, "mule_pickup.fbx")
        bpy.ops.export_scene.fbx(
            filepath=fbx, use_selection=True, object_types={"EMPTY", "MESH"},
            use_mesh_modifiers=True, mesh_smooth_type="OFF", use_tspace=False,
            add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=True,
            # the truck's nose is +Y in Blender -> -Z in the file = Roblox "Front"
            axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_UNITS", global_scale=1.0, colors_type="NONE",
        )
        log("exported", fbx)
        glb = os.path.join(out_dir, "mule_pickup.glb")
        bpy.ops.export_scene.gltf(
            filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
            export_apply=True, export_texcoords=True, export_normals=True,
            export_materials="EXPORT", export_cameras=False, export_lights=False,
            export_extras=False,
        )
        log("exported", glb)
    finally:
        scale_scene(root, 1.0 / S)

    with open(os.path.join(out_dir, "mule_manifest.json"), "w") as f:
        json.dump(data, f, indent=1, default=float)
    import luau
    luau.write_setup_module(data, os.path.join(out_dir, "roblox", "MuleSetup.lua"))
    log("manifest + Roblox setup module written")
    return data
