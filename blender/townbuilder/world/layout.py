"""The map of Port Solace: coastline, harbour, creek, rail line, districts, road network
and the fixed landmark placements.

Units are studs, Blender axes (+X east, +Y north).  The map spans 2560 x 2560 studs
centred on the origin.  The sea wraps the east side and the south-east; Solace Creek
runs from the north-west hills to the harbour; Route 13 arrives from the desert to the
west, runs through the motel strip and the commercial strip and becomes Harbor Boulevard
at the edge of downtown.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TOWN_NAME = "Port Solace"
HALF = 1280.0
CHUNK = 512.0

# --------------------------------------------------------------------------- water

# Sea polygon (land is everything outside it).  Clockwise from the north-east corner.
SEA = [
    (1280, 1280), (1120, 1280), (1100, 1150), (1120, 1000), (1090, 850), (1060, 700),
    (1040, 560), (1010, 420), (960, 300), (915, 205),
    # harbour: north shore, west shore (marina), Lighthouse Point
    (870, 120), (830, 60), (790, -20), (750, -100), (720, -170), (700, -250), (690, -330),
    (695, -420), (725, -515), (760, -600), (820, -655), (900, -695), (965, -725),
    (995, -765), (970, -805), (900, -822), (820, -815), (730, -818),
    # south beach running west-south-west
    (620, -840), (480, -878), (330, -920), (170, -962), (0, -1000), (-180, -1040),
    (-380, -1086), (-600, -1136), (-820, -1188), (-1040, -1240), (-1160, -1280),
    (1280, -1280),
]

# Solace Creek, mouth first.  (x, y, half-width)
CREEK = [
    (930, 140, 26), (860, 150, 24), (780, 172, 22), (690, 206, 21), (590, 244, 20),
    (480, 292, 19), (370, 350, 18), (262, 420, 17), (160, 500, 16), (60, 578, 15),
    (-40, 660, 14), (-130, 760, 13), (-210, 880, 12), (-280, 1010, 11), (-340, 1140, 10),
    (-380, 1300, 10),
]

# --------------------------------------------------------------------------- rail

RAIL = [(-1300, 470), (-900, 488), (-600, 508), (-300, 528), (-100, 546), (60, 580),
        (200, 618), (400, 648), (650, 660), (800, 648), (880, 636)]
RAIL_HEIGHT = 14.0          # embankment height above the town surface
RAIL_YARD = [(350, 604), (580, 610)]   # parallel sidings between Kiln St and Cannery Row

# --------------------------------------------------------------------------- terrain bumps

# (x, y, radius, height): smooth macro elevation features
HILLS = [
    (-860, 960, 380, 72.0),     # Water Tower Hill
    (-1150, 650, 300, 40.0),    # west ridge
    (-500, 1200, 420, 46.0),    # north woods
    (300, 1150, 360, 34.0),     # north fields rise
    (920, 1020, 240, 52.0),     # Corrigan Bluff (estate)
    (-1100, -150, 300, 22.0),   # western rolling hills
    (-420, 260, 260, 7.0),      # low rise under the old neighbourhood
    (520, 760, 300, 10.0),      # industrial plateau
]

# --------------------------------------------------------------------------- districts

DISTRICTS = {
    # name: polygon (checked in order)
    "WATERFRONT": [(560, -210), (700, -150), (760, -600), (1000, -780), (700, -860),
                   (520, -790), (540, -470)],
    "CIVIC": [(410, -230), (560, -210), (700, -150), (760, 20), (700, 170), (470, 240),
              (360, 120), (380, -60)],
    "DOWNTOWN": [(-80, -360), (420, -290), (380, 120), (360, 140), (-120, 90)],
    "MIXED_USE": [(-500, -380), (-80, -360), (-120, 90), (-130, 170), (-520, 170)],
    "INDUSTRIAL": [(110, 610), (300, 410), (520, 290), (760, 190), (930, 160), (1060, 560),
                   (1100, 900), (700, 960), (300, 900), (120, 760)],
    "LOW_INCOME": [(-640, 170), (-130, 170), (360, 150), (300, 400), (110, 560),
                   (-640, 520)],
    "COMMERCIAL": [(-760, -720), (420, -680), (520, -500), (450, -330), (-80, -360),
                   (-500, -380), (-760, -360)],
    "MOTEL": [(-1260, -740), (-760, -720), (-760, -360), (-1260, -380)],
    "RESIDENTIAL": [(-1080, -380), (-500, -380), (-520, 170), (-640, 170), (-640, 520),
                    (-1080, 520)],
    "RESIDENTIAL_N": [(-780, 560), (110, 610), (120, 760), (300, 900), (240, 1080),
                      (-760, 1080)],
}

# district -> exterior collection name
DISTRICT_COLLECTION = {
    "WATERFRONT": "WATERFRONT", "CIVIC": "CIVIC", "DOWNTOWN": "DOWNTOWN",
    "MIXED_USE": "MIXED_USE", "INDUSTRIAL": "INDUSTRIAL", "LOW_INCOME": "LOW_INCOME",
    "COMMERCIAL": "COMMERCIAL", "MOTEL": "MOTEL", "RESIDENTIAL": "RESIDENTIAL",
    "RESIDENTIAL_N": "RESIDENTIAL", "OUTSKIRTS": "OUTSKIRTS", "BEACH": "PARKS",
}

# --------------------------------------------------------------------------- roads


@dataclass
class RoadDef:
    name: str
    kind: str                    # major arterial street residential alley service rural dirt
    pts: list
    frontage: str = "both"       # both | left | right | none  (lot placement)
    smooth: bool = True
    markings: bool = True
    lights: bool = True
    tags: set = field(default_factory=set)


ROAD_SPECS = {
    # kind: (carriageway width, sidewalk width, surface, lane marking style)
    "major": (52.0, 8.0, "asphalt", "double_yellow_4lane"),
    "arterial": (36.0, 7.0, "asphalt", "double_yellow"),
    "street": (32.0, 10.0, "asphalt", "dashed_yellow"),
    "residential": (24.0, 6.0, "asphalt", "none"),
    "alley": (14.0, 0.0, "asphalt_old", "none"),
    "service": (30.0, 0.0, "asphalt_old", "dashed_yellow"),
    "rural": (24.0, 0.0, "asphalt_old", "dashed_yellow"),
    "dirt": (18.0, 0.0, "gravel", "none"),
    "lot": (24.0, 0.0, "asphalt", "none"),
}

# Downtown runs on a grid rotated 8 degrees around this centre
DT_CENTER = (170.0, -100.0)
DT_ROT = math.radians(8.0)


def dt(u, v):
    """Downtown grid (u east-ish, v north-ish) to world coordinates."""
    c, s = math.cos(DT_ROT), math.sin(DT_ROT)
    return (DT_CENTER[0] + u * c - v * s, DT_CENTER[1] + u * s + v * c)


def dts(*uv):
    return [dt(u, v) for (u, v) in uv]


AVE_U = [-210.0, -70.0, 70.0, 210.0]       # downtown avenues (N-S)
ST_V = [-230.0, -50.0, 130.0]               # downtown streets (E-W)
ALLEY_V = [-140.0, 40.0]                    # mid-block alleys

ROADS: list[RoadDef] = [
    # ---- arterials ---------------------------------------------------------------
    RoadDef("Route 13", "major", [(-1300, -520), (-1100, -536), (-900, -540), (-760, -522),
                                  (-560, -500), (-300, -478), (-60, -462), (140, -452),
                                  (270, -432)], tags={"route13"}),
    RoadDef("Harbor Boulevard", "major", [(270, -432), (380, -378), (480, -322), (566, -282),
                                          (612, -262)], tags={"route13"}),
    RoadDef("Bayshore Drive", "arterial",
            [(-1180, -1120), (-900, -1060), (-600, -1000), (-300, -940), (0, -880),
             (260, -828), (470, -776), (580, -730), (604, -650), (600, -540), (592, -430),
             (594, -330), (612, -262), (640, -170), (668, -80), (708, 10), (760, 100),
             (812, 172), (858, 240), (888, 340), (896, 450), (904, 580), (918, 720),
             (950, 860), (978, 960), (1006, 1080), (1040, 1300)], tags={"coastal"}),
    RoadDef("Founders Avenue", "arterial",
            [(-130, 1300), (-120, 1120), (-100, 960), (-80, 820), (-62, 690), (-58, 600),
             (-60, 520), (-62, 420), (-58, 300), (-50, 200), dt(AVE_U[0], ST_V[-1] + 70),
             dt(AVE_U[0], ST_V[-1]), dt(AVE_U[0], ST_V[1]), dt(AVE_U[0], ST_V[0]),
             (-62, -462), (-58, -560), (-40, -700), (-10, -840), (0, -880)],
            tags={"avenue"}),
    RoadDef("Mill Street", "arterial",
            [(-640, 300), (-420, 296), (-200, 300), (-58, 300), (100, 312), (240, 330),
             (400, 336), (560, 340), (720, 360), (906, 400)]),
    RoadDef("Palisade Road", "arterial",
            [(-640, -500), (-660, -360), (-690, -180), (-700, 0), (-690, 160), (-680, 300),
             (-676, 420), (-672, 520), (-660, 640), (-640, 760), (-680, 880), (-760, 960),
             (-860, 1040), (-960, 1140), (-1060, 1300)]),
    RoadDef("Ridge Road", "arterial",
            [(-660, 760), (-480, 820), (-300, 860), (-210, 878), (-80, 900), (60, 900),
             (200, 880), (360, 860), (520, 880), (700, 900), (860, 920), (978, 960)]),
    # ---- downtown grid -----------------------------------------------------------
    RoadDef("Cannery Avenue", "street", dts((AVE_U[1], ST_V[0] - 60), (AVE_U[1], ST_V[2] + 30))
            + [(130, 300)], tags={"avenue"}),
    RoadDef("Lighthouse Avenue", "street", dts((AVE_U[2], ST_V[0] - 40),
                                                 (AVE_U[2], ST_V[2] + 20)) + [(250, 330)],
            tags={"avenue"}),
    RoadDef("Pier Street", "street", dts((AVE_U[3], ST_V[0] - 70), (AVE_U[3], ST_V[2] + 60)),
            tags={"avenue"}),
    RoadDef("Front Street", "street", dts((AVE_U[0] - 300, ST_V[0] + 6), (AVE_U[0], ST_V[0]),
                                          (AVE_U[3], ST_V[0])), frontage="left"),
    RoadDef("Market Street", "street", dts((AVE_U[0] - 420, ST_V[1] - 6), (AVE_U[0], ST_V[1]),
                                           (AVE_U[3], ST_V[1]))),
    RoadDef("Bell Street", "street", dts((AVE_U[0] - 400, ST_V[2] + 10), (AVE_U[0], ST_V[2]),
                                         (AVE_U[3], ST_V[2]))),
    # mid-block alleys (rear service access for downtown and mixed-use shops); whole blocks
    # are left without an alley for the parking structure and the office tower
    RoadDef("Fishmonger Alley", "alley", dts((AVE_U[0] - 300, ALLEY_V[0]),
                                             (AVE_U[1], ALLEY_V[0])), frontage="none",
            markings=False, lights=False),
    RoadDef("Chandler Alley", "alley", dts((AVE_U[2], ALLEY_V[0]), (AVE_U[3], ALLEY_V[0])),
            frontage="none", markings=False, lights=False),
    RoadDef("Net Loft Alley", "alley", dts((AVE_U[0] - 300, ALLEY_V[1]), (AVE_U[1], ALLEY_V[1])),
            frontage="none", markings=False, lights=False),
    # ---- mixed-use / old town grid west of downtown ---------------------------------
    RoadDef("Elm Street", "street", dts((AVE_U[0] - 140, ST_V[0] - 50), (AVE_U[0] - 140, ST_V[2]))
            + [(-180, 300), (-176, 400), (-172, 497)]),
    RoadDef("Oak Street", "street", dts((AVE_U[0] - 290, ST_V[0] - 60), (AVE_U[0] - 290, ST_V[2]))
            + [(-330, 300), (-326, 396), (-322, 490)]),
    RoadDef("Pine Street", "residential", [(-470, -340), (-480, -150), (-484, 40), (-490, 180),
                                           (-480, 300), (-478, 392), (-480, 480)]),
    # ---- low-income neighbourhood ----------------------------------------------------
    RoadDef("Railroad Avenue", "residential", [(-640, 470), (-480, 480), (-320, 490),
                                               (-170, 498), (-62, 505)], frontage="right"),
    RoadDef("Fisher Street", "residential", [(-640, 390), (-480, 392), (-330, 396),
                                             (-176, 400), (-62, 404), (60, 410), (150, 440)]),
    RoadDef("Tannery Lane", "residential", [(-62, 226), (40, 230), (160, 240), (300, 250),
                                            (380, 200)]),
    RoadDef("Gull Court", "residential", [(40, 230), (60, 300), (64, 380), (40, 404)]),
    # ---- west suburbs -----------------------------------------------------------------
    RoadDef("Maple Drive", "residential", [(-690, -250), (-800, -250), (-900, -230),
                                           (-980, -180), (-1010, -80), (-990, 30)]),
    RoadDef("Harbor View Circle", "residential", [(-700, -40), (-800, -50), (-880, 0),
                                                  (-900, 90), (-860, 170), (-780, 190),
                                                  (-695, 170)]),
    RoadDef("Sunset Lane", "residential", [(-690, 260), (-800, 270), (-920, 290),
                                           (-1010, 320), (-1040, 400)]),
    RoadDef("Juniper Way", "residential", [(-640, -380), (-760, -380), (-880, -370),
                                           (-960, -340)]),
    RoadDef("Seaview Terrace", "residential", [(-470, -200), (-560, -200), (-660, -190)],
            frontage="both"),
    RoadDef("Cypress Court", "residential", [(-484, 60), (-560, 70), (-640, 64)]),
    # ---- north suburbs (across the creek) -----------------------------------------------
    RoadDef("Northgate Avenue", "residential", [(-80, 900), (-90, 980), (-100, 1060)]),
    RoadDef("Heron Loop", "residential", [(-400, 840), (-420, 940), (-340, 1000),
                                          (-260, 960), (-250, 900)]),
    RoadDef("Alder Street", "residential", [(-640, 760), (-560, 700), (-440, 660),
                                            (-300, 640), (-160, 636), (-62, 640)]),
    RoadDef("Birch Lane", "residential", [(-440, 660), (-450, 760), (-480, 820)]),
    RoadDef("Wren Court", "residential", [(-160, 636), (-170, 720), (-200, 800)]),
    RoadDef("Orchard Road", "residential", [(60, 900), (80, 1000), (40, 1100), (-100, 1160)]),
    # ---- industrial -------------------------------------------------------------------
    RoadDef("Foundry Road", "service", [(260, 470), (420, 470), (580, 480), (740, 500),
                                        (930, 500)]),
    RoadDef("Cannery Row", "service", [(560, 340), (590, 470), (610, 600), (620, 700),
                                       (630, 860), (640, 892)]),
    RoadDef("Depot Street", "service", [(200, 780), (360, 790), (520, 800), (700, 800),
                                        (962, 790)]),
    RoadDef("Kiln Street", "service", [(300, 470), (300, 560), (300, 690), (300, 790),
                                       (310, 870)]),
    # ---- commercial strip -----------------------------------------------------------
    RoadDef("Commerce Way", "arterial", [(-300, -478), (-310, -600), (-260, -700),
                                         (-100, -760), (100, -760), (240, -700),
                                         (300, -600), (300, -460)]),
    RoadDef("Tidewater Avenue", "street", [(140, -452), (150, -560), (180, -680),
                                           (200, -760), (260, -828)]),
    # ---- motel strip / west entrance -----------------------------------------------------
    RoadDef("Dusty Mile Road", "rural", [(-900, -540), (-920, -420), (-940, -300),
                                         (-960, -200)]),
    RoadDef("Old Mission Road", "rural", [(-1100, -536), (-1120, -680), (-1100, -820),
                                          (-1000, -960), (-900, -1090)]),
    # ---- waterfront ------------------------------------------------------------------
    RoadDef("Point Road", "rural", [(612, -650), (700, -690), (800, -716), (880, -740),
                                    (930, -760)], frontage="none"),
    # ---- civic --------------------------------------------------------------------------
    RoadDef("Civic Center Drive", "street", [dt(AVE_U[3], ST_V[2]), (440, 52), (540, 40),
                                             (640, 28), (708, 10)]),
    # ---- outskirts ------------------------------------------------------------------------
    RoadDef("Quarry Road", "rural", [(-760, 960), (-820, 900), (-860, 860), (-880, 800)],
            frontage="right"),
    RoadDef("Old County Road", "rural", [(-1300, 220), (-1150, 230), (-1010, 320)]),
    RoadDef("Farm Lane", "dirt", [(-1150, 230), (-1180, 420), (-1150, 600), (-1100, 760)]),
    RoadDef("Bluff Road", "rural", [(978, 960), (930, 1020), (880, 1060), (840, 1060)],
            frontage="none"),
    RoadDef("Creekside Trail", "dirt", [(-180, 900), (-210, 1000), (-266, 1120),
                                        (-300, 1240)], frontage="none"),
    RoadDef("Lookout Road", "rural", [(-130, 1120), (100, 1150), (300, 1180), (500, 1160),
                                      (700, 1120), (840, 1060)]),
]

# --------------------------------------------------------------------------- fixed sites

# Landmark / key building placements. Either on a road frontage (road, t=fraction along
# the road, side) or absolute (x, y, yaw).  Placed before the procedural fill.
SITES = [
    # civic centre: town hall faces the police and fire stations across Civic Center Drive
    dict(arch="town_hall", road="Civic Center Drive", near=(520, 40), side="right", w=104,
         d=78, district="CIVIC"),
    dict(arch="police_station", road="Civic Center Drive", near=(612, 30), side="left", w=100,
         d=112, district="CIVIC"),
    dict(arch="fire_station", road="Civic Center Drive", near=(470, 46), side="left", w=80,
         d=92, district="CIVIC"),
    dict(arch="office_tower", road="Bell Street", near=dt(140, ST_V[2]), side="right", w=70,
         d=62, district="DOWNTOWN", opts={"floors": 7}, name="Harbor Trust Building"),
    dict(arch="parking_structure", road="Market Street", near=dt(0, ST_V[1]), side="right",
         w=76, d=80, district="DOWNTOWN"),
    dict(arch="supermarket", road="Route 13", near=(-470, -490), side="right", w=136, d=104,
         district="COMMERCIAL"),
    dict(arch="car_dealership", road="Route 13", near=(-150, -470), side="right", w=86, d=70,
         district="COMMERCIAL"),
    dict(arch="motel", road="Route 13", near=(-960, -540), side="right", w=158, d=112,
         district="MOTEL"),
    dict(arch="diner", road="Route 13", near=(-820, -530), side="left", w=56, d=52,
         district="MOTEL", name="The Blue Marlin", opts={"marlin": True}),
    dict(arch="gas_station", road="Route 13", near=(-1140, -536), side="left", w=52, d=46,
         district="MOTEL"),
    dict(arch="factory", road="Foundry Road", near=(450, 470), side="left", w=120, d=100,
         district="INDUSTRIAL", name="Solace Cannery", setback=22),
    dict(arch="storage_facility", road="Foundry Road", near=(760, 500), side="right", w=126,
         d=64, district="INDUSTRIAL", setback=16),
    dict(arch="warehouse", road="Depot Street", near=(420, 790), side="right", w=112, d=72,
         district="INDUSTRIAL", name="Bayline Logistics", setback=22),
    dict(arch="warehouse", road="Foundry Road", near=(660, 488), side="left", w=96, d=70,
         district="INDUSTRIAL", name="Coastal Freight Co.", setback=20),
    dict(arch="fish_warehouse", road="Bayshore Drive", near=(900, 560), side="right", w=96,
         d=74, district="WATERFRONT", setback=16),
    dict(arch="marina_office", road="Bayshore Drive", near=(596, -460), side="right", w=44,
         d=36, district="WATERFRONT", setback=8),
    dict(arch="boat_storage", road="Bayshore Drive", near=(600, -560), side="left", w=80,
         d=66, district="WATERFRONT"),
    dict(arch="waterfront_restaurant", road="Bayshore Drive", near=(200, -842), side="right",
         w=58, d=50, district="WATERFRONT", setback=6),
    dict(arch="lighthouse", x=936.0, y=-788.0, yaw=math.radians(-110), district="WATERFRONT"),
    dict(arch="water_tower", road="Quarry Road", near=(-850, 880), side="left",
         district="OUTSKIRTS"),
    dict(arch="mansion", x=868.0, y=1078.0, yaw=math.radians(160), w=78, d=64,
         district="OUTSKIRTS", name="Corrigan Estate"),
]

# Parks and open spaces (polygons) dressed with lawn, trees, paths and benches.
PARKS = {
    "Town Square": dts((AVE_U[1] + 26, ST_V[1] + 26), (AVE_U[2] - 26, ST_V[1] + 26),
                       (AVE_U[2] - 26, ST_V[2] - 26), (AVE_U[1] + 26, ST_V[2] - 26)),
    "Riverside Park": [(300, 452), (300, 420), (400, 384), (500, 372), (540, 392), (540, 446),
                       (420, 456)],
    "Solace Beach": [(-900, -1150), (150, -940), (150, -905), (-600, -1028)],
    "Creek Green": [(-150, 590), (-90, 600), (-80, 680), (-150, 720), (-220, 690)],
}

# Marina docks: (x0, y, length into the harbour, slips)
MARINA_DOCKS = [(690, -360, 120, 8), (695, -440, 140, 9), (715, -520, 120, 7)]
PIER = [(200, -948), (226, -1210)]   # public fishing pier at the beach (start, end)
POWER_LINE = [(-1300, 900), (-1000, 860), (-760, 780), (-560, 640), (-300, 560),
              (-120, 560)]
BILLBOARDS = [(-980, -470, 0.0), (-640, -440, 0.0), (-160, -540, math.pi), (380, -560, 2.8)]
