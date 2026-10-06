"""Shared dimensions for the Mule (a Hilux-style double-cab pickup).

Units are metres. Axes: +X = the truck's right side, +Y = forward,
+Z = up, ground at Z = 0, origin halfway between the axles.
Exported files are scaled by STUDS_PER_METRE so 1 unit = 1 Roblox stud.

The proportions follow a 2021 Hilux double cab (5.3 m long, 1.86 m wide,
1.81 m tall, 3.085 m wheelbase). At 4.25 studs per metre the cabin fits
seated R15 characters: about 3.7 studs from cushion to head top clears the
headliner, and a 4-stud-wide avatar's outer arm stays inside the side glass
(the two front occupants' inner arms overlap over the console instead,
which is not visible from outside).
"""

STUDS_PER_METRE = 4.25

# Wheels and axles
WHEELBASE = 3.085
Y_FRONT_AXLE = WHEELBASE / 2
Y_REAR_AXLE = -WHEELBASE / 2
TIRE_R = 0.385
TIRE_W = 0.255
RIM_R = 0.216            # 17 inch rim, bead seat radius
AXLE_Z = TIRE_R - 0.005  # a little tyre squash under load
X_WHEEL_F = 0.775        # track 1.55 m
X_WHEEL_R = 0.780

# Overall body extents
Y_NOSE = Y_FRONT_AXLE + 0.905     # front of the bumper
Y_TAIL = Y_REAR_AXLE - 1.290      # back of the rear step bumper
HALF_W = 0.905                    # body side half width (flares go wider)
ROOF_Z = 1.805

# Long-section stations (Y)
Y_HOOD_FRONT = Y_NOSE - 0.045
Y_COWL = 0.87
Y_WS_BASE = 0.835                 # windshield base at the centreline
Z_WS_BASE = 1.240
Y_WS_TOP = 0.055                  # windshield top at the centreline
Z_WS_TOP = 1.770
Y_RW_TOP = -1.035                 # rear window top
Y_RW_BOT = -1.070                 # rear window bottom (at the belt)
Y_CAB_BACK = -1.085
Y_BED_FRONT = -1.125
Y_BED_BACK = -2.775               # tailgate outer skin
Z_BED_FLOOR = 0.820
Z_BED_RAIL = 1.290

# Doors / pillars
Y_DOOR_F_FRONT = 0.805            # front door leading edge (below belt)
Y_B_PILLAR = -0.345               # seam between front and rear doors
Y_DOOR_R_BACK = -1.030            # rear door trailing edge
Z_DOOR_BOTTOM = 0.540
Z_SILL = 0.470                    # bottom of the cab body
Z_BELT_F = 1.290                  # belt line at the front door
Z_BELT_R = 1.305                  # belt line at the rear door


def belt_z(y):
    t = (Y_DOOR_F_FRONT - y) / (Y_DOOR_F_FRONT - Y_DOOR_R_BACK)
    t = min(max(t, 0.0), 1.0) if isinstance(t, float) else t.clip(0, 1)
    return Z_BELT_F + (Z_BELT_R - Z_BELT_F) * t


# Interior / seating (seat cushion tops; R15 characters sit on these)
Z_FLOOR_FRONT = 0.525
Z_FLOOR_REAR = 0.545
SEAT_X = 0.360                    # lateral offset of each seat centre
Z_CUSHION_FRONT = 0.775
Z_CUSHION_REAR = 0.765
Y_FRONT_SEATBACK = -0.270         # front face of the front seat backs (at cushion level)
Y_REAR_SEATBACK = -0.950          # front face of the rear bench back
Z_HEADLINER = 1.745
