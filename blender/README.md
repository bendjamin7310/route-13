# Port Solace: Blender town generator and Roblox pipeline

This folder generates **Port Solace**, a 2560 × 2560-stud coastal town for a stylized
criminal sandbox, as a Blender scene. It also exports the town to Roblox Studio. You can
walk into every building: room-based floor plans produce the walls, doors, windows, stairs,
floors and roofs, so each window opens onto a real furnished room. Floors are linked by
stairs, and roofs, basements, back rooms and garages are all reachable.

For the world design (districts, landmarks, routes, gameplay spaces), see
[`docs/TOWN_MAP.md`](../docs/TOWN_MAP.md). For every building, landmark and road with its
coordinates, see [`docs/TOWN_DIRECTORY.md`](../docs/TOWN_DIRECTORY.md).

## Quick start

You need **Blender 4.2+**. Alternatively, use the `bpy==4.2.0` wheel from PyPI with Python 3.11.

```bash
cd blender
# Blender
blender --background --python build_town.py -- --out ../build --roblox --fbx --render all
# or the bpy module
python build_town.py --out ../build --roblox --fbx --render all
```

| Option | Meaning |
|---|---|
| `--out DIR` | Output folder (default `../build`) |
| `--seed N` | World seed (default 7; all docs and images use 7) |
| `--density F`, `--vegetation F` | Building fill and vegetation multipliers |
| `--roblox` | Write the Roblox data modules, `manifest.json` and `PortSolace.rbxmx` |
| `--fbx` | Write chunked FBX files for the Roblox 3D Importer |
| `--render LIST` | Cycles previews: `overview,aerial,downtown,harbor,motel,industrial,civic,street,night` or `all` |
| `--samples N` | Cycles samples per preview (default 32) |
| `--lights all\|night\|none` | Which light objects to create in Blender |
| `--no-interiors` | Leave interior geometry out of the `.blend` (the exports keep it) |
| `--no-blend` | Do not save `PortSolace.blend` |
| `--max-buildings N` | Build only the first N lots (quick tests) |

A full build with `--roblox --fbx` takes about 12 minutes on 4 cores. Generating the
world takes 1 minute, creating the Blender objects about 8, the Roblox export a few
seconds and the FBX export about 3. Each preview render adds 1.5–3 minutes. The output
is deterministic for a given seed.

### Outputs

```
build/
├── PortSolace.blend            the whole town (~35 MB compressed)
├── previews/*.png              Cycles renders
├── roblox/
│   ├── PortSolace.rbxmx        drag into ServerStorage (data + TownBuilder + TownRuntime)
│   ├── manifest.json           roads, junctions, districts, landmarks, every building/room
│   └── PortSolace/             the same modules as files (for Rojo, see roblox/)
│       ├── Palette.lua  Kit.lua  TerrainData.lua  Manifest.lua
│       └── Chunks/C0_0.lua … C4_4.lua
└── fbx/
    ├── PortSolace_C0_0.fbx …   one file per 512-stud chunk
    └── anchors.json            where each chunk's ANCHOR cube belongs in Roblox
```

## Scale, axes and chunks

* **1 Blender unit = 1 stud.** The map runs from -1280 to +1280 on X and Y. The dense core
  is roughly 1900 studs across, and woods, hills, fields, beach and the bluff fill the rest.
* Blender axes: +X east, +Y north, +Z up. Roblox position = `(x, z, -y)`, so north is
  Roblox -Z.
* The world is split into 5 × 5 chunks of 512 studs, named `C{i}_{j}`. `i` counts
  from the west and `j` from the south. For example, `C0_0` is the south-west corner and
  `C2_2` is downtown. The Roblox data, the FBX files and the Blender objects (custom
  property `chunk`) all use these names.

## The Blender scene

```
TOWN
├── TERRAIN (+ WATER)          4-stud height-field tiles (256²), sea, creek surface
├── ROADS (+ BRIDGES, RAIL)    swept road meshes, junction plates, markings, bridges, rail line
├── SIDEWALKS
├── DOWNTOWN, MIXED_USE, RESIDENTIAL, LOW_INCOME, MOTEL, INDUSTRIAL, COMMERCIAL,
│   WATERFRONT, POLICE, CIVIC, FIRE, PARKS, OUTSKIRTS        building exteriors per district
├── PROPS, VEGETATION, VEHICLES, LANDMARKS
├── INTERIORS / INT_RESIDENTIAL, INT_COMMERCIAL, INT_INDUSTRIAL, INT_CIVIC, INT_SERVICE
├── LIGHTING                   ~5,100 lights, the late-afternoon sun, RobloxLighting preset empty
└── GAMEPLAY                   entrance, stair, roof, safehouse, POI, vehicle … empties
KIT (excluded)                 one master mesh per prop; placed props are linked duplicates
```

