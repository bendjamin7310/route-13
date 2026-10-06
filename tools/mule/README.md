# Mule generator

Procedural source for the **Mule**, the Hilux-style double-cab pickup in
[`assets/vehicles/mule`](../../assets/vehicles/mule). Everything (meshes,
material split, wear textures, exports, the Roblox setup module) comes out
of `build.py`, so the truck can be tweaked by editing numbers and rebuilt.

## Requirements

Python 3.13 with Blender as a module:

```sh
python -m venv .venv
.venv/bin/pip install bpy scikit-image scipy numba
```

## Build

```sh
MULE_PREVIEW_EXT=jpg .venv/bin/python tools/mule/build.py --textures --export \
    --render front34,rear34,side,front,rear,top,low34,bed,cabin,driver,interior \
    --r15 cabin,front34 --out assets/vehicles/mule
```

| Flag | What it does |
|---|---|
| `--only Door_,Hood` | Build only parts whose names start with these prefixes (quick iteration). |
| `--textures` | UV-unwrap the atlases and compute the wear textures into `<out>/textures`. |
| `--export` | Write `.blend` (metres), `.fbx` and `.glb` (studs), `mule_manifest.json` and `roblox/MuleSetup.lua`. |
| `--render v1,v2` | Cycles preview renders (views are listed in `preview.py`). |
| `--r15 v1,v2` | Re-render views with blocky R15-sized stand-ins in all four seats, to check the fit. |
| `--res`, `--samples` | Render size and samples. `MULE_PREVIEW_EXT=jpg` writes JPEGs; `MULE_VERBOSE=1` lists every mesh's triangle count. |

Meshes are cached in `tools/mule/.cache/`, keyed on the source of the
modules that produce them, so a rebuild only re-meshes what changed. A cold
build takes about half an hour on 4 CPU cores (most of it decimating the
cab body); the preview renders add roughly a minute each.

## How it works

| Module | Role |
|---|---|
| `dims.py` | Every shared dimension: wheelbase, axle positions, belt line, seat positions. |
| `sdf.py` | Signed distance primitives and operators (rounded unions/intersections, 2D polygons). |
| `body.py` | Cab, greenhouse, cabin cavity, window openings, bed; hood/doors/tailgate/fuel door/cowl cut out as panels with 5 mm gaps. |
| `exterior.py` | Bumpers, grille, headlights (lens, housing, reflectors, DRL, indicator), fog lamps, tail lights, mirrors, handles, wipers, mud flaps. |
| `wheels.py` | Parametric tyre (revolved sidewalls, separate tread blocks), SDF six-spoke rim, disc + caliper (front), drums (rear), spare. |
| `glass.py` | Two-sided glass sheets that tuck under the window frames. |
| `interior.py` | Seats, dashboard, cluster, screen, vents, controls, glovebox, steering wheel and column, console, shifter, handbrake, pedals, mirror, visors. |
| `underbody.py`, `plates.py`, `seats.py` | Frame/axles/exhaust, licence plates, Roblox seat anchors and `MuleRoot`. |
| `mesher.py` | Narrow-band SDF sampling, marching cubes, quadric decimation to a triangle budget, smooth + weighted normals. |
| `classify.py` | Splits SDF meshes into single-material parts (paint, wheel wells, window seals, door trim...). |
| `textures.py` | Numpy rasteriser that computes dust, grime and roughness per texel. |
| `export.py`, `luau.py` | Exports and the generated `MuleSetup.lua`. |

Each SDF part is sampled on a 1.5-7 mm grid, polygonised, then decimated to
its budget, which keeps curvature where it matters and puts few triangles on
flat panels. Weighted normals keep the big panels smooth; edges sharper than
about 48° stay crisp.

## Testing the Roblox module

`luau_test/` runs the generated `MuleSetup.lua` in the Luau VM (via the
`luau-web` WASM build) against a mocked model built from the manifest:

```sh
npm install luau-web
node tools/mule/luau_test/run.mjs assets/vehicles/mule
```

It checks that seats, colliders and welds are created once (Setup is
idempotent), materials are applied, the front plate is hidden and the
light switching works. The mock only covers the APIs the module uses.
