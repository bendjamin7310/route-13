"""Assemble the whole town: terrain -> roads -> rail -> lots -> buildings -> dressing."""

from __future__ import annotations

import math
import random
import time

import numpy as np

from .. import kit, archetypes
from ..archetypes import ARCH
from ..archi.build import build_plan
from . import layout as Lay
from .model import World, BuildingRec
from .terrain import Terrain, _poly_mask
from .roads import RoadNetwork, RoadGeometry, Sweep
from .rail import RailLine
from .placement import Placer, district_at
from .dressing import Dresser

LANDMARK_COLLECTION = {
    "police_station": "POLICE", "fire_station": "FIRE", "town_hall": "CIVIC",
    "lighthouse": "LANDMARKS", "water_tower": "LANDMARKS", "parking_structure": "LANDMARKS",
    "mansion": "LANDMARKS", "office_tower": "LANDMARKS", "motel": "MOTEL",
    "supermarket": "LANDMARKS", "factory": "LANDMARKS", "marina_office": "WATERFRONT",
}
HIGH_DETAIL = {"DOWNTOWN", "CIVIC", "MIXED_USE", "WATERFRONT", "MOTEL"}


def log(msg, t0=[time.time()]):
    print(f"[town {time.time() - t0[0]:6.1f}s] {msg}", flush=True)


def detail_for(lot, sites_high=True):
    if getattr(lot, "site", False):
        return 3
    if lot.district in HIGH_DETAIL:
        return 3
    if lot.district == "OUTSKIRTS":
        return 1
    return 2


def build_world(seed=7, density=1.0, veg_density=1.0, max_buildings=None, log_fn=log):
    rng = random.Random(seed)
    kit.load_all()
    archetypes.load_all()
    archetypes.reset_names()          # business names are unique per generated town
    W = World()
    log_fn("terrain macro")
    T = Terrain(seed)
    W.terrain = T
    net = RoadNetwork(T)
    W.net = net
    log_fn(f"roads: {len(net.roads)} roads, {len(net.junctions)} junctions")
    for msg in net.issues:
        log_fn(f"road layout issue: {msg}")
        W.issues.append(msg)
    rail = RailLine(Lay.RAIL, T, net)
    W.rail = rail
    placer = Placer(net, T, seed=seed + 6, density=density)
    placer.place_sites()
    placer.fill()
    placer.finish()
    if max_buildings:
        placer.lots = placer.lots[:max_buildings]
    log_fn(f"placement: {len(placer.lots)} lots")
    W.placer = placer

    # ---- terrain stamps: roads, lots, rail -----------------------------------------------
    for r in net.roads:
        core = r.half + r.sw + 1.0
        paint = "gravel" if r.kind in ("rural", "dirt") else None
        for i in range(len(r.P) - 1):
            if r.bridge[i] or r.bridge[i + 1]:
                continue
            (ax, ay), (bx, by) = r.P[i], r.P[i + 1]
            T.stamp_segment(ax, ay, r.Z[i] - 0.25, bx, by, r.Z[i + 1] - 0.25, core, 20.0,
                            paint=paint)
    for lot in placer.lots:
        T.stamp_rect(lot.yard_rect, lot.z - 0.6, 4.0, 18.0)
    rail.stamp()
    # district codes for terrain texture/noise: 1 urban, 2 residential, 3 industrial,
    # 4 outskirts fields, 5 downtown (paved)
    X, Y = T.X, T.Y
    dg = np.full(X.shape, 4, dtype=np.int8)
    for name, poly in Lay.DISTRICTS.items():
        code = {"RESIDENTIAL": 2, "RESIDENTIAL_N": 2, "INDUSTRIAL": 3, "DOWNTOWN": 5}.get(name, 1)
        m = _poly_mask(X, Y, poly)
        dg = np.where(m & (dg == 4), code, dg)
    for name, poly in Lay.PARKS.items():
        m = _poly_mask(X, Y, poly)
        T.paint = np.where(m, 1 if name != "Solace Beach" else 4, T.paint)
    T.finalize(dg)
    net.clear_under_bridges(T)
    log_fn("terrain finalized")

    # ---- roads + rail geometry ----------------------------------------------------------
    rg = RoadGeometry(net, district_at, rng)
    rg.build()
    W.sweeps.extend(rg.sweeps)
    W.patches.extend(rg.patches)
    W.boxes.extend(rg.boxes)
    W.props.extend((p, "PROPS") for p in rg.props)
    W.lights.extend(rg.lights)
    W.markers.extend(rg.markers)
    rail.geometry(W)
    rail.park_train(W, rng)
    log_fn(f"road geometry: {len(W.sweeps)} sweeps, {len(W.patches)} patches")

    # ---- water surfaces ----------------------------------------------------------------
    _water(W, T)

    # ---- buildings ----------------------------------------------------------------------
    nprim = 0
    for k, lot in enumerate(placer.lots):
        a = ARCH[lot.arch]
        det = detail_for(lot)
        plan = archetypes.make(lot.arch, lot.w, lot.d, seed * 1000 + k,
                               district=lot.district, quality=lot.quality, detail=det,
                               blind=set(lot.blind), name=lot.name, opts=dict(lot.opts))
        plan.detail = det
        built = build_plan(plan, seed * 1000 + k)
        coll = LANDMARK_COLLECTION.get(lot.arch) if getattr(lot, "site", False) else None
        coll = coll or Lay.DISTRICT_COLLECTION.get(lot.district, a.collection)
        rec = BuildingRec(lot, plan, built, lot.xform(), ("TOWN", coll),
                          ("TOWN", "INTERIORS", a.interior), getattr(lot, "site", False))
        W.buildings.append(rec)
        nprim += len(built.ext.prims) + len(built.int.prims)
        for wmsg in built.warnings:
            W.issues.append(f"{lot.id} {lot.arch}: {wmsg}")
        if (k + 1) % 50 == 0:
            log_fn(f"buildings {k + 1}/{len(placer.lots)}")
    log_fn(f"buildings: {len(W.buildings)} ({nprim} primitives)")

    # ---- dressing -------------------------------------------------------------------------
    D = Dresser(W, placer, rng)
    D.yards()
    D.parks()
    D.pier()
    D.docks()
    D.seawall()
    D.power_line()
    D.outskirts()
    nhide = D.hideouts()
    nveg = D.vegetation(veg_density)
    log_fn(f"dressing done ({nveg} vegetation instances)")
    W.stats = {
        "buildings": len(W.buildings),
        "building_props": sum(len(b.built.props) for b in W.buildings),
        "world_props": len(W.props),
        "lights": len(W.lights) + sum(len(b.built.lights) for b in W.buildings),
        "markers": len(W.markers) + sum(len(b.built.markers) for b in W.buildings),
        "rooms": sum(len(b.plan.rooms) for b in W.buildings),
        "roads": len(net.roads), "junctions": len(net.junctions),
        "road_length": round(sum(r.length for r in net.roads)),
        "vegetation": nveg, "hideouts": nhide,
    }
    return W