* **Buildings:** each building has a root empty, `B###_Name`, with custom properties
  `building_id`, `archetype`, `district`, `levels`, `detail`, `landmark` and `chunk`. The
  shell (`B###.ext.<material>`) and interior (`B###.int.<material>`) are split into one
  object per material, so each becomes one Roblox MeshPart. Furniture and fixtures are
  linked duplicates of the KIT masters. Recolourable parts (`$fabric`, `$paint`, `$car` …)
  use object-level material slots, so one mesh serves every colour variant.
* **Materials:** every material carries the custom properties `roblox_material`,
  `roblox_color` (0–255) and `roblox_transparency`.
* **Infrastructure:** roads, sidewalks, bridges, rail and so on are merged per
  (category, chunk, material), for example `Roads_C2_2.asphalt`.
* **Construction:** walls are a 0.8-stud facade skin plus a 0.2-stud interior finish, and
  interior walls are 0.6 studs. Floors are a 0.8-stud slab plus a 0.2-stud finish. No two
  faces overlap in the same plane, so nothing z-fights.

## Into Roblox Studio

### Workflow A: native parts (recommended)

All building geometry is made of boxes, wedges and cylinders, so the town can be rebuilt
from native Parts exactly. No mesh import is needed, collisions are exact, and the
materials are real Roblox materials.

1. Drag `build/roblox/PortSolace.rbxmx` into **ServerStorage**, or sync with Rojo using
   [`roblox/default.project.json`](../roblox/default.project.json).
2. Run this in the command bar:
   ```lua
   require(game.ServerStorage.PortSolace.TownBuilder).build()
   ```
   This builds the voxel terrain with sea and creek water, every building inside and out,
   furniture, street props, vehicles, vegetation, lights, signs, gameplay markers and the
   lighting preset. It also clears terrain from building footprints and from above roads.
3. Move `ServerStorage.PortSolace.TownRuntime` into **ServerScriptService**. The Rojo
   project does this for you.
4. Save the place. You don't need the builder at runtime.

Useful options for `build{...}`:

| Option | Default | |
|---|---|---|
| `chunks` | all | e.g. `{"C2_2","C3_2"}` to build downtown and the civic centre only |
| `interiors` | `true` | interior walls, floors and furniture |
| `interiorFilter` | `nil` | only these buildings get interiors: a list of ids (`{"B001","B007"}`) or `function(id, info)` (`info.landmark`, `.district`, `.archetype`, `.quality` …) |
| `propDetail` | `3` | 1 = essential furniture only, 2 = + normal, 3 = + clutter/decor |
| `terrain`, `carve`, `water` | `true` | voxel terrain, footprint/road clearing, sea + creek |
| `lights`, `signs`, `markers`, `props` | `true` | |
| `colliders`, `visualParts` | `false`, `true` | for Workflow B |
| `streaming` | `true` | enables `StreamingEnabled` (target radius 768) |

Everything included, the town is about 365k parts. About 175k are structural (shells,
interiors, roads) and about 190k belong to the ~33k furniture and prop models. Without
interiors it's about 150k parts. Use `interiorFilter` to keep interiors only where your
game needs them; landmark buildings and a downtown core are a common choice. Building
the full town in Studio takes a few minutes; it yields regularly so Studio stays
responsive.

### Workflow B: FBX MeshParts

1. Import each `build/fbx/PortSolace_C*.fbx` with the **3D Importer**. Set
   *File Dimensions* to **Studs** and keep the scene hierarchy.
2. Move each imported chunk so that its `ANCHOR_<chunk>` cube sits at the
   `roblox_position` recorded in `fbx/anchors.json`, then delete the anchor.
3. Set the MeshParts' `CanCollide` to false. Then run
   `TownBuilder.build({ visualParts = false, colliders = true })`. This adds props,
   lights, signs, markers, terrain and invisible box colliders, which are far more
   accurate than MeshPart collision fidelity.

Objects over 19k triangles are split automatically.

### What the runtime does

`TownRuntime` (Script) handles these behaviours:

* **Day and night.** An optional cycle (script attributes `DayCycle`, `MinutesPerDay`,
  `StartClock`) moves the clock, and lights follow their schedule:
  * `night`: street and exterior lights, on from dusk.
  * `res`: homes. Each light gets its own seed, so some houses stay dark.
  * `biz`: shops, during opening hours.
  * `late`: bars, diners and the motel office.
  * `work`: industry, some lit all night.
  * `always` and `dark`: always on and never on.
* **Doors.** Every door gets a ProximityPrompt. Hinged doors swing away from the player.
  Garage and roll-up doors lift, and double or sliding doors slide. A door whose
  `locked` attribute is true stays shut and records `LastLockedAttempt`, so your
  lock-picking or keys system can hook in.
* **Lighthouse.** The beam rotates at night.

### Tags, attributes and data for game code

