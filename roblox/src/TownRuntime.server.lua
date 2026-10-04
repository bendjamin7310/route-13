--[[
	Port Solace - TownRuntime (Script, ServerScriptService)

	Brings the built town to life:
	  * day/night cycle (optional) starting in the late afternoon
	  * light schedules: street lights at dusk, homes in the evening, shops during
	    opening hours, bars and diners late, industry during shifts
	  * openable doors (ProximityPrompt): hinged doors swing away from the player,
	    garage / roll-up doors lift, double and sliding doors slide; locked doors stay
	    shut until something sets their "locked" attribute to false
	  * rotating lighthouse beam at night

	Attributes on this script (all optional):
	  DayCycle (bool, default true)        advance Lighting.ClockTime
	  MinutesPerDay (number, default 24)   real minutes per in-game day
	  StartClock (number, default 17.6)    clock time when the server starts
	  TownName (string, default "PortSolace")
]]

local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local function attr(name, default)
	local v = script:GetAttribute(name)
	if v == nil then
		return default
	end
	return v
end

local DAY_CYCLE = attr("DayCycle", true)
local MINUTES_PER_DAY = attr("MinutesPerDay", 24)
Lighting.ClockTime = attr("StartClock", 17.6)

-- ---------------------------------------------------------------------------------
-- light schedules

local function inRange(t, a, b)
	-- [a, b) on a 24h clock, b may exceed 24
	if b <= 24 then
		return t >= a and t < b
	end
	return t >= a or t < (b - 24)
end

local SCHEDULES = {
	always = function()
		return true
	end,
	dark = function()
		return false
	end,
	night = function(t, s)
		return inRange(t, 17.8 + s * 0.4, 30.3 + s * 0.3)
	end,
	res = function(t, s)
		if s < 0.15 then
			return false -- nobody home
		end
		if inRange(t, 17.2 + s * 1.6, 22.3 + s * 2.6) then
			return true
		end
		return s > 0.6 and inRange(t, 5.8, 7.2)
	end,
	biz = function(t, s)
		return inRange(t, 7.5, 21 + s * 2)
	end,
	late = function(t, s)
		return inRange(t, 11, 26 + s * 2)
	end,
	work = function(t, s)
		return s < 0.3 or inRange(t, 6, 19)
	end,
}

local lights = {}

local function registerLight(anchor)
	local l = anchor:FindFirstChildWhichIsA("Light")
	if l then
		lights[anchor] = {
			light = l,
			fn = SCHEDULES[anchor:GetAttribute("Schedule") or "always"] or SCHEDULES.always,
			seed = anchor:GetAttribute("Seed") or 0.5,
		}
	end
end

for _, a in ipairs(CollectionService:GetTagged("PS_Light")) do
	registerLight(a)
end
CollectionService:GetInstanceAddedSignal("PS_Light"):Connect(registerLight)
CollectionService:GetInstanceRemovedSignal("PS_Light"):Connect(function(a)
	lights[a] = nil
end)

local neonSigns = CollectionService:GetTagged("PS_NeonSign")

local function updateLights()
	local t = Lighting.ClockTime
	for _, rec in pairs(lights) do
		local on = rec.fn(t, rec.seed)
		if rec.light.Enabled ~= on then
			rec.light.Enabled = on
		end
	end
	local dark = inRange(t, 17.5, 30.5)
	for _, s in ipairs(neonSigns) do
		local gui = s:FindFirstChildWhichIsA("SurfaceGui")
		if gui then
			gui.Brightness = dark and 3 or 1.2
		end
	end
end

-- ---------------------------------------------------------------------------------
-- doors

local OPEN_TIME = 0.45

local function leafPart(model)
	local best, vol = nil, -1
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			local v = d.Size.X * d.Size.Y * d.Size.Z
			if v > vol then
				best, vol = d, v
			end
		end
	end
	return best
end

local function tweenPivot(model, target)
	local cv = Instance.new("CFrameValue")
	cv.Value = model:GetPivot()
	cv.Changed:Connect(function(v)
		model:PivotTo(v)
	end)
	local tw = TweenService:Create(cv, TweenInfo.new(OPEN_TIME, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Value = target,
	})
	tw.Completed:Connect(function()
		cv:Destroy()
	end)
	tw:Play()
end

local function hingeTarget(model, closed, player)
	local width = model:GetAttribute("width") or 4
	local hinge = model:GetAttribute("hinge") or -width / 2
	local side = 1
	local char = player and player.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if root then
		local rel = closed:PointToObjectSpace(root.Position)
		side = rel.Z >= 0 and 1 or -1
	end
	local angle = math.rad(88) * side * (hinge < 0 and 1 or -1)
	local h = CFrame.new(hinge, 0, 0)
	return closed * h * CFrame.Angles(0, angle, 0) * h:Inverse()
end

-- Non-hinged doors move individual parts (door-local space: X across, Y up, Z depth):
--   double  - each leaf slides outward into the wall
--   sliding - the moving pane slides over the fixed one
--   garage / rollup - the panel folds up into a band at the top of the opening
local FOLD = 0.12

