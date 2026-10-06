"""Seat anchors: invisible marker boxes where Roblox Seat parts go.

Each anchor's top face sits on the seat cushion and its centre is where a
seated R15 character's HumanoidRootPart lines up (over the hips). The Luau
setup module turns them into a VehicleSeat (driver) and Seats.
"""

import bpy
import numpy as np

import materials
from dims import *  # noqa: F401,F403

# name: (x, y, cushion top z). Driver sits on the left (left-hand drive).
# R15 torso is 1 stud deep; its centre sits half a stud ahead of the seat back.
_HALF_TORSO = 0.5 / STUDS_PER_METRE
ANCHORS = {
    "SeatAnchor_Driver": (-SEAT_X, Y_FRONT_SEATBACK + _HALF_TORSO, Z_CUSHION_FRONT),
    "SeatAnchor_Passenger": (SEAT_X, Y_FRONT_SEATBACK + _HALF_TORSO, Z_CUSHION_FRONT),
    "SeatAnchor_RearLeft": (-SEAT_X, Y_REAR_SEATBACK + _HALF_TORSO, Z_CUSHION_REAR),
    "SeatAnchor_RearRight": (SEAT_X, Y_REAR_SEATBACK + _HALF_TORSO, Z_CUSHION_REAR),
}
SIZE = (0.40, 0.40, 0.05)   # metres: 1.7 x 1.7 x 0.2 studs


def _box(sx, sy, sz):
    v = np.array([(x * sx / 2, y * sy / 2, z * sz / 2) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=np.float32)
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return v, f


def make_anchors(group):
    objs = []
    v, f = _box(*SIZE)
    for name, (x, y, ztop) in ANCHORS.items():
        me = bpy.data.meshes.new(name)
        me.from_pydata(v.tolist(), [], f)
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (x, y, ztop - SIZE[2] / 2)
        me.materials.append(materials.get("Anchor"))
        ob["mule_material"] = "Anchor"
        ob.parent = group
        objs.append(ob)
    # MuleRoot: reference/PrimaryPart at the centre between the axles, axle height
    v, f = _box(0.25, 0.25, 0.25)
    me = bpy.data.meshes.new("MuleRoot")
    me.from_pydata(v.tolist(), [], f)
    me.update()
    ob = bpy.data.objects.new("MuleRoot", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0.0, 0.0, AXLE_Z)
    me.materials.append(materials.get("Anchor"))
    ob["mule_material"] = "Anchor"
    ob.parent = group.parent
    objs.append(ob)
    return objs
