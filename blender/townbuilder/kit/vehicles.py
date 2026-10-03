"""Stylised everyday vehicles and boats (static set dressing + spawn references).

Vehicles face -Y (front bumper at -length/2).  In Roblox each placed vehicle
also gets a ``VehicleSpawn`` marker so a drivable chassis can replace it.
"""

from __future__ import annotations

import math

from . import prop
from .shapes import car_wheel
from ..geom import rot_x


def _car(k, w=6.4, l=15.6, body_h=3.4, cab0=-2.2, cab1=4.4, cab_h=2.0, wheel_r=1.15,
         paint="$car", hood_slope=True, lower="trim_dark", roof_paint=None):
    zb = 0.9
    k.box(paint, -w / 2, -l / 2 + 0.6, zb, w / 2, l / 2 - 0.4, body_h)
    k.box(lower, -w / 2 + 0.05, -l / 2, zb, w / 2 - 0.05, -l / 2 + 0.7, zb + 1.0, collide=False)
    k.box(lower, -w / 2 + 0.05, l / 2 - 0.5, zb, w / 2 - 0.05, l / 2, zb + 1.0, collide=False)
    # cabin glass + pillars + roof
    zc = body_h
    k.box("car_window", -w / 2 + 0.35, cab0 + 0.5, zc, w / 2 - 0.35, cab1 - 0.5, zc + cab_h,
          collide=False)
    k.wedge("car_window", 0, cab0 - 0.3, zc + cab_h / 2, w - 0.7, 1.6, cab_h, yaw=math.pi,
            collide=False)
    k.wedge("car_window", 0, cab1 + 0.2, zc + cab_h / 2, w - 0.7, 1.4, cab_h, collide=False)
    k.box(roof_paint or paint, -w / 2 + 0.3, cab0 + 0.4, zc + cab_h, w / 2 - 0.3, cab1 - 0.4,
          zc + cab_h + 0.3)
    for y in (cab0 + 0.4, (cab0 + cab1) / 2, cab1 - 0.6):
        k.box(paint, -w / 2 + 0.3, y, zc, -w / 2 + 0.45, y + 0.2, zc + cab_h, collide=False)
        k.box(paint, w / 2 - 0.45, y, zc, w / 2 - 0.3, y + 0.2, zc + cab_h, collide=False)
    # lights
    for sx in (-1, 1):
        k.box("headlight", sx * (w / 2 - 1.2) - 0.6, -l / 2 + 0.55, body_h - 1.0,
              sx * (w / 2 - 1.2) + 0.6, -l / 2 + 0.6, body_h - 0.5, collide=False)
        k.box("taillight", sx * (w / 2 - 1.0) - 0.6, l / 2 - 0.45, body_h - 1.0,
              sx * (w / 2 - 1.0) + 0.6, l / 2 - 0.4, body_h - 0.5, collide=False)
    k.box("trim_dark", -1.2, -l / 2 + 0.55, zb + 1.0, 1.2, -l / 2 + 0.6, body_h - 1.1,
          collide=False)
    # wheels
    wy = l / 2 - 3.0
    for sy in (-1, 1):
        for sx in (-1, 1):
            car_wheel(k, sx * (w / 2 - 0.4), sy * wy, wheel_r, 0.9)


@prop("car_sedan", "vehicle", tags=("vehicle",))
def car_sedan(k):
    _car(k)


@prop("car_compact", "vehicle", tags=("vehicle",))
def car_compact(k):
    _car(k, w=6.0, l=12.6, body_h=3.2, cab0=-2.6, cab1=3.6, cab_h=2.1, wheel_r=1.0)


@prop("car_coupe", "vehicle", tags=("vehicle",))
def car_coupe(k):
    _car(k, w=6.4, l=15.0, body_h=3.0, cab0=-1.6, cab1=3.2, cab_h=1.7, wheel_r=1.15)


@prop("car_wagon", "vehicle", tags=("vehicle",))
def car_wagon(k):
    _car(k, w=6.4, l=16.4, body_h=3.4, cab0=-2.4, cab1=7.4, cab_h=2.1)


