"""World dressing: yards, parking lots, loading yards, plazas, parks, the beach and pier,
marina docks, power lines, vegetation and the outskirts."""

from __future__ import annotations

import math
import random

from . import layout as Lay
from .placement import district_at
from .roads import Sweep
from ..archetypes import ARCH
from ..geom import Prim, rot_z, point_in_poly, catmull_rom, seg_point_dist
from ..records import PropPlace, Marker, LightRec
from .. import palette as pal

CARS = ["car_sedan", "car_compact", "car_suv", "car_pickup", "car_wagon", "car_van", "car_coupe"]


def _pp(name, x, y, z, yaw=0.0, ch=None, scale=(1.0, 1.0, 1.0)):
    return PropPlace(name, x, y, z, yaw, scale, ch or {}, False)


# Gameplay hideouts: archetype -> (marker kind, tier, room kinds by preference,
#                                 markers per building, buildings in town)
HIDEOUTS = {
    "trailer": ("safehouse", "starter", ("living",), 1, 4),
    "motel": ("safehouse", "motel", ("motel_room",), 2, 1),
    "apartment_lowrise": ("safehouse", "apartment", ("unit_living",), 1, 3),
    "mixed_use": ("safehouse", "apartment", ("unit_living",), 1, 3),
    "house_old": ("safehouse", "house", ("basement", "living"), 1, 4),
    "warehouse_small": ("hideout", "workshop", ("workshop", "warehouse"), 1, 4),
    "auto_shop": ("hideout", "chop shop", ("garage_bay",), 1, 2),
    "storage_facility": ("stash", "storage unit", ("storage_unit",), 6, 1),
    "warehouse": ("stash", "warehouse office", ("office",), 1, 2),
    "pawn_shop": ("stash", "fence", ("storage", "office"), 1, 3),
    "bar": ("stash", "back room", ("storage", "office"), 1, 3),
}


