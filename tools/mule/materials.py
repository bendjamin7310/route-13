"""Material palette.

Each key is used for a Blender preview material and for the Roblox
mapping (Enum.Material, Color3 in 0-255 sRGB, Transparency, Reflectance)
written to the generated Luau setup module.
"""

import bpy

# key: (sRGB hex, roughness, metallic, roblox material, transparency, reflectance, emission)
PALETTE = {
    "Paint":        ("D8D6CF", 0.32, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "TrimBlack":    ("1F2022", 0.62, 0.0, "Plastic", 0.0, 0.0, 0.0),
    "TrimDark":     ("2B2D30", 0.45, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "Chrome":       ("B4B8BC", 0.18, 1.0, "Metal", 0.0, 0.15, 0.0),
    "Gunmetal":     ("4A4D51", 0.45, 0.8, "Metal", 0.0, 0.0, 0.0),
    "Rubber":       ("1B1B1C", 0.85, 0.0, "Rubber", 0.0, 0.0, 0.0),
    "Glass":        ("2E3539", 0.06, 0.0, "Glass", 0.45, 0.05, 0.0),
    "LensClear":    ("D5DCE2", 0.05, 0.0, "Glass", 0.6, 0.05, 0.0),
    "LensRed":      ("8C1C1C", 0.15, 0.0, "SmoothPlastic", 0.1, 0.0, 0.0),
    "LensAmber":    ("C2690F", 0.15, 0.0, "SmoothPlastic", 0.1, 0.0, 0.0),
    "LensWhite":    ("E4E5E2", 0.15, 0.0, "SmoothPlastic", 0.05, 0.0, 0.0),
    "LightDRL":     ("F3F5F8", 0.2, 0.0, "SmoothPlastic", 0.0, 0.0, 2.0),
    "MirrorGlass":  ("8E959B", 0.03, 1.0, "Glass", 0.0, 0.6, 0.0),
    "Bedliner":     ("28292B", 0.9, 0.0, "Plastic", 0.0, 0.0, 0.0),
    "WheelWell":    ("19191A", 0.9, 0.0, "Plastic", 0.0, 0.0, 0.0),
    "Underbody":    ("2A2B2D", 0.8, 0.0, "Plastic", 0.0, 0.0, 0.0),
    "InteriorTrim": ("3A3C3F", 0.6, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "DoorTrim":     ("4E5155", 0.6, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "Headliner":    ("5D5F63", 0.9, 0.0, "Fabric", 0.0, 0.0, 0.0),
    "FloorRubber":  ("1C1D1F", 0.9, 0.0, "Rubber", 0.0, 0.0, 0.0),
    "Dash":         ("2A2C2F", 0.55, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "SeatFabric":   ("2E3033", 0.95, 0.0, "Fabric", 0.0, 0.0, 0.0),
    "MetalAccent":  ("8B8F94", 0.3, 1.0, "Metal", 0.0, 0.0, 0.0),
    "Screen":       ("0D0F11", 0.08, 0.0, "Glass", 0.0, 0.1, 0.0),
    "Gauge":        ("C9CDD2", 0.4, 0.0, "SmoothPlastic", 0.0, 0.0, 0.3),
    "RimPaint":     ("26272A", 0.4, 0.3, "SmoothPlastic", 0.0, 0.0, 0.0),
    "BrakeDisc":    ("6C6E70", 0.45, 1.0, "Metal", 0.0, 0.0, 0.0),
    "Plate":        ("ECECE6", 0.4, 0.0, "SmoothPlastic", 0.0, 0.0, 0.0),
    "Anchor":       ("4FA3FF", 0.5, 0.0, "SmoothPlastic", 1.0, 0.0, 0.0),
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def linear_rgb(h):
    return tuple(srgb_to_linear(v / 255.0) for v in hex_rgb(h))


_CACHE = {}


def get(key):
    """Blender material for a palette key (created on first use)."""
    if key in _CACHE:
        return _CACHE[key]
    hexc, rough, metal, _rbx, transp, refl, emit = PALETTE[key]
    m = bpy.data.materials.new(key)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    col = linear_rgb(hexc)
    p.inputs["Base Color"].default_value = (*col, 1.0)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if transp > 0:
        p.inputs["Alpha"].default_value = 1.0 - transp
        if key in ("Glass", "LensClear"):
            p.inputs["Transmission Weight"].default_value = 0.0
    if emit > 0:
        p.inputs["Emission Color"].default_value = (*col, 1.0)
        p.inputs["Emission Strength"].default_value = emit
    if key == "Paint":
        p.inputs["Coat Weight"].default_value = 0.25
        p.inputs["Coat Roughness"].default_value = 0.15
    m.diffuse_color = (*col, 1.0 - transp)
    m["roblox_material"] = _rbx
    _CACHE[key] = m
    return m


def reset():
    _CACHE.clear()