@prop("car_suv", "vehicle", tags=("vehicle",))
def car_suv(k):
    _car(k, w=6.8, l=16.2, body_h=4.4, cab0=-2.6, cab1=7.4, cab_h=2.4, wheel_r=1.4)


@prop("car_pickup", "vehicle", tags=("vehicle",))
def car_pickup(k):
    w, l = 6.8, 17.6
    _car(k, w=w, l=l, body_h=4.2, cab0=-3.2, cab1=1.6, cab_h=2.4, wheel_r=1.4)
    # carve the bed: dark floor + side rails
    k.box("metal_dark", -w / 2 + 0.4, 2.0, 2.4, w / 2 - 0.4, l / 2 - 0.6, 4.25, collide=False)


@prop("car_pickup_old", "vehicle", tags=("vehicle",))
def car_pickup_old(k):
    w, l = 6.6, 17.0
    _car(k, w=w, l=l, body_h=4.0, cab0=-3.0, cab1=1.4, cab_h=2.3, wheel_r=1.3,
         paint="car_rust")
    k.box("metal_dark", -w / 2 + 0.4, 1.8, 2.3, w / 2 - 0.4, l / 2 - 0.6, 4.05, collide=False)


@prop("car_van", "vehicle", tags=("vehicle",))
def car_van(k):
    w, l = 7.0, 18.0
    zb = 1.0
    k.box("$car", -w / 2, -l / 2 + 2.0, zb, w / 2, l / 2, 8.4)
    k.box("$car", -w / 2, -l / 2, zb, w / 2, -l / 2 + 2.1, 4.2)
    k.wedge("car_window", 0, -l / 2 + 1.4, 6.3, w - 0.6, 1.4, 4.2, yaw=math.pi, collide=False)
    k.box("car_window", -w / 2 - 0.02, -l / 2 + 2.6, 4.6, -w / 2, -l / 2 + 5.6, 7.4,
          collide=False)
    k.box("car_window", w / 2, -l / 2 + 2.6, 4.6, w / 2 + 0.02, -l / 2 + 5.6, 7.4, collide=False)
    for sx in (-1, 1):
        k.box("headlight", sx * 2.2 - 0.6, -l / 2 - 0.05, 2.8, sx * 2.2 + 0.6, -l / 2, 3.4,
              collide=False)
        k.box("taillight", sx * 3.0 - 0.3, l / 2, 3.0, sx * 3.0 + 0.3, l / 2 + 0.05, 5.0,
              collide=False)
    k.box("trim_dark", -w / 2, -l / 2 - 0.2, zb, w / 2, -l / 2, zb + 1.2, collide=False)
    for sy in (-1, 1):
        for sx in (-1, 1):
            car_wheel(k, sx * (w / 2 - 0.4), sy * (l / 2 - 3.2), 1.25, 0.9)


@prop("box_truck", "vehicle", tags=("vehicle",))
def box_truck(k):
    w, l = 8.0, 28.0
    k.box("$car", -w / 2, -l / 2, 1.4, w / 2, -l / 2 + 7.0, 6.4)
    k.box("car_window", -w / 2 + 0.3, -l / 2 - 0.02, 6.4, w / 2 - 0.3, -l / 2 + 4.0, 8.6,
          collide=False)
    k.box("$car", -w / 2, -l / 2 + 4.0, 6.4, w / 2, -l / 2 + 7.0, 9.0)
    k.box("metal_white", -w / 2 - 0.2, -l / 2 + 7.4, 1.8, w / 2 + 0.2, l / 2, 12.6)
    k.box("metal_dark", -w / 2, -l / 2 + 7.0, 1.0, w / 2, l / 2, 1.8)
    k.box("rollup_door", -w / 2 + 0.3, l / 2, 2.0, w / 2 - 0.3, l / 2 + 0.05, 12.2,
          collide=False)
    for sx in (-1, 1):
        k.box("headlight", sx * 2.6 - 0.6, -l / 2 - 0.05, 2.6, sx * 2.6 + 0.6, -l / 2, 3.2,
              collide=False)
    for y in (-l / 2 + 3.6, l / 2 - 5.0, l / 2 - 8.0):
        car_wheel(k, -w / 2 + 0.4, y, 1.6, 1.1)
        car_wheel(k, w / 2 - 0.4, y, 1.6, 1.1)