class Dresser:
    def __init__(self, world, placer, rng):
        self.W = world
        self.P = placer
        self.rng = rng
        self.T = world.terrain
        self.net = world.net
        self.claimed = []        # polygons where vegetation must not grow

    # -- helpers ------------------------------------------------------------------------
    def prop(self, name, x, y, z=None, yaw=0.0, ch=None, cat="PROPS", scale=(1, 1, 1)):
        if z is None:
            z = self.T.h(x, y)
        self.W.props.append((_pp(name, x, y, z, yaw, ch, scale), cat))

    def lbox(self, lot, cat, mat, x0, y0, x1, y1, z0, z1, collide=True):
        """Axis-aligned box in lot-local coordinates."""
        cx, cy = lot.local_to_world((x0 + x1) / 2, (y0 + y1) / 2)
        self.W.boxes.append((cat, Prim("box", mat, (cx, cy, (z0 + z1) / 2),
                                       (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)),
                                       rot_z(lot.yaw), collide)))

    def lprop(self, lot, name, lx, ly, lyaw=0.0, ch=None, z=None, cat="PROPS"):
        x, y = lot.local_to_world(lx, ly)
        zz = lot.z - 0.6 if z is None else z
        self.W.props.append((_pp(name, x, y, zz, lot.yaw + lyaw, ch), cat))
        return x, y

    # -- lots -------------------------------------------------------------------------------
    def yards(self):
        for b in self.W.buildings:
            lot = b.lot
            kind = ARCH[lot.arch].yard
            self.claimed.append(lot.yard_rect)
            fn = getattr(self, "yard_" + kind, None)
            if fn:
                fn(b, lot)
            if lot.opts.get("marlin"):
                self.marlin(b, lot)

    def _front_entrance(self, b, roles=("main",)):
        for e in b.built.entrances:
            if e["role"] in roles and e["side"] == "front" and e["level"] == 0:
                return e
        return None

    def _walk(self, lot, x, width=4.0):
        """Path from the facade to the sidewalk in front of the lot (local x centre)."""
        if lot.setback < 2:
            return
        self.lbox(lot, "SIDEWALKS", "sidewalk", x - width / 2, -lot.setback - 0.4,
                  x + width / 2, 0.0, lot.z - 0.75, lot.z - 0.45, True)

    def yard_residential(self, b, lot):
        rng = self.rng
        built = b.built
        g = None
        for e in built.entrances:
            if e["role"] == "garage" and e["side"] == "front":
                g = e
        main = self._front_entrance(b)
        if main:
            self._walk(lot, main["x"])
        mail_x = 3.0
        if g:
            gw = g["w"] + 2.0
            self.lbox(lot, "SIDEWALKS", "concrete_light", g["x"] - gw / 2, -lot.setback - 0.4,
                      g["x"] + gw / 2, 0.0, lot.z - 0.8, lot.z - 0.5, True)
            mail_x = g["x"] + gw / 2 + 2.0
            if rng.random() < 0.65 and lot.setback >= 12:
                car = rng.choice(CARS if lot.quality != "cheap" else
                                 ["car_pickup_old", "car_sedan", "car_wagon", "car_compact"])
                cx, cy = self.lprop(lot, car, g["x"], -lot.setback / 2, 0.0,
                                    {"$car": rng.choice(pal.CAR_PAINTS if lot.quality != "cheap"
                                                        else pal.CAR_PAINTS_OLD)},
                                    z=lot.z - 0.5, cat="VEHICLES")
                self.W.markers.append(Marker("vehicle", cx, cy, lot.z - 0.5, lot.yaw, car,
                                             {"driveway": lot.id}))
        elif lot.setback >= 12 and rng.random() < 0.5:
            # driveway/parking pad to the side of the house
            self.lbox(lot, "SIDEWALKS", "concrete_light", -lot.side_gap / 2 + 1, -lot.setback,
                      -lot.side_gap / 2 + 11, lot.d * 0.5, lot.z - 0.8, lot.z - 0.5, True)
            if rng.random() < 0.7:
                car = rng.choice(["car_pickup_old", "car_sedan", "car_wagon", "car_compact"])
                self.lprop(lot, car, -lot.side_gap / 2 + 6, lot.d * 0.1, 0.0,
                           {"$car": rng.choice(pal.CAR_PAINTS_OLD)}, z=lot.z - 0.5,
                           cat="VEHICLES")
        if lot.setback >= 6:
            self.lprop(lot, "mailbox_post", mail_x, -lot.setback + 1.5, 0.0,
                       {"$metal": rng.choice(["metal_gray", "metal_dark", "metal_white"])})
        # foundation shrubs and yard trees
        for k in range(rng.randint(2, 5)):
            x = rng.uniform(2, lot.w - 2)
            if g and abs(x - g["x"]) < g["w"] / 2 + 3:
                continue
            if main and abs(x - main["x"]) < 4:
                continue
            self.lprop(lot, rng.choice(["bush_round", "bush_small", "bush_flowering"]), x,
                       -2.2, rng.uniform(0, 6.28), {"$leaf": rng.choice(["leaf", "leaf_dark",
                                                                         "hedge"])},
                       cat="VEGETATION")
        if lot.setback >= 14 and rng.random() < 0.7:
            tx = rng.choice([lot.w * 0.2, lot.w * 0.8])
            if not (g and abs(tx - g["x"]) < g["w"]):
                self.lprop(lot, rng.choice(["tree_oak", "tree_oak_b", "tree_maple",
                                            "tree_birch"]), tx, -lot.setback * 0.55,
                           rng.uniform(0, 6.28), {"$leaf": rng.choice(["leaf", "leaf_light"])},
                           cat="VEGETATION")
        # back yard: fence + play/garden items
        rear = lot.rear / 2
        if rear >= 6:
            fence = "fence_wood" if lot.quality != "cheap" else rng.choice(["fence_chain",
                                                                             "fence_wood"])
            if lot.quality == "nice" and rng.random() < 0.5:
                fence = "hedge_row"
            x0, x1 = -lot.side_gap / 2 + 0.6, lot.w + lot.side_gap / 2 - 0.6
            y0, y1 = lot.d * 0.7, lot.d + rear - 0.6
            self._fence_line(lot, fence, x0, y1, x1, y1)
            self._fence_line(lot, fence, x0, y0, x0, y1)
            self._fence_line(lot, fence, x1, y0, x1, y1)
            items = ["swing_set", "trampoline", "garden_bed", "kiddie_pool", "lawn_mower",
                     "woodpile", "doghouse", "bbq_grill", "lawn_chair"]
            if lot.quality == "cheap":
                items += ["car_wreck", "clutter_pile", "tire_stack", "boxes_stack"]
            for k in range(rng.randint(1, 3)):
                nm = rng.choice(items)
                self.lprop(lot, nm, rng.uniform(4, lot.w - 4), lot.d + rng.uniform(3, rear - 3),
                           rng.choice([0.0, math.pi / 2, math.pi]),
                           {"$fabric": rng.choice(pal.FABRICS), "$wood": "wood_weathered",
                            "$car": rng.choice(pal.CAR_PAINTS_OLD)})
            if rng.random() < 0.6:
                self.lprop(lot, rng.choice(["tree_oak", "tree_maple", "tree_pine",
                                            "tree_oak_b"]), rng.uniform(4, lot.w - 4),
                           lot.d + rear * 0.6, rng.uniform(0, 6.28), {"$leaf": "leaf"},
                           cat="VEGETATION")
        if "pool" in b.plan.tags and rear > 20:
            self._pool(lot, lot.w * 0.3, lot.d + 8, lot.w * 0.7, lot.d + min(rear - 4, 22))

    def _fence_line(self, lot, name, x0, y0, x1, y1):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(round(L / 8.0)))
        yaw = math.atan2(y1 - y0, x1 - x0)
        for k in range(n):
            t = (k + 0.5) / n
            lx, ly = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            x, y = lot.local_to_world(lx, ly)
            sx = L / n / 8.0
            self.W.props.append((_pp(name, x, y, self.T.h(x, y) - 0.3, lot.yaw + yaw,
                                     {"$wood": "wood_weathered", "$paint": "block_painted"},
                                     (sx, 1.0, 1.0)), "PROPS"))

    def _pool(self, lot, x0, y0, x1, y1):
        z = lot.z - 0.6
        self.lbox(lot, "PARKS", "concrete_light", x0 - 4, y0 - 4, x1 + 4, y1 + 4, z, z + 0.6)
        self.lbox(lot, "PARKS", "tile_bath_blue", x0, y0, x1, y1, z + 0.05, z + 0.62, False)
        self.lbox(lot, "PARKS", "water", x0 + 0.4, y0 + 0.4, x1 - 0.4, y1 - 0.4, z + 0.3,
                  z + 0.64, False)
        self.lprop(lot, "pool_ladder", x1 - 2, y0 + 0.4, 0.0, z=z + 0.6)
        self.lprop(lot, "pool_lounger", x0 - 2.5, (y0 + y1) / 2, math.pi / 2, z=z + 0.6)

    def _lot_parking(self, lot, x0, y0, x1, y1, rows_along_x=True, occupancy=0.55,
                     lights=True, cars=None, ch_fn=None):
        """Asphalt lot (lot-local rect) with painted stalls and parked cars."""
        rng = self.rng
        z = lot.z - 0.6
        self.lbox(lot, "ROADS", "asphalt", x0, y0, x1, y1, z, z + 0.25, True)
        stall_w, stall_d, aisle = 9.0, 18.0, 22.0
        y = y0 + 1.0
        row = 0
        while y + stall_d <= y1 - 0.5:
            x = x0 + 1.0
            while x + stall_w <= x1 - 0.5:
                self.lbox(lot, "ROADS", "paint_line_white", x, y, x + 0.3, y + stall_d,
                          z + 0.25, z + 0.3, False)
                if rng.random() < occupancy:
                    car = rng.choice(cars or CARS)
                    yaw = 0.0 if row % 2 == 0 else math.pi
                    cx, cy = self.lprop(lot, car, x + stall_w / 2, y + stall_d / 2, yaw,
                                        ch_fn() if ch_fn else
                                        {"$car": rng.choice(pal.CAR_PAINTS)},
                                        z=z + 0.25, cat="VEHICLES")
                    self.W.markers.append(Marker("vehicle", cx, cy, z, lot.yaw + yaw, car,
                                                 {"parked": True}))
                else:
                    cx, cy = lot.local_to_world(x + stall_w / 2, y + stall_d / 2)
                    self.W.markers.append(Marker("parking_spot", cx, cy, z,
                                                 lot.yaw + (0.0 if row % 2 == 0 else math.pi),
                                                 "stall"))
                x += stall_w
            y += stall_d + (aisle if row % 2 == 0 else 0.0)
            row += 1
        if lights:
            for lx in (x0 + 2, x1 - 2):
                for ly in ((y0 + y1) / 2,):
                    if x1 - x0 > 30 and y1 - y0 > 24:
                        wx, wy = self.lprop(lot, "parking_light", lx, ly, 0.0, z=z + 0.25)
                        self.W.lights.append(LightRec(wx, wy, z + 22.5, (1.0, 0.94, 0.86), 60,
                                                      1.6, "spot", "night"))

    def yard_parking(self, b, lot):
        rng = self.rng
        main = self._front_entrance(b, ("main", "shop"))
        if lot.setback >= 20:
            self._lot_parking(lot, 2.0, -lot.setback + 1.0, lot.w - 2.0, -3.0)
        elif lot.side_gap >= 10:
            pass
        if main and lot.setback < 20:
            self._walk(lot, main["x"], 6.0)
        # back service area
        rear = lot.rear / 2
        if rear >= 5:
            self.lbox(lot, "ROADS", "asphalt_old", 0, lot.d, lot.w, lot.d + rear,
                      lot.z - 0.6, lot.z - 0.35, True)

    def yard_lot(self, b, lot):
        rng = self.rng
        self.lbox(lot, "ROADS", "gravel" if lot.quality == "cheap" else "asphalt_old",
                  -lot.side_gap / 2 + 1, -lot.setback + 1, lot.w + lot.side_gap / 2 - 1,
                  lot.d + lot.rear / 2 - 1, lot.z - 0.62, lot.z - 0.4, True)
        for k in range(rng.randint(2, 5)):
            car = rng.choice(["car_sedan", "car_pickup_old", "car_wreck", "car_van",
                              "car_compact", "tow_truck"])
            self.lprop(lot, car, rng.uniform(6, lot.w - 6), -rng.uniform(6, lot.setback - 6)
                       if lot.setback > 14 else lot.d + 6, rng.choice([0.0, math.pi / 2, 1.2]),
                       {"$car": rng.choice(pal.CAR_PAINTS_OLD)}, z=lot.z - 0.4, cat="VEHICLES")
        for k in range(rng.randint(1, 3)):
            self.lprop(lot, rng.choice(["tire_stack", "barrels_group", "engine_block",
                                        "crate_stack"]), rng.uniform(2, lot.w - 2),
                       lot.d + rng.uniform(2, 6), 0.0, z=lot.z - 0.4)

    def yard_loading(self, b, lot):
        rng = self.rng
        rear = lot.rear / 2
        z = lot.z - 0.6
        if lot.setback >= 12:
            self._lot_parking(lot, 4.0, -lot.setback + 2.0, min(lot.w - 4.0, 120.0), -4.0,
                              occupancy=0.4)
        if rear >= 10:
            self.lbox(lot, "ROADS", "asphalt_old", -lot.side_gap / 2 + 1, lot.d,
                      lot.w + lot.side_gap / 2 - 1, lot.d + rear, z, z + 0.25, True)
            # trucks at the dock doors
            for e in b.built.entrances:
                if e["side"] == "back" and e["kind"] in ("rollup", "rollup_small") and \
                        rng.random() < 0.6:
                    nm = rng.choice(["box_truck", "semi_trailer", "box_truck"])
                    size = 28.0 if nm == "box_truck" else 48.0
                    if size / 2 + 2 > rear:
                        nm, size = "car_van", 18.0
                    self.lprop(lot, nm, e["x"], lot.d + size / 2 + 1.0, math.pi,
                               {"$car": rng.choice(["car_white", "car_silver", "car_blue",
                                                    "car_red"])}, z=z + 0.25, cat="VEHICLES")
            for k in range(rng.randint(2, 5)):
                self.lprop(lot, rng.choice(["pallet_boxes", "pallet", "pallet_drums",
                                            "crate_stack", "ibc_tote", "barrels_group"]),
                           rng.uniform(4, lot.w - 4), lot.d + rear - rng.uniform(3, 6), 0.0,
                           z=z + 0.25)
            if rear > 24 and rng.random() < 0.7:
                self.lprop(lot, "shipping_container", rng.uniform(10, lot.w - 10),
                           lot.d + rear - 6, math.pi / 2,
                           {"$metal": rng.choice(["metal_red", "metal_blue", "metal_green",
                                                  "metal_orange"])}, z=z + 0.25)
            # perimeter chain-link around the yard
            x0, x1 = -lot.side_gap / 2 + 0.5, lot.w + lot.side_gap / 2 - 0.5
            y1 = lot.d + rear - 0.5
            self._fence_line(lot, "fence_chain", x0, y1, x1, y1)
            self._fence_line(lot, "fence_chain", x0, lot.d, x0, y1)
            self._fence_line(lot, "fence_chain", x1, lot.d, x1, y1)

    def yard_gated(self, b, lot):
        rng = self.rng
        z = lot.z - 0.6
        x0, x1 = -lot.side_gap / 2 + 0.5, lot.w + lot.side_gap / 2 - 0.5
        y0, y1 = -lot.setback + 2.0, lot.d + lot.rear / 2 - 0.5
        self.lbox(lot, "ROADS", "asphalt_old", x0, y0, x1, y1, z, z + 0.22, True)
        gate_w = 18.0
        gx = min(lot.w * 0.8, x1 - gate_w - 2)
        self._fence_line(lot, "fence_chain_barbed", x0, y0, gx, y0)
        self._fence_line(lot, "fence_chain_barbed", gx + gate_w, y0, x1, y0)
        self._fence_line(lot, "fence_chain_barbed", x0, y0, x0, y1)
        self._fence_line(lot, "fence_chain_barbed", x1, y0, x1, y1)
        self._fence_line(lot, "fence_chain_barbed", x0, y1, x1, y1)
        self.lprop(lot, "gate_arm", gx + 1.0, y0, 0.0, z=z + 0.2)
        self.lprop(lot, "guard_booth", gx + gate_w + 4.0, y0 + 5.0, 0.0, z=z + 0.2)
        cx, cy = lot.local_to_world(gx + gate_w / 2, y0)
        self.W.markers.append(Marker("gate", cx, cy, z, lot.yaw, f"{b.name} gate"))

    def yard_police(self, b, lot):
        rng = self.rng
        z = lot.z - 0.6
        # visitor parking in front + a fenced secure lot down the right side
        if lot.setback >= 18:
            self._lot_parking(lot, 4.0, -lot.setback + 1.0, lot.w * 0.42, -3.0, occupancy=0.4)
            self._lot_parking(lot, lot.w * 0.6, -lot.setback + 1.0, lot.w - 4.0, -3.0,
                              occupancy=0.8, cars=["police_cruiser", "police_suv",
                                                   "police_cruiser"],
                              ch_fn=lambda: {})
        main = self._front_entrance(b)
        if main:
            self._walk(lot, main["x"], 8.0)

    def yard_apron(self, b, lot):
        z = lot.z - 0.6
        self.lbox(lot, "ROADS", "concrete_light", 0, -lot.setback, 3 * 16.0 + 1, 0, z,
                  z + 0.3, True)
        self.lbox(lot, "ROADS", "concrete_light", 0, lot.d, 3 * 16.0 + 1, lot.d + lot.rear / 2,
                  z, z + 0.3, True)
        main = self._front_entrance(b)
        if main:
            self._walk(lot, main["x"])
        self._lot_parking(lot, 3 * 16.0 + 4, -lot.setback + 2, lot.w - 2, -4.0, occupancy=0.6,
                          lights=False)

    def yard_plaza(self, b, lot):
        rng = self.rng
        z = lot.z - 0.6
        if lot.setback < 4:
            return
        self.lbox(lot, "PARKS", "brick_paver", -lot.side_gap / 2 + 1, -lot.setback, lot.w +
                  lot.side_gap / 2 - 1, 0.0, z, z + 0.4, True)
        cx = lot.w / 2
        if lot.setback >= 24:
            fx, fy = self.lprop(lot, "fountain", cx, -lot.setback * 0.5, 0.0, z=z + 0.4)
            self.W.markers.append(Marker("poi", fx, fy, z, 0.0, f"{b.name} plaza"))
            for k in (-1, 1):
                self.lprop(lot, "bench_park", cx + k * 16, -lot.setback * 0.5, math.pi / 2 * k,
                           z=z + 0.4)
                self.lprop(lot, "planter_box", cx + k * 26, -lot.setback * 0.3, 0.0, z=z + 0.4)
                self.lprop(lot, "lamppost_classic", cx + k * 22, -lot.setback * 0.75, 0.0,
                           z=z + 0.4)
                wx, wy = lot.local_to_world(cx + k * 22, -lot.setback * 0.75)
                self.W.lights.append(LightRec(wx, wy, z + 11.4, (1.0, 0.85, 0.65), 30, 1.2,
                                              "point", "night"))
            if b.arch == "town_hall":
                self.lprop(lot, "statue", cx, -lot.setback * 0.82, math.pi, z=z + 0.4)
        # side parking
        if lot.side_gap >= 14 and lot.rear >= 10:
            self.lbox(lot, "ROADS", "asphalt", 0, lot.d, lot.w, lot.d + lot.rear / 2, z, z + 0.25)

    def yard_carlot(self, b, lot):
        rng = self.rng
        self._lot_parking(lot, 2.0, -lot.setback + 1.0, lot.w - 2.0, -3.0, occupancy=0.9,
                          cars=["car_sedan", "car_suv", "car_coupe", "car_pickup", "car_wagon"])
        for k in range(5):
            x = 4 + k * (lot.w - 8) / 4
            self.lprop(lot, "bollard", x, -lot.setback + 1.0, 0.0)
        for x in (6.0, lot.w - 6.0):
            self.lprop(lot, "flagpole", x, -lot.setback + 3.0, 0.0)

    def yard_fuel(self, b, lot):
        z = lot.z - 0.6
        self.lbox(lot, "ROADS", "concrete_light", -8, -lot.setback, lot.w + 8, 0.0, z, z + 0.3,
                  True)
        cx, cy = lot.local_to_world(lot.w / 2, -26.0)
        self.W.markers.append(Marker("fuel", cx, cy, z, lot.yaw, f"{b.name} pumps"))

    def yard_motel(self, b, lot):
        rng = self.rng
        z = lot.z - 0.6
        # front parking lot facing the rooms
        self._lot_parking(lot, 30.0, -lot.setback + 2.0, lot.w - 4.0, -10.0, occupancy=0.45,
                          cars=CARS + ["car_pickup_old", "car_wagon", "motorcycle"])
        for k in range(4):
            self.lprop(lot, "tree_palm", 30 + k * 34, -8.5, rng.uniform(0, 6.28),
                       cat="VEGETATION")

    def yard_estate(self, b, lot):
        rng = self.rng
        z = lot.z - 0.6
        # long gravel drive, hedges, gate pillars
        self.lbox(lot, "ROADS", "gravel", lot.w * 0.15 - 6, -lot.setback, lot.w * 0.15 + 6, 0.0,
                  z, z + 0.25, True)
        for x in (lot.w * 0.15 - 8, lot.w * 0.15 + 8):
            self.lbox(lot, "PROPS", "limestone", x - 1.2, -lot.setback, x + 1.2,
                      -lot.setback + 2.4, z, z + 8.0, True)
        for k in range(6):
            self.lprop(lot, "hedge_row", lot.w * 0.3 + k * 8, -lot.setback + 1.5, 0.0)
        for k in range(8):
            self.lprop(lot, rng.choice(["tree_oak", "tree_pine_tall", "tree_birch"]),
                       rng.uniform(-10, lot.w + 10), rng.uniform(-lot.setback, -6),
                       rng.uniform(0, 6.28), cat="VEGETATION")
        self.lprop(lot, "car_coupe", lot.w * 0.15, -12.0, 0.0, {"$car": "car_black"},
                   z=z + 0.25, cat="VEHICLES")

    # -- marlin landmark --------------------------------------------------------------------
    def marlin(self, b, lot):
        """Giant fibreglass marlin on a pole above the Blue Marlin diner."""
        from ..geom import mat_mul, rot_x, rot_y
        top = b.plan.height + lot.z
        cx, cy = lot.local_to_world(lot.w * 0.5, lot.d * 0.35)
        yaw = lot.yaw
        W = self.W
        W.boxes.append(("LANDMARKS", Prim("cyl", "metal_gray", (cx, cy, top + 7.0),
                                          (1.2, 1.2, 14.0), rot_z(0.0), True, 8)))
        z = top + 18.0
        W.boxes.append(("LANDMARKS", Prim("ball", "metal_blue", (cx, cy, z), (30.0, 7.0, 9.0),
                                          rot_z(yaw), False)))
        W.boxes.append(("LANDMARKS", Prim("ball", "plastic_white", (cx, cy, z - 1.6),
                                          (26.0, 6.4, 5.0), rot_z(yaw), False)))
        c, s = math.cos(yaw), math.sin(yaw)
        for (dx, dz, sx, sz, ang) in ((-17.0, 3.0, 2.0, 9.0, 0.6), (-17.0, -3.0, 2.0, 9.0, -0.6)):
            W.boxes.append(("LANDMARKS", Prim("wedge", "metal_blue",
                                              (cx + c * dx, cy + s * dx, z + dz),
                                              (1.0, sx * 3, sz),
                                              mat_mul(rot_z(yaw + math.pi / 2), rot_x(ang)),
                                              False)))
        W.boxes.append(("LANDMARKS", Prim("cyl", "metal_gray", (cx + c * 19.0, cy + s * 19.0, z),
                                          (0.8, 0.8, 12.0), mat_mul(rot_z(yaw), rot_y(math.pi / 2)),
                                          False, 6)))
        W.boxes.append(("LANDMARKS", Prim("wedge", "metal_blue", (cx, cy, z + 6.0),
                                          (1.0, 10.0, 6.0), rot_z(yaw + math.pi / 2), False)))
        W.lights.append(LightRec(cx, cy, z - 8.0, (0.5, 0.7, 1.0), 40, 1.4, "point", "late"))
        W.markers.append(Marker("landmark", cx, cy, top, 0.0, "Blue Marlin Sign"))

    # -- parks, beach, pier, docks ------------------------------------------------------------
    def parks(self):
        rng = self.rng
        for name, poly in Lay.PARKS.items():
            self.claimed.append(poly)
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            area = 0
            beach = name == "Solace Beach"
            # scatter trees / benches inside the polygon
            n = 0
            for _ in range(600):
                x = rng.uniform(min(xs), max(xs))
                y = rng.uniform(min(ys), max(ys))
                if not point_in_poly(x, y, poly):
                    continue
                cl, _, _ = self.net.dist_to_road(x, y, 60.0)
                if cl < 3:
                    continue
                n += 1
                if beach:
                    if n > 40:
                        break
                    nm = rng.choice(["patio_set", "pool_lounger", "patio_set", "pool_lounger",
                                     "trash_bin_street", "tree_palm"])
                    self.prop(nm, x, y, None, rng.uniform(0, 6.28),
                              {"$fabric": rng.choice(["fabric_red", "fabric_teal",
                                                      "fabric_mustard", "fabric_blue"])},
                              cat="PARKS")
                    continue
                if n > 70:
                    break
                r = rng.random()
                if r < 0.55:
                    self.prop(rng.choice(["tree_oak", "tree_maple", "tree_oak_b", "tree_birch"]),
                              x, y, None, rng.uniform(0, 6.28), {"$leaf": rng.choice(
                                  ["leaf", "leaf_light", "leaf_dark"])}, cat="VEGETATION")
                elif r < 0.7:
                    self.prop("bench_park", x, y, None, rng.uniform(0, 6.28), cat="PARKS")
                elif r < 0.8:
                    self.prop("picnic_table", x, y, None, rng.uniform(0, 6.28), cat="PARKS")
                elif r < 0.9:
                    self.prop(rng.choice(["bush_round", "bush_flowering", "flower_planter"]),
                              x, y, None, rng.uniform(0, 6.28), cat="VEGETATION")
                else:
                    self.prop("lamppost_classic", x, y, None, 0.0, cat="PARKS")
                    self.W.lights.append(LightRec(x, y, self.T.h(x, y) + 11.0,
                                                  (1.0, 0.85, 0.65), 30, 1.1, "point", "night"))
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            if name == "Town Square":
                self.prop("fountain", cx, cy, None, 0.0, cat="PARKS")
                self.prop("statue", cx, cy + 24, None, math.pi, cat="PARKS")
                self.prop("playground", cx - 30, cy - 22, None, 0.0, cat="PARKS")
            elif name == "Riverside Park":
                self.prop("playground", cx, cy, None, 0.3, cat="PARKS")
            self.W.markers.append(Marker("park", cx, cy, self.T.h(cx, cy), 0.0, name))

    def pier(self):
        """Public fishing pier on Solace Beach (landmark)."""
        (x0, y0), (x1, y1) = Lay.PIER
        L = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -ty, tx
        zt = 8.0
        smp = []
        n = int(L / 8)
        for k in range(n + 1):
            t = k / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            z = max(zt, self.T.h(x, y) + 0.6) if k < 3 else zt
            smp.append((x, y, z, nx, ny))
        W = self.W
        W.sweeps.append(Sweep("LANDMARKS", "deck_teak", smp,
                              [(-8.0, -1.2), (-8.0, 0.0), (8.0, 0.0), (8.0, -1.2)][::-1],
                              closed=True, name="Solace Pier deck"))
        for side in (-1, 1):
            c = side * 7.8
            W.sweeps.append(Sweep("LANDMARKS", "wood_white", smp,
                                  [(c - 0.2, 3.0), (c - 0.2, 3.4), (c + 0.2, 3.4),
                                   (c + 0.2, 3.0)][::-1], closed=True, name="pier rail"))
        for k in range(0, n + 1, 2):
            x, y, z, _, _ = smp[k]
            for side in (-1, 1):
                px, py = x + nx * side * 7.0, y + ny * side * 7.0
                bed = min(self.T.h(px, py), -1.0)
                W.boxes.append(("LANDMARKS", Prim("cyl", "wood_weathered",
                                                  (px, py, (bed - 4 + z - 1.2) / 2),
                                                  (1.6, 1.6, z - 1.2 - (bed - 4)), rot_z(0), True,
                                                  8)))
                if k % 6 == 0:
                    self.prop("lamppost_classic", px - nx * side * 0.8, py - ny * side * 0.8, z,
                              0.0, cat="LANDMARKS")
                    W.lights.append(LightRec(px, py, z + 11.0, (1.0, 0.85, 0.65), 30, 1.1,
                                             "point", "night"))
                if k % 4 == 2:
                    self.prop("bench_park", px - nx * side * 2.5, py - ny * side * 2.5, z,
                              math.atan2(-nx * side, ny * side) + math.pi, cat="LANDMARKS")
        # bait hut at the end
        ex, ey = x1 - tx * 10, y1 - ty * 10
        yaw = math.atan2(ty, tx) - math.pi / 2
        W.boxes.append(("LANDMARKS", Prim("box", "siding_blue", (ex, ey, zt + 5.0),
                                          (14.0, 10.0, 10.0), rot_z(yaw), True)))
        W.boxes.append(("LANDMARKS", Prim("wedge", "roof_metal_red", (ex, ey - 0.0, zt + 12.0),
                                          (15.0, 11.0, 4.0), rot_z(yaw + math.pi), False)))
        W.markers.append(Marker("landmark", (x0 + x1) / 2, (y0 + y1) / 2, zt, 0.0,
                                "Solace Pier"))
        W.markers.append(Marker("vantage", x1, y1, zt, 0.0, "End of the pier"))

    def docks(self):
        """Marina finger docks with moored boats."""
        rng = self.rng
        W = self.W
        for (x0, y, length, slips) in Lay.MARINA_DOCKS:
            # main walkway heading east into the harbour
            z = 1.6
            W.boxes.append(("WATERFRONT", Prim("box", "deck_teak", (x0 + length / 2, y, z - 0.4),
                                               (length, 8.0, 0.8), rot_z(0.0), True)))
            for k in range(slips):
                fx = x0 + 14 + k * (length - 18) / max(1, slips - 1)
                for side in (-1, 1):
                    W.boxes.append(("WATERFRONT", Prim("box", "deck_teak",
                                                       (fx, y + side * 12.0, z - 0.4),
                                                       (4.0, 16.0, 0.8), rot_z(0.0), True)))
                    W.boxes.append(("WATERFRONT", Prim("cyl", "wood_weathered",
                                                       (fx, y + side * 20.0, -2.0),
                                                       (1.2, 1.2, 10.0), rot_z(0.0), True, 8)))
                    if rng.random() < 0.75:
                        boat = rng.choice(["boat_motor", "boat_sail", "boat_fishing",
                                           "boat_dinghy", "boat_motor", "boat_yacht",
                                           "boat_pontoon"])
                        bx = fx + 8.0 if boat not in ("boat_fishing", "boat_yacht") else fx + 10
                        self.prop(boat, bx, y + side * 14.0, 0.0, 0.0 if side < 0 else math.pi,
                                  {"$hull": rng.choice(pal.HULLS), "$fabric": "fabric_cream"},
                                  cat="WATERFRONT")
                        W.markers.append(Marker("boat", bx, y + side * 14.0, 0.0, 0.0, boat))
                if k % 2 == 0:
                    self.prop("bollard_dock", fx, y + 3.4, z, 0.0, cat="WATERFRONT")
            self.prop("lamppost_classic", x0 + length - 3, y, z, 0.0, cat="WATERFRONT")
            W.lights.append(LightRec(x0 + length - 3, y, z + 11.0, (1.0, 0.85, 0.65), 30, 1.0,
                                     "point", "night"))
            W.markers.append(Marker("dock", x0 + 6, y, z, 0.0, "Marina dock"))

    def power_line(self):
        pts = catmull_rom(Lay.POWER_LINE, 8.0)
        from .roads import _resample
        towers = []
        acc = 0.0
        last = None
        for p in pts:
            if last is not None:
                acc += math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
            if acc >= 210.0 or not towers:
                cl, _, _ = self.net.dist_to_road(p[0], p[1], 60.0)
                if cl < 12 or self.T.is_water(p[0], p[1], 10):
                    continue
                towers.append(p)
                acc = 0.0
        prev = None
        for (x, y) in towers:
            z = self.T.h(x, y)
            yaw = 0.0
            if prev:
                yaw = math.atan2(y - prev[1], x - prev[0]) + math.pi / 2
            self.prop("power_tower", x, y, z - 0.5, yaw, cat="PROPS")
            if prev:
                px, py, pz, pyaw = prev[0], prev[1], prev[2], prev[3]
                c, s = math.cos(yaw), math.sin(yaw)
                for off, hz in ((-11.0, 58.0), (-7.0, 66.0), (7.0, 66.0), (11.0, 58.0)):
                    ax, ay = px + c * off, py + s * off
                    bx, by = x + c * off, y + s * off
                    self._wire(ax, ay, pz + hz, bx, by, z + hz, 6.0)
            prev = (x, y, z, yaw)

    def _wire(self, ax, ay, az, bx, by, bz, sag):
        smp = []
        n = 10
        L = math.hypot(bx - ax, by - ay) or 1.0
        tx, ty = (bx - ax) / L, (by - ay) / L
        for k in range(n + 1):
            t = k / n
            z = az + (bz - az) * t - sag * 4 * t * (1 - t)
            smp.append((ax + (bx - ax) * t, ay + (by - ay) * t, z, -ty, tx))
        self.W.sweeps.append(Sweep("PROPS", "rubber", smp, [(-0.1, -0.1), (-0.1, 0.1),
                                                            (0.1, 0.1), (0.1, -0.1)][::-1],
                                   closed=True, name="transmission line", collide=False))

    def seawall(self):
        """Concrete harbour wall + bollards along the marina shore."""
        pts = Lay.SEA[12:20]
        for (a, b) in zip(pts[:-1], pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            yaw = math.atan2(b[1] - a[1], b[0] - a[0])
            cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            self.W.boxes.append(("WATERFRONT", Prim("box", "concrete", (cx, cy, -2.0),
                                                    (L + 2.0, 4.0, 6.4), rot_z(yaw), True)))
            n = int(L / 30)
            for k in range(n):
                t = (k + 0.5) / max(1, n)
                self.prop("bollard_dock", a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                          1.2, 0.0, cat="WATERFRONT")

    # -- vegetation ------------------------------------------------------------------------
    def vegetation(self, density=1.0):
        rng = self.rng
        T = self.T
        step = 14.0
        n = int(2 * Lay.HALF / step)
        claimed = self.claimed
        rail = catmull_rom(Lay.RAIL, 16.0)
        count = 0
        for i in range(n):
            for j in range(n):
                x = -Lay.HALF + (j + rng.random()) * step
                y = -Lay.HALF + (i + rng.random()) * step
                dist = district_at(x, y)
                p = {"OUTSKIRTS": 0.42, "RESIDENTIAL": 0.10, "RESIDENTIAL_N": 0.14,
                     "LOW_INCOME": 0.05, "INDUSTRIAL": 0.02, "DOWNTOWN": 0.0, "MIXED_USE": 0.02,
                     "COMMERCIAL": 0.03, "MOTEL": 0.06, "WATERFRONT": 0.04,
                     "CIVIC": 0.03}.get(dist, 0.1) * density
                # forest clumps on the hills
                macro = T.T(x, y)
                if dist == "OUTSKIRTS":
                    wild = 0.5 + 0.5 * math.sin(x * 0.011 + math.cos(y * 0.007) * 2.0) * \
                        math.cos(y * 0.013 - 0.4)
                    p *= 0.4 + 1.6 * wild
                if rng.random() > p:
                    continue
                if T.is_water(x, y, 6.0) or abs(x) > Lay.HALF - 8 or abs(y) > Lay.HALF - 8:
                    continue
                cl, _, _ = self.net.dist_to_road(x, y, 40.0)
                if cl < 4.0:
                    continue
                if any(point_in_poly(x, y, poly) for poly in claimed if
                       abs(poly[0][0] - x) < 260 and abs(poly[0][1] - y) < 260):
                    continue
                near_rail = False
                for k in range(0, len(rail) - 1):
                    if abs(rail[k][0] - x) > 60:
                        continue
                    d, _ = seg_point_dist(rail[k][0], rail[k][1], rail[k + 1][0], rail[k + 1][1],
                                          x, y)
                    if d < 26:
                        near_rail = True
                        break
                if near_rail:
                    continue
                z = T.h(x, y)
                coast = T.coast_d[int((y + Lay.HALF) / 4), int((x + Lay.HALF) / 4)]
                if coast < 90:
                    nm = rng.choice(["tree_palm", "reeds", "tall_grass", "rock_small", "weeds",
                                     "bush_small"])
                elif macro > 40 or (dist == "OUTSKIRTS" and y > 700):
                    nm = rng.choice(["tree_pine", "tree_pine_tall", "tree_pine", "rock_med",
                                     "tree_dead", "bush_round", "tree_pine_tall"])
                elif dist == "OUTSKIRTS":
                    nm = rng.choice(["tree_oak", "tree_oak_b", "tree_maple", "tree_birch",
                                     "bush_round", "tall_grass", "weeds", "rock_small",
                                     "tree_pine", "tree_dead", "rock_large"])
                elif dist in ("INDUSTRIAL", "LOW_INCOME", "MOTEL"):
                    nm = rng.choice(["weeds", "tall_grass", "bush_small", "tree_dead",
                                     "tree_oak_b"])
                else:
                    nm = rng.choice(["tree_oak", "tree_maple", "tree_birch", "bush_round",
                                     "tree_oak_b"])
                sc = rng.uniform(0.8, 1.3)
                self.W.props.append((_pp(nm, x, y, z - 0.3, rng.uniform(0, 6.28),
                                         {"$leaf": rng.choice(["leaf", "leaf_dark", "leaf_light",
                                                               "leaf_autumn" if rng.random() < 0.1
                                                               else "leaf"])},
                                         (sc, sc, sc)), "VEGETATION"))
                count += 1
        return count

    def hideouts(self):
        """Safehouse / hideout / stash markers in suitable rooms (spread across town)."""
        order = list(self.W.buildings)
        random.Random(len(order) * 7919).shuffle(order)   # own stream: keeps vegetation stable
        used = {}
        n_total = 0
        for b in order:
            spec = HIDEOUTS.get(b.arch)
            if not spec or used.get(b.arch, 0) >= spec[4]:
                continue
            kind, tier, kinds, per, _ = spec
            rooms = sorted((r for r in b.plan.rooms if r.kind in kinds and r.cells),
                           key=lambda r: (kinds.index(r.kind), r.id))
            if b.arch == "motel":
                rooms = rooms[::-1]          # rooms at the far end of the wing
            n = 0
            for r in rooms:
                lv = min(r.cells)
                rect = r.cells[lv][0]
                wx, wy, wz = b.xf.point((rect.cx, rect.cy, b.plan.level_z(lv)))
                self.W.markers.append(Marker(kind, wx, wy, wz, b.xf.yaw,
                                             f"{b.name} - {r.name or r.kind}",
                                             {"tier": tier, "building": b.id, "room": r.id}))
                n += 1
                if n >= per:
                    break
            if n:
                used[b.arch] = used.get(b.arch, 0) + 1
                n_total += n
        return n_total

    def outskirts(self):
        """Junkyard by Old Mission Road and crop fields along Farm Lane."""
        rng = self.rng
        jx, jy = -1060.0, -760.0
        if not self.T.is_water(jx, jy):
            for k in range(26):
                x = jx + rng.uniform(-50, 50)
                y = jy + rng.uniform(-40, 40)
                cl, _, _ = self.net.dist_to_road(x, y, 40.0)
                if cl < 4:
                    continue
                self.prop(rng.choice(["car_wreck", "car_wreck", "tire_stack", "car_pickup_old",
                                      "barrels_group", "engine_block"]), x, y, None,
                          rng.uniform(0, 6.28), {"$car": rng.choice(pal.CAR_PAINTS_OLD)},
                          cat="VEHICLES")
            for (a, b) in (((jx - 56, jy - 46), (jx + 56, jy - 46)),
                           ((jx - 56, jy + 46), (jx + 56, jy + 46)),
                           ((jx - 56, jy - 46), (jx - 56, jy + 46)),
                           ((jx + 56, jy - 46), (jx + 56, jy + 46))):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                yaw = math.atan2(b[1] - a[1], b[0] - a[0])
                for k in range(int(L / 8)):
                    t = (k + 0.5) / int(L / 8)
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    self.prop("fence_chain", x, y, None, yaw, cat="PROPS")
            self.claimed.append([(jx - 60, jy - 50), (jx + 60, jy - 50), (jx + 60, jy + 50),
                                 (jx - 60, jy + 50)])
            self.W.markers.append(Marker("poi", jx, jy, self.T.h(jx, jy), 0.0, "Junkyard"))
        # fields: painted dirt with crop rows
        for (fx, fy, fw, fd) in ((-1210, 380, 70, 140), (-1210, 560, 70, 120)):
            poly = [(fx - fw / 2, fy - fd / 2), (fx + fw / 2, fy - fd / 2),
                    (fx + fw / 2, fy + fd / 2), (fx - fw / 2, fy + fd / 2)]
            self.claimed.append(poly)
            for k in range(int(fw / 6)):
                x = fx - fw / 2 + 3 + k * 6
                self.W.boxes.append(("OUTSKIRTS", Prim("box", "leaf_light" if k % 2 else
                                                       "leaf", (x, fy, self.T.T(x, fy) + 0.4),
                                                       (2.4, fd, 1.4), rot_z(0.0), False)))