| CollectionService tag | On | Attributes |
|---|---|---|
| `PS_Building` | building Model | `BuildingId`, `DisplayName`, `Archetype`, `District`, `Levels` |
| `PS_Door` | door Model | `DoorKind`, `door`, `role` (entrance/interior/…), `locked`, `width`, `height`, `hinge`, `ClosedPivot` |
| `PS_Light` | light anchor Part | `Schedule`, `Seed`, `Owner` |
| `PS_Marker`, `PS_Marker_<kind>` | invisible Part | `Kind`, `Label`, `Owner`, `Chunk` + kind-specific (`tier`, `room`, `level`, `door` …) |
| `PS_Vehicle`, `PS_Boat`, `PS_Police`, `PS_Fire`, `PS_Gate`, `PS_RailCar` | prop Model | |
| `PS_NeonSign` | sign Part | `SignText` |

These marker kinds are placed in the town:

* `entrance`: 863 entrances, with role main, secondary, service, loading, garage, staff,
  vehicle and so on.
* `stair`, `roof_access`, `fire_escape`, `ladder`
* `safehouse`, `hideout`, `stash`: starter trailers, motel rooms, apartments, basements,
  workshops, chop shops, storage units, pawn back rooms and bar cellars.
* `vehicle` and `parking_spot`: cars parked in garages and lots.
* `boat`, `dock`, `fuel`, `gate`
* `bus_stop`, `traffic_signal`, `street_sign`
* `bridge`, `underpass`
* `landmark`, `vantage`, `poi`, `park`
* `building`: one per building.

The `Manifest` module, and `TownBuilder.building(id)`, look up any building's name,
archetype, district, centre, floors and entrances. `manifest.json` adds every room, with
its kind, name, levels, area and apartment unit.

## Conventions

* **Wedges:** full height at Blender local -Y, sloping to zero at +Y. That is Roblox
  local +Z (back) to -Z (front), which is exactly how a WedgePart is built.
* **Cylinders:** the Blender axis is local Z. The exporter rotates them so the Roblox
  Cylinder's X axis runs along it, and `Size.X` is the length.
* **Kit props:** the origin is at floor centre, with the front facing -Y (Roblox +Z).
  Ceiling props hang below z = 0.
* **Signs:** the face points along Blender -Y, which is the SurfaceGui `Back` face in Roblox.
* **Records:** chunk records are CSV lines inside long strings. Group headers
  (`#B004|Exterior`) map records to building or category Models. The line formats are
  documented at the top of [`townbuilder/rbx/export.py`](townbuilder/rbx/export.py).

## Code map

```
build_town.py                 CLI entry point
townbuilder/
├── geom.py                   primitives (box/wedge/cyl/ball/mesh), transforms, Roblox conversion
├── palette.py                ~330 materials (colour, Roblox material, roughness, glow)
├── records.py                PropPlace, LightRec, Marker, SignRec
├── kit/                      ~430 props: furniture, kitchen/bath, commercial, industrial,
│                             street, vehicles & boats, vegetation, doors
├── archi/
│   ├── plan.py               Plan / Room / Door / Stair / Facade / Roof / Sign
│   ├── build.py              plan → walls, openings, slabs, stairs, roofs, facade dressing
│   └── furnish.py            furnishing rules for ~100 room kinds, 3 detail levels
├── archetypes/               residential, commercial, industrial, civic, waterfront,
│                             roadside, landmarks (+ common helpers)
├── world/
│   ├── layout.py             THE MAP: coast, creek, rail, hills, districts, roads, sites, parks
│   ├── terrain.py            height field, materials, creek channel, stamping
│   ├── roads.py              road network, junctions, bridges, swept meshes, street furniture
│   ├── rail.py               rail line, embankments, truss bridge, underpasses, parked train
│   ├── placement.py          district mixes, lot placement along road frontage
│   ├── dressing.py           yards, parking, parks, pier, docks, seawall, power line,
│   │                         hideouts, vegetation, outskirts
│   ├── model.py              World / BuildingRec
│   └── build.py              build_world(): runs everything above (no bpy needed)
├── bl/                       Blender realisation, materials, meshing, renders, FBX export
└── rbx/export.py             Roblox data modules, manifest, rbxmx bundle
tools/
├── preview_building.py       render one archetype: exterior + per-floor cutaways
├── plot_layout.py, plot_lots.py   2D plans of the map and the placed lots
├── label_map.py              annotated overview map (docs/images/map.jpg)
└── write_directory.py        docs/TOWN_DIRECTORY.md from manifest.json
```

`townbuilder.world` and `townbuilder.rbx` don't need Blender. Run `build_world()` and
`export_roblox()` with plain Python and numpy to regenerate Roblox data in about a minute.

## Extending

* **Move or add roads, sites or districts:** edit `world/layout.py`. Roads are polylines
  with a class. Sites pin landmark buildings near a road position, and districts are
  polygons with a building mix in `world/placement.py` (`MIX`).
* **New building type:** add an `@archetype` function that returns a `Plan`. Declare rooms
  per level, doors between rooms (or to `"out"`), stairs, a facade, a roof and signs. The
  engine derives everything else. `tools/preview_building.py <archetype> <w> <d> <dir>`
  renders it with per-floor cutaways.
* **New prop:** add a `@prop` builder in `kit/`. It emits primitives with palette materials
  or `$channel` materials, plus an optional light. Furnishing rules in `archi/furnish.py`
  place props by room kind.
