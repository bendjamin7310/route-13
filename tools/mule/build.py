"""Build the Mule pickup and export it for Roblox.

Run with Blender's Python module (pip install bpy scikit-image scipy numba):

    python tools/mule/build.py --out assets/vehicles/mule --render --export

Meshes are cached in tools/mule/.cache (keyed on the source of the modules
that define them), so re-runs only rebuild what changed.
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import materials  # noqa: E402
import mesher  # noqa: E402
import spec  # noqa: E402
from mesher import log  # noqa: E402

GROUPS = ["Body", "Doors", "Lights", "Glass", "Wheels", "Interior", "Seats", "Underbody", "Plates"]


def collect_parts(selected=None):
    import body
    import exterior
    mods = [body, exterior]
    for name in ("glass", "wheels", "interior", "underbody", "plates"):
        try:
            mods.append(__import__(name))
        except ModuleNotFoundError:
            pass
    parts = []
    for m in mods:
        parts += m.parts()
    if selected:
        parts = [p for p in parts if any(p.name.startswith(s) for s in selected)]
    return parts


# ----------------------------------------------------------------- objects

def _face_frames(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return (a + b + c) / 3.0, n / np.maximum(ln, 1e-12)


def _submesh(v, f, mask):
    ff = f[mask]
    used, inv = np.unique(ff.ravel(), return_inverse=True)
    return v[used], inv.reshape(-1, 3).astype(np.int32)


def _make_object(name, v, f, mat_key, group_obj, origin, sharp, uv=None, smooth=True):
    v = np.asarray(v, dtype=np.float64)
    if origin is None:
        origin = (v.min(axis=0) + v.max(axis=0)) / 2.0
    origin = np.asarray(origin, dtype=np.float64)
    me = mesher.mesh_from_arrays(name, (v - origin).astype(np.float32), f)
    if uv is not None:
        lay = me.uv_layers.new(name="UVMap")
        lay.data.foreach_set("uv", np.asarray(uv, dtype=np.float32).ravel())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = origin
    me.materials.append(materials.get(mat_key))
    ob["mule_material"] = mat_key
    if smooth:
        mesher.finish_shading(ob, sharp_angle=sharp)
    if group_obj is not None:
        ob.parent = group_obj
    return ob


def build_part(p, groups):
    t = time.time()
    if isinstance(p, spec.MeshPart):
        v, f = np.asarray(p.verts, dtype=np.float32), p.faces
    else:
        v, f = mesher.sdf_part(p.name, p.sdf, p.lo, p.hi, p.h, p.tris,
                               key_extra=(spec.source_hash(*p.deps),))
    variants = [(p.name, v, f, p.origin, 1.0)]
    if p.mirror:
        o = None if p.origin is None else (-p.origin[0], p.origin[1], p.origin[2])
        variants.append((spec.mirror_name(p.name), v, f, o, -1.0))
    objs = []
    for name, vv, ff, origin, sx in variants:
        vv = np.asarray(vv, dtype=np.float32).copy()
        if isinstance(ff, np.ndarray):
            ff = ff.copy()
        if sx < 0:
            vv[:, 0] *= -1
            if isinstance(ff, np.ndarray):
                ff = ff[:, ::-1].copy()
            else:
                ff = [list(reversed(poly)) for poly in ff]
        uv = getattr(p, "uv", None)
        if uv is not None and sx < 0:
            uv = None  # mirrored copies get regenerated UVs later
        if callable(p.mat):
            cent, nrm = _face_frames(vv, ff)
            labels = p.mat(cent, nrm)
            for lab in sorted(set(labels)):
                mask = labels == lab
                sv, sf = _submesh(vv, ff, mask)
                oname = p.names.get(lab, name if lab == "Paint" else f"{name}_{lab}")
                if sx < 0 and lab in p.names:
                    oname = spec.mirror_name(oname)
                objs.append(_make_object(oname, sv, sf, lab, groups[p.group], origin, p.sharp))
        else:
            objs.append(_make_object(name, vv, ff, p.mat, groups[p.group], origin, p.sharp,
                                     uv=uv, smooth=getattr(p, "smooth", True)))
    log(f"{p.name}: {sum(mesher.tri_count(o) for o in objs)} tris, {len(objs)} objects ({time.time()-t:.1f}s)")
    return objs


def make_groups():
    root = bpy.data.objects.new("Mule", None)
    bpy.context.scene.collection.objects.link(root)
    groups = {}
    for g in GROUPS:
        e = bpy.data.objects.new(g, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        groups[g] = e
    return root, groups


def report(objs):
    total = 0
    rows = []
    for o in objs:
        n = mesher.tri_count(o)
        total += n
        rows.append((n, o.name))
    rows.sort(reverse=True)
    log(f"TOTAL triangles: {total} in {len(objs)} meshes; largest:")
    for n, name in rows[:(len(rows) if os.environ.get("MULE_VERBOSE") else 12)]:
        log(f"   {n:6d}  {name}")
    over = [r for r in rows if r[0] > 20000]
    if over:
        log("WARNING: meshes over Roblox's 20k triangle limit:", over)
    return total, rows


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "assets", "vehicles", "mule"))
    ap.add_argument("--only", default="")
    ap.add_argument("--render", default="")
    ap.add_argument("--render-dir", default="")
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--textures", action="store_true")
    ap.add_argument("--r15", default="", help="views to re-render with R15 proxy characters seated")
    args = ap.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials.reset()
    root, groups = make_groups()
    selected = [s for s in args.only.split(",") if s]
    objs = []
    for p in collect_parts(selected):
        objs += build_part(p, groups)
    if not selected or any(s.startswith("Seat") for s in selected):
        try:
            import seats
            objs += seats.make_anchors(groups["Seats"])
        except ModuleNotFoundError:
            pass
    total, rows = report([o for o in objs if o.type == "MESH" and not o.name.startswith("SeatAnchor")
                          and o.name != "MuleRoot"])

    if args.textures:
        import textures
        textures.bake_all(objs, os.path.join(args.out, "textures"))

    if args.export:
        import export
        export.export_all(root, objs, args.out, rows)

    if args.render or args.r15:
        import preview
        w, h = (int(v) for v in args.res.split("x"))
        preview.setup_scene(res=(w, h), samples=args.samples)
        rdir = args.render_dir or os.path.join(args.out, "previews")
        ext = os.environ.get("MULE_PREVIEW_EXT", "png")
        for view in [v for v in args.render.split(",") if v]:
            preview.render_view(view, os.path.join(rdir, f"mule_{view}.{ext}"), hide=("SeatAnchor", "MuleRoot"))
        if args.r15:
            import seats
            preview.add_r15_proxies(seats.ANCHORS)
            for view in args.r15.split(","):
                preview.render_view(view, os.path.join(rdir, f"mule_{view}_r15.{ext}"), hide=("SeatAnchor", "MuleRoot"))


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    main(argv)
