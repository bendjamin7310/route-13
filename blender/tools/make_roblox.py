"""Generate the Roblox files without Blender (plain Python + numpy; cargo for rbxconv).

    python tools/make_roblox.py [--out ../build/roblox] [--seed 7]

Writes the data bundle (PortSolace.rbxmx, PortSolace/, manifest.json) and the ready-to-open
PortSolace.rbxl, PortSolace_Lite.rbxl and PortSolace_Town.rbxm.
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from townbuilder.world.build import build_world          # noqa: E402
from townbuilder.rbx.export import export_roblox        # noqa: E402
from townbuilder.rbx.place import build_all             # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "..", "build", "roblox"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--density", type=float, default=1.0)
    ap.add_argument("--vegetation", type=float, default=1.0)
    a = ap.parse_args()
    t0 = time.time()

    def log(msg):
        print(f"[roblox {time.time() - t0:6.1f}s] {msg}", flush=True)

    W = build_world(seed=a.seed, density=a.density, veg_density=a.vegetation)
    log(f"world: {W.stats}")
    out = os.path.abspath(a.out)
    export_roblox(W, out, log=log)
    build_all(out, log=log)
    log("done")


if __name__ == "__main__":
    main()
