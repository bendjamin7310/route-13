"""Realise the engine-agnostic world description as a Blender scene.

Collections follow the brief:

TOWN
├── TERRAIN, ROADS, SIDEWALKS
├── DOWNTOWN, MIXED_USE, RESIDENTIAL, LOW_INCOME, MOTEL, INDUSTRIAL, COMMERCIAL,
│   WATERFRONT, POLICE, CIVIC, FIRE, PARKS, OUTSKIRTS      (building exteriors)
├── PROPS, VEGETATION, VEHICLES, LANDMARKS
├── INTERIORS / RESIDENTIAL, COMMERCIAL, INDUSTRIAL, CIVIC, SERVICE
├── LIGHTING
└── GAMEPLAY   (entrances, spawns, POIs as empties)
KIT (excluded from the view layer): one master mesh per reusable prop.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

from .. import palette as pal
from ..kit import KIT
from . import materials
from .meshing import build_mesh, split_by_material

TOP = ["TERRAIN", "ROADS", "SIDEWALKS", "DOWNTOWN", "MIXED_USE", "RESIDENTIAL", "LOW_INCOME",
       "MOTEL", "INDUSTRIAL", "COMMERCIAL", "WATERFRONT", "POLICE", "CIVIC", "FIRE", "PARKS",
       "OUTSKIRTS", "PROPS", "VEGETATION", "VEHICLES", "LANDMARKS", "INTERIORS", "LIGHTING",
       "GAMEPLAY"]
INTERIOR_SUB = ["RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "CIVIC", "SERVICE"]


def light_energy(brightness, rng, kind):
    base = 55.0 if kind == "point" else 900.0
    return base * brightness * (rng / 20.0) ** 2


class SceneBuilder:
    def __init__(self, town_name="TOWN", lights_mode="all"):
        self.cols = {}
        self.kit_meshes = {}
        self.kit_slots = {}
        self.lights_mode = lights_mode
        self.stats = {"objects": 0, "props": 0, "lights": 0, "tris": 0}
        self.root = bpy.data.collections.new("TOWN")
        bpy.context.scene.collection.children.link(self.root)
        self.cols[("TOWN",)] = self.root
        for t in TOP:
            self.collection(("TOWN", t))
        for t in INTERIOR_SUB:
            self.collection(("TOWN", "INTERIORS", t))
        self.kit_col = bpy.data.collections.new("KIT")
        bpy.context.scene.collection.children.link(self.kit_col)
        lc = bpy.context.view_layer.layer_collection.children["KIT"]
        lc.exclude = True

    def collection(self, path):
        path = tuple(path)
        c = self.cols.get(path)
        if c:
            return c
        parent = self.collection(path[:-1])
        c = bpy.data.collections.new(path[-1] if len(path) < 3 or path[1] != "INTERIORS"
                                     else f"INT_{path[-1]}")
        parent.children.link(c)
        self.cols[path] = c
        return c

    # -- kit ------------------------------------------------------------------------
    def kit_mesh(self, name):
        me = self.kit_meshes.get(name)
        if me is None:
            d = KIT[name]
            me, slots = build_mesh(f"KIT_{name}", d.prims, mat_slots={m for m in
                                                                     (p.mat for p in d.prims)
                                                                     if m.startswith("$")})
            master = bpy.data.objects.new(f"KIT_{name}", me)
            master["kit_prop"] = name
            master["category"] = d.cat
            self.kit_col.objects.link(master)
            self.kit_meshes[name] = me
            self.kit_slots[name] = slots
        return me

    # -- objects ----------------------------------------------------------------------
    def empty(self, name, col_path, matrix=None, parent=None, kind="PLAIN_AXES", size=2.0):
        o = bpy.data.objects.new(name, None)
        o.empty_display_type = kind
        o.empty_display_size = size
        if matrix is not None:
            o.matrix_world = matrix
        if parent is not None:
            o.parent = parent
        self.collection(col_path).objects.link(o)
        return o

    def prims_objects(self, base_name, prims, col_path, parent=None, per_material=True,
                      props=None):
        """Create one object per material (Roblox: one MeshPart per material)."""
        out = []
        if not prims:
            return out
        groups = split_by_material(prims) if per_material else {"mix": prims}
        col = self.collection(col_path)
        for m, ps in groups.items():
            if m == "invisible":
                continue
            me, slots = build_mesh(f"{base_name}.{m}", ps)
            if not me.polygons:
                bpy.data.meshes.remove(me)
                continue
            o = bpy.data.objects.new(f"{base_name}.{m}", me)
            if parent is not None:
                o.parent = parent
            if props:
                for k, v in props.items():
                    o[k] = v
            o["material_key"] = m
            col.objects.link(o)
            self.stats["objects"] += 1
            self.stats["tris"] += sum(len(p.vertices) - 2 for p in me.polygons)
            out.append(o)
        return out

    def prop(self, pp, col_path, parent=None):
        d = KIT.get(pp.name)
        if d is None:
            return None
        me = self.kit_mesh(pp.name)
        o = bpy.data.objects.new(pp.name, me)
        o.location = (pp.x, pp.y, pp.z)
        o.rotation_euler = (0.0, 0.0, pp.yaw)
        if pp.scale != (1.0, 1.0, 1.0):
            o.scale = pp.scale
        if parent is not None:
            o.parent = parent
        o["kit_prop"] = pp.name
        if pp.room:
            o["room"] = pp.room
        if pp.meta:
            for k, v in pp.meta.items():
                if v is None:
                    continue
                o[f"meta_{k}"] = v if isinstance(v, (int, float, str)) else str(v)
        slots = self.kit_slots.get(pp.name, [])
        if any(s.startswith("$") for s in slots):
            for i, s in enumerate(slots):
                if s.startswith("$"):
                    mat = pal.resolve(s, pp.channels)
                    ms = o.material_slots[i] if i < len(o.material_slots) else None
                    if ms is not None:
                        ms.link = "OBJECT"
                        ms.material = materials.get(mat)
                        o[f"chan_{s[1:]}"] = mat
        self.collection(col_path).objects.link(o)
        self.stats["props"] += 1
        return o

    def light(self, lr, col_path, parent=None):
        if self.lights_mode == "none":
            return None
        if self.lights_mode == "night" and lr.schedule not in ("night", "late", "always"):
            return None
        kind = "SPOT" if lr.kind == "spot" else "POINT"
        ld = bpy.data.lights.new("L", kind)
        ld.color = lr.color
        ld.energy = light_energy(lr.brightness, lr.range, lr.kind)
        ld.shadow_soft_size = 0.6
        if kind == "SPOT":
            ld.spot_size = math.radians(110)
            ld.spot_blend = 0.6
        try:
            ld.use_custom_distance = True
            ld.cutoff_distance = lr.range * 1.5
        except Exception:
            pass
        o = bpy.data.objects.new(f"Light.{lr.schedule}", ld)
        o.location = (lr.x, lr.y, lr.z)
        if kind == "SPOT":
            dx, dy, dz = lr.dir
            o.rotation_euler = Vector((dx, dy, dz)).to_track_quat("-Z", "Y").to_euler()
        if parent is not None:
            o.parent = parent
        o["schedule"] = lr.schedule
        o["range"] = lr.range
        o["brightness"] = lr.brightness
        if lr.room:
            o["room"] = lr.room
        self.collection(col_path).objects.link(o)
        self.stats["lights"] += 1
        return o

    def marker(self, mk, col_path, parent=None, prefix=""):
        o = bpy.data.objects.new(f"{prefix}{mk.kind}.{mk.label}"[:60], None)
        o.empty_display_type = "SINGLE_ARROW" if mk.kind in ("entrance", "vehicle",
                                                             "spawn") else "SPHERE"
        o.empty_display_size = 2.0
        o.location = (mk.x, mk.y, mk.z)
        o.rotation_euler = (math.pi / 2 if o.empty_display_type == "SINGLE_ARROW" else 0, 0,
                            mk.yaw)
        if parent is not None:
            o.parent = parent
        o["marker"] = mk.kind
        o["label"] = mk.label
        for k, v in (mk.meta or {}).items():
            if isinstance(v, (int, float, str)):
                o[f"meta_{k}"] = v
        self.collection(col_path).objects.link(o)
        return o

    def sign(self, sg, col_path, name="Sign"):
        """Sign board + extruded text converted to a mesh (world coordinates)."""
        objs = []
        rot = Matrix.Rotation(sg.yaw, 4, "Z")
        base = Matrix.Translation((sg.x, sg.y, sg.z)) @ rot
        fg = sg.fg
        if sg.neon and fg.startswith("sign_"):
            fg = "neon_" + fg[5:] if ("neon_" + fg[5:]) in pal.P else "neon_white"
        if sg.board:
            from ..geom import Sink
            s = Sink()
            s.box(sg.bg, -sg.w / 2, 0.0, -sg.h / 2, sg.w / 2, 0.4, sg.h / 2, True)
            if sg.neon:
                s.box(fg if fg.startswith("neon_") else "neon_white", -sg.w / 2 - 0.15, -0.05,
                      -sg.h / 2 - 0.15, sg.w / 2 + 0.15, 0.02, -sg.h / 2, False)
            for o in self.prims_objects(f"{name}.board", s.prims, col_path):
                o.matrix_world = base
                objs.append(o)
        cu = bpy.data.curves.new(f"{name}.text", "FONT")
        cu.body = sg.text
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.extrude = 0.12
        cu.resolution_u = 2
        size = min(sg.h * 0.62, (sg.w * 0.92) / max(1.0, len(sg.text) * 0.62))
        cu.size = max(0.5, size)
        to = bpy.data.objects.new(f"{name}.text_tmp", cu)
        bpy.context.scene.collection.objects.link(to)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = to.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        bpy.context.scene.collection.objects.unlink(to)
        bpy.data.objects.remove(to)
        bpy.data.curves.remove(cu)
        me.materials.append(materials.get(fg))
        o = bpy.data.objects.new(f"{name}.text.{fg}", me)
        # text is built in XY; stand it up facing -Y, just in front of the board
        o.matrix_world = base @ Matrix.Translation((0, -0.06, 0)) @ \
            Matrix.Rotation(math.pi / 2, 4, "X")
        o["sign_text"] = sg.text
        o["material_key"] = fg
        self.collection(col_path).objects.link(o)
        self.stats["objects"] += 1
        objs.append(o)
        return objs
