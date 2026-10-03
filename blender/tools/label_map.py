"""Annotate the orthographic overview render with districts, landmarks and main roads.

    python tools/label_map.py build/previews/overview.png build/roblox/manifest.json out.jpg
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from PIL import Image

from townbuilder.world import layout as L

ORTHO = 2600.0          # render.VIEWS["overview"] ortho scale, centred on (0, 0)

DISTRICT_TITLES = {
    "DOWNTOWN": "DOWNTOWN", "CIVIC": "CIVIC\nCENTER", "MIXED_USE": "OLD TOWN",
    "COMMERCIAL": "ROUTE 13 STRIP", "WATERFRONT": "WATERFRONT", "INDUSTRIAL": "INDUSTRIAL\n& RAIL YARD",
    "LOW_INCOME": "THE FLATS", "MOTEL": "MOTEL ROW", "RESIDENTIAL": "WESTSIDE",
    "RESIDENTIAL_N": "NORTH HILL",
}
DISTRICT_NUDGE = {"CIVIC": (110, -40), "WATERFRONT": (-60, -150), "INDUSTRIAL": (40, 120),
                  "COMMERCIAL": (-160, -60), "RESIDENTIAL_N": (0, 80), "MOTEL": (0, -110)}
ROADS = ["Route 13", "Bayshore Drive", "Founders Avenue", "Mill Street", "Palisade Road",
         "Ridge Road", "Harbor Boulevard", "Commerce Way", "Lookout Road", "Market Street"]
SHORT = {"Port Solace Fire Station No. 1": "Fire Station No. 1",
         "Port Solace Police Department": "Police Dept.", "Port Solace Town Hall": "Town Hall",
         "Port Solace Water Tower": "Water Tower"}
SKIP_LANDMARKS = {"Blue Marlin Sign", "Town Hall Clock Tower", "Hose Tower", "Cannery Smokestack"}


def main(img_path, manifest_path, out):
    im = Image.open(img_path).convert("RGB")
    W, H = im.size
    m = json.load(open(manifest_path))

    def px(x, y):
        return (x + ORTHO / 2) / ORTHO * W, (ORTHO / 2 - y) / ORTHO * H

    fig = plt.figure(figsize=(16, 16), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(im)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    halo = [pe.withStroke(linewidth=4, foreground="white")]
    dark = [pe.withStroke(linewidth=3, foreground="black")]
    placed = []                                  # label boxes in pixels (x0, y0, x1, y1)

    def box(x, y, text, size, ha="left", va="center"):
        lines_ = text.split("\n")
        k = W / 1600.0                           # font points -> image pixels
        w = max(len(t) for t in lines_) * size * 0.62 * 100 / 72 * k
        h = len(lines_) * size * 1.25 * 100 / 72 * k
        x0 = x - (w / 2 if ha == "center" else (w if ha == "right" else 0))
        y0 = y - (h / 2 if va == "center" else 0)
        return (x0, y0, x0 + w, y0 + h)

    def overlap(b):
        tot = 0.0
        for c in placed:
            ix = min(b[2], c[2]) - max(b[0], c[0])
            iy = min(b[3], c[3]) - max(b[1], c[1])
            if ix > 0 and iy > 0:
                tot += ix * iy
        if b[0] < 0 or b[2] > W or b[1] < 0 or b[3] > H:
            tot += 1e6
        return tot

    for k, poly in L.DISTRICTS.items():
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        dx, dy = DISTRICT_NUDGE.get(k, (0, 0))
        x, y = px(cx + dx, cy + dy)
        t = DISTRICT_TITLES.get(k, k)
        placed.append(box(x, y, t, 17, "center"))
        ax.text(x, y, t, fontsize=17, weight="bold", color="#3a2a18",
                ha="center", va="center", alpha=0.85, path_effects=halo)
    # landmarks: try right / left / above / below and keep the least crowded spot
    done = set()
    for lm in m["landmarks"]:
        n = lm["name"]
        if n in done or n in SKIP_LANDMARKS:
            continue
        done.add(n)
        x, y = px(lm["pos"][0], -lm["pos"][2])
        label = SHORT.get(n, n.title() if n.isupper() else n)
        best = None
        for (ox, oy, ha) in ((12, -10, "left"), (-12, -10, "right"), (0, -26, "center"),
                             (0, 22, "center"), (12, 14, "left"), (-12, 14, "right")):
            b = box(x + ox, y + oy, label, 11, ha)
            sc = overlap(b)
            if best is None or sc < best[0]:
                best = (sc, ox, oy, ha, b)
        _, ox, oy, ha, b = best
        placed.append(b)
        placed.append((x - 6, y - 6, x + 6, y + 6))
        ax.plot([x], [y], marker="o", ms=9, mfc="#d8402a", mec="white", mew=2)
        ax.text(x + ox, y + oy, label, fontsize=11, color="#1a1a1a", weight="bold",
                ha=ha, va="center", path_effects=halo)
    # roads: along the road where the label collides least
    for r in m["roads"]:
        if r["name"] not in ROADS:
            continue
        pts = [(p[0], -p[2]) for p in r["points"]]
        best = None
        for f in (0.5, 0.35, 0.65, 0.25, 0.75, 0.45, 0.55, 0.3, 0.7):
            i = int(len(pts) * f)
            a, b2 = pts[max(0, i - 2)], pts[min(len(pts) - 1, i + 2)]
            ang = math.degrees(math.atan2(b2[1] - a[1], b2[0] - a[0]))
            x, y = px(*pts[i])
            bx = box(x, y, r["name"], 11, "center")
            if abs(ang) > 45 and abs(ang) < 135:          # mostly vertical road
                cx_, cy_ = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
                hw, hh = (bx[3] - bx[1]) / 2, (bx[2] - bx[0]) / 2
                bx = (cx_ - hw, cy_ - hh, cx_ + hw, cy_ + hh)
            sc = overlap(bx)
            if best is None or sc < best[0]:
                best = (sc, x, y, ang, bx)
        _, x, y, ang, bx = best
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        placed.append(bx)
        ax.text(x, y, r["name"], fontsize=11, color="white", rotation=ang, ha="center",
                va="center", weight="bold", path_effects=dark, rotation_mode="anchor")
    # compass + scale bar
    ax.annotate("N", xy=(W - 90, 90), xytext=(W - 90, 190), fontsize=22, weight="bold",
                ha="center", arrowprops=dict(arrowstyle="-|>", lw=3, color="black"),
                path_effects=halo)
    s0 = px(-1200, -1230)
    s1 = px(-700, -1230)
    ax.plot([s0[0], s1[0]], [s0[1], s1[1]], color="black", lw=5)
    ax.text((s0[0] + s1[0]) / 2, s0[1] - 18, "500 studs", ha="center", fontsize=13,
            weight="bold", path_effects=halo)
    fig.savefig(out, dpi=100, pil_kwargs={"quality": 88})
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