local function partMoves(model, closed, kind)
	local width = model:GetAttribute("width") or 4
	local height = model:GetAttribute("height") or 7.5
	local moves = {}
	for _, p in ipairs(model:GetDescendants()) do
		if p:IsA("BasePart") then
			local lc = closed:ToObjectSpace(p.CFrame)
			local lp = lc.Position
			local openLocal, openSize = nil, p.Size
			if kind == "double" then
				local dir = lp.X < 0 and -1 or 1
				openLocal = CFrame.new(dir * width * 0.48, 0, 0) * lc
			elseif kind == "sliding" then
				if lp.X > 0 and lp.X < width * 0.45 then
					openLocal = CFrame.new(-width * 0.45, 0, 0.14) * lc
				end
			else -- garage / rollup: fold everything below the housing into the top band
				local bottom = lp.Y - p.Size.Y / 2
				if bottom < height * 0.9 then
					local y = height * (1 - FOLD) + lp.Y * FOLD
					openLocal = CFrame.new(lp.X, y, lp.Z) * lc.Rotation
					openSize = Vector3.new(p.Size.X, math.max(0.05, p.Size.Y * FOLD), p.Size.Z)
				end
			end
			if openLocal then
				table.insert(moves, {
					part = p,
					closedCF = p.CFrame,
					closedSize = p.Size,
					openCF = closed * openLocal,
					openSize = openSize,
				})
			end
		end
	end
	return moves
end

local function tweenParts(moves, opening)
	local nv = Instance.new("NumberValue")
	nv.Value = opening and 0 or 1
	nv.Changed:Connect(function(a)
		for _, m in ipairs(moves) do
			m.part.CFrame = m.closedCF:Lerp(m.openCF, a)
			m.part.Size = m.closedSize:Lerp(m.openSize, a)
		end
	end)
	local tw = TweenService:Create(nv, TweenInfo.new(OPEN_TIME, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Value = opening and 1 or 0,
	})
	tw.Completed:Connect(function()
		nv:Destroy()
	end)
	tw:Play()
end

local function setupDoor(model)
	if not model:IsA("Model") or model:GetAttribute("PS_DoorReady") then
		return
	end
	local leaf = leafPart(model)
	if not leaf then
		return
	end
	model:SetAttribute("PS_DoorReady", true)
	local closed = model:GetAttribute("ClosedPivot") or model:GetPivot()
	local kind = model:GetAttribute("DoorKind") or "hinged"
	local moves = nil
	if kind ~= "hinged" then
		moves = partMoves(model, closed, kind)
	end
	local att = Instance.new("Attachment")
	att.Name = "DoorPrompt"
	att.Parent = leaf
	local prompt = Instance.new("ProximityPrompt")
	prompt.ObjectText = model:GetAttribute("Interior") and "Door" or "Entrance"
	prompt.ActionText = "Open"
	prompt.MaxActivationDistance = 8
	prompt.RequiresLineOfSight = false
	prompt.HoldDuration = 0
	prompt.Style = Enum.ProximityPromptStyle.Default
	prompt.Parent = att
	local open = false
	local busy = false
	local function refresh()
		if model:GetAttribute("locked") and not open then
			prompt.ActionText = "Locked"
		else
			prompt.ActionText = open and "Close" or "Open"
		end
	end
	refresh()
	model:GetAttributeChangedSignal("locked"):Connect(refresh)
	prompt.Triggered:Connect(function(player)
		if busy then
			return
		end
		if model:GetAttribute("locked") and not open then
			model:SetAttribute("LastLockedAttempt", player and player.UserId or 0)
			return
		end
		busy = true
		open = not open
		if moves then
			tweenParts(moves, open)
		elseif open then
			tweenPivot(model, hingeTarget(model, closed, player))
		else
			tweenPivot(model, closed)
		end
		refresh()
		task.delay(OPEN_TIME, function()
			busy = false
		end)
	end)
end

for _, d in ipairs(CollectionService:GetTagged("PS_Door")) do
	setupDoor(d)
end
CollectionService:GetInstanceAddedSignal("PS_Door"):Connect(setupDoor)

-- ---------------------------------------------------------------------------------
-- lighthouse beam

local beams = {}

local function setupBeam(marker)
	local rpm = marker:GetAttribute("rpm") or 4
	for anchor in pairs(lights) do
		if (anchor.Position - marker.Position).Magnitude < 4 then
			local a0 = Instance.new("Attachment")
			a0.Parent = anchor
			local a1 = Instance.new("Attachment")
			a1.Position = Vector3.new(0, 0, -260)
			a1.Parent = anchor
			local beam = Instance.new("Beam")
			beam.Attachment0 = a0
			beam.Attachment1 = a1
			beam.Width0 = 3
			beam.Width1 = 46
			beam.FaceCamera = true
			beam.LightEmission = 1
			beam.LightInfluence = 0
			beam.Color = ColorSequence.new(Color3.fromRGB(255, 236, 196))
			beam.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 0.55),
				NumberSequenceKeypoint.new(1, 1),
			})
			beam.Segments = 2
			beam.Parent = anchor
			table.insert(beams, {
				anchor = anchor,
				beam = beam,
				pos = anchor.Position,
				tilt = math.rad(-4),
				speed = rpm * 2 * math.pi / 60,
				angle = 0,
			})
		end
	end
end

-- ---------------------------------------------------------------------------------
-- main loop

task.defer(function()
	for _, m in ipairs(CollectionService:GetTagged("PS_Marker_lighthouse_beam")) do
		setupBeam(m)
	end
end)

local acc = 0
RunService.Heartbeat:Connect(function(dt)
	if DAY_CYCLE and MINUTES_PER_DAY > 0 then
		Lighting.ClockTime = (Lighting.ClockTime + dt * 24 / (MINUTES_PER_DAY * 60)) % 24
	end
	for _, b in ipairs(beams) do
		b.angle = (b.angle + dt * b.speed) % (2 * math.pi)
		b.anchor.CFrame = CFrame.new(b.pos) * CFrame.Angles(0, b.angle, 0) * CFrame.Angles(b.tilt, 0, 0)
		local rec = lights[b.anchor]
		b.beam.Enabled = rec ~= nil and rec.light.Enabled
	end
	acc += dt
	if acc >= 2 then
		acc = 0
		updateLights()
	end
end)

updateLights()
