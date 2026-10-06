"""Part specification shared by all builders."""

import hashlib
import os
from dataclasses import dataclass, field

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def source_hash(*modules):
    h = hashlib.sha1()
    for m in ("sdf", "dims", "mesher") + modules:
        with open(os.path.join(HERE, m + ".py"), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:12]


@dataclass
class Part:
    """One SDF-built mesh.

    mat is either a material key or a classifier
    `fn(centroids (N,3), normals (N,3)) -> array of material keys`, in which
    case the mesh is split into one object per material.
    """
    name: str
    sdf: object
    lo: tuple
    hi: tuple
    h: float
    tris: int
    mat: object
    group: str = "Body"
    mirror: bool = False          # build +X side, mirror a copy to -X
    origin: tuple = None          # pivot; default = bounding box centre
    deps: tuple = ("body",)       # modules whose source affects this part
    sharp: float = 48.0           # sharp edge angle for shading
    names: dict = field(default_factory=dict)  # material key -> object name override


@dataclass
class MeshPart:
    """A part given directly as arrays (parametric geometry)."""
    name: str
    verts: np.ndarray
    faces: object
    mat: object
    group: str = "Body"
    mirror: bool = False
    origin: tuple = None
    sharp: float = 40.0
    uv: np.ndarray = None         # optional per-loop UVs (N_loops, 2)
    smooth: bool = True


def mirror_name(name):
    if name.endswith("_R"):
        return name[:-2] + "_L"
    if "_R_" in name:
        return name.replace("_R_", "_L_")
    if "FR" in name:
        return name.replace("FR", "FL")
    if "RR" in name:
        return name.replace("RR", "RL")
    return name + "_L"