@prop("semi_tractor", "vehicle", tags=("vehicle",))
def semi_tractor(k):
    w, l = 8.4, 22.0
    k.box("$car", -w / 2, -l / 2, 2.0, w / 2, -l / 2 + 9.0, 8.0)
    k.box("$car", -w / 2, -l / 2 + 5.0, 8.0, w / 2, -l / 2 + 9.0, 12.4)
    k.box("car_window", -w / 2 + 0.3, -l / 2 + 4.98, 8.4, w / 2 - 0.3, -l / 2 + 5.0, 11.4,
          collide=False)
    k.box("metal_chrome", -w / 2 + 0.6, -l / 2 - 0.1, 2.6, w / 2 - 0.6, -l / 2, 6.6,
          collide=False)
    k.box("metal_dark", -3.0, -l / 2 + 9.0, 1.4, 3.0, l / 2, 3.0)
    for x in (-w / 2 - 0.2, w / 2 + 0.2):
        k.cyl("metal_chrome", x, -l / 2 + 9.5, 3.0, 0.4, 11.0, 8, collide=False)
    for y in (-l / 2 + 3.0, l / 2 - 5.0, l / 2 - 2.0):
        car_wheel(k, -w / 2 + 0.4, y, 1.8, 1.2)
        car_wheel(k, w / 2 - 0.4, y, 1.8, 1.2)


@prop("semi_trailer", "vehicle", tags=("vehicle",))
def semi_trailer(k):
    w, l = 8.4, 48.0
    k.box("$car", -w / 2, -l / 2, 4.0, w / 2, l / 2, 13.6)
    k.box("metal_dark", -w / 2 + 0.5, -l / 2 + 2.0, 0, -w / 2 + 0.9, -l / 2 + 2.4, 4.0)
    k.box("metal_dark", w / 2 - 0.9, -l / 2 + 2.0, 0, w / 2 - 0.5, -l / 2 + 2.4, 4.0)
    for y in (l / 2 - 8.0, l / 2 - 4.0):
        car_wheel(k, -w / 2 + 0.4, y, 1.8, 1.2)
        car_wheel(k, w / 2 - 0.4, y, 1.8, 1.2)


@prop("motorcycle", "vehicle", tags=("vehicle",), collide=[(-0.8, -3.4, 0, 0.8, 3.4, 3.4)])
def motorcycle(k):
    k.hcyl("rubber", 0, -2.6, 1.1, 1.1, 0.5, axis="x", sides=12)
    k.hcyl("rubber", 0, 2.6, 1.1, 1.1, 0.6, axis="x", sides=12)
    k.box("$car", -0.6, -1.4, 1.4, 0.6, 1.0, 2.8)
    k.box("leather_black", -0.55, 0.0, 2.8, 0.55, 2.6, 3.2)
    k.box("metal_chrome", -0.4, -1.0, 0.8, 0.4, 0.8, 1.6)
    k.obox("metal_chrome", 0, -2.2, 2.6, 0.2, 0.2, 3.4, rot_x(0.4))
    k.box("metal_chrome", -1.4, -2.9, 3.8, 1.4, -2.7, 4.0)
    k.box("headlight", -0.4, -3.1, 3.2, 0.4, -2.9, 3.7)


@prop("taxi", "vehicle", tags=("vehicle",))
def taxi(k):
    _car(k, paint="car_yellow")
    k.box("sign_white", -1.2, 0.4, 5.7, 1.2, 1.6, 6.5)
    k.box("trim_dark", -3.22, -3.0, 2.0, 3.22, 3.0, 2.3, collide=False)


@prop("police_cruiser", "vehicle", tags=("vehicle", "police"))
def police_cruiser(k):
    _car(k, paint="car_police", roof_paint="car_white")
    k.box("car_white", -3.22, -2.6, 1.4, 3.22, 3.8, 3.0, collide=False)
    k.box("lightbar_red", -2.2, 0.3, 5.7, -0.1, 1.3, 6.2, collide=False)
    k.box("lightbar_blue", 0.1, 0.3, 5.7, 2.2, 1.3, 6.2, collide=False)
    k.box("metal_dark", -2.4, -8.2, 1.4, 2.4, -7.8, 3.2, collide=False)


