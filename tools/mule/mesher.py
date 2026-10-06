"""Turn signed distance functions into game-ready Blender meshes.

Pipeline per part:
  narrow-band SDF sampling -> marching cubes -> Blender mesh ->
  quadric decimation to a triangle budget -> cached as .npz
Shading (smooth + sharp-by-angle + weighted normals) is applied later by
`finish_shading` once the object is in its final place.
"""

import hashlib
import math
import os
import time

import bmesh
import bpy
import numpy as np
from skimage import measure

CACHE_DIR = os.environ.get("MULE_CACHE", os.path.join(os.path.dirname(__file__), ".cache"))


def log(*a):
    print("[mule]", *a, flush=True)


# ----------------------------------------------------------- sampling

def sample_volume(f, lo, hi, h, block=8, band=2.0, chunk=3_000_000):
    """Evaluate f on a regular grid, exactly only near the surface.

    Blocks whose centre is far from the surface (|d| larger than the block's
    half diagonal times `band`) are filled with the centre value, which keeps
    the sign right and costs one evaluation per block.
    """
    lo = np.asarray(lo, dtype=np.float64)
    hi = np.asarray(hi, dtype=np.float64)
    n = np.ceil((hi - lo) / h).astype(int) + 1
    nb = (n + block - 1) // block
    N = nb * block
    vol = np.empty(tuple(N), dtype=np.float32)

    cx = lo[0] + ((np.arange(nb[0]) + 0.5) * block - 0.5) * h
    cy = lo[1] + ((np.arange(nb[1]) + 0.5) * block - 0.5) * h
    cz = lo[2] + ((np.arange(nb[2]) + 0.5) * block - 0.5) * h
    CX, CY, CZ = np.meshgrid(cx.astype(np.float32), cy.astype(np.float32), cz.astype(np.float32), indexing="ij")
    dc = f(CX, CY, CZ).astype(np.float32)

    v6 = vol.reshape(nb[0], block, nb[1], block, nb[2], block).transpose(0, 2, 4, 1, 3, 5)
    v6[...] = dc[:, :, :, None, None, None]

    half_diag = math.sqrt(3) * block * h * 0.5
    near = np.argwhere(np.abs(dc) < half_diag * band + 2 * h)
    off = np.arange(block, dtype=np.float32) * h
    OX, OY, OZ = np.meshgrid(off, off, off, indexing="ij")
    OX, OY, OZ = OX.ravel(), OY.ravel(), OZ.ravel()
    per_block = block ** 3
    nblk = max(1, chunk // per_block)
    for s in range(0, len(near), nblk):
        idx = near[s:s + nblk]
        bx = (lo[0] + idx[:, 0] * block * h).astype(np.float32)
        by = (lo[1] + idx[:, 1] * block * h).astype(np.float32)
        bz = (lo[2] + idx[:, 2] * block * h).astype(np.float32)
        X = (bx[:, None] + OX[None, :])
        Y = (by[:, None] + OY[None, :])
        Z = (bz[:, None] + OZ[None, :])
        d = f(X, Y, Z).astype(np.float32).reshape(len(idx), block, block, block)
        v6[idx[:, 0], idx[:, 1], idx[:, 2]] = d
    return vol, lo, len(near) / max(1, dc.size)


def polygonize(f, lo, hi, h, **kw):
    t = time.time()
    vol, lo, frac = sample_volume(f, lo, hi, h, **kw)
    t1 = time.time()
    if vol.min() >= 0 or vol.max() <= 0:
        raise RuntimeError("SDF has no surface inside the sampling box")
    verts, faces, _n, _v = measure.marching_cubes(vol, 0.0, spacing=(h, h, h), allow_degenerate=False)
    verts = verts + lo
    # orient faces outward (SDF negative inside)
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    signed = np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum()
    if signed < 0:
        faces = faces[:, ::-1]
    log(f"  sampled {vol.size/1e6:.1f}M voxels ({frac*100:.0f}% near band) in {t1-t:.1f}s, "
        f"mc {len(faces)} tris in {time.time()-t1:.1f}s")
    return verts.astype(np.float32), faces.astype(np.int32)


# ----------------------------------------------------------- blender glue

def mesh_from_arrays(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    if not isinstance(faces, np.ndarray) and len({len(p) for p in faces}) == 1:
        faces = np.asarray(faces, dtype=np.int32)
    if isinstance(faces, np.ndarray) and faces.ndim == 2:
        faces = faces.astype(np.int32)
        sizes = np.full(len(faces), faces.shape[1], dtype=np.int32)
        flat = faces.ravel()
    else:  # list of polygons
        sizes = np.array([len(p) for p in faces], dtype=np.int32)
        flat = np.concatenate(faces).astype(np.int32)
    me.loops.add(len(flat))
    me.loops.foreach_set("vertex_index", flat)
    me.polygons.add(len(sizes))
    starts = np.zeros(len(sizes), dtype=np.int32)
    starts[1:] = np.cumsum(sizes)[:-1]
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    return me


def arrays_from_mesh(me):
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tri = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    return co.reshape(-1, 3), tri.reshape(-1, 3)


def link_object(name, me, collection=None):
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def decimate_arrays(verts, faces, target_tris, name="tmp"):
    me = mesh_from_arrays(name, verts, faces)
    ob = link_object(name, me)
    cur = len(faces)
    if target_tris < cur:
        m = ob.modifiers.new("dec", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = target_tris / cur
        m.use_collapse_triangulate = True
        apply_modifiers(ob)
    v, f = arrays_from_mesh(ob.data)
    me = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return v, f


# ----------------------------------------------------------- cache

def cache_key(*parts):
    hsh = hashlib.sha1()
    for p in parts:
        hsh.update(repr(p).encode())
    return hsh.hexdigest()[:16]


def sdf_part(name, f, lo, hi, h, tris, key_extra=(), **kw):
    """Polygonize + decimate with an on-disk cache. Returns (verts, faces)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = cache_key(name, lo, hi, h, tris, key_extra)
    path = os.path.join(CACHE_DIR, f"{name}_{key}.npz")
    if os.path.exists(path):
        d = np.load(path)
        return d["v"], d["f"]
    log(f"meshing {name} (h={h*1000:.1f}mm, target {tris} tris)")
    v, f_ = polygonize(f, lo, hi, h, **kw)
    v, f_ = decimate_arrays(v, f_, tris, name)
    np.savez_compressed(path, v=v, f=f_)
    return v, f_


# ----------------------------------------------------------- shading

def finish_shading(ob, sharp_angle=48.0, weighted=True):
    me = ob.data
    me.shade_smooth()
    if sharp_angle is not None:
        me.set_sharp_from_angle(angle=math.radians(sharp_angle))
    if weighted:
        m = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
        m.mode = "FACE_AREA"
        m.weight = 50
        m.keep_sharp = True
        m.thresh = 0.01
        apply_modifiers(ob)


def tri_count(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


def merge_close(me, dist=1e-5):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(me)
    bm.free()
