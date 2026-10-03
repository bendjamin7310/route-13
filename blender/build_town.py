"""Generate the Port Solace town in Blender and (optionally) export it for Roblox.

Run with Blender (4.2+):

    blender --background --python build_town.py -- --out ../build

or with the ``bpy`` module from PyPI (same Blender version):

    python build_town.py --out ../build

Options:
    --out DIR            output folder (default: ../build)
    --seed N             world seed (default 7)
    --density F          building fill density multiplier (default 1.0)
    --vegetation F       vegetation density multiplier (default 1.0)
    --no-blend           do not save PortSolace.blend
    --fbx                export chunked FBX files for the Roblox 3D Importer
    --roblox             export Roblox data (Luau modules, rbxmx bundles, manifest)
    --render NAMES       comma list of preview renders (overview,downtown,harbor,motel,
                         industrial,street,interior) or "all"
    --samples N          Cycles samples for previews (default 32)
    --lights MODE        all | night | none   (Blender light objects to create)
    --no-interiors       skip interior geometry/props in the Blender scene (exports keep them)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def parse():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "build"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--density", type=float, default=1.0)
    ap.add_argument("--vegetation", type=float, default=1.0)
    ap.add_argument("--no-blend", action="store_true")
    ap.add_argument("--fbx", action="store_true")
    ap.add_argument("--roblox", action="store_true")
    ap.add_argument("--render", default="")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--lights", default="all")
    ap.add_argument("--no-interiors", action="store_true")
    ap.add_argument("--max-buildings", type=int, default=0)
    return ap.parse_args(argv)


def main():
    a = parse()
    import bpy
    from townbuilder.world.build import build_world
    from townbuilder.bl import materials
    from townbuilder.bl.realize import realize
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    def log(msg):
        print(f"[build {time.time() - t0:7.1f}s] {msg}", flush=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials.reset()
    W = build_world(seed=a.seed, density=a.density, veg_density=a.vegetation,
                    max_buildings=a.max_buildings or None)
    log(f"world: {W.stats}")
    sb = realize(W, lights_mode=a.lights, log=log, include_interiors=not a.no_interiors)
    bpy.context.scene.unit_settings.system = "NONE"
    bpy.context.scene["town_name"] = "Port Solace"
    bpy.context.scene["studs_per_unit"] = 1.0
    if a.roblox:
        from townbuilder.rbx.export import export_roblox
        export_roblox(W, os.path.join(out, "roblox"), log=log)
    if a.fbx:
        from townbuilder.bl.export_fbx import export_fbx
        export_fbx(os.path.join(out, "fbx"), log=log)
    if not a.no_blend:
        path = os.path.join(out, "PortSolace.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
        log(f"saved {path}")
    if a.render:
        from townbuilder.bl.render import render_views
        names = a.render.split(",")
        render_views(W, names, os.path.join(out, "previews"), samples=a.samples, log=log)
    log("done")


if __name__ == "__main__":
    main()
