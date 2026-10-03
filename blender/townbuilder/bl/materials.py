"""Blender materials generated from the palette (one material per palette key)."""

from __future__ import annotations

import bpy

from .. import palette as pal

_cache: dict[str, bpy.types.Material] = {}


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def get(name: str) -> bpy.types.Material:
    m = _cache.get(name)
    if m is not None:
        return m
    spec = pal.P[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    r, g, b = (srgb_to_linear(v) for v in spec["rgb"])
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = spec["rough"]
    bsdf.inputs["Metallic"].default_value = spec["metal"]
    m.diffuse_color = (r, g, b, spec["alpha"])
    if spec["alpha"] < 1.0:
        bsdf.inputs["Alpha"].default_value = max(0.0, spec["alpha"])
        if spec["rbx"] == "Glass" and spec["alpha"] > 0.0:
            # glass: mostly transmissive but keep the tint readable
            bsdf.inputs["Transmission Weight"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.05
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else m.blend_method
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    if spec["emit"] > 0:
        bsdf.inputs["Emission Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Emission Strength"].default_value = spec["emit"]
    # export hints for the Roblox assembler (also visible in the material panel)
    m["roblox_material"] = spec["rbx"]
    m["roblox_color"] = [float(c) for c in spec["rgb"]]          # 0-255 (floats for FBX)
    m["roblox_transparency"] = round(1.0 - spec["alpha"], 3)
    _cache[name] = m
    return m


def reset():
    _cache.clear()
