--[[
	Port Solace - TerrainLoader (Script)

	Voxel terrain cannot be stored by the generator, so this script writes it from the
	TerrainData module when the game runs and the terrain is still empty (sea, beach,
	hills, creek; building footprints and road beds are cleared).  Until then the town
	stands on a coarse part-based "PreviewGround", which is removed once real terrain
	exists.

	To bake the terrain into the place once (recommended - edit mode then shows it, and
	servers start instantly), run this in the Studio command bar and save the place:

		require(game.ServerStorage.PortSolace.TownBuilder).buildTerrain()

	(model version: require(workspace.PortSolace.PortSolaceData.TownBuilder).buildTerrain())

	After that the PortSolaceTerrain attribute is set on Terrain and this script does
	nothing.
]]

local ServerStorage = game:GetService("ServerStorage")

local terrain = workspace.Terrain
if terrain:GetAttribute("PortSolaceTerrain") then
	return
end

-- data: ServerStorage.PortSolace (place) or a PortSolaceData folder next to this script (model)
local function findData()
	local s = ServerStorage:FindFirstChild("PortSolace")
	if s and s:FindFirstChild("TerrainData") then
		return s
	end
	local here = script.Parent and script.Parent:FindFirstChild("PortSolaceData")
	if here and here:FindFirstChild("TerrainData") then
		return here
	end
	return nil
end

local data = findData()
if not data then
	warn("[PortSolace] TerrainLoader: no TerrainData found (expected ServerStorage.PortSolace)")
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

print("[PortSolace] generating terrain (bake it once from the command bar to skip this)")
local TownBuilder = require(data:WaitForChild("TownBuilder"))
local t0 = os.clock()
TownBuilder.buildTerrain({ data = data, verbose = false })
print(string.format("[PortSolace] terrain generated in %.1fs", os.clock() - t0))
