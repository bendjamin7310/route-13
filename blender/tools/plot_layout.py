"""Plot the 2D map layout (coast, creek, rail, districts, roads, sites) to a PNG."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from townbuilder.world import layout as L
from townbuilder.geom import catmull_rom


def main(out):
    fig, ax = plt.subplots(figsize=(14, 14))
    ax.set_facecolor("#cfd8b8")
    ax.add_patch(Polygon(L.SEA, closed=True, fc="#6aa0b8", ec="#40708a"))
    cols = {"WATERFRONT": "#9fc4d6", "CIVIC": "#d9c27a", "DOWNTOWN": "#d98c6b",
            "MIXED_USE": "#e0b090", "INDUSTRIAL": "#a8a8a8", "LOW_INCOME": "#c9b49a",
            "COMMERCIAL": "#e8d27c", "MOTEL": "#e7a3c0", "RESIDENTIAL": "#b5d39b",
            "RESIDENTIAL_N": "#a3cc8f"}
    for n, poly in L.DISTRICTS.items():
        ax.add_patch(Polygon(poly, closed=True, fc=cols[n], ec="k", alpha=0.45, lw=0.5))
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        ax.text(cx, cy, n, fontsize=8, ha="center", alpha=0.7)
    for n, poly in L.PARKS.items():
        ax.add_patch(Polygon(poly, closed=True, fc="#6fae5a", ec="#3c7a2c", alpha=0.7))
    cr = catmull_rom([(x, y) for x, y, _ in L.CREEK], 8)
    ax.plot([p[0] for p in cr], [p[1] for p in cr], color="#4a86a8", lw=4)
    rl = catmull_rom(L.RAIL, 8)
    ax.plot([p[0] for p in rl], [p[1] for p in rl], color="#5a4a3a", lw=2, ls="--")
    for r in L.ROADS:
        pts = catmull_rom(r.pts, 8) if r.smooth else r.pts
        w = L.ROAD_SPECS[r.kind][0]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#333",
                lw=max(0.6, w / 14), solid_capstyle="round")
        mid = pts[len(pts) // 2]
        ax.text(mid[0], mid[1], r.name, fontsize=5, color="#222")
    for h in L.HILLS:
        ax.add_patch(plt.Circle((h[0], h[1]), h[2], fill=False, ls=":", ec="#6b5a3a"))
    for s in L.SITES:
        if "x" in s:
            ax.plot(s["x"], s["y"], "r*", ms=10)
            ax.text(s["x"], s["y"], s["arch"], fontsize=6, color="r")
    ax.set_xlim(-1280, 1280)
    ax.set_ylim(-1280, 1280)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    fig.savefig(out, dpi=90, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1])