@prop("police_suv", "vehicle", tags=("vehicle", "police"))
def police_suv(k):
    _car(k, w=6.8, l=16.2, body_h=4.4, cab0=-2.6, cab1=7.4, cab_h=2.4, wheel_r=1.4,
         paint="car_police", roof_paint="car_white")
    k.box("car_white", -3.42, -2.6, 2.0, 3.42, 4.4, 4.0, collide=False)
    k.box("lightbar_red", -2.4, 0.3, 7.1, -0.1, 1.4, 7.6, collide=False)
    k.box("lightbar_blue", 0.1, 0.3, 7.1, 2.4, 1.4, 7.6, collide=False)


@prop("fire_engine", "vehicle", tags=("vehicle", "fire"))
def fire_engine(k):
    w, l = 8.6, 34.0
    k.box("car_fire", -w / 2, -l / 2, 1.8, w / 2, -l / 2 + 9.0, 10.0)
    k.box("car_window", -w / 2 + 0.3, -l / 2 - 0.02, 6.4, w / 2 - 0.3, -l / 2 + 3.0, 9.4,
          collide=False)
    k.box("car_fire", -w / 2, -l / 2 + 9.0, 1.8, w / 2, l / 2, 9.0)
    for i in range(4):
        y = -l / 2 + 10.0 + i * 5.5
        k.box("metal_chrome", -w / 2 - 0.05, y, 2.6, -w / 2, y + 5.0, 8.2, collide=False)
        k.box("metal_chrome", w / 2, y, 2.6, w / 2 + 0.05, y + 5.0, 8.2, collide=False)
    k.box("metal_chrome", -3.4, -l / 2 + 12.0, 9.0, 3.4, l / 2 - 2.0, 10.6, collide=False)
    k.box("metal_white", -w / 2 - 0.06, -l / 2, 5.0, w / 2 + 0.06, l / 2, 5.6, collide=False)
    k.box("lightbar_red", -3.5, -l / 2 + 2.0, 10.0, 3.5, -l / 2 + 3.0, 10.7, collide=False)
    k.box("metal_chrome", -w / 2 + 0.3, -l / 2 - 0.4, 1.8, w / 2 - 0.3, -l / 2, 3.2,
          collide=False)
    for y in (-l / 2 + 4.0, l / 2 - 8.0, l / 2 - 4.4):
        car_wheel(k, -w / 2 + 0.4, y, 1.8, 1.2, hub="metal_chrome")
        car_wheel(k, w / 2 - 0.4, y, 1.8, 1.2, hub="metal_chrome")


@prop("ladder_truck", "vehicle", tags=("vehicle", "fire"))
def ladder_truck(k):
    w, l = 8.6, 40.0
    k.box("car_fire", -w / 2, -l / 2, 1.8, w / 2, -l / 2 + 9.0, 10.0)
    k.box("car_window", -w / 2 + 0.3, -l / 2 - 0.02, 6.4, w / 2 - 0.3, -l / 2 + 3.0, 9.4,
          collide=False)
    k.box("car_fire", -w / 2, -l / 2 + 9.0, 1.8, w / 2, l / 2, 7.4)
    k.box("metal_white", -w / 2 - 0.06, -l / 2, 5.0, w / 2 + 0.06, l / 2, 5.6, collide=False)
    k.cyl("metal_white", 0, l / 2 - 6.0, 7.4, 2.2, 1.6, 12)
    k.obox("metal_chrome", 0, -2.0, 10.4, 3.6, 34.0, 1.4, rot_x(-0.04), collide=False)
    for i in range(14):
        k.box("metal_chrome", -1.6, -18.0 + i * 2.4, 10.8, 1.6, -17.8 + i * 2.4, 11.4,
              collide=False)
    k.box("lightbar_red", -3.5, -l / 2 + 2.0, 10.0, 3.5, -l / 2 + 3.0, 10.7, collide=False)
    for y in (-l / 2 + 4.0, l / 2 - 9.0, l / 2 - 5.2):
        car_wheel(k, -w / 2 + 0.4, y, 1.8, 1.2, hub="metal_chrome")
        car_wheel(k, w / 2 - 0.4, y, 1.8, 1.2, hub="metal_chrome")


