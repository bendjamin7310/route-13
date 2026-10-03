"""Reusable prop kit.

A prop is defined once (a builder that emits primitives in prop-local space)
and instanced everywhere: in Blender as linked duplicates sharing one mesh, in
Roblox as clones of one imported Model.  Conventions:

* origin at the centre of the footprint, on the floor (z = 0)
* the prop's *front* faces -Y; its back is at +Y (so a wall prop's back
  touches the wall at y = +depth/2)
* ceiling props hang below z = 0 (origin is the ceiling attach point)
* recolourable surfaces use "$channel" materials (see palette.CHANNEL_DEFAULTS)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..geom import Sink

KIT: dict[str, "PropDef"] = {}


@dataclass
class PropDef:
    name: str
    cat: str
    builder: object
    mount: str = "floor"          # floor | wall | ceiling | surface
    collide: object = "box"       # "box" | "none" | list of (x0,y0,z0,x1,y1,z1)
    light: dict | None = None     # {"at":(x,y,z), "color":(r,g,b), "range":r, "brightness":b, "kind":..}
    tags: tuple = ()
    detail: int = 1               # 1 = always, 2 = medium+, 3 = high only
    _prims: list | None = field(default=None, repr=False)
    _bbox: tuple | None = field(default=None, repr=False)

    @property
    def prims(self):
        if self._prims is None:
            k = Sink()
            self.builder(k)
            self._prims = k.prims
        return self._prims

    @property
    def bbox(self):
        if self._bbox is None:
            self._bbox = prims_bbox(self.prims)
        return self._bbox

    @property
    def size(self):
        b = self.bbox
        return (b[3] - b[0], b[4] - b[1], b[5] - b[2])

    @property
    def channels(self):
        return sorted({p.mat for p in self.prims if p.mat.startswith("$")})

    def collision_boxes(self):
        if self.collide == "none":
            return []
        if self.collide == "box":
            return [self.bbox]
        return list(self.collide)


def prims_bbox(prims):
    import math
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    for p in prims:
        if p.kind == "mesh":
            verts = p.data[0]
            for v in verts:
                for i in range(3):
                    c = v[i] + p.pos[i]
                    lo[i] = min(lo[i], c)
                    hi[i] = max(hi[i], c)
            continue
        hx, hy, hz = p.size[0] / 2, p.size[1] / 2, p.size[2] / 2
        r = p.rot
        for i in range(3):
            ext = abs(r[i * 3]) * hx + abs(r[i * 3 + 1]) * hy + abs(r[i * 3 + 2]) * hz
            lo[i] = min(lo[i], p.pos[i] - ext)
            hi[i] = max(hi[i], p.pos[i] + ext)
    if lo[0] > hi[0]:
        return (0, 0, 0, 0, 0, 0)
    return (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])


def prop(name, cat, mount="floor", collide="box", light=None, tags=(), detail=1):
    def deco(fn):
        if name in KIT:
            raise ValueError(f"duplicate prop {name}")
        KIT[name] = PropDef(name, cat, fn, mount, collide, light, tuple(tags), detail)
        return fn
    return deco


def variant(name, base, cat=None, **kw):
    """Register a prop built by calling ``base`` with keyword args."""
    def fn(k, _b=base, _kw=kw):
        _b(k, **_kw)
    src = KIT.get(base.__name__)
    KIT[name] = PropDef(name, cat or (src.cat if src else "misc"), fn,
                        src.mount if src else "floor", src.collide if src else "box",
                        src.light if src else None, src.tags if src else (),
                        src.detail if src else 1)
    return KIT[name]


def get(name) -> PropDef:
    return KIT[name]


def load_all():
    # Import order matters only for registration.
    from . import furniture, kitchen_bath, commercial, industrial, street, vehicles, \
        vegetation, doors  # noqa: F401
    return KIT


WARM = (1.0, 0.82, 0.62)
NEUTRAL = (1.0, 0.92, 0.82)
COOL = (0.86, 0.92, 1.0)
SODIUM = (1.0, 0.72, 0.42)
