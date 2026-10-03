"""Floor-plan data model.

A building is described by *rooms*, not by walls.  Each room owns one or more
axis-aligned rectangles per level (so L-shapes and double-height spaces are
possible).  Walls, door openings, windows, floor slabs, ceilings and roofs are
all *derived* from the rooms, which is what guarantees interior/exterior
continuity: a window only exists where a room is behind it, a door only where
two spaces (or a space and the outside) actually meet.

Local frame: x in [0, w] along the street frontage, y in [0, d] from the
front facade (y = 0, facing -Y / the street) to the back, z = 0 ground floor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..geom import Rect

SIDES = ("front", "back", "left", "right")
OPPOSITE = {"front": "back", "back": "front", "left": "right", "right": "left"}


def R(x0, y0, x1, y1) -> Rect:
    """Rounded rectangle constructor (plans live on a 0.25 stud grid)."""
    q = lambda v: round(v * 4) / 4.0
    return Rect(q(min(x0, x1)), q(min(y0, y1)), q(max(x0, x1)), q(max(y0, y1)))


@dataclass
class Room:
    id: str
    kind: str
    cells: dict = field(default_factory=dict)  # level -> [Rect]
    floor: str | None = None
    wall: str | None = None
    ceiling: str | None = None
    name: str = ""
    tags: set = field(default_factory=set)
    window: str | None = None   # window policy override
    light: str | None = None    # ceiling fixture override ("none" for dark rooms)
    unit: str | None = None     # apartment / motel unit id
    furnish: bool = True

    def levels(self):
        return sorted(self.cells)

    def rects(self, level):
        return self.cells.get(level, [])

    def main_rect(self, level):
        rs = self.rects(level)
        return max(rs, key=lambda r: r.area) if rs else None

    def area(self, level=None):
        if level is None:
            return sum(r.area for rs in self.cells.values() for r in rs)
        return sum(r.area for r in self.rects(level))


@dataclass
class Door:
    a: str                      # room id
    b: str | None               # room id, or None for an exterior door
    level: int = 0
    kind: str = "interior"      # interior exterior metal glass glass_double opening garage
                                # rollup bay sliding cell double
    side: str | None = None     # exterior doors: front/back/left/right
    at: float | None = None     # absolute coordinate along the wall axis (centre)
    width: float | None = None
    height: float | None = None
    role: str | None = None     # main secondary service garage emergency balcony
    locked: bool = False


@dataclass
class Stair:
    rect: Rect
    level: int                  # bottom level
    kind: str = "straight"      # straight | u
    up: str = "+y"              # direction of travel while ascending (first flight for u)
    to_roof: bool = False
    rail: bool = True


@dataclass
class Facade:
    mat: str = "brick_red"
    ground: str | None = None           # ground-floor material (shopfront base)
    trim: str = "trim_white"
    frame: str = "trim_white"           # window frames
    glass: str = "glass"
    base: str | None = "concrete"       # plinth / base course
    cornice: bool = False
    band: bool = False                  # string course between floors
    shutters: str | None = None
    storefront: tuple = ()              # sides with ground-floor shopfront glazing
    awning: str | None = None           # material
    awning_sides: tuple = ("front",)
    side_mats: dict = field(default_factory=dict)  # side -> material
    blind: set = field(default_factory=set)        # party-wall sides (no openings)
    bay: float = 10.0                   # facade bay width used to align windows
    window_w: float | None = None       # override window width
    lit_sign: bool = True


@dataclass
class Roof:
    kind: str = "flat"          # flat | gable | shed | none
    mat: str = "roof_membrane"
    pitch: float = 0.5          # rise / run for gable & shed
    ridge: str = "x"            # gable ridge axis
    overhang: float = 1.2
    parapet: float = 2.5        # flat roofs
    coping: str = "concrete_light"
    equipment: str = "auto"     # auto | none
    chimney: bool = False
    access: bool = False        # roof reachable (stair bulkhead or hatch present)
    gable_mat: str | None = None
    masses: list | None = None  # [(Rect, ridge)] pitched-roof volumes; default = cells


@dataclass
class Sign:
    text: str
    side: str = "front"
    level: int = 0
    style: str = "board"        # board | blade | roof | letters | neon | pole
    bg: str = "sign_red"
    fg: str = "sign_white"
    at: float | None = None
    width: float | None = None
    neon: bool = False
    offset: float = 14.0        # pole signs: distance in front of the facade
    z: float | None = None      # override the sign centre height


@dataclass
class Plan:
    w: float
    d: float
    levels: list                         # heights of levels 0..n-1
    rooms: list = field(default_factory=list)
    doors: list = field(default_factory=list)
    stairs: list = field(default_factory=list)
    basement: float | None = None        # height of level -1
    facade: Facade = field(default_factory=Facade)
    roof: Roof = field(default_factory=Roof)
    signs: list = field(default_factory=list)
    extras: list = field(default_factory=list)   # callables(builder)
    name: str = ""
    archetype: str = ""
    quality: str = "normal"              # cheap | normal | nice | abandoned
    detail: int = 3                      # 3 high, 2 medium, 1 simplified
    tags: set = field(default_factory=set)
    exterior_props: list = field(default_factory=list)  # (prop, x, y, z, yaw, channels)
    lighting: str = "res"                # light schedule family
    yard: dict = field(default_factory=dict)

    # -- construction helpers -------------------------------------------------
    def room(self, id, kind, rect, level=0, **kw):
        r = Room(id, kind, {level: [rect]}, **kw)
        self.rooms.append(r)
        return r

    def get(self, id) -> Room:
        for r in self.rooms:
            if r.id == id:
                return r
        raise KeyError(id)

    def has(self, id):
        return any(r.id == id for r in self.rooms)

    def door(self, a, b=None, level=0, kind=None, **kw):
        if kind is None:
            kind = "interior" if b is not None else "exterior"
        d = Door(a, b, level, kind, **kw)
        self.doors.append(d)
        return d

    def stair(self, rect, level, kind="straight", up="+y", **kw):
        s = Stair(rect, level, kind, up, **kw)
        self.stairs.append(s)
        return s

    @property
    def top(self):
        return len(self.levels) - 1

    @property
    def lowest(self):
        return -1 if self.basement else 0

    def level_z(self, L):
        if L < 0:
            return -(self.basement or 0)
        return sum(self.levels[:L])

    def level_h(self, L):
        if L < 0:
            return self.basement
        return self.levels[L]

    @property
    def height(self):
        return sum(self.levels)

    def all_levels(self):
        return list(range(self.lowest, len(self.levels)))

    def mirror(self):
        """Flip the plan left/right (variety without new layouts)."""
        w = self.w
        for r in self.rooms:
            r.cells = {L: [c.mirror_x(w) for c in rs] for L, rs in r.cells.items()}
        for s in self.stairs:
            s.rect = s.rect.mirror_x(w)
            if s.up == "+x":
                s.up = "-x"
            elif s.up == "-x":
                s.up = "+x"
        for d in self.doors:
            if d.side == "left":
                d.side = "right"
            elif d.side == "right":
                d.side = "left"
            if d.at is not None and d.side in ("front", "back", None):
                d.at = w - d.at
        f = self.facade
        # f.blind refers to the lot's real neighbours, so it is NOT mirrored
        f.side_mats = {("right" if s == "left" else "left" if s == "right" else s): m
                       for s, m in f.side_mats.items()}
        for sg in self.signs:
            if sg.side == "left":
                sg.side = "right"
            elif sg.side == "right":
                sg.side = "left"
            if sg.at is not None and sg.side in ("front", "back"):
                sg.at = w - sg.at
        new_ext = []
        for (p, x, y, z, yaw, ch) in self.exterior_props:
            import math
            new_ext.append((p, w - x, y, z, math.pi - yaw if yaw else yaw, ch))
        self.exterior_props = new_ext
        return self


def split(a, b, sizes):
    """Split interval [a, b] by absolute sizes; a ``None`` size takes the remainder."""
    fixed = sum(s for s in sizes if s is not None)
    n_free = sum(1 for s in sizes if s is None)
    free = (b - a - fixed) / n_free if n_free else 0
    out = []
    x = a
    for s in sizes:
        v = free if s is None else s
        out.append((x, x + v))
        x += v
    return out


def fsplit(a, b, fracs):
    tot = sum(fracs)
    out = []
    x = a
    for f in fracs:
        v = (b - a) * f / tot
        out.append((round(x * 4) / 4, round((x + v) * 4) / 4))
        x += v
    out[-1] = (out[-1][0], b)
    return out