@prop("ambulance", "vehicle", tags=("vehicle",))
def ambulance(k):
    w, l = 7.6, 22.0
    k.box("car_white", -w / 2, -l / 2, 1.2, w / 2, -l / 2 + 6.0, 5.6)
    k.wedge("car_window", 0, -l / 2 + 4.6, 7.0, w - 0.6, 2.8, 2.8, yaw=math.pi, collide=False)
    k.box("car_white", -w / 2, -l / 2 + 6.0, 1.2, w / 2, l / 2, 10.4)
    k.box("fire_red", -w / 2 - 0.05, -l / 2 + 6.0, 6.0, w / 2 + 0.05, l / 2, 6.8, collide=False)
    k.box("lightbar_red", -3.0, -l / 2 + 6.0, 10.4, 3.0, -l / 2 + 7.0, 11.0, collide=False)
    for y in (-l / 2 + 3.4, l / 2 - 4.0):
        car_wheel(k, -w / 2 + 0.4, y, 1.4, 1.0)
        car_wheel(k, w / 2 - 0.4, y, 1.4, 1.0)


@prop("city_bus", "vehicle", tags=("vehicle",))
def city_bus(k):
    w, l = 8.6, 40.0
    k.box("$car", -w / 2, -l / 2, 1.4, w / 2, l / 2, 10.8)
    k.box("car_window", -w / 2 - 0.03, -l / 2 + 2.0, 5.4, w / 2 + 0.03, l / 2 - 3.0, 9.0,
          collide=False)
    k.box("car_window", -w / 2 + 0.4, -l / 2 - 0.03, 4.0, w / 2 - 0.4, -l / 2, 9.6,
          collide=False)
    k.box("metal_white", -w / 2 - 0.04, -l / 2, 1.4, w / 2 + 0.04, l / 2, 3.0, collide=False)
    k.box("neon_orange", -2.6, -l / 2 - 0.05, 9.7, 2.6, -l / 2, 10.5, collide=False)
    for y in (-l / 2 + 6.0, l / 2 - 8.0):
        car_wheel(k, -w / 2 + 0.4, y, 1.6, 1.1)
        car_wheel(k, w / 2 - 0.4, y, 1.6, 1.1)


@prop("tow_truck", "vehicle", tags=("vehicle",))
def tow_truck(k):
    car_pickup(k)
    k.box("metal_yellow", -0.4, 4.0, 4.2, 0.4, 5.0, 9.0, collide=False)
    k.obox("metal_yellow", 0, 6.4, 8.0, 0.6, 5.0, 0.6, rot_x(-0.5), collide=False)
    k.box("lightbar_red", -2.0, -0.4, 6.6, 2.0, 0.4, 7.0, collide=False)


@prop("car_wreck", "vehicle", tags=("vehicle",))
def car_wreck(k):
    _car(k, paint="car_rust")
    k.box("rock_dark", -3.0, -7.0, 0, 3.0, 7.0, 0.9)


@prop("golf_cart", "vehicle", tags=("vehicle",), detail=2)
def golf_cart(k):
    k.box("$car", -2.2, -3.6, 1.0, 2.2, 3.6, 2.6)
    k.box("roof_metal", -2.3, -3.0, 6.2, 2.3, 3.2, 6.5)
    for (x, y) in ((-2.0, -2.8), (2.0, -2.8), (-2.0, 2.8), (2.0, 2.8)):
        k.box("metal_gray", x - 0.1, y - 0.1, 2.6, x + 0.1, y + 0.1, 6.2, collide=False)
    for sy in (-1, 1):
        for sx in (-1, 1):
            car_wheel(k, sx * 2.0, sy * 2.6, 0.8, 0.6)


# --- Boats (z = 0 is the waterline) ----------------------------------------------------

