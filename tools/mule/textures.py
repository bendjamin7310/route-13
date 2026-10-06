"""Wear textures: UV-unwrap shared atlases and compute subtle dust/grime
directly per texel (numpy rasteriser, no GPU bake needed).

Atlases (1024 px, Roblox's upload limit):
  paint      body-coloured panels: dust low down and sprayed round the
             wheel arches, a little grime in panel gaps, faint roughness
             variation (ColorMap + RoughnessMap)
  bedliner   bed floor/walls: dust in the floor, scuffs (Color + Roughness)
  tire       shared by all four tyres: dusty shoulders, worn tread tops
"""

import math
import os

import bpy
import numpy as np

import body
import materials
from dims import *  # noqa: F401,F403

RES = 1024

PAINT_PARTS = ("Body_Cab", "Hood", "Door_FL", "Door_FR", "Door_RL", "Door_RR", "Body_Bed", "Tailgate",
               "FuelDoor", "Bumper_Front")
BEDLINER_PARTS = ("Body_Bed_Bedliner", "Tailgate_Bedliner")
DUST = np.array([0.56, 0.48, 0.38])      # sRGB desert dust
GRIME = np.array([0.30, 0.28, 0.25])


# ------------------------------------------------------------------ noise

def _hash3(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float64) / 65535.0


def value_noise(p, freq, seed=0):
    q = p * freq
    i = np.floor(q).astype(np.int64)
    f = q - i
    u = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                out = out + w * _hash3(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return out


def fbm(p, freq, octaves=4, seed=0):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * value_noise(p, freq * (2 ** o), seed + o * 17)
        norm += amp
        amp *= 0.5
    return total / norm


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ uv + raster

def unwrap(objs, margin=0.004):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


def _tri_data(ob):
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    loops = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("loops", loops)
    vidx = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", vidx)
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)[loops].reshape(nt, 3, 2)
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    pos = co[vidx].reshape(nt, 3, 3)
    n = np.cross(pos[:, 1] - pos[:, 0], pos[:, 2] - pos[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return uv, pos, n


def rasterize(objs, res=RES):
    """Per-texel world position, normal and object index for the atlas."""
    P = np.zeros((res, res, 3), np.float32)
    N = np.zeros((res, res, 3), np.float32)
    ID = np.full((res, res), -1, np.int16)
    for k, ob in enumerate(objs):
        uv, pos, nrm = _tri_data(ob)
        px = uv * res - 0.5
        for t in range(len(px)):
            a, b, c = px[t]
            x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0)
            x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), res - 1)
            y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0)
            y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), res - 1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            v0, v1 = b - a, c - a
            d = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(d) < 1e-12:
                continue
            wx, wy = gx - a[0], gy - a[1]
            l1 = (wx * v1[1] - v1[0] * wy) / d
            l2 = (v0[0] * wy - wx * v0[1]) / d
            l0 = 1 - l1 - l2
            m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
            if not m.any():
                continue
            p = l0[m, None] * pos[t, 0] + l1[m, None] * pos[t, 1] + l2[m, None] * pos[t, 2]
            P[gy[m], gx[m]] = p
            N[gy[m], gx[m]] = nrm[t]
            ID[gy[m], gx[m]] = k
    return P, N, ID


