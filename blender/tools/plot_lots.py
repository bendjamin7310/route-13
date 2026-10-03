"""Build terrain, roads and lot placement (no Blender) and plot the result."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from townbuilder import kit, archetypes
from townbuilder.world import layout as L
from townbuilder.world.terrain import Terrain
from townbuilder.world.roads import RoadNetwork
from townbuilder.world.placement import Placer


def main(out):
    kit.load_all()
    archetypes.load_all()
    t = time.time()
    T = Terrain()
    print("terrain", round(time.time() - t, 1))
    t = time.time()
    net = RoadNetwork(T)
    print("roads", round(time.time() - t, 1), "junctions", len(net.junctions))
    for r in net.roads:
        nb = sum(r.bridge)
        if nb:
            i = r.bridge.index(True)
            print(f"  bridge on {r.name} at {r.P[i]} ({nb} samples)")
    t = time.time()
    P = Placer(net, T)
    P.place_sites()
    P.fill()
    P.finish()
    print("placement", round(time.time() - t, 1), "lots", len(P.lots), P.reject)
    from collections import Counter
    print(Counter(l.arch for l in P.lots).most_common())
    fig, ax = plt.subplots(figsize=(16, 16))
    ax.set_facecolor("#cfd8b8")
    ax.add_patch(Polygon(L.SEA, closed=True, fc="#6aa0b8"))
    ax.plot([p[0] for p in T.creek_pts], [p[1] for p in T.creek_pts], color="#4a86a8", lw=4)
    for r in net.roads:
        ax.plot([p[0] for p in r.P], [p[1] for p in r.P], color="#555",
                lw=max(0.5, r.w / 10), solid_capstyle="butt")
        for i in range(len(r.P)):
            if r.bridge[i]:
                ax.plot(r.P[i][0], r.P[i][1], "c.", ms=2)
    for j in net.junctions:
        ax.plot(j.x, j.y, "k.", ms=3)
    cmap = {}
    import random
    rng = random.Random(1)
    for lot in P.lots:
        if lot.arch not in cmap:
            cmap[lot.arch] = (rng.random() * 0.7 + 0.3, rng.random() * 0.7, rng.random() * 0.7)
        ax.add_patch(Polygon(lot.footprint, closed=True, fc=cmap[lot.arch], ec="k", lw=0.3))
        if getattr(lot, "site", False):
            cx, cy = lot.center
            ax.text(cx, cy, lot.arch, fontsize=6)
    ax.set_xlim(-1280, 1280)
    ax.set_ylim(-1280, 1280)
    ax.set_aspect("equal")
    fig.savefig(out, dpi=80, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1])
