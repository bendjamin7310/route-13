"""Building archetypes: functions that return a ``Plan`` for a given lot size.

Each archetype is registered with its footprint ranges, the Blender collection
its exterior goes in, the interior category, and how it sits on a lot.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

ARCH: dict[str, "ArchDef"] = {}


@dataclass
class Ctx:
    w: float
    d: float
    rng: random.Random
    district: str = "RESIDENTIAL"
    quality: str = "normal"
    detail: int = 3
    blind: set = field(default_factory=set)
    name: str = ""
    opts: dict = field(default_factory=dict)

    def pick(self, seq):
        return self.rng.choice(seq)

    def pick_name(self, seq):
        """Like pick() (same single rng draw) but skips names already used in the town."""
        seq = list(seq)
        i = seq.index(self.rng.choice(seq))
        for k in range(len(seq)):
            cand = seq[(i + k) % len(seq)]
            if cand not in USED_NAMES:
                USED_NAMES.add(cand)
                return cand
        n = 2
        while f"{seq[i]} {n}" in USED_NAMES:
            n += 1
        USED_NAMES.add(f"{seq[i]} {n}")
        return f"{seq[i]} {n}"

    def chance(self, p):
        return self.rng.random() < p

    def r(self, a, b, step=0.5):
        v = self.rng.uniform(a, b)
        return round(v / step) * step


@dataclass
class ArchDef:
    name: str
    fn: object
    w: tuple
    d: tuple
    collection: str          # exterior collection (district-level override possible)
    interior: str            # INTERIORS sub-collection
    front_setback: float = 0.0
    rear_clear: float = 6.0
    side_gap: float = 6.0
    yard: str = "none"       # none | residential | parking | loading | lot
    tags: tuple = ()


def archetype(name, w, d, collection="RESIDENTIAL", interior="RESIDENTIAL", **kw):
    def deco(fn):
        ARCH[name] = ArchDef(name, fn, w, d, collection, interior, **kw)
        return fn
    return deco


MODULES = ("residential", "commercial", "industrial", "civic", "waterfront", "roadside",
           "landmarks")


def load_all():
    import importlib
    for m in MODULES:
        try:
            importlib.import_module(f"{__name__}.{m}")
        except ModuleNotFoundError as e:
            if e.name != f"{__name__}.{m}":
                raise
    return ARCH


USED_NAMES = set()


def reset_names():
    USED_NAMES.clear()


def make(arch, w, d, seed, **kw):
    a = ARCH[arch]
    ctx = Ctx(w, d, random.Random(seed), **kw)
    plan = a.fn(ctx)
    plan.archetype = arch
    if not plan.name:
        plan.name = ctx.name or arch
    return plan