def dilate(img, mask, iters=8):
    img = img.copy()
    m = mask.copy()
    for _ in range(iters):
        acc = np.zeros_like(img)
        cnt = np.zeros(m.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            sm = np.roll(np.roll(m, dy, 0), dx, 1)
            si = np.roll(np.roll(img, dy, 0), dx, 1)
            acc += si * sm[..., None]
            cnt += sm
        fill = (~m) & (cnt > 0)
        img[fill] = acc[fill] / cnt[fill, None]
        m = m | fill
    img[~m] = img[m].mean(axis=0)
    return img


def save_png(path, arr):
    arr = np.clip(arr, 0, 1)
    h, w = arr.shape[:2]
    ch = 1 if arr.ndim == 2 else arr.shape[2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True, float_buffer=False)
    rgba = np.ones((h, w, 4), np.float32)
    if ch == 1:
        rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = arr
    else:
        rgba[..., :3] = arr[..., :3]
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


# ------------------------------------------------------------------ wear functions

def paint_wear(P, N):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n1 = fbm(P, 3.0, 4, 1)
    n2 = fbm(P * np.array([1.0, 1.0, 0.25]), 9.0, 3, 7)   # vertical streaks
    n3 = fbm(P, 22.0, 2, 11)
    low = sstep(0.95, 0.50, z)
    rho_f = body.arch_rho(y.astype(np.float32), z.astype(np.float32), Y_FRONT_AXLE)
    rho_r = body.arch_rho(y.astype(np.float32), z.astype(np.float32), Y_REAR_AXLE)
    spray = np.exp(-np.maximum(rho_f - 1, 0) * 3.2) * (0.6 + 0.4 * (y < Y_FRONT_AXLE)) + \
        np.exp(-np.maximum(rho_r - 1, 0) * 3.2) * (0.6 + 0.4 * (y < Y_REAR_AXLE))
    side = np.clip(np.abs(N[:, 0]) + 0.3, 0, 1)
    dirt = (0.75 * low * (0.50 + 0.50 * n2) + 0.65 * spray * (0.40 + 0.60 * n1)) * side
    rear = sstep(-2.55, -2.80, y) * sstep(1.15, 0.70, z) * 0.45      # dust behind the tailgate
    top = sstep(0.6, 0.95, N[:, 2]) * 0.16 * n1                        # a film of dust on flat tops
    dirt = np.clip(dirt + rear + top, 0, 1) * (0.55 + 0.45 * n3)
    # grime in panel gaps
    gap = np.full(len(P), 1.0, np.float32)
    for name in ("Door_FL", "Door_FR", "Door_RL", "Door_RR", "Hood", "Tailgate"):
        reg = body.PANELS[name][1]
        gap = np.minimum(gap, np.abs(reg(x.astype(np.float32), y.astype(np.float32), z.astype(np.float32))))
    grime = sstep(0.012, 0.0, gap) * 0.35 * (0.5 + 0.5 * n1)
    return dirt, grime, n3


def bake_paint(objs, out_dir):
    import time
    from mesher import log
    t = time.time()
    unwrap(objs)
    log(f"  unwrap {time.time()-t:.0f}s")
    t = time.time()
    P, N, ID = rasterize(objs)
    log(f"  raster {time.time()-t:.0f}s")
    mask = ID >= 0
    pts, nrm = P[mask].astype(np.float64), N[mask].astype(np.float64)
    dirt, grime, n3 = paint_wear(pts, nrm)
    base = np.array(materials.hex_rgb(materials.PALETTE["Paint"][0])) / 255.0
    col = base[None, :] * (0.985 + 0.03 * (n3[:, None] - 0.5))
    col = col * (1 - dirt[:, None] * 0.72) + DUST[None, :] * dirt[:, None] * 0.72
    col = col * (1 - grime[:, None]) + GRIME[None, :] * grime[:, None]
    rough = 0.30 + 0.05 * (n3 - 0.5) + dirt * 0.45 + grime * 0.3
    C = np.zeros((RES, RES, 3), np.float32)
    R = np.zeros((RES, RES, 1), np.float32)
    C[mask] = col
    R[mask, 0] = rough
    C = dilate(C, mask)
    R = dilate(R, mask)
    cpath = os.path.join(out_dir, "mule_paint_color.png")
    rpath = os.path.join(out_dir, "mule_paint_roughness.png")
    return save_png(cpath, C), save_png(rpath, R[..., 0])


def bake_bedliner(objs, out_dir):
    unwrap(objs, margin=0.006)
    P, N, ID = rasterize(objs)
    mask = ID >= 0
    pts, nrm = P[mask].astype(np.float64), N[mask].astype(np.float64)
    n1 = fbm(pts, 4.0, 4, 3)
    n2 = fbm(pts, 30.0, 3, 5)
    floor = sstep(0.5, 0.9, nrm[:, 2])
    corner = sstep(0.95, 0.83, pts[:, 2])
    dust = np.clip(0.55 * floor * n1 + 0.35 * corner * n1, 0, 1)
    scuff = sstep(0.62, 0.78, n2) * floor * 0.35
    base = np.array(materials.hex_rgb(materials.PALETTE["Bedliner"][0])) / 255.0
    col = base[None, :] * (0.92 + 0.16 * n2[:, None])
    col = col * (1 - dust[:, None] * 0.5) + DUST[None, :] * dust[:, None] * 0.5
    col = col + scuff[:, None] * 0.06
    rough = 0.82 + 0.1 * dust - 0.25 * scuff
    C = np.zeros((RES, RES, 3), np.float32)
    R = np.zeros((RES, RES, 1), np.float32)
    C[mask] = col
    R[mask, 0] = rough
    C = dilate(C, mask)
    R = dilate(R, mask)
    return (save_png(os.path.join(out_dir, "mule_bedliner_color.png"), C),
            save_png(os.path.join(out_dir, "mule_bedliner_roughness.png"), R[..., 0]))


def bake_tire(ob, out_dir):
    """The tyre UVs are cylindrical: u = angle, v = profile (see wheels.tyre)."""
    res = 512
    u = (np.arange(res) + 0.5) / res
    U, V = np.meshgrid(u, u)
    p = np.stack([np.cos(U * 2 * np.pi) * 3, np.sin(U * 2 * np.pi) * 3, V * 4], -1).reshape(-1, 3)
    n1 = fbm(p, 1.5, 4, 21).reshape(res, res)
    n2 = fbm(p, 8.0, 3, 23).reshape(res, res)
    base = np.array(materials.hex_rgb(materials.PALETTE["Rubber"][0])) / 255.0
    # v: 0..0.42 outer sidewall (bead->shoulder), 0.42..0.6 groove, 0.62..0.74 blocks, 0..0.30 inner
    shoulder = sstep(0.18, 0.40, V) * (V < 0.6)
    groove = ((V > 0.42) & (V < 0.6)).astype(np.float32)
    dust = np.clip(0.55 * shoulder * (0.5 + 0.5 * n1) + 0.65 * groove * n1, 0, 1)
    worn = ((V > 0.61) & (V < 0.70)).astype(np.float32) * (0.4 + 0.3 * n2)
    col = base[None, None, :] * (0.95 + 0.1 * n2[..., None])
    col = col * (1 - dust[..., None] * 0.45) + DUST[None, None, :] * 0.55 * dust[..., None] * 0.45
    col = col + worn[..., None] * 0.035
    rough = 0.86 + 0.08 * dust - 0.12 * worn
    return (save_png(os.path.join(out_dir, "mule_tire_color.png"), col),
            save_png(os.path.join(out_dir, "mule_tire_roughness.png"), rough))


# ------------------------------------------------------------------ material hookup

def textured_material(name, key, color_img, rough_img):
    hexc, _r, metal, *_ = materials.PALETTE[key]
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = color_img
    tr = nt.nodes.new("ShaderNodeTexImage")
    tr.image = rough_img
    rough_img.colorspace_settings.name = "Non-Color"
    nt.links.new(tc.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(tr.outputs["Color"], p.inputs["Roughness"])
    p.inputs["Metallic"].default_value = metal
    if key == "Paint":
        p.inputs["Coat Weight"].default_value = 0.2
        p.inputs["Coat Roughness"].default_value = 0.2
    m["roblox_material"] = materials.PALETTE[key][3]
    m["mule_texture_color"] = os.path.basename(color_img.filepath_raw)
    m["mule_texture_roughness"] = os.path.basename(rough_img.filepath_raw)
    return m


def _assign(objs, mat):
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


def bake_all(objs, out_dir):
    import time
    from mesher import log
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)
    by_name = {o.name: o for o in objs if o.type == "MESH"}
    paint = [by_name[n] for n in PAINT_PARTS if n in by_name]
    if paint:
        c, r = bake_paint(paint, out_dir)
        _assign(paint, textured_material("PaintWorn", "Paint", c, r))
        log(f"paint atlas done ({time.time()-t0:.0f}s)")
    bed = [by_name[n] for n in BEDLINER_PARTS if n in by_name]
    if bed:
        c, r = bake_bedliner(bed, out_dir)
        _assign(bed, textured_material("BedlinerWorn", "Bedliner", c, r))
    tires = [o for n, o in by_name.items() if n.endswith("_Tire")]
    if tires:
        c, r = bake_tire(tires[0], out_dir)
        _assign(tires, textured_material("TireWorn", "Rubber", c, r))
    log(f"textures done ({time.time()-t0:.0f}s)")
