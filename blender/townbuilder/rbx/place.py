"""Prebuilt Roblox place / model: the whole town as ready-made instances.

``write_instances`` expands the Roblox export (``build/roblox/PortSolace``: chunk modules,
palette, kit) into a JSON-lines instance list with exactly the structure
``roblox/src/TownBuilder.lua`` builds inside Studio: Parts, prop Models, lights, signs,
markers, lighting, the runtime scripts and a terrain loader.  ``tools/rbxconv`` (Rust,
rbx-dom) turns that list into a binary ``.rbxl`` place or ``.rbxm`` model, typing every
property through the Roblox reflection database.

Voxel terrain cannot be written into the file (its storage format is not public), so the
place carries ``TerrainLoader``: it generates the terrain from ``TerrainData`` the first
time the place runs, or once from the command bar so it can be saved with the place.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess

from .. import palette as pal
from ..kit import KIT
from ..world import layout as Lay
from ..geom import tri_wedges
from .export import KIT_NAMES, PAL_NAMES, PAL_INDEX, part_line, REPO_ROBLOX

BLOCK_RE = re.compile(r"\t(\w+) = \[(=+)\[\n(.*?)\n\]\2\]", re.S)

PROP_TAGS = {"door": "PS_Door", "vehicle": "PS_Vehicle", "boat": "PS_Boat", "gate": "PS_Gate",
             "rail": "PS_RailCar", "police": "PS_Police", "fire": "PS_Fire"}
LIGHT_CLASS = {"point": "PointLight", "spot": "SpotLight", "surface": "SurfaceLight"}
FONT_SIGN = {"family": "rbxasset://fonts/families/GothamSSm.json", "weight": "Heavy"}
FONT_NEON = {"family": "rbxasset://fonts/families/FredokaOne.json", "weight": "Regular"}


# ---------------------------------------------------------------------------------------
# small CFrame helpers (row-major 3x3 + position, Roblox space)

def q2m(qx, qy, qz, qw):
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw) or 1.0
    x, y, z, w = qx / n, qy / n, qz / n, qw / n
    return (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y))


def mmul(a, b):
    return tuple(sum(a[r * 3 + k] * b[k * 3 + c] for k in range(3)) for r in range(3)
                 for c in range(3))


def mvec(m, v):
    return (m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
            m[6] * v[0] + m[7] * v[1] + m[8] * v[2])


IDENT = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def cf(pos, rot=IDENT):
    return [round(pos[0], 4), round(pos[1], 4), round(pos[2], 4)] + [round(v, 6) for v in rot]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return (c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c)


def look_at(pos, d):
    """Roblox CFrame.lookAt(pos, pos + d, up) rotation (columns right, up, -look)."""
    n = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    lx, ly, lz = d[0] / n, d[1] / n, d[2] / n
    up = (1.0, 0.0, 0.0) if abs(ly) > 0.98 else (0.0, 1.0, 0.0)
    rx, ry, rz = ly * up[2] - lz * up[1], lz * up[0] - lx * up[2], lx * up[1] - ly * up[0]
    rn = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
    rx, ry, rz = rx / rn, ry / rn, rz / rn
    ux, uy, uz = ry * lz - rz * ly, rz * lx - rx * lz, rx * ly - ry * lx
    return (rx, ux, -lx, ry, uy, -ly, rz, uz, -lz)


def attr_value(v):
    try:
        x = float(v)
        if math.isfinite(x):
            return x
    except ValueError:
        pass
    if v in ("True", "true"):
        return True
    if v in ("False", "false"):
        return False
    return v


def kv(s):
    out = {}
    for item in (s or "").split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            out[k] = v
    return out


def fix_shape(kind, size):
    """Roblox cylinders are round (diameter = min(Y, Z)) and SpecialMesh ellipsoids lose
    their material: equalise cylinder diameters, make near-uniform ellipsoids balls."""
    if kind == "C" and abs(size[1] - size[2]) > 1e-3:
        d = max(size[1], size[2])
        return kind, (size[0], d, d)
    if kind == "E" and max(size) <= min(size) * 1.15:
        d = sum(size) / 3.0
        return "S", (d, d, d)
    return kind, size


class SpawnProbe:
    """Collidable part boxes near the spawn plaza, to find a clear spot for the pad."""

    def __init__(self, cx, cz, radius=120.0):
        self.cx, self.cz, self.r = cx, cz, radius
        self.boxes = []

    def add(self, pos, rot, size):
        if abs(pos[0] - self.cx) > self.r or abs(pos[2] - self.cz) > self.r:
            return
        ext = [sum(abs(rot[i * 3 + k]) * size[k] / 2 for k in range(3)) for i in range(3)]
        self.boxes.append((pos[0] - ext[0], pos[1] - ext[1], pos[2] - ext[2],
                           pos[0] + ext[0], pos[1] + ext[1], pos[2] + ext[2]))

    def clear(self, x, y, z, half=7.0, height=9.0):
        for (x0, y0, z0, x1, y1, z1) in self.boxes:
            if x1 > x - half and x0 < x + half and z1 > z - half and z0 < z + half and \
                    y1 > y + 0.05 and y0 < y + height:
                return False
        return True


class TerrainGrid:
    """Decoded TerrainData.lua (heights, material ids, water levels; Roblox X/Z lookups)."""

    def __init__(self, path):
        src = open(path).read()
        self.N = int(re.search(r"size = (\d+)", src).group(1))
        self.res = float(re.search(r"res = ([\d.]+)", src).group(1))
        self.origin = float(re.search(r"origin = (-?[\d.]+)", src).group(1))
        self.offset = int(re.search(r"offset = (\d+)", src).group(1))
        self.scale = float(re.search(r"scale = ([\d.]+)", src).group(1))
        alpha = re.search(r'alphabet = "([^"]+)"', src).group(1)
        self.lookup = {ch: i for i, ch in enumerate(alpha)}
        self.mat_names = re.findall(r'"([^"]+)"', re.search(r"\tmaterials = \{([^}]*)\}",
                                                            src).group(1))

        def rows(name):
            block = re.search(r"\t" + name + r" = \{\n(.*?)\n\t\}", src, re.S).group(1)
            return re.findall(r'"([^"]*)"', block)
        lk = self.lookup
        self.H = [[((lk[r[2 * j]] * 64 + lk[r[2 * j + 1]]) - self.offset) / self.scale
                   for j in range(self.N)] for r in rows("heights")]
        self.M = [[lk[ch] for ch in r] for r in rows("mats")]
        self.W = [[None if r[2 * j] == "_" else
                   ((lk[r[2 * j]] * 64 + lk[r[2 * j + 1]]) - self.offset) / self.scale
                   for j in range(self.N)] for r in rows("water")]

    def ij(self, x, z):
        """Grid indices for Roblox X/Z (row i = Blender y = -Z)."""
        j = (x - self.origin) / self.res
        i = (-z - self.origin) / self.res
        return i, j

    def h(self, x, z):
        i, j = self.ij(x, z)
        i0 = max(0, min(self.N - 2, int(math.floor(i))))
        j0 = max(0, min(self.N - 2, int(math.floor(j))))
        ti, tj = min(1.0, max(0.0, i - i0)), min(1.0, max(0.0, j - j0))
        H = self.H
        return (H[i0][j0] * (1 - tj) + H[i0][j0 + 1] * tj) * (1 - ti) + \
            (H[i0 + 1][j0] * (1 - tj) + H[i0 + 1][j0 + 1] * tj) * ti


# ---------------------------------------------------------------------------------------

class Writer:
    def __init__(self, path):
        self.fh = open(path, "w")
        self.n = 0
        self.counts = {}

    def add(self, parent, cls, props=None, attrs=None, tags=None):
        self.n += 1
        rec = {"r": self.n, "p": parent, "c": cls, "props": props or {}}
        if attrs:
            rec["attrs"] = attrs
        if tags:
            rec["tags"] = tags
        self.fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
        self.counts[cls] = self.counts.get(cls, 0) + 1
        return self.n

    def close(self):
        self.fh.close()


class PlaceBuilder:
    def __init__(self, data_dir, manifest, w: Writer, interiors=True, prop_detail=3):
        self.data_dir = data_dir
        self.m = manifest
        self.w = w
        self.interiors = interiors
        self.prop_detail = prop_detail
        self.mats = []
        for n in PAL_NAMES:
            e = pal.P[n]
            self.mats.append((e["rbx"], tuple(c / 255.0 for c in e["rgb"]),
                              round(1.0 - e["alpha"], 3)))
        self.chan_default = {k[1:]: PAL_INDEX[v] for k, v in pal.CHANNEL_DEFAULTS.items()}
        self.fallback = PAL_INDEX.get("plastic_gray", 1)
        self.kit_cache = {}
        self.buildings = {b["id"]: b for b in manifest["buildings"]}
        self.bmodel = {}
        self.folders = {}
        self.stats = {"parts": 0, "props": 0, "lights": 0, "markers": 0, "signs": 0}
        self.parks = {}
        self.spawn_probe = None

    # -- containers ------------------------------------------------------------------------
    def folder(self, parent, name, cls="Folder"):
        key = (parent, name)
        if key not in self.folders:
            self.folders[key] = self.w.add(parent, cls, {"Name": name})
        return self.folders[key]

    def building(self, bid):
        if bid in self.bmodel:
            return self.bmodel[bid]
        info = self.buildings.get(bid)
        props = {"Name": f"{bid} {info['name']}" if info else bid}
        attrs = {"BuildingId": bid}
        if info:
            c = info["center"]
            props["WorldPivotData"] = cf((c[0], c[2], -c[1]))
            attrs.update({"DisplayName": info["name"], "Archetype": info["archetype"],
                          "District": info["district"], "Levels": float(info["levels"])})
            if info.get("address"):
                attrs["Address"] = info["address"]
        ref = self.w.add(self.buildings_root, "Model", props, attrs, ["PS_Building"])
        self.bmodel[bid] = ref
        return ref

    def group(self, chunk, header):
        m = re.match(r"^#([^|]+)\|?(.*)$", header)
        owner, part = m.group(1), m.group(2)
        if re.match(r"^B\d+$", owner):
            b = self.building(owner)
            sub = part or "Props"
            return self.folder(b, sub, "Folder" if sub == "Props" else "Model"), sub, owner
        if owner == "Infrastructure":
            cat = self.folder(self.infra_root, part)
            return self.folder(cat, chunk, "Model"), part, None
        cat = self.folder(self.world_root, owner)
        return self.folder(cat, chunk), owner, None

    # -- parts -----------------------------------------------------------------------------
    def part_props(self, kind, pos, rot, size, mat_idx, collide):
        rbx, color, transp = self.mats[mat_idx - 1] if 0 < mat_idx <= len(self.mats) \
            else self.mats[self.fallback - 1]
        cls = "WedgePart" if kind == "W" else "Part"
        p = {"Anchored": True, "Size": [round(max(0.001, s), 4) for s in size],
             "CFrame": cf(pos, rot), "Material": rbx, "Color": list(color),
             "CanCollide": collide, "CanTouch": False,
             "TopSurface": "Smooth", "BottomSurface": "Smooth"}
        if transp > 0:
            p["Transparency"] = transp
        if not collide:
            p["CanQuery"] = False
        if kind == "C":
            p["Shape"] = "Cylinder"
        elif kind == "S":
            p["Shape"] = "Ball"
        return cls, p

    def emit_part(self, parent, kind, pos, rot, size, mat_idx, collide):
        kind, size = fix_shape(kind, size)
        if collide and self.spawn_probe is not None:
            self.spawn_probe.add(pos, rot, size)
        cls, p = self.part_props(kind, pos, rot, size, mat_idx, collide)
        ref = self.w.add(parent, cls, p)
        if kind == "E":
            self.w.add(ref, "SpecialMesh", {"MeshType": "Sphere"})
        self.stats["parts"] += 1
        return ref

    def parts_block(self, chunk, block):
        parent, sub, owner = None, None, None
        skip, pending, ground = False, None, 0.0
        for line in block.split("\n"):
            if not line:
                continue
            if line[0] == "#":
                m = re.match(r"^#(B\d+)\|Interior$", line)
                if m and not self.interior_wanted(m.group(1)):
                    # no interior: keep only the ground-floor slabs so the entrances lead
                    # onto a floor; the Interior model is created only if one is kept
                    skip, pending, parent, owner = True, line, None, m.group(1)
                    ground = self.ground_level(owner)
                    continue
                skip, pending = False, None
                parent, sub, owner = self.group(chunk, line)
                continue
            f = line.split(",")
            pos = (float(f[1]), float(f[2]), float(f[3]))
            rot = q2m(float(f[4]), float(f[5]), float(f[6]), float(f[7]))
            size = (float(f[8]), float(f[9]), float(f[10]))
            if skip:
                if not (f[0] == "B" and abs(rot[4]) > 0.99 and size[1] <= 2.0 and
                        size[0] * size[2] >= 4.0 and abs(pos[1] + size[1] / 2 - ground) < 0.7):
                    continue
                if parent is None:
                    parent, sub, owner = self.group(chunk, pending)
            self.emit_part(parent, f[0], pos, rot, size, int(f[11]), f[12] == "1")

    def ground_level(self, owner):
        info = self.buildings.get(owner)
        return info["center"][2] if info else 0.0

    def interior_wanted(self, owner):
        if not self.interiors:
            return False
        if self.interiors is True or owner is None:
            return True
        return self.interiors(owner, self.buildings.get(owner))

    # -- props -----------------------------------------------------------------------------
    def kit_parts(self, kit_idx):
        if kit_idx not in self.kit_cache:
            d = KIT[KIT_NAMES[kit_idx - 1]]
            out = []
            for p in d.prims:
                f = part_line(p, keep_channel=True).split(",")
                out.append((f[0], (float(f[1]), float(f[2]), float(f[3])),
                            q2m(float(f[4]), float(f[5]), float(f[6]), float(f[7])),
                            (float(f[8]), float(f[9]), float(f[10])), f[11], f[12] == "1"))
            self.kit_cache[kit_idx] = (d, out)
        return self.kit_cache[kit_idx]

    def props_block(self, chunk, block):
        parent, owner = None, None
        for line in block.split("\n"):
            if not line:
                continue
            if line[0] == "#":
                parent, _, owner = self.group(chunk, line)
                continue
            f = line.split(",")
            kit_idx = int(f[0])
            flags = int(f[11])
            interior = bool(flags & 1)
            detail = flags >> 1
            if kit_idx < 1 or detail > self.prop_detail:
                continue
            if interior and not self.interior_wanted(owner):
                continue
            d, prims = self.kit_parts(kit_idx)
            ppos = (float(f[1]), float(f[2]), float(f[3]))
            prot = q2m(float(f[4]), float(f[5]), float(f[6]), float(f[7]))
            scale = (float(f[8]), float(f[9]), float(f[10]))
            chans = {k: int(v) for k, v in kv(f[12]).items()}
            meta = kv(f[13])
            attrs = {k: attr_value(v) for k, v in meta.items()}
            if interior:
                attrs["Interior"] = True
            tags = sorted({PROP_TAGS[t] for t in d.tags if t in PROP_TAGS})
            if "door" in meta and not interior and owner and not self.interior_wanted(owner) \
                    and ppos[1] > self.ground_level(owner) + 2.0:
                attrs["locked"] = True          # upper-floor door of a building without interior
            if "door" in meta:
                kind = "hinged"
                for t in d.tags:
                    if t in ("double", "garage", "rollup", "sliding"):
                        kind = t
                attrs["DoorKind"] = kind
            model = self.w.add(parent, "Model", {"Name": d.name, "WorldPivotData": cf(ppos, prot)},
                               attrs or None, tags or None)
            scaled = any(abs(s - 1.0) > 1e-3 for s in scale)
            for (kind, lpos, lrot, lsize, mkey, collide) in prims:
                if mkey.startswith("$"):
                    ch = mkey[1:]
                    mat_idx = chans.get(ch) or self.chan_default.get(ch) or self.fallback
                else:
                    mat_idx = int(mkey)
                if scaled:
                    cols = [(lrot[0], lrot[3], lrot[6]), (lrot[1], lrot[4], lrot[7]),
                            (lrot[2], lrot[5], lrot[8])]
                    lsize = tuple(lsize[i] * math.sqrt(sum((cols[i][k] * scale[k]) ** 2
                                                           for k in range(3)))
                                  for i in range(3))
                    lpos = (lpos[0] * scale[0], lpos[1] * scale[1], lpos[2] * scale[2])
                wp = mvec(prot, lpos)
                pos = (ppos[0] + wp[0], ppos[1] + wp[1], ppos[2] + wp[2])
                self.emit_part(model, kind, pos, mmul(prot, lrot), lsize, mat_idx, collide)
            self.stats["props"] += 1

    # -- lights / markers / signs ------------------------------------------------------------
    def lights_block(self, chunk, block):
        for line in block.split("\n"):
            if not line:
                continue
            f = line.split(",")
            pos = (float(f[0]), float(f[1]), float(f[2]))
            d = (float(f[10]), float(f[11]), float(f[12]))
            if d[0] ** 2 + d[1] ** 2 + d[2] ** 2 < 1e-6:
                d = (0.0, -1.0, 0.0)
            owner = f[13] if len(f) > 13 else ""
            parent = self.folder(self.building(owner), "Fixtures") if owner else \
                self.folder(self.folder(self.root, "Lights"), chunk)
            kind = f[3]
            schedule = f[9] or "always"
            attrs = {"Schedule": schedule,
                     "Seed": float((math.floor(pos[0] * 7.13 + pos[2] * 3.71) % 1000) / 1000)}
            if owner:
                attrs["Owner"] = owner
            anchor = self.w.add(parent, "Part", {
                "Name": "Light", "Size": [0.2, 0.2, 0.2], "Transparency": 1.0, "Anchored": True,
                "CanCollide": False, "CanTouch": False, "CanQuery": False, "CastShadow": False,
                "CFrame": cf(pos, look_at(pos, d))}, attrs, ["PS_Light"])
            lp = {"Color": [float(f[4]), float(f[5]), float(f[6])],
                  "Range": max(2.0, min(60.0, float(f[7]))),
                  "Brightness": round(float(f[8]) * 1.4, 4), "Shadows": False,
                  "Enabled": schedule == "always"}
            if kind == "spot":
                lp.update({"Face": "Front", "Angle": 100.0})
            elif kind == "surface":
                lp.update({"Face": "Front", "Angle": 120.0})
            self.w.add(anchor, LIGHT_CLASS.get(kind, "PointLight"), lp)
            self.stats["lights"] += 1

    def markers_block(self, chunk, block):
        root = self.folder(self.root, "Markers")
        for line in block.split("\n"):
            if not line:
                continue
            f = line.split(",")
            kind = f[0]
            pos = (float(f[1]), float(f[2]), float(f[3]))
            attrs = {"Kind": kind, "Label": f[5], "Chunk": chunk}
            if f[6]:
                attrs["Owner"] = f[6]
            for k, v in kv(f[7]).items():
                attrs[k] = attr_value(v)
            if kind == "park":
                self.parks[f[5]] = pos
            self.w.add(self.folder(root, kind), "Part", {
                "Name": f[5] or kind, "Size": [1, 1, 1], "Transparency": 1.0, "Anchored": True,
                "CanCollide": False, "CanTouch": False, "CanQuery": False, "CastShadow": False,
                "CFrame": cf(pos, rot_y(math.radians(float(f[4]))))},
                attrs, ["PS_Marker", "PS_Marker_" + kind])
            self.stats["markers"] += 1

    def signs_block(self, chunk, block):
        for line in block.split("\n"):
            if not line:
                continue
            f = line.split(",", 14)
            pos = (float(f[0]), float(f[1]), float(f[2]))
            rot = q2m(float(f[3]), float(f[4]), float(f[5]), float(f[6]))
            w_, h_ = float(f[7]), float(f[8])
            bg, fg = int(f[9]), int(f[10])
            neon, board = f[11] == "1", f[12] == "1"
            owner, text = f[13], f[14]
            off = mvec(rot, (0.0, 0.0, -0.2))
            p = {"Name": "Sign " + text, "Anchored": True, "CanTouch": False,
                 "Size": [w_, h_, 0.4],
                 "CFrame": cf((pos[0] + off[0], pos[1] + off[1], pos[2] + off[2]), rot),
                 "TopSurface": "Smooth", "BottomSurface": "Smooth"}
            if board:
                rbx, color, transp = self.mats[bg - 1]
                p.update({"Material": rbx, "Color": list(color)})
                if transp > 0:
                    p["Transparency"] = transp
            else:
                p.update({"Transparency": 1.0, "CanCollide": False, "CanQuery": False})
            parent = self.folder(self.building(owner), "Signs") if owner else \
                self.folder(self.folder(self.root, "Signs"), chunk)
            sign = self.w.add(parent, "Part", p, {"SignText": text},
                              ["PS_NeonSign"] if neon else None)
            gui = self.w.add(sign, "SurfaceGui", {
                "Face": "Back", "SizingMode": "PixelsPerStud", "PixelsPerStud": 24.0,
                "LightInfluence": 0.0 if neon else 1.0, "Brightness": 2.5 if neon else 1.0,
                "MaxDistance": 600.0})
            self.w.add(gui, "TextLabel", {
                "Size": [0.94, 0, 0.86, 0], "Position": [0.03, 0, 0.07, 0],
                "BackgroundTransparency": 1.0, "Text": text, "TextScaled": True,
                "TextColor3": list(self.mats[fg - 1][1]),
                "FontFace": FONT_NEON if neon else FONT_SIGN})
            self.stats["signs"] += 1

    # -- preview ground ------------------------------------------------------------------------
    def preview_ground(self, grid: TerrainGrid, carve="", cell=32.0, fine=16.0, thickness=1.2,
                       tol=0.8, clearance=0.35):
        """Part-based ground + water so the town is not floating in edit mode before the voxel
        terrain is generated (buildTerrain() removes this folder).

        A triangulated surface on a 32-stud lattice, refined to 16 studs where the terrain is
        not flat enough.  Vertices start on the terrain and are lowered until no 4-stud
        sample of any triangle rises above the terrain or above the bottom of a carve volume
        (roads, sidewalks and building floors) minus ``clearance``.  Edge midpoints shared
        with a coarse cell stay on the coarse edge, so the surface has no cracks."""
        import numpy as np
        root = self.folder(self.root, "PreviewGround")
        land = self.folder(root, "Land", "Model")
        water = self.folder(root, "Water", "Model")
        res, N, org = grid.res, grid.N, grid.origin
        H = np.array(grid.H, dtype=float)                 # [row i (Blender y), col j (X)]
        M = np.array(grid.M, dtype=np.int32)
        Wl = np.array([[np.nan if v is None else v for v in row] for row in grid.W])
        lim = H - clearance
        # carve volumes: the preview stays under their bottom face
        gx = org + np.arange(N) * res                     # X of column j
        gz = -(org + np.arange(N) * res)                  # Roblox Z of row i
        for line in carve.split("\n"):
            f = line.split(",")
            if len(f) < 11:
                continue
            c = np.array([float(f[1]), float(f[2]), float(f[3])])
            R = q2m(float(f[4]), float(f[5]), float(f[6]), float(f[7]))
            sx, sy, sz = float(f[8]), float(f[9]), float(f[10])
            ax = np.array([R[0], R[3], R[6]])
            up = np.array([R[1], R[4], R[7]])
            bk = np.array([R[2], R[5], R[8]])
            if up[1] < 0.5:
                continue
            ext_x = abs(ax[0]) * sx / 2 + abs(up[0]) * sy / 2 + abs(bk[0]) * sz / 2
            ext_z = abs(ax[2]) * sx / 2 + abs(up[2]) * sy / 2 + abs(bk[2]) * sz / 2
            j0 = max(0, int(np.floor((c[0] - ext_x - org) / res)))
            j1 = min(N - 1, int(np.ceil((c[0] + ext_x - org) / res)))
            i0 = max(0, int(np.floor((-(c[2] + ext_z) - org) / res)))
            i1 = min(N - 1, int(np.ceil((-(c[2] - ext_z) - org) / res)))
            if i0 > i1 or j0 > j1:
                continue
            X, Z = np.meshgrid(gx[j0:j1 + 1], gz[i0:i1 + 1])
            b = c - up * sy / 2                            # bottom face centre
            # bottom plane height at each sample, then inside-footprint test in the plane
            yb = b[1] - (up[0] * (X - b[0]) + up[2] * (Z - b[2])) / up[1]
            d = np.stack([X - b[0], yb - b[1], Z - b[2]])
            u = ax[0] * d[0] + ax[1] * d[1] + ax[2] * d[2]
            v = bk[0] * d[0] + bk[1] * d[1] + bk[2] * d[2]
            inside = (np.abs(u) <= sx / 2 + res / 2) & (np.abs(v) <= sz / 2 + res / 2)
            sub = lim[i0:i1 + 1, j0:j1 + 1]
            lim[i0:i1 + 1, j0:j1 + 1] = np.where(inside, np.minimum(sub, yb - clearance), sub)
        n = int(round((N - 1) * res / fine))              # fine cells per side
        fs = int(round(fine / res))                       # samples per fine cell
        nv = n + 1
        # vertex grid V[a, b]: a -> X (column), b -> row; starts on the limit surface
        V = lim[::fs, ::fs].T.copy()
        # coarse cells: 2 triangles if the fine vertices are within tol of that plane
        nc = n // 2
        coarse = np.zeros((nc, nc), dtype=bool)
        for A in range(nc):
            for B in range(nc):
                a, b = 2 * A, 2 * B
                c00, c10, c11, c01 = V[a, b], V[a + 2, b], V[a + 2, b + 2], V[a, b + 2]
                # triangles (00,10,11) and (00,11,01): plane values at the 5 inner vertices
                est = {(1, 0): (c00 + c10) / 2, (2, 1): (c10 + c11) / 2,
                       (1, 2): (c11 + c01) / 2, (0, 1): (c00 + c01) / 2,
                       (1, 1): (c00 + c11) / 2}
                coarse[A, B] = all(abs(V[a + da, b + db] - e) <= tol
                                   for (da, db), e in est.items())
        # constrained midpoints (on an edge of a coarse cell): (vertex, parent1, parent2)
        cons = {}
        for A in range(nc):
            for B in range(nc):
                if not coarse[A, B]:
                    continue
                a, b = 2 * A, 2 * B
                for (m, p1, p2) in (((a + 1, b), (a, b), (a + 2, b)),
                                    ((a + 2, b + 1), (a + 2, b), (a + 2, b + 2)),
                                    ((a + 1, b + 2), (a, b + 2), (a + 2, b + 2)),
                                    ((a, b + 1), (a, b), (a, b + 2))):
                    cons[m] = (p1, p2)
        # triangles as vertex index triples (a, b) and the sample window of their cell
        tris = []                                          # (v0, v1, v2, cellA, cellB)
        for A in range(nc):
            for B in range(nc):
                a, b = 2 * A, 2 * B
                if coarse[A, B]:
                    q = [(a, b), (a + 2, b), (a + 2, b + 2), (a, b + 2)]
                    tris.append((q[0], q[1], q[2], A, B))
                    tris.append((q[0], q[2], q[3], A, B))
                else:
                    for da in (0, 1):
                        for db in (0, 1):
                            q = [(a + da, b + db), (a + da + 1, b + db),
                                 (a + da + 1, b + db + 1), (a + da, b + db + 1)]
                            tris.append((q[0], q[1], q[2], A, B))
                            tris.append((q[0], q[2], q[3], A, B))
        # samples -> containing triangle + barycentric weights (in grid index space)
        T = len(tris)
        flat = lambda v: v[0] * nv + v[1]
        sid, sv, ss, sw = [], [], [], []
        for t, (p0, p1, p2, A, B) in enumerate(tris):
            # vertex positions in sample units: column j = a * fs, row i = b * fs
            P = np.array([[p[0] * fs, p[1] * fs] for p in (p0, p1, p2)], dtype=float)
            jlo, jhi = int(P[:, 0].min()), int(P[:, 0].max())
            ilo, ihi = int(P[:, 1].min()), int(P[:, 1].max())
            J, I = np.meshgrid(np.arange(jlo, jhi + 1), np.arange(ilo, ihi + 1))
            J, I = J.ravel(), I.ravel()
            (x0, y0), (x1, y1), (x2, y2) = P
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            w0 = ((y1 - y2) * (J - x2) + (x2 - x1) * (I - y2)) / den
            w1 = ((y2 - y0) * (J - x2) + (x0 - x2) * (I - y2)) / den
            w2 = 1 - w0 - w1
            ok = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            k = int(ok.sum())
            sid.append(np.full(k, t))
            ss.append(I[ok] * N + J[ok])
            sv.append(np.tile([flat(p0), flat(p1), flat(p2)], (k, 1)))
            sw.append(np.stack([w0[ok], w1[ok], w2[ok]], 1))
        tri_of = np.concatenate(sid)
        samp = np.concatenate(ss)
        verts = np.concatenate(sv)
        W3 = np.concatenate(sw)
        limf = lim.ravel()[samp]
        tri_v = np.array([[flat(p0), flat(p1), flat(p2)] for (p0, p1, p2, _, _) in tris])
        Vf = V.ravel()
        cm = np.array([flat(m) for m in cons], dtype=int)
        cp1 = np.array([flat(p[0]) for p in cons.values()], dtype=int)
        cp2 = np.array([flat(p[1]) for p in cons.values()], dtype=int)
        if len(cm):
            Vf[cm] = (Vf[cp1] + Vf[cp2]) / 2
        for _ in range(40):
            plane = (Vf[verts] * W3).sum(1)
            viol = plane - limf
            tv = np.full(T, 0.0)
            np.maximum.at(tv, tri_of, viol)
            if tv.max() <= 0.01:
                break
            low = np.zeros(len(Vf))
            np.maximum.at(low, tri_v.ravel(), np.repeat(tv, 3))
            Vf -= low
            if len(cm):
                # a lowered midpoint drags its coarse edge down with it
                need = np.maximum((Vf[cp1] + Vf[cp2]) / 2 - Vf[cm], 0.0)
                d1 = np.zeros(len(Vf))
                np.maximum.at(d1, cp1, need)
                np.maximum.at(d1, cp2, need)
                Vf -= d1
                Vf[cm] = (Vf[cp1] + Vf[cp2]) / 2
        V = Vf.reshape(nv, nv)
        final = (Vf[verts] * W3).sum(1) - limf
        self.stats["preview_max_violation"] = round(float(final.max()), 3)
        # water: one part per wet coarse cell (as before)
        cs = 2 * fs
        names = grid.mat_names
        cell_lvl = {}
        for A in range(nc):
            for B in range(nc):
                i0, j0 = B * cs, A * cs
                wl = Wl[i0:i0 + cs:2, j0:j0 + cs:2]
                wet = np.isfinite(wl)
                if not wet.any():
                    continue
                lvl = float(np.nanmax(wl))
                if np.all(np.abs(wl[wet]) < 0.01):
                    lvl = 0.0
                cell_lvl[(A, B)] = lvl
                if wet.sum() * 4 >= wl.size:
                    x0 = org + A * cell
                    z0 = -(org + B * cell)
                    self.w.add(water, "Part", {
                        "Name": "Water", "Anchored": True, "CanCollide": False,
                        "CanTouch": False, "CanQuery": False, "CastShadow": False,
                        "Size": [cell, 1.0, cell],
                        "CFrame": cf((x0 + cell / 2, lvl - 0.55, z0 - cell / 2)),
                        "Material": "SmoothPlastic", "Color": [52 / 255, 102 / 255, 118 / 255],
                        "Transparency": 0.3, "TopSurface": "Smooth",
                        "BottomSurface": "Smooth"})
        wedges = 0
        mat_cache = {}

        def material(a, b):
            # majority terrain material of the fine cell at vertex (a, b)
            key = (a, b)
            if key not in mat_cache:
                blk = M[b * fs:(b + 1) * fs, a * fs:(a + 1) * fs].ravel()
                mid = int(np.bincount(blk).argmax()) if blk.size else 0
                nm = names[mid] if mid < len(names) else "grass"
                e = pal.P.get(nm, pal.P["grass"])
                mat_cache[key] = (e["rbx"], [c / 255.0 for c in e["rgb"]])
            return mat_cache[key]

        for (p0, p1, p2, A, B) in tris:
            pts = [(org + p[0] * fine, float(V[p[0], p[1]]), -(org + p[1] * fine))
                   for p in (p0, p1, p2)]
            lvl = cell_lvl.get((A, B))
            if lvl is not None and all(pt[1] < lvl - 3.0 for pt in pts):
                continue                      # fully under water: the floor is not needed
            ma = min(p[0] for p in (p0, p1, p2))
            mb = min(p[1] for p in (p0, p1, p2))
            rbx, color = material(min(ma, n - 1), min(mb, n - 1))
            for (pos, rot, size) in tri_wedges(*pts, thickness):
                self.w.add(land, "WedgePart", {
                    "Anchored": True, "CanTouch": False, "CastShadow": False,
                    "Size": [round(v, 4) for v in size], "CFrame": cf(pos, rot),
                    "Material": rbx, "Color": color,
                    "TopSurface": "Smooth", "BottomSurface": "Smooth"})
                wedges += 1
        self.stats["preview_wedges"] = wedges
        self.stats["preview_fine_cells"] = int((~coarse).sum())

    def spawn_spot(self, grid: TerrainGrid):
        """A clear 12x12 spot on the Town Square lawn (first ring around the marker)."""
        sx, sy, sz = getattr(self, "square", (164.4, 8.2, 60.4))
        for r in (0.0, 14.0, 20.0, 26.0, 32.0, 40.0, 48.0, 56.0):
            for k in range(16 if r else 1):
                a = 2 * math.pi * k / 16
                x, z = sx + math.cos(a) * r, sz + math.sin(a) * r
                y = grid.h(x, z)
                if abs(y - sy) < 3.0 and self.spawn_probe.clear(x, y, z):
                    return (x, y, z)
        return (sx + 30.0, sy, sz)

    # -- top level -----------------------------------------------------------------------------
    def build_town(self, workspace_ref, chunk_names=None):
        self.root = self.w.add(workspace_ref, "Folder", {"Name": "PortSolace"},
                               {"Town": self.m.get("town", "Port Solace")})
        self.buildings_root = self.folder(self.root, "Buildings")
        self.infra_root = self.folder(self.root, "Infrastructure")
        self.world_root = self.folder(self.root, "World")
        cdir = os.path.join(self.data_dir, "Chunks")
        names = chunk_names or sorted(fn[:-4] for fn in os.listdir(cdir) if fn.endswith(".lua"))
        chunks = []
        for name in names:
            src = open(os.path.join(cdir, name + ".lua")).read()
            blocks = {m.group(1): m.group(3) for m in BLOCK_RE.finditer(src)}
            chunks.append((name, blocks))
            for line in blocks.get("markers", "").split("\n"):
                f = line.split(",")
                if len(f) > 5 and f[0] == "park" and f[5] == "Town Square":
                    self.square = (float(f[1]), float(f[2]), float(f[3]))
        sq = getattr(self, "square", (164.4, 8.2, 60.4))
        self.spawn_probe = SpawnProbe(sq[0], sq[2])
        carve = []
        for name, blocks in chunks:
            self.parts_block(name, blocks.get("parts", ""))
            self.props_block(name, blocks.get("props", ""))
            self.lights_block(name, blocks.get("lights", ""))
            self.markers_block(name, blocks.get("markers", ""))
            self.signs_block(name, blocks.get("signs", ""))
            carve.append(blocks.get("carve", ""))
        return "\n".join(c for c in carve if c)


def lighting(w: Writer):
    lit = w.add(None, "Lighting", {
        "ClockTime": 17.6, "GeographicLatitude": 34.0, "Brightness": 2.4,
        "EnvironmentDiffuseScale": 0.6, "EnvironmentSpecularScale": 0.5,
        "Ambient": [90 / 255, 82 / 255, 96 / 255], "OutdoorAmbient": [128 / 255, 118 / 255, 132 / 255],
        "ColorShift_Top": [1.0, 222 / 255, 186 / 255], "GlobalShadows": True,
        "Technology": "Future"})
    w.add(lit, "Atmosphere", {"Name": "PortSolaceAtmosphere", "Density": 0.32, "Haze": 1.6,
                              "Color": [214 / 255, 186 / 255, 160 / 255],
                              "Decay": [120 / 255, 96 / 255, 110 / 255], "Glare": 0.4,
                              "Offset": 0.1})
    w.add(lit, "BloomEffect", {"Name": "PortSolaceBloom", "Intensity": 0.35, "Size": 28.0,
                               "Threshold": 1.6})
    w.add(lit, "ColorCorrectionEffect", {"Name": "PortSolaceGrade", "Saturation": 0.05,
                                         "Contrast": 0.06,
                                         "TintColor": [1.0, 244 / 255, 232 / 255]})
    w.add(lit, "SunRaysEffect", {"Name": "PortSolaceSunRays", "Intensity": 0.06, "Spread": 0.6})
    return lit


MAX_SOURCE = 150_000           # characters per ModuleScript (keeps every script small)


def _long(text):
    eq = "=" * 3
    while f"]{eq}]" in text:
        eq += "="
    return f"[{eq}[\n{text}\n]{eq}]"


def _packs(items, size_of, limit=MAX_SOURCE):
    pack, n = [], 0
    for it in items:
        k = size_of(it)
        if pack and n + k > limit:
            yield pack
            pack, n = [], 0
        pack.append(it)
        n += k
    if pack:
        yield pack


def terrain_modules(w, parent, src):
    """TerrainData as a small header module plus child modules of row strings."""
    head = src[:src.index("\theights = {")]
    body = head[head.index("return {") + len("return {"):]
    rows = {}
    for name in ("heights", "mats", "water"):
        block = re.search(r"\t" + name + r" = \{\n(.*?)\n\t\}", src, re.S).group(1)
        rows[name] = re.findall(r'"([^"]*)"', block)
    lua = ("-- Generated terrain data: 4-stud grid, row i = Blender Y (Roblox -Z), col j = X.\n"
           "-- Rows live in child modules so that no script is very large.\n"
           "local T = {" + body.rstrip() + "\n}\n"
           "local function rows(prefix)\n"
           "\tlocal out, k = {}, 1\n"
           "\twhile script:FindFirstChild(prefix .. k) do\n"
           "\t\tfor _, r in ipairs(require(script[prefix .. k])) do\n"
           "\t\t\tout[#out + 1] = r\n\t\tend\n\t\tk += 1\n\tend\n\treturn out\nend\n"
           "T.heights = rows(\"Heights\")\nT.mats = rows(\"Mats\")\nT.water = rows(\"Water\")\n"
           "return T\n")
    td = w.add(parent, "ModuleScript", {"Name": "TerrainData", "Source": lua})
    for name, prefix in (("heights", "Heights"), ("mats", "Mats"), ("water", "Water")):
        for k, pack in enumerate(_packs(rows[name], lambda r: len(r) + 6), 1):
            src_k = "return {\n" + "\n".join(f'\t"{r}",' for r in pack) + "\n}\n"
            w.add(td, "ModuleScript", {"Name": f"{prefix}{k}", "Source": src_k})


def carve_modules(w, parent, carve):
    """CarveData: returns the carve records as one string, stored in small child modules."""
    lua = ("-- Generated: terrain volumes cleared inside buildings and above roads\n"
           "local parts, k = {}, 1\n"
           "while script:FindFirstChild(\"Part\" .. k) do\n"
           "\tparts[k] = require(script[\"Part\" .. k])\n\tk += 1\nend\n"
           "return table.concat(parts, \"\\n\")\n")
    cd = w.add(parent, "ModuleScript", {"Name": "CarveData", "Source": lua})
    lines = [ln for ln in carve.split("\n") if ln]
    for k, pack in enumerate(_packs(lines, lambda ln: len(ln) + 1), 1):
        w.add(cd, "ModuleScript", {"Name": f"Part{k}",
                                   "Source": "return " + _long("\n".join(pack)) + "\n"})


def write_instances(data_dir, manifest_path, out_jsonl, mode="place", interiors=True,
                    prop_detail=3, preview=True, chunks=None, log=print):
    """Expand the Roblox export into an instance list for rbxconv."""
    manifest = json.load(open(manifest_path))
    grid = TerrainGrid(os.path.join(data_dir, "TerrainData.lua"))
    w = Writer(out_jsonl)
    ws = None
    if mode == "place":
        ws = w.add(None, "Workspace", {"StreamingEnabled": True, "StreamingTargetRadius": 768,
                                       "StreamingMinRadius": 256})
    pb = PlaceBuilder(data_dir, manifest, w, interiors=interiors, prop_detail=prop_detail)
    carve = pb.build_town(ws, chunks)
    if preview:
        pb.preview_ground(grid, carve)
    # spawn on a clear spot of the town square (it has ground even before the terrain)
    x, y, z = pb.spawn_spot(grid)
    pb.stats["spawn"] = (round(x, 1), round(y, 1), round(z, 1))
    w.add(ws if mode == "place" else pb.root, "SpawnLocation", {
        "Name": "TownSquareSpawn", "Anchored": True, "Neutral": True, "Size": [12, 1, 12],
        "CFrame": cf((x, y + 0.1, z)), "Material": "Cobblestone",
        "Color": [0.62, 0.6, 0.56], "TopSurface": "Smooth", "BottomSurface": "Smooth",
        "Duration": 0})
    # scripts + data
    rd = lambda p: open(p).read()
    if mode == "place":
        lighting(w)
        sss = w.add(None, "ServerScriptService", {})
        store = w.add(w.add(None, "ServerStorage", {}), "Folder", {"Name": "PortSolace"})
    else:
        # a model: scripts run from the town folder itself, data sits next to them
        sss = pb.root
        store = pb.folder(pb.root, "PortSolaceData")
    w.add(sss, "Script", {"Name": "TownRuntime",
                          "Source": rd(os.path.join(REPO_ROBLOX, "TownRuntime.server.lua"))})
    w.add(sss, "Script", {"Name": "TerrainLoader",
                          "Source": rd(os.path.join(REPO_ROBLOX, "TerrainLoader.server.lua"))})
    w.add(store, "ModuleScript", {"Name": "TownBuilder",
                                  "Source": rd(os.path.join(REPO_ROBLOX, "TownBuilder.lua"))})
    for nm in ("Manifest", "Palette"):
        w.add(store, "ModuleScript", {"Name": nm,
                                      "Source": rd(os.path.join(data_dir, nm + ".lua"))})
    terrain_modules(w, store, rd(os.path.join(data_dir, "TerrainData.lua")))
    carve_modules(w, store, carve)
    w.close()
    log(f"{os.path.basename(out_jsonl)}: {w.n} instances ({pb.stats})")
    return w.n, pb.stats, w.counts


def find_rbxconv():
    """Path to the rbxconv binary, building it with cargo if needed."""
    env = os.environ.get("RBXCONV")
    if env and os.path.exists(env):
        return env
    tool = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "tools",
                                         "rbxconv"))
    exe = os.path.join(tool, "target", "release", "rbxconv")
    if not os.path.exists(exe):
        if not shutil.which("cargo"):
            return None
        subprocess.run(["cargo", "build", "--release"], cwd=tool, check=True)
    return exe


def build_place(data_dir, manifest_path, out_path, mode="place", log=print, **kw):
    jsonl = out_path + ".jsonl"
    write_instances(data_dir, manifest_path, jsonl, mode=mode, log=log, **kw)
    exe = find_rbxconv()
    if exe is None:
        log("place: cargo not found; instance list left at " + jsonl)
        return None
    subprocess.run([exe, mode, jsonl, out_path], check=True)
    if not os.environ.get("PS_KEEP_JSONL"):          # keep the instance list for audits
        os.remove(jsonl)
    log(f"place: wrote {out_path} ({os.path.getsize(out_path) / 1e6:.1f} MB)")
    return out_path


LITE_DISTRICTS = ("DOWNTOWN", "CIVIC")


def lite_interiors(bid, info):
    """Lite variant: interiors only for landmarks and the downtown/civic core."""
    return bool(info) and (info.get("landmark") or info.get("district") in LITE_DISTRICTS)


def build_all(roblox_dir, log=print):
    """Ready-to-open files next to the Roblox export: full place, lite place, town model."""
    data = os.path.join(roblox_dir, "PortSolace")
    man = os.path.join(roblox_dir, "manifest.json")
    out = []
    out.append(build_place(data, man, os.path.join(roblox_dir, "PortSolace.rbxl"), "place",
                           log=log))
    out.append(build_place(data, man, os.path.join(roblox_dir, "PortSolace_Lite.rbxl"), "place",
                           log=log, interiors=lite_interiors))
    out.append(build_place(data, man, os.path.join(roblox_dir, "PortSolace_Town.rbxm"), "model",
                           log=log))
    return out