def _hull(k, mat, w, l, depth, freeboard, deck="deck_teak"):
    hw = w / 2
    bow = -l / 2
    stern = l / 2
    top = [(-hw, stern), (hw, stern), (hw, bow + l * 0.35), (0, bow), (-hw, bow + l * 0.35)]
    bot = [(-hw * 0.5, stern - 0.6), (hw * 0.5, stern - 0.6), (hw * 0.4, bow + l * 0.4),
           (0, bow + l * 0.12), (-hw * 0.4, bow + l * 0.4)]
    verts = [(x, y, freeboard) for (x, y) in top] + [(x, y, -depth) for (x, y) in bot]
    n = len(top)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    k.mesh(mat, verts, faces)
    inset = [(x * 0.86, y * 0.94 + 0.2) for (x, y) in top]
    dverts = [(x, y, freeboard - 0.6) for (x, y) in inset] + \
        [(x, y, freeboard - 0.45) for (x, y) in inset]
    dfaces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        dfaces.append((i, j, n + j, n + i))
    k.mesh(deck, dverts, dfaces)


@prop("boat_dinghy", "boat", tags=("boat",), collide=[(-2.5, -6, -1, 2.5, 6, 1.6)])
def boat_dinghy(k):
    _hull(k, "$hull", 5.0, 12.0, 1.0, 1.6, deck="wood_raw")
    k.box("wood_raw", -2.0, 0.0, 0.6, 2.0, 0.8, 1.0)
    k.box("plastic_black", -0.6, 5.6, 0.4, 0.6, 6.6, 2.6)


@prop("boat_motor", "boat", tags=("boat",), collide=[(-4, -11, -1.5, 4, 11, 3)])
def boat_motor(k):
    _hull(k, "$hull", 8.0, 22.0, 1.6, 2.6)
    k.box("glass_tint", -2.6, -3.0, 2.2, 2.6, -2.4, 4.6)
    k.box("leather_cream", -3.0, 2.0, 2.0, 3.0, 6.0, 3.0)
    k.box("plastic_black", -1.0, 10.4, 0.0, 1.0, 11.8, 3.4)


@prop("boat_fishing", "boat", tags=("boat",), collide=[(-6, -18, -2.5, 6, 18, 12)])
def boat_fishing(k):
    _hull(k, "$hull", 12.0, 36.0, 3.0, 4.0, deck="wood_weathered")
    k.box("hull_white", -4.0, -8.0, 3.6, 4.0, 2.0, 11.0)
    k.box("car_window", -4.05, -7.0, 8.0, 4.05, 1.0, 10.0, collide=False)
    k.box("roof_metal", -4.4, -8.4, 11.0, 4.4, 2.4, 11.5)
    k.cyl("metal_dark", 0, -2.0, 11.5, 0.3, 10.0, 6, collide=False)
    k.box("metal_dark", -0.15, 4.0, 3.6, 0.15, 4.3, 18.0, collide=False)
    k.obox("metal_dark", 0, 10.0, 14.0, 0.25, 14.0, 0.25, rot_x(0.7), collide=False)
    k.ball("net", 0, 12.0, 4.6, 3.0, 2.6, 1.0)
    k.box("plastic_blue", 2.0, 6.0, 3.6, 5.0, 9.0, 5.4)


@prop("boat_sail", "boat", tags=("boat",), collide=[(-4.5, -13, -2, 4.5, 13, 3)])
def boat_sail(k):
    _hull(k, "$hull", 9.0, 26.0, 2.0, 2.6)
    k.box("hull_white", -2.6, -2.0, 2.0, 2.6, 6.0, 4.4)
    k.cyl("metal_white", 0, -3.0, 2.0, 0.25, 34.0, 6, collide=False)
    k.box("metal_white", -0.15, -3.0, 6.0, 0.15, 7.0, 6.4, collide=False)
    k.box("fabric_white", -0.08, -2.8, 6.4, 0.08, 6.6, 14.0, collide=False)


@prop("boat_yacht", "boat", tags=("boat",), collide=[(-7, -21, -2.5, 7, 21, 14)])
def boat_yacht(k):
    _hull(k, "hull_white", 14.0, 42.0, 3.0, 4.6)
    k.box("hull_white", -5.0, -10.0, 4.2, 5.0, 12.0, 9.6)
    k.box("glass_tint", -5.05, -9.0, 5.6, 5.05, 11.0, 8.6, collide=False)
    k.box("hull_white", -4.0, -6.0, 9.6, 4.0, 6.0, 13.0)
    k.box("glass_tint", -4.05, -5.0, 10.4, 4.05, -2.0, 12.4, collide=False)
    k.box("metal_chrome", -4.6, -6.6, 13.0, 4.6, 7.0, 13.4)


