# Port Solace: Roblox side

* `src/TownBuilder.lua` (ModuleScript): builds the town in Studio from the generated data
  modules. It creates voxel terrain and water, every building as native Parts with its
  interior, furniture and props, lights, signs and gameplay markers, and the lighting
  preset.
* `src/TownRuntime.server.lua` (Script): runs the day/night cycle and the light schedules,
  makes doors openable with ProximityPrompts, and rotates the lighthouse beam.
* `default.project.json`: a Rojo project. It maps the generated data in
  `../build/roblox/PortSolace` and the builder to `ServerStorage.PortSolace`, and the
  runtime to `ServerScriptService`.

The data comes from the Blender generator:

```bash
cd blender && python build_town.py --roblox --no-blend
```

That writes `build/roblox/PortSolace.rbxmx`, which bundles the data, the builder and the
runtime. You can sync the same files with Rojo instead.

Then run this in the Studio command bar:

```lua
require(game.ServerStorage.PortSolace.TownBuilder).build()
```

For build options, tags and attributes, and the FBX/MeshPart workflow, see
[`blender/README.md`](../blender/README.md#into-roblox-studio).
