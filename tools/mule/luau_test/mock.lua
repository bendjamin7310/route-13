-- Minimal stand-ins for the Roblox APIs MuleSetup touches, so the generated
-- module can be executed outside Studio (see run.mjs). Only what the module
-- uses is implemented; rotation in CFrame is ignored.

local V3mt = {}
V3mt.__index = function(t, k)
	if k == "Magnitude" then
		return math.sqrt(t.X * t.X + t.Y * t.Y + t.Z * t.Z)
	end
	return nil
end
V3mt.__add = function(a, b)
	return Vector3.new(a.X + b.X, a.Y + b.Y, a.Z + b.Z)
end
Vector3 = {}
function Vector3.new(x, y, z)
	return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0 }, V3mt)
end

local CFmt = {}
CFmt.__mul = function(a, b)
	return CFrame.new(a.Position + b.Position)
end
CFrame = {}
function CFrame.new(x, y, z)
	if type(x) == "table" then
		return setmetatable({ Position = x }, CFmt)
	end
	return setmetatable({ Position = Vector3.new(x, y, z) }, CFmt)
end

Color3 = {}
function Color3.fromRGB(r, g, b)
	assert(type(r) == "number" and type(g) == "number" and type(b) == "number", "Color3.fromRGB expects numbers")
	return { R = r / 255, G = g / 255, B = b / 255 }
end

Enum = setmetatable({}, {
	__index = function(_, enumName)
		return setmetatable({}, {
			__index = function(_, item)
				return { Name = item, EnumType = enumName }
			end,
		})
	end,
})

local BASEPART = { Part = true, MeshPart = true, Seat = true, VehicleSeat = true }
local PROPS = {
	BasePart = {
		Size = function() return Vector3.new(1, 1, 1) end,
		CFrame = function() return CFrame.new(0, 0, 0) end,
		Transparency = 0, Reflectance = 0, CanCollide = true, CanTouch = true, CanQuery = true,
		Massless = false, CastShadow = true, Anchored = false,
		CollisionFidelity = function() return Enum.CollisionFidelity.Default end,
		Material = function() return Enum.Material.Plastic end,
		Color = function() return Color3.fromRGB(163, 162, 165) end,
	},
	Model = { PrimaryPart = false },
	WeldConstraint = { Part0 = false, Part1 = false },
	SurfaceAppearance = { ColorMap = "", RoughnessMap = "" },
	SpotLight = { Enabled = true, Face = false, Angle = 90, Range = 16, Brightness = 1, Color = false },
	PointLight = { Enabled = true, Range = 8, Brightness = 1, Color = false },
	Folder = {},
}

local Inst = {}
Inst.__index = function(self, k)
	local raw = rawget(self, "_props")
	if k == "Parent" then
		return raw.Parent
	end
	if raw[k] ~= nil then
		return raw[k]
	end
	if Inst[k] then
		return Inst[k]
	end
	error("mock: unknown member '" .. tostring(k) .. "' on " .. raw.ClassName, 2)
end
Inst.__newindex = function(self, k, v)
	local raw = rawget(self, "_props")
	if k == "Parent" then
		local old = raw.Parent
		if old then
			local kids = rawget(old, "_children")
			for i, c in ipairs(kids) do
				if c == self then
					table.remove(kids, i)
					break
				end
			end
		end
		raw.Parent = v
		if v then
			table.insert(rawget(v, "_children"), self)
		end
		return
	end
	if raw[k] == nil and k ~= "Name" then
		error("mock: cannot set unknown property '" .. tostring(k) .. "' on " .. raw.ClassName, 2)
	end
	raw[k] = v
end

Instance = {}
function Instance.new(className)
	local props = { ClassName = className, Name = className, Parent = false }
	local defaults = BASEPART[className] and PROPS.BasePart or PROPS[className]
	if defaults == nil then
		error("mock: Instance.new does not know " .. className)
	end
	for k, v in pairs(defaults) do
		props[k] = type(v) == "function" and v() or v
	end
	props.Parent = nil
	local self = setmetatable({ _props = props, _children = {}, _attrs = {} }, Inst)
	return self
end

function Inst:IsA(c)
	if c == "BasePart" then
		return BASEPART[self.ClassName] == true
	end
	return self.ClassName == c
end
function Inst:GetChildren()
	local out = {}
	for i, c in ipairs(rawget(self, "_children")) do
		out[i] = c
	end
	return out
end
function Inst:GetDescendants()
	local out = {}
	local function walk(n)
		for _, c in ipairs(rawget(n, "_children")) do
			table.insert(out, c)
			walk(c)
		end
	end
	walk(self)
	return out
end
function Inst:FindFirstChild(name, recursive)
	for _, c in ipairs(rawget(self, "_children")) do
		if c.Name == name then
			return c
		end
	end
	if recursive then
		for _, c in ipairs(rawget(self, "_children")) do
			local f = c:FindFirstChild(name, true)
			if f then
				return f
			end
		end
	end
	return nil
end
function Inst:FindFirstChildOfClass(cls)
	for _, c in ipairs(rawget(self, "_children")) do
		if c.ClassName == cls then
			return c
		end
	end
	return nil
end
function Inst:Destroy()
	self.Parent = nil
end
function Inst:SetAttribute(k, v)
	rawget(self, "_attrs")[k] = v
end
function Inst:GetAttribute(k)
	return rawget(self, "_attrs")[k]
end
function Inst:GetFullName()
	local p = rawget(self, "_props")
	if p.Parent then
		return p.Parent:GetFullName() .. "." .. p.Name
	end
	return p.Name
end
