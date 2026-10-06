-- Exercises the generated MuleSetup module against a fake imported model
-- built from mule_manifest.json (PARTS is injected by run.mjs).

local model = Instance.new("Model")
model.Name = "Mule"
local groups = {}
local function group(name)
	if name == "" or name == "Mule" then
		return model
	end
	if groups[name] == nil then
		local g = Instance.new("Model")
		g.Name = name
		if string.sub(name, 1, 6) == "Wheel_" then
			g.Parent = group("Wheels")
		else
			g.Parent = model
		end
		groups[name] = g
	end
	return groups[name]
end

for _, p in ipairs(PARTS) do
	local part = Instance.new("MeshPart")
	part.Name = p.name
	part.Size = Vector3.new(p.size[1], p.size[2], p.size[3])
	part.CFrame = CFrame.new(p.pos[1], p.pos[2], p.pos[3])
	part.Parent = group(p.group)
end

local function count(cls)
	local n = 0
	for _, d in ipairs(model:GetDescendants()) do
		if d.ClassName == cls then
			n += 1
		end
	end
	return n
end

local function check()
	assert(count("VehicleSeat") == 1, "expected one VehicleSeat, got " .. count("VehicleSeat"))
	assert(count("Seat") == 3, "expected three Seats, got " .. count("Seat"))
	assert(model:FindFirstChild("SeatAnchor_Driver", true) == nil, "anchors should be replaced")
	local colliders = model:FindFirstChild("Colliders")
	assert(colliders and #colliders:GetChildren() == #MuleSetup.Colliders, "collider count")
	local parts, welds = 0, 0
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and d.Name ~= "MuleRoot" then
			parts += 1
			if d:FindFirstChild("MuleWeld") then
				welds += 1
			end
		end
	end
	assert(parts == welds, ("every part welded (%d parts, %d welds)"):format(parts, welds))
	assert(model.PrimaryPart == model:FindFirstChild("MuleRoot", true), "PrimaryPart")
	assert(model:FindFirstChild("Plate_Front", true).Transparency == 1, "front plate hidden")
	assert(model:FindFirstChild("Body_Cab", true).Material.Name == "SmoothPlastic", "paint material")
	assert(model:FindFirstChild("Glass_Windshield", true).Transparency > 0, "glass transparent")
	return parts
end

MuleSetup.StudioPrep(model)
assert(model:FindFirstChild("Body_Cab", true).CollisionFidelity.Name == "Box", "box collision")
MuleSetup.Setup(model)
local parts = check()
MuleSetup.Setup(model)       -- idempotent
check()
MuleSetup.SetLights(model, { Head = true, Brake = true })
assert(model:FindFirstChild("Headlight_DRL_L", true).Material.Name == "Neon", "DRL on")
assert(model:FindFirstChild("Headlight_Lens_R", true):FindFirstChild("MuleLight").Enabled == true, "headlight spot on")
assert(model:FindFirstChild("TailLight_Reverse_L", true).Material.Name ~= "Neon", "reverse off")
MuleSetup.SetLights(model, {})
assert(model:FindFirstChild("Headlight_Lens_R", true):FindFirstChild("MuleLight").Enabled == false, "headlight spot off")
MuleSetup.SetFrontPlate(model, true)
assert(model:FindFirstChild("Plate_Front", true).Transparency == 0, "front plate shown")
print(("MuleSetup OK: %d parts, %d colliders, 4 seats"):format(parts, #MuleSetup.Colliders))
