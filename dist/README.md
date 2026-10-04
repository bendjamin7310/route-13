# Port Solace: ready-to-open Roblox files

| File | What it is | Size |
|---|---|---|
| **[PortSolace.rbxl](PortSolace.rbxl)** | The whole town as a Roblox place: every building with its interior, furniture, street props, cars, boats, trees, ~5,400 lights, signs, gameplay markers, the lighting preset, a spawn point and the runtime scripts. | ~8 MB |
| **[PortSolace_Lite.rbxl](PortSolace_Lite.rbxl)** | The same place, but only landmarks and the downtown/civic core have interiors (~210k parts instead of ~365k). Start here on an average PC. | ~5 MB |
| **[PortSolace_Town.rbxm](PortSolace_Town.rbxm)** | The town as a model, for inserting into a place you already have. | ~8 MB |
| [PortSolace_Test.rbxl](PortSolace_Test.rbxl) | Just the downtown block (about 36k instances), with every kind of object the big file has. If the big file won't open, try this one to narrow down why. | ~1 MB |

## Open it

1. Download **PortSolace.rbxl** (or the Lite one).
2. In **Roblox Studio** (not the Roblox player app), use **File → Open from File…** and pick
   the `.rbxl`. `.rbxm` files are models: insert those into a place instead of opening them.
   A big place takes a little while to open.
3. Press **Play** to walk around. You spawn on the Town Square.

That's all you need to do. The town stands on a coarse preview ground made of parts until the
real terrain exists.

## The terrain (one command, recommended)

Roblox voxel terrain (grass, beach, hills, the sea and the creek) can't be stored by the
generator. Instead, a script builds it from data that ships inside the file:

* **Automatically on Play.** `TerrainLoader` builds the terrain when the game starts. It
  starts around the spawn and takes a few seconds. Terrain created during Play disappears
  again when you press Stop. That's how Studio works.
* **Permanently (recommended).** Open **View → Command Bar**, paste this line, press Enter
  and wait for "terrain done". Then **File → Save**:

  ```lua
  require(game.ServerStorage.PortSolace.TownBuilder).buildTerrain()
  ```

  The terrain is now part of your place. The preview ground is removed, edit mode shows the
  real landscape, and servers start instantly. For the model version, the line is
  `require(workspace.PortSolace.PortSolaceData.TownBuilder).buildTerrain()`.

## Insert the model into another place

1. Drag **PortSolace_Town.rbxm** into Studio, or use right-click on **Workspace → Insert
   from File…**. Everything lands in `Workspace.PortSolace`, centred on the origin and about
   2,560 × 2,560 studs.
2. The scripts inside the folder run as they are: `TownRuntime` (lights, doors, lighthouse)
   and `TerrainLoader`.
3. Run the terrain line above once and save.
4. Optional: copy the lighting values from the place file. Its Lighting has ClockTime 17.6,
   Atmosphere, Bloom and colour grading, with Technology set to Future.

## What works when you press Play

* **Doors.** Doors open with **E**. Hinged doors swing away from you, garage and roll-up
  doors fold up, and sliding and double doors slide. Locked doors (cells, the evidence
  room and so on) stay shut until you set their `locked` attribute to false.
* **Day and night.** The clock runs one in-game day per 24 real minutes, starting at
  sunset. Street lights come on at dusk, homes light up one by one, shops close, bars and
  the motel stay lit, and the lighthouse beam sweeps the bay. Adjust this with attributes
  on `ServerScriptService.TownRuntime`: `DayCycle`, `MinutesPerDay` and `StartClock`.
* **Game hooks.** Everything is tagged for your code:
  * `PS_Building`
  * `PS_Door`
  * `PS_Light`
  * `PS_Marker_safehouse`, `PS_Marker_hideout`, `PS_Marker_stash`
  * `PS_Marker_entrance`, `PS_Vehicle` and more

  `ServerStorage.PortSolace.Manifest` lists every building, with its name, type, district
  and entrances. See [`docs/TOWN_DIRECTORY.md`](../docs/TOWN_DIRECTORY.md) for the full
  directory, and [`docs/TOWN_MAP.md`](../docs/TOWN_MAP.md) for the map and districts.

## Performance

The full place is about **365k parts**, so plan for a decent PC. The place has
StreamingEnabled on, which helps players in a live game but not Studio's edit mode. If Studio
struggles:

* Use **PortSolace_Lite.rbxl**.
* Set **Lighting → Technology** to *ShadowMap*.
* Set the `DayCycle` attribute on `TownRuntime` to false, so the lights stop switching.

## Rebuilding the files

These files are generated. To make them again, or to make them with a different seed:

```bash
cd blender
python tools/make_roblox.py      # writes build/roblox/*.rbxl and *.rbxm (no Blender needed)
```

This needs Python with numpy, and cargo for the small Rust converter in
`blender/tools/rbxconv`. See [`blender/README.md`](../blender/README.md).
