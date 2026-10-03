"""World container: everything generated, engine-agnostic, ready to realise/export."""

from __future__ import annotations

import math

from .. import geom
from . import layout as Lay


def chunk_of(x, y, size=Lay.CHUNK):
    n = int(2 * Lay.HALF / size)
    i = int(min(n - 1, max(0, (x + Lay.HALF) // size)))
    j = int(min(n - 1, max(0, (y + Lay.HALF) // size)))
    return (i, j)


def chunk_name(c):
    return f"C{c[0]}_{c[1]}"


class BuildingRec:
    def __init__(self, lot, plan, built, xf, ext_path, int_path, landmark=False):
        self.id = lot.id
        self.lot = lot
        self.plan = plan
        self.built = built
        self.xf = xf
        self.ext_path = ext_path
        self.int_path = int_path
        self.landmark = landmark
        # street address from the frontage road: odd numbers on the left side
        self.address = ""
        if getattr(lot, "road", None) is not None:
            num = 10 + 2 * int(lot.s / 6.0) + (1 if lot.side > 0 else 0)
            self.address = f"{num} {lot.road.name}"
        named = plan.name and plan.name != plan.archetype
        self.name = plan.name if named else (self.address or plan.archetype)
        self.arch = plan.archetype
        self.district = lot.district

    @property
    def chunk(self):
        return chunk_of(*self.lot.center)

    def summary(self):
        p = self.plan
        ents = []
        for e in self.built.entrances:
            wx, wy, wz = self.xf.point((e["x"], e["y"], e["z"]))
            ents.append({"role": e["role"], "kind": e["kind"], "side": e["side"],
                         "room": e["room"], "level": e["level"],
                         "pos": [round(wx, 2), round(wy, 2), round(wz, 2)]})
        cx, cy = self.lot.center
        return {
            "id": self.id, "name": self.name, "address": self.address,
            "archetype": p.archetype,
            "district": self.district, "quality": p.quality, "detail": p.detail,
            "landmark": self.landmark,
            "center": [round(cx, 2), round(cy, 2), round(self.xf.z, 2)],
            "yaw_deg": round(math.degrees(self.xf.yaw), 2),
            "size": [p.w, p.d, round(p.height, 2)], "levels": len(p.levels),
            "basement": bool(p.basement), "roof_access": bool(p.roof.access),
            "entrances": ents, "rooms": self.built.room_info,
            "tags": sorted(p.tags), "chunk": chunk_name(self.chunk),
        }


class World:
    def __init__(self):
        self.terrain = None
        self.net = None
        self.buildings: list[BuildingRec] = []
        self.sweeps = []          # roads.Sweep (world coords); .cat -> collection
        self.patches = []         # (cat, mat, verts, faces, center)
        self.boxes = []           # (cat, Prim) world coords
        self.props = []           # (PropPlace world, cat)
        self.lights = []          # LightRec world
        self.markers = []         # Marker world
        self.signs = []           # (SignRec world, cat)
        self.water = []           # (name, mat, verts, faces)
        self.stats = {}
        self.issues = []

    # convenience for dressing code
    def add_prop(self, pp, cat="PROPS"):
        self.props.append((pp, cat))

    def add_box(self, cat, mat, cx, cy, cz, sx, sy, sz, yaw=0.0, collide=True):
        self.boxes.append((cat, geom.Prim("box", mat, (cx, cy, cz), (sx, sy, sz),
                                          geom.rot_z(yaw), collide)))
