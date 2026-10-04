--[[
	Port Solace - TownBuilder

	Builds the generated town inside Roblox Studio from the data modules written by
	blender/build_town.py --roblox (Palette, Kit, TerrainData, Manifest, Chunks/*).

	Already have PortSolace.rbxl (the prebuilt place)?  Only the terrain step is needed:

		require(game.ServerStorage.PortSolace.TownBuilder).buildTerrain()

	Usage (Studio command bar, after inserting PortSolace.rbxmx into ServerStorage):

		require(game.ServerStorage.PortSolace.TownBuilder).build()

	or with options:

		require(game.ServerStorage.PortSolace.TownBuilder).build({
			chunks = { "C2_2", "C1_2" },   -- only these 512x512 chunks (nil = all 25)
			interiors = true,             -- interior walls, floors, furniture
			propDetail = 2,               -- 1 essential, 2 normal, 3 everything
			interiorFilter = function(id, info)   -- e.g. interiors for landmarks + downtown only
				return info.district == "DOWNTOWN" or info.district == "CIVIC"
			end,
		})

	Coordinates are studs.  Everything is anchored.  The result is one Model per
	building (Exterior / Interior / Props / Fixtures / Signs), infrastructure grouped
	by category and chunk, world props by category and chunk, gameplay markers, voxel
	terrain with water, and the late-afternoon lighting preset.
]]

local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")

local TownBuilder = {}

TownBuilder.DEFAULTS = {
	data = nil, -- Folder with Palette/Kit/TerrainData/Manifest/Chunks (default: script.Parent)
	parent = nil, -- default: workspace
	name = "PortSolace",
	clear = true, -- destroy a previous build with the same name
	chunks = nil, -- list of chunk names, nil = all
	structures = true, -- building shells + infrastructure as native parts
	interiors = true,
	-- nil = every building; or a list/set of building ids ({"B001", "B007"}), or
	-- function(id, info) -> bool (info = Manifest.buildings[id]: archetype, district ...)
	interiorFilter = nil,
	props = true,
	propDetail = 3,
	lights = true,
	markers = true,
	signs = true,
	terrain = true,
	carve = true, -- clear voxel terrain inside buildings and above roads
	water = true,
	lighting = true,
	streaming = true, -- turn on Workspace.StreamingEnabled (when allowed)
	colliders = false, -- invisible collision boxes (for the FBX / MeshPart workflow)
	visualParts = true, -- false when the visuals come from imported FBX MeshParts
	yieldEvery = 1200, -- parts created between task.wait() calls (0 = never yield)
	verbose = true,
}

-- ---------------------------------------------------------------------------------
-- small helpers

local split = string.split
local gmatch = string.gmatch
local tonumber = tonumber

local function lines(block)
	return gmatch(block or "", "[^\n]+")
end

local function cf7(f, i)
	return CFrame.new(
		tonumber(f[i]),
		tonumber(f[i + 1]),
		tonumber(f[i + 2]),
		tonumber(f[i + 3]),
		tonumber(f[i + 4]),
		tonumber(f[i + 5]),
		tonumber(f[i + 6])
	)
end

local function v3(f, i)
	return Vector3.new(
		math.max(0.001, tonumber(f[i]) or 1),
		math.max(0.001, tonumber(f[i + 1]) or 1),
		math.max(0.001, tonumber(f[i + 2]) or 1)
	)
end

local function parseKV(s)
	local t = {}
	if s == nil or s == "" then
		return t
	end
	for _, kv in ipairs(split(s, ";")) do
		local k, v = string.match(kv, "^([^=]+)=(.*)$")
		if k then
			t[k] = v
		end
	end
	return t
end

local function attrValue(v)
	local n = tonumber(v)
	if n then
		return n
	end
	if v == "True" or v == "true" then
		return true
	end
	if v == "False" or v == "false" then
		return false
	end
	return v
end

local function folder(parent, name, class)
	local f = parent:FindFirstChild(name)
	if not f then
		f = Instance.new(class or "Folder")
		f.Name = name
		f.Parent = parent
	end
	return f
end

-- materials voxel terrain accepts
local TERRAIN_MATERIALS = {}
for _, n in ipairs({
	"Grass", "Slate", "Concrete", "Brick", "Sand", "WoodPlanks", "Rock", "Glacier", "Snow",
	"Sandstone", "Mud", "Basalt", "Ground", "CrackedLava", "Asphalt", "Cobblestone", "Ice",
	"LeafyGrass", "Salt", "Limestone", "Pavement",
}) do
	TERRAIN_MATERIALS[n] = true
end

-- ---------------------------------------------------------------------------------
-- builder state

local Builder = {}
Builder.__index = Builder

function Builder.new(opts)
	local self = setmetatable({}, Builder)
	self.opts = opts
	local data = opts.data
	self.data = data
	if not data:FindFirstChild("Kit") then
		error(
			"[PortSolace] this data folder has no Kit/Chunks modules: the town is already built "
				.. "into this place. Use TownBuilder.buildTerrain() here, or insert PortSolace.rbxmx "
				.. "into an empty place to build from scratch.",
			2
		)
	end
	self.Palette = require(data:WaitForChild("Palette"))
	self.Kit = require(data:WaitForChild("Kit"))
	self.Manifest = require(data:WaitForChild("Manifest"))
	self.mats = {}
	for i, e in ipairs(self.Palette) do
		local ok, m = pcall(function()
			return Enum.Material[e.material]
		end)
		self.mats[i] = {
			material = (ok and m) or Enum.Material.SmoothPlastic,
			color = Color3.fromRGB(e.color[1], e.color[2], e.color[3]),
			transparency = e.transparency or 0,
			glow = e.glow or 0,
			name = e.name,
		}
	end
	self.fallbackMat = self.Palette.index and self.Palette.index["plastic_gray"] or 1
	self.templates = {}
	self.count = 0
	self.stats = { parts = 0, props = 0, lights = 0, markers = 0, signs = 0, colliders = 0, carves = 0 }
	self.carves = {}
	self.buildings = {}
	self.interiorCache = {}
	return self
end

function Builder:log(...)
	if self.opts.verbose then
		print("[PortSolace]", ...)
	end
end

function Builder:tick(n)
	self.count += n or 1
	local every = self.opts.yieldEvery
	if every and every > 0 and self.count >= every then
		self.count = 0
		task.wait()
	end
end

function Builder:applyMat(p, idx)
	local m = self.mats[idx] or self.mats[self.fallbackMat]
	p.Material = m.material
	p.Color = m.color
	if m.transparency > 0 then
		p.Transparency = m.transparency
	end
end

local SHAPES = {
	B = function()
		return Instance.new("Part")
	end,
	W = function()
		return Instance.new("WedgePart")
	end,
	C = function()
		local p = Instance.new("Part")
		p.Shape = Enum.PartType.Cylinder
		return p
	end,
	S = function()
		local p = Instance.new("Part")
		p.Shape = Enum.PartType.Ball
		return p
	end,
	E = function()
		local p = Instance.new("Part")
		local m = Instance.new("SpecialMesh")
		m.MeshType = Enum.MeshType.Sphere
		m.Parent = p
		return p
	end,
}

-- Roblox cylinders are round (diameter = min of Y/Z) and SpecialMesh ellipsoids lose their
-- material, so: equal cylinder diameters, and near-uniform ellipsoids become balls.
local function fixShape(kind, size)
	if kind == "C" and math.abs(size.Y - size.Z) > 1e-3 then
		local d = math.max(size.Y, size.Z)
		return kind, Vector3.new(size.X, d, d)
	elseif kind == "E" then
		local lo = math.min(size.X, size.Y, size.Z)
		local hi = math.max(size.X, size.Y, size.Z)
		if hi <= lo * 1.15 then
			local d = (size.X + size.Y + size.Z) / 3
			return "S", Vector3.new(d, d, d)
		end
	end
	return kind, size
end

-- Part record: K,x,y,z,qx,qy,qz,qw,sx,sy,sz,mat,collide
function Builder:makePart(f, matIdx, cf, size)
	local kind
	kind, size = fixShape(f[1], size or v3(f, 9))
	local p = (SHAPES[kind] or SHAPES.B)()
	p.Anchored = true
	p.Size = size
	p.CFrame = cf or cf7(f, 2)
	self:applyMat(p, matIdx or tonumber(f[12]))
	local collide = f[13] == "1"
	p.CanCollide = collide
	p.CanTouch = false
	if not collide then
		p.CanQuery = false
	end
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	return p
end

-- ---------------------------------------------------------------------------------
-- containers

function Builder:buildingModel(id)
	local m = self.buildings[id]
	if m then
		return m
	end
	local info = self.Manifest.buildings and self.Manifest.buildings[id]
	m = Instance.new("Model")
	m.Name = info and (id .. " " .. info.name) or id
	m:SetAttribute("BuildingId", id)
	if info then
		m:SetAttribute("DisplayName", info.name)
		m:SetAttribute("Archetype", info.archetype)
		m:SetAttribute("District", info.district)
		m:SetAttribute("Levels", info.levels)
		if info.center then
			m.WorldPivot = CFrame.new(info.center)
		end
	end
	m.Parent = self.root.Buildings
	CollectionService:AddTag(m, "PS_Building")
	self.buildings[id] = m
	return m
end

-- "#B004|Exterior" -> building sub-model; "#Infrastructure|Roads" -> category/chunk model
function Builder:groupContainer(chunk, header)
	local owner, part = string.match(header, "^#([^|]+)|?(.*)$")
	if owner == nil then
		return self.root, nil
	end
	if string.match(owner, "^B%d+$") then
		local b = self:buildingModel(owner)
		local sub = part ~= "" and part or "Props"
		return folder(b, sub, sub == "Props" and "Folder" or "Model"), sub
	end
	if owner == "Infrastructure" then
		local cat = folder(self.root.Infrastructure, part)
		return folder(cat, chunk, "Model"), part
	end
	-- world prop categories ("#Vegetation", "#Props", ...)
	local cat = folder(self.root.World, owner)
	return folder(cat, chunk, "Folder"), owner
end

function Builder:interiorWanted(owner)
	local o = self.opts
	if not o.interiors then
		return false
	end
	local f = o.interiorFilter
	if f == nil or owner == nil then
		return true
	end
	local cache = self.interiorCache
	if cache[owner] == nil then
		local want
		if type(f) == "function" then
			want = f(owner, self.Manifest.buildings and self.Manifest.buildings[owner]) and true or false
		elseif type(f) == "table" then
			want = f[owner] == true or table.find(f, owner) ~= nil
		else
			want = true
		end
		cache[owner] = want
	end
	return cache[owner]
end

local function ownerOf(header)
	return string.match(header, "^#(B%d+)")
end

-- ---------------------------------------------------------------------------------
-- structures

function Builder:buildParts(chunk, block)
	local opts = self.opts
	local container, sub = self.root, nil
	local skip = false
	for line in lines(block) do
		if string.sub(line, 1, 1) == "#" then
			container, sub = self:groupContainer(chunk, line)
			skip = (sub == "Interior" and not self:interiorWanted(ownerOf(line)))
		elseif not skip then
			local f = split(line, ",")
			local p = self:makePart(f)
			p.Parent = container
			self.stats.parts += 1
			self:tick()
		end
	end
end

function Builder:buildColliders(chunk, block)
	local container
	local skip = false
	for line in lines(block) do
		if string.sub(line, 1, 1) == "#" then
			local c, sub = self:groupContainer(chunk, line)
			skip = (sub == "Interior" and not self:interiorWanted(ownerOf(line)))
			container = folder(c, "Colliders", "Model")
		elseif not skip then
			local f = split(line, ",")
			local p = (f[1] == "W") and Instance.new("WedgePart") or Instance.new("Part")
			if f[1] == "C" then
				p.Shape = Enum.PartType.Cylinder
			end
			p.Anchored = true
			p.Size = v3(f, 9)
			p.CFrame = cf7(f, 2)
			p.Transparency = 1
			p.CanTouch = false
			p.CastShadow = false
			p.Parent = container or self.root
			self.stats.colliders += 1
			self:tick()
		end
	end
end

-- ---------------------------------------------------------------------------------
-- props (kit instances)

function Builder:template(kitIdx, chanStr, sx, sy, sz)
	local key = kitIdx .. "|" .. chanStr .. "|" .. sx .. "," .. sy .. "," .. sz
	local t = self.templates[key]
	if t then
		return t
	end
	local def = self.Kit.defs[kitIdx]
	local chans = {}
	for k, v in pairs(parseKV(chanStr)) do
		chans[k] = tonumber(v)
	end
	local defaults = self.Palette.channelDefaults or {}
	local scale = Vector3.new(sx, sy, sz)
	local scaled = math.abs(sx - 1) > 1e-3 or math.abs(sy - 1) > 1e-3 or math.abs(sz - 1) > 1e-3
	t = Instance.new("Model")
	t.Name = def and def.name or ("kit" .. kitIdx)
	for line in lines(self.Kit.prims[kitIdx]) do
		local f = split(line, ",")
		local m = f[12]
		local idx
		if string.sub(m, 1, 1) == "$" then
			local ch = string.sub(m, 2)
			idx = chans[ch] or defaults[ch] or self.fallbackMat
		else
			idx = tonumber(m)
		end
		local cf = cf7(f, 2)
		local size = v3(f, 9)
		if scaled then
			size = Vector3.new(
				size.X * (cf.XVector * scale).Magnitude,
				size.Y * (cf.YVector * scale).Magnitude,
				size.Z * (cf.ZVector * scale).Magnitude
			)
			cf = CFrame.new(cf.Position * scale) * cf.Rotation
		end
		local p = self:makePart(f, idx, cf, size)
		p.Parent = t
	end
	t.WorldPivot = CFrame.new()
	self.templates[key] = t
	return t
end

local PROP_TAGS = {
	door = "PS_Door",
	vehicle = "PS_Vehicle",
	boat = "PS_Boat",
	gate = "PS_Gate",
	rail = "PS_RailCar",
	police = "PS_Police",
	fire = "PS_Fire",
}

-- Prop record: kit,x,y,z,qx,qy,qz,qw,sx,sy,sz,flags,channels,meta
function Builder:buildProps(chunk, block)
	local opts = self.opts
	local container = self.root
	local owner = nil
	for line in lines(block) do
		if string.sub(line, 1, 1) == "#" then
			container = self:groupContainer(chunk, line)
			owner = ownerOf(line)
		else
			local f = split(line, ",")
			local kitIdx = tonumber(f[1]) or 0
			local flags = tonumber(f[12]) or 2
			local interior = bit32.band(flags, 1) == 1
			local detail = bit32.rshift(flags, 1)
			local def = self.Kit.defs[kitIdx]
			if def and detail <= opts.propDetail and (not interior or self:interiorWanted(owner)) then
				local sx, sy, sz = tonumber(f[9]) or 1, tonumber(f[10]) or 1, tonumber(f[11]) or 1
				local t = self:template(kitIdx, f[13] or "", sx, sy, sz)
				local m = t:Clone()
				m:PivotTo(cf7(f, 2))
				if interior then
					m:SetAttribute("Interior", true)
				end
				local meta = parseKV(f[14])
				for k, v in pairs(meta) do
					m:SetAttribute(k, attrValue(v))
				end
				for _, tag in ipairs(def.tags or {}) do
					local ct = PROP_TAGS[tag]
					if ct then
						CollectionService:AddTag(m, ct)
					end
				end
				if meta.door then
					local kind = "hinged"
					for _, tag in ipairs(def.tags or {}) do
						if tag == "double" or tag == "garage" or tag == "rollup" or tag == "sliding" then
							kind = tag
						end
					end
					m:SetAttribute("DoorKind", kind)
					m:SetAttribute("ClosedPivot", m:GetPivot())
				end
				m.Parent = container
				self.stats.props += 1
				self:tick(#t:GetChildren())
			end
		end
	end
end

-- ---------------------------------------------------------------------------------
-- lights, markers, signs

local LIGHT_CLASS = { point = "PointLight", spot = "SpotLight", surface = "SurfaceLight" }

-- x,y,z,kind,r,g,b,range,brightness,schedule,dx,dy,dz,owner
function Builder:buildLights(chunk, block)
	for line in lines(block) do
		local f = split(line, ",")
		local pos = Vector3.new(tonumber(f[1]), tonumber(f[2]), tonumber(f[3]))
		local dir = Vector3.new(tonumber(f[11]) or 0, tonumber(f[12]) or -1, tonumber(f[13]) or 0)
		local owner = f[14] or ""
		local parent
		if owner ~= "" then
			parent = folder(self:buildingModel(owner), "Fixtures", "Folder")
		else
			parent = folder(folder(self.root, "Lights"), chunk, "Folder")
		end
		local anchor = Instance.new("Part")
		anchor.Name = "Light"
		anchor.Size = Vector3.new(0.2, 0.2, 0.2)
		anchor.Transparency = 1
		anchor.Anchored = true
		anchor.CanCollide = false
		anchor.CanTouch = false
		anchor.CanQuery = false
		anchor.CastShadow = false
		if dir.Magnitude < 1e-3 then
			dir = Vector3.new(0, -1, 0)
		end
		dir = dir.Unit
		local up = math.abs(dir.Y) > 0.98 and Vector3.new(1, 0, 0) or Vector3.new(0, 1, 0)
		anchor.CFrame = CFrame.lookAt(pos, pos + dir, up)
		local kind = f[4]
		local l = Instance.new(LIGHT_CLASS[kind] or "PointLight")
		l.Color = Color3.new(tonumber(f[5]) or 1, tonumber(f[6]) or 1, tonumber(f[7]) or 1)
		l.Range = math.clamp(tonumber(f[8]) or 16, 2, 60)
		l.Brightness = (tonumber(f[9]) or 1) * 1.4
		l.Shadows = false
		if kind == "spot" then
			l.Face = Enum.NormalId.Front
			l.Angle = 100
		elseif kind == "surface" then
			l.Face = Enum.NormalId.Front
			l.Angle = 120
		end
		local schedule = f[10] or "always"
		l.Enabled = schedule == "always"
		l.Parent = anchor
		anchor:SetAttribute("Schedule", schedule)
		anchor:SetAttribute("Seed", (math.floor(pos.X * 7.13 + pos.Z * 3.71) % 1000) / 1000)
		if owner ~= "" then
			anchor:SetAttribute("Owner", owner)
		end
		CollectionService:AddTag(anchor, "PS_Light")
		anchor.Parent = parent
		self.stats.lights += 1
		self:tick()
	end
end

-- kind,x,y,z,yawDeg,label,owner,meta
function Builder:buildMarkers(chunk, block)
	local root = folder(self.root, "Markers")
	for line in lines(block) do
		local f = split(line, ",")
		local kind = f[1]
		local p = Instance.new("Part")
		p.Name = (f[6] ~= nil and f[6] ~= "") and f[6] or kind
		p.Size = Vector3.new(1, 1, 1)
		p.Transparency = 1
		p.Anchored = true
		p.CanCollide = false
		p.CanTouch = false
		p.CanQuery = false
		p.CastShadow = false
		local pos = Vector3.new(tonumber(f[2]), tonumber(f[3]), tonumber(f[4]))
		-- Blender yaw (CCW about +Z) = Roblox rotation about +Y
		p.CFrame = CFrame.new(pos) * CFrame.Angles(0, math.rad(tonumber(f[5]) or 0), 0)
		p:SetAttribute("Kind", kind)
		p:SetAttribute("Label", f[6] or "")
		p:SetAttribute("Chunk", chunk)
		if f[7] and f[7] ~= "" then
			p:SetAttribute("Owner", f[7])
		end
		for k, v in pairs(parseKV(f[8])) do
			p:SetAttribute(k, attrValue(v))
		end
		CollectionService:AddTag(p, "PS_Marker")
		CollectionService:AddTag(p, "PS_Marker_" .. kind)
		p.Parent = folder(root, kind)
		self.stats.markers += 1
		self:tick()
	end
end

-- x,y,z,qx,qy,qz,qw,w,h,bg,fg,neon,board,owner,text
function Builder:buildSigns(chunk, block)
	for line in lines(block) do
		local f = split(line, ",")
		local cf = cf7(f, 1)
		local w, h = tonumber(f[8]) or 4, tonumber(f[9]) or 2
		local bg, fg = tonumber(f[10]), tonumber(f[11])
		local neon, board = f[12] == "1", f[13] == "1"
		local owner = f[14] or ""
		local text = f[15] or ""
		local p = Instance.new("Part")
		p.Name = "Sign " .. text
		p.Anchored = true
		p.CanTouch = false
		-- board spans local Blender y 0..0.4 behind the face; the face looks along Roblox +Z
		p.Size = Vector3.new(w, h, 0.4)
		p.CFrame = cf * CFrame.new(0, 0, -0.2)
		if board then
			self:applyMat(p, bg)
		else
			p.Transparency = 1
			p.CanCollide = false
			p.CanQuery = false
		end
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Back
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 24
		gui.LightInfluence = neon and 0 or 1
		gui.Brightness = neon and 2.5 or 1
		gui.MaxDistance = 600
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(0.94, 0.86)
		t.Position = UDim2.fromScale(0.03, 0.07)
		t.BackgroundTransparency = 1
		t.Text = text
		t.TextScaled = true
		t.Font = neon and Enum.Font.FredokaOne or Enum.Font.GothamBlack
		local fm = self.mats[fg or 0]
		t.TextColor3 = fm and fm.color or Color3.new(1, 1, 1)
		t.Parent = gui
		gui.Parent = p
		p:SetAttribute("SignText", text)
		if neon then
			CollectionService:AddTag(p, "PS_NeonSign")
		end
		if owner ~= "" then
			p.Parent = folder(self:buildingModel(owner), "Signs", "Folder")
		else
			p.Parent = folder(folder(self.root, "Signs"), chunk, "Folder")
		end
		self.stats.signs += 1
		self:tick()
	end
end

-- ---------------------------------------------------------------------------------
-- terrain

function Builder:buildTerrain()
	local terrain = workspace.Terrain
	local TD = require(self.data:WaitForChild("TerrainData"))
	local N, res, origin, offset, scale = TD.size, TD.res, TD.origin, TD.offset, TD.scale
	local lookup = {}
	for i = 1, #TD.alphabet do
		lookup[string.byte(TD.alphabet, i)] = i - 1
	end
	local mats = {}
	for i, name in ipairs(TD.robloxMaterials) do
		-- only terrain-capable materials (Pebble, Plastic ... are part-only)
		mats[i - 1] = TERRAIN_MATERIALS[name] and Enum.Material[name] or Enum.Material.Ground
	end
	terrain.WaterColor = Color3.fromRGB(52, 102, 118)
	terrain.WaterTransparency = 0.55
	terrain.WaterReflectance = 0.6
	terrain.WaterWaveSize = 0.12
	terrain.WaterWaveSpeed = 8
	local UNDER = Enum.Material.Rock
	local AIR = Enum.Material.Air
	local WATER = Enum.Material.Water
	local byte = string.byte
	-- decode rows lazily: H[i][j], W[i][j] (nil = dry), M[i][j]
	local H, W, M = {}, {}, {}
	local function row(i)
		local r = H[i]
		if r then
			return r
		end
		local hs, ws, ms = TD.heights[i + 1], TD.water[i + 1], TD.mats[i + 1]
		r = {}
		local wr, mr = {}, {}
		for j = 0, N - 1 do
			local a, b = byte(hs, 2 * j + 1, 2 * j + 2)
			r[j] = ((lookup[a] * 64 + lookup[b]) - offset) / scale
			local c1, c2 = byte(ws, 2 * j + 1, 2 * j + 2)
			if c1 ~= 95 then -- "_"
				wr[j] = ((lookup[c1] * 64 + lookup[c2]) - offset) / scale
			end
			mr[j] = lookup[byte(ms, j + 1)]
		end
		H[i], W[i], M[i] = r, wr, mr
		return r
	end
	-- Roblox X = Blender x ; Roblox Z = -Blender y
	local function sample(x, z)
		local gx = (x - origin) / res
		local gy = (-z - origin) / res
		local j0 = math.clamp(math.floor(gx), 0, N - 2)
		local i0 = math.clamp(math.floor(gy), 0, N - 2)
		local tx, ty = math.clamp(gx - j0, 0, 1), math.clamp(gy - i0, 0, 1)
		local r0, r1 = row(i0), row(i0 + 1)
		local h = (r0[j0] * (1 - tx) + r0[j0 + 1] * tx) * (1 - ty) + (r1[j0] * (1 - tx) + r1[j0 + 1] * tx) * ty
		local ni = (ty < 0.5) and i0 or i0 + 1
		local nj = (tx < 0.5) and j0 or j0 + 1
		local w = W[ni][nj]
		if w == nil then
			-- any wet neighbour keeps shorelines continuous
			w = W[i0][j0] or W[i0][j0 + 1] or W[i0 + 1][j0] or W[i0 + 1][j0 + 1]
		end
		return h, w, M[ni][nj]
	end

	local half = -origin
	local SLAB = 32 -- voxels per slab side (128 studs)
	local nvox = math.floor(2 * half / 4)
	local useChannels = self.opts.water
	local channelsOk = true
	-- nearest slabs first, so the ground around the spawn exists within a second or two
	local focus = self.opts.terrainFocus or Vector3.new(164, 0, 60)
	local slabs = {}
	for sx = 0, nvox - 1, SLAB do
		for sz = 0, nvox - 1, SLAB do
			local cx = -half + (sx + SLAB / 2) * 4
			local cz = -half + (sz + SLAB / 2) * 4
			table.insert(slabs, { sx, sz, (cx - focus.X) ^ 2 + (cz - focus.Z) ^ 2 })
		end
	end
	table.sort(slabs, function(a, b)
		return a[3] < b[3]
	end)
	for slabIndex, slab in ipairs(slabs) do
		local sx, sz = slab[1], slab[2]
		do
			local cols = {}
			local lo, hi = math.huge, -math.huge
			local nx = math.min(SLAB, nvox - sx)
			local nz = math.min(SLAB, nvox - sz)
			for a = 1, nx do
				cols[a] = {}
				local x = -half + (sx + a - 1) * 4 + 2
				for b = 1, nz do
					local z = -half + (sz + b - 1) * 4 + 2
					local h, w, m = sample(x, z)
					if not self.opts.water then
						w = nil
					end
					cols[a][b] = { h, w, m }
					lo = math.min(lo, h)
					hi = math.max(hi, h, w or -math.huge)
				end
			end
			local y0 = math.floor((lo - 12) / 4) * 4
			local y1 = math.ceil((hi + 4) / 4) * 4
			local ny = math.max(1, (y1 - y0) / 4)
			local matA, occA, liqA = {}, {}, {}
			for a = 1, nx do
				local ma, oa, la = {}, {}, {}
				matA[a], occA[a], liqA[a] = ma, oa, la
				for yi = 1, ny do
					local mb, ob, lb = {}, {}, {}
					ma[yi], oa[yi], la[yi] = mb, ob, lb
					local bottom = y0 + (yi - 1) * 4
					for b = 1, nz do
						local c = cols[a][b]
						local h, w = c[1], c[2]
						local occ = math.clamp((h - bottom) / 4, 0, 1)
						local liq = 0
						if w and w > bottom then
							liq = math.clamp((w - bottom) / 4, 0, 1)
						end
						if occ > 0 then
							mb[b] = (h - bottom > 10) and UNDER or (mats[c[3]] or Enum.Material.Grass)
							ob[b] = occ
						elseif liq > 0 then
							mb[b] = WATER
							ob[b] = liq
						else
							mb[b] = AIR
							ob[b] = 0
						end
						lb[b] = (occ >= 1) and 0 or liq
					end
				end
			end
			local region = Region3.new(
				Vector3.new(-half + sx * 4, y0, -half + sz * 4),
				Vector3.new(-half + (sx + nx) * 4, y0 + ny * 4, -half + (sz + nz) * 4)
			)
			local wrote = false
			if useChannels and channelsOk then
				-- shoreline-aware path: solid + liquid in the same voxel
				local solidMat, solidOcc = {}, {}
				for a = 1, nx do
					solidMat[a], solidOcc[a] = {}, {}
					for yi = 1, ny do
						local sm, so = {}, {}
						solidMat[a][yi], solidOcc[a][yi] = sm, so
						for b = 1, nz do
							local m = matA[a][yi][b]
							if m == WATER then
								sm[b], so[b] = AIR, 0
							else
								sm[b], so[b] = m, occA[a][yi][b]
							end
						end
					end
				end
				local ok = pcall(function()
					terrain:WriteVoxelChannels(region, 4, {
						SolidMaterial = solidMat,
						SolidOccupancy = solidOcc,
						LiquidOccupancy = liqA,
					})
				end)
				wrote = ok
				if not ok then
					channelsOk = false
				end
			end
			if not wrote then
				local ok, err = pcall(function()
					terrain:WriteVoxels(region, 4, matA, occA)
				end)
				if not ok then
					warn("[PortSolace] terrain slab failed:", err)
				end
			end
			if slabIndex % 50 == 0 then
				self:log(string.format("terrain %d/%d", slabIndex, #slabs))
			end
			task.wait()
		end
	end
	self:log("terrain written")
end

function Builder:carveTerrain()
	local terrain = workspace.Terrain
	local AIR = Enum.Material.Air
	for _, f in ipairs(self.carves) do
		terrain:FillBlock(cf7(f, 2), v3(f, 9), AIR)
		self.stats.carves += 1
		self:tick(4)
	end
end

-- ---------------------------------------------------------------------------------
-- lighting preset (late afternoon -> dusk)

function Builder:applyLighting()
	Lighting.ClockTime = 17.6
	Lighting.GeographicLatitude = 34
	Lighting.Brightness = 2.4
	Lighting.EnvironmentDiffuseScale = 0.6
	Lighting.EnvironmentSpecularScale = 0.5
	Lighting.Ambient = Color3.fromRGB(90, 82, 96)
	Lighting.OutdoorAmbient = Color3.fromRGB(128, 118, 132)
	Lighting.ColorShift_Top = Color3.fromRGB(255, 222, 186)
	Lighting.GlobalShadows = true
	pcall(function()
		Lighting.Technology = Enum.Technology.Future
	end)
	local function ensure(class, name)
		local o = Lighting:FindFirstChild(name)
		if not o then
			o = Instance.new(class)
			o.Name = name
			o.Parent = Lighting
		end
		return o
	end
	local atm = ensure("Atmosphere", "PortSolaceAtmosphere")
	atm.Density = 0.32
	atm.Haze = 1.6
	atm.Color = Color3.fromRGB(214, 186, 160)
	atm.Decay = Color3.fromRGB(120, 96, 110)
	atm.Glare = 0.4
	atm.Offset = 0.1
	local bloom = ensure("BloomEffect", "PortSolaceBloom")
	bloom.Intensity = 0.35
	bloom.Size = 28
	bloom.Threshold = 1.6
	local cc = ensure("ColorCorrectionEffect", "PortSolaceGrade")
	cc.Saturation = 0.05
	cc.Contrast = 0.06
	cc.TintColor = Color3.fromRGB(255, 244, 232)
	local sun = ensure("SunRaysEffect", "PortSolaceSunRays")
	sun.Intensity = 0.06
	sun.Spread = 0.6
end

-- ---------------------------------------------------------------------------------

function Builder:run()
	local opts = self.opts
	local parent = opts.parent or workspace
	if opts.clear then
		local old = parent:FindFirstChild(opts.name)
		if old then
			old:Destroy()
		end
	end
	local root = Instance.new("Folder")
	root.Name = opts.name
	root:SetAttribute("Town", self.Manifest.town or "Port Solace")
	folder(root, "Buildings")
	folder(root, "Infrastructure")
	folder(root, "World")
	root.Parent = parent
	self.root = root

	if opts.streaming then
		pcall(function()
			workspace.StreamingEnabled = true
			workspace.StreamingTargetRadius = 768
			workspace.StreamingMinRadius = 256
		end)
	end
	if opts.lighting then
		self:applyLighting()
	end
	if opts.terrain then
		self:buildTerrain()
	end

	local chunksFolder = self.data:WaitForChild("Chunks")
	local list = {}
	if opts.chunks then
		for _, n in ipairs(opts.chunks) do
			local m = chunksFolder:FindFirstChild(n)
			if m then
				table.insert(list, m)
			end
		end
	else
		list = chunksFolder:GetChildren()
		table.sort(list, function(a, b)
			return a.Name < b.Name
		end)
	end
	for _, mod in ipairs(list) do
		local d = require(mod)
		local chunk = d.name or mod.Name
		if opts.visualParts and opts.structures then
			self:buildParts(chunk, d.parts)
		end
		if opts.colliders then
			self:buildColliders(chunk, d.colliders)
		end
		if opts.props then
			self:buildProps(chunk, d.props)
		end
		if opts.lights then
			self:buildLights(chunk, d.lights)
		end
		if opts.markers then
			self:buildMarkers(chunk, d.markers)
		end
		if opts.signs then
			self:buildSigns(chunk, d.signs)
		end
		if opts.carve and opts.terrain then
			for line in lines(d.carve) do
				table.insert(self.carves, split(line, ","))
			end
		end
		self:log(
			string.format(
				"chunk %s: %d parts, %d props, %d lights so far",
				chunk,
				self.stats.parts,
				self.stats.props,
				self.stats.lights
			)
		)
	end
	if opts.carve and opts.terrain then
		self:carveTerrain()
	end
	for _, t in pairs(self.templates) do
		t:Destroy()
	end
	self.templates = {}
	self:log("done", self.stats.parts, "parts,", self.stats.props, "props,", self.stats.lights, "lights,",
		self.stats.markers, "markers,", self.stats.signs, "signs")
	return root, self.stats
end

-- ---------------------------------------------------------------------------------
-- public API

function TownBuilder.build(options)
	local opts = table.clone(TownBuilder.DEFAULTS)
	for k, v in pairs(options or {}) do
		opts[k] = v
	end
	opts.data = opts.data or script.Parent
	local b = Builder.new(opts)
	return b:run()
end

-- Rebuild only voxel terrain (+ carving) without touching parts.
function TownBuilder.buildTerrain(options)
	local opts = table.clone(TownBuilder.DEFAULTS)
	for k, v in pairs(options or {}) do
		opts[k] = v
	end
	opts.data = opts.data or script.Parent
	-- terrain needs only TerrainData (+ CarveData or the chunk modules), not the kit/palette
	local b = setmetatable({
		opts = opts,
		data = opts.data,
		count = 0,
		carves = {},
		stats = { carves = 0 },
	}, Builder)
	b:buildTerrain()
	if opts.carve then
		local carveData = b.data:FindFirstChild("CarveData")
		if carveData then
			for line in lines(require(carveData)) do
				table.insert(b.carves, split(line, ","))
			end
		else
			for _, mod in ipairs(b.data:WaitForChild("Chunks"):GetChildren()) do
				for line in lines(require(mod).carve) do
					table.insert(b.carves, split(line, ","))
				end
			end
		end
		b:carveTerrain()
	end
	workspace.Terrain:SetAttribute("PortSolaceTerrain", true)
	-- the prebuilt place ships a coarse part-based preview of the ground; real terrain
	-- replaces it
	local town = workspace:FindFirstChild("PortSolace")
	local preview = town and town:FindFirstChild("PreviewGround")
	if preview then
		preview:Destroy()
	end
	if opts.verbose then
		print("[PortSolace] terrain done - save the place (File > Save) to keep it")
	end
	return b.stats
end

-- Apply only the lighting preset.
function TownBuilder.applyLighting()
	Builder.applyLighting(nil)
end

-- Look up a building record (name, archetype, district, entrances ...) by id.
function TownBuilder.building(id, data)
	local M = require((data or script.Parent):WaitForChild("Manifest"))
	return M.buildings[id]
end

return TownBuilder
