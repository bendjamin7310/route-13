--[[
	Port Solace - TerrainLoader (Script, ServerScriptService)

	Voxel terrain cannot be stored by the generator, so this script writes it from
	ServerStorage.PortSolace.TerrainData when the place runs and the terrain is still
	empty (sea, beach, hills, creek; footprints and road beds are cleared).

	To bake the terrain into the place once (recommended before publishing), run this in
	the Studio command bar and save:

		require(game.ServerStorage.PortSolace.TownBuilder).buildTerrain()

	The script then sees the PortSolaceTerrain attribute (or existing ground) and does
	nothing.
]]

local ServerStorage = game:GetService("ServerStorage")

local terrain = workspace.Terrain
if terrain:GetAttribute("PortSolaceTerrain") then
	return
end

-- already has ground under the town square? (terrain baked without the attribute)
local probe = Region3.new(Vector3.new(156, -12, 48), Vector3.new(172, 12, 64)):ExpandToGrid(4)
local materials = terrain:ReadVoxels(probe, 4)
for x = 1, #materials do
	for y = 1, #materials[x] do
		for z = 1, #materials[x][y] do
			if materials[x][y][z] ~= Enum.Material.Air then
				return
			end
		end
	end
end

local data = ServerStorage:WaitForChild("PortSolace")
local TownBuilder = require(data:WaitForChild("TownBuilder"))
local t0 = os.clock()
TownBuilder.buildTerrain({ data = data, verbose = false })
print(string.format("[PortSolace] terrain generated in %.1fs", os.clock() - t0))