@prop("boat_pontoon", "boat", tags=("boat",), collide=[(-5, -12, -1.5, 5, 12, 6)])
def boat_pontoon(k):
    for x in (-3.4, 3.4):
        k.hcyl("metal_chrome", x, 0, -0.2, 1.3, 24.0, axis="y", sides=10)
    k.box("deck_teak", -5.0, -12.0, 1.0, 5.0, 12.0, 1.5)
    k.box("$fabric", -4.6, 2.0, 1.5, 4.6, 10.0, 3.2)
    k.box("roof_metal", -4.6, 0.0, 7.4, 4.6, 10.0, 7.8)
    for (x, y) in ((-4.4, 0.4), (4.4, 0.4), (-4.4, 9.6), (4.4, 9.6)):
        k.box("metal_chrome", x - 0.1, y - 0.1, 1.5, x + 0.1, y + 0.1, 7.4, collide=False)


# --- Rolling stock (static set dressing in the rail yard) --------------------------------

def _bogies(k, l, gauge=4.6):
    for y in (-l / 2 + 6.0, l / 2 - 6.0):
        k.box("metal_dark", -3.0, y - 3.0, 0.8, 3.0, y + 3.0, 2.4)
        for dy in (-1.6, 1.6):
            for x in (-gauge / 2, gauge / 2):
                k.hcyl("metal_dark", x, y + dy, 1.4, 1.4, 0.5, axis="x", sides=10,
                       collide=False)


@prop("rail_boxcar", "rail", tags=("vehicle", "rail"))
def rail_boxcar(k):
    l = 48.0
    _bogies(k, l)
    k.box("metal_dark", -4.4, -l / 2, 2.4, 4.4, l / 2, 3.2)
    k.box("$car", -4.6, -l / 2 + 0.5, 3.2, 4.6, l / 2 - 0.5, 15.0)
    for i in range(12):
        y = -l / 2 + 2.0 + i * 3.8
        k.box("$car", -4.75, y, 3.4, 4.75, y + 0.3, 14.8, collide=False)
    k.box("metal_dark", -4.8, -4.0, 4.0, 4.8, 4.0, 14.0, collide=False)
    k.box("metal_gray", -4.7, -l / 2 + 0.5, 15.0, 4.7, l / 2 - 0.5, 15.5)


@prop("rail_flatcar", "rail", tags=("vehicle", "rail"))
def rail_flatcar(k):
    l = 48.0
    _bogies(k, l)
    k.box("metal_dark", -4.4, -l / 2, 2.4, 4.4, l / 2, 3.6)
    k.box("$metal", -4.0, -20.0, 3.6, 4.0, 20.0, 12.2)
    for i in range(16):
        y = -19.0 + i * 2.5
        k.box("$metal", -4.15, y, 3.9, 4.15, y + 0.6, 11.9, collide=False)


@prop("rail_locomotive", "rail", tags=("vehicle", "rail"))
def rail_locomotive(k):
    l = 56.0
    _bogies(k, l)
    k.box("metal_dark", -4.6, -l / 2, 2.4, 4.6, l / 2, 3.6)
    k.box("$car", -4.0, -l / 2 + 10.0, 3.6, 4.0, l / 2 - 1.0, 13.0)
    k.box("$car", -4.6, -l / 2 + 1.0, 3.6, 4.6, -l / 2 + 10.0, 15.5)
    k.box("car_window", -4.62, -l / 2 + 2.0, 11.0, 4.62, -l / 2 + 9.0, 14.0, collide=False)
    k.box("car_window", -3.6, -l / 2 + 0.98, 11.0, 3.6, -l / 2 + 1.0, 14.0, collide=False)
    k.box("hazard_yellow", -4.65, -l / 2, 4.0, 4.65, l / 2, 5.0, collide=False)
    k.box("headlight", -0.8, -l / 2 - 0.05, 13.0, 0.8, -l / 2, 14.0, collide=False)
    for y in (-6.0, 6.0, 16.0):
        k.cyl("metal_dark", 0.0, y, 13.0, 1.4, 1.2, 10, collide=False)