def _water(W, T):
    """Sea plane tiles and the creek surface ribbon."""
    tile = 256.0
    n = int(2 * Lay.HALF / tile)
    for i in range(n):
        for j in range(n):
            x0 = -Lay.HALF + j * tile
            y0 = -Lay.HALF + i * tile
            ci = slice(int(i * tile / 4), int((i + 1) * tile / 4) + 1)
            cj = slice(int(j * tile / 4), int((j + 1) * tile / 4) + 1)
            if not T.sea[ci, cj].any():
                continue
            verts = [(x0, y0, 0.0), (x0 + tile, y0, 0.0), (x0 + tile, y0 + tile, 0.0),
                     (x0, y0 + tile, 0.0)]
            W.water.append((f"Sea_{i}_{j}", "water", verts, [(0, 1, 2, 3)]))
    pts = T.creek_pts
    lv = T.creek_level
    hw = T.creek_hw
    run = 40
    for k0 in range(0, len(pts) - 1, run):
        idx = list(range(k0, min(len(pts), k0 + run + 1)))
        verts, faces = [], []
        for m, i in enumerate(idx):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            w = hw[i] + 6.0
            z = lv[i] + 0.2
            verts.append((pts[i][0] - nx * w, pts[i][1] - ny * w, z))
            verts.append((pts[i][0] + nx * w, pts[i][1] + ny * w, z))
            if m > 0:
                a0 = 2 * (m - 1)
                faces.append((a0, a0 + 2, a0 + 3, a0 + 1))
        W.water.append((f"Creek_{k0 // run}", "water_river", verts, faces))
