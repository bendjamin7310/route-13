"""Plain records shared by the building engine, the world and the exporters."""

from __future__ import annotations

import math


class PropPlace:
    """One instance of a kit prop."""

    __slots__ = ("name", "x", "y", "z", "yaw", "scale", "channels", "interior", "room", "meta")

    def __init__(self, name, x, y, z, yaw=0.0, scale=(1.0, 1.0, 1.0), channels=None,
                 interior=True, room=None, meta=None):
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.yaw = yaw
        self.scale = scale
        self.channels = channels or {}
        self.interior = interior
        self.room = room
        self.meta = meta

    def moved(self, xf):
        p = xf.point((self.x, self.y, self.z))
        return PropPlace(self.name, p[0], p[1], p[2], self.yaw + xf.yaw, self.scale,
                         self.channels, self.interior, self.room, self.meta)


class LightRec:
    """A light source.  ``schedule`` drives the Roblox day/night script:

    always   - on day and night (interiors of open businesses, emergency)
    night    - street / exterior lights, on from dusk to dawn
    res      - residential interiors, on in the evening for a random subset
    biz      - shops/offices: on during opening hours and most of the evening
    late     - bars/diners/motel office: on all evening and night
    work     - industrial: on in working hours, some left on overnight
    dark     - never (abandoned buildings keep fixtures but no light)
    """

    __slots__ = ("x", "y", "z", "color", "range", "brightness", "kind", "schedule", "room",
                 "shadows", "dir")

    def __init__(self, x, y, z, color=(1.0, 0.85, 0.7), range_=20.0, brightness=1.0,
                 kind="point", schedule="res", room=None, shadows=False, dir_=None):
        self.x, self.y, self.z = x, y, z
        self.color = color
        self.range = range_
        self.brightness = brightness
        self.kind = kind
        self.schedule = schedule
        self.room = room
        self.shadows = shadows
        self.dir = dir_ or (0.0, 0.0, -1.0)

    def moved(self, xf):
        p = xf.point((self.x, self.y, self.z))
        d = xf.vec(self.dir)
        return LightRec(p[0], p[1], p[2], self.color, self.range, self.brightness, self.kind,
                        self.schedule, self.room, self.shadows, d)


class Marker:
    """Gameplay reference point (entrances, spawns, POIs, safehouse spots ...)."""

    __slots__ = ("kind", "x", "y", "z", "yaw", "label", "meta")

    def __init__(self, kind, x, y, z, yaw=0.0, label="", meta=None):
        self.kind = kind
        self.x, self.y, self.z = x, y, z
        self.yaw = yaw
        self.label = label
        self.meta = meta or {}

    def moved(self, xf):
        p = xf.point((self.x, self.y, self.z))
        return Marker(self.kind, p[0], p[1], p[2], self.yaw + xf.yaw, self.label, self.meta)


class SignRec:
    """A text sign: a board (or bare letters) facing ``yaw`` (its front faces -Y local)."""

    __slots__ = ("text", "x", "y", "z", "yaw", "w", "h", "bg", "fg", "neon", "board")

    def __init__(self, text, x, y, z, yaw, w, h, bg="sign_red", fg="sign_white", neon=False,
                 board=True):
        self.text = text
        self.x, self.y, self.z = x, y, z
        self.yaw = yaw
        self.w, self.h = w, h
        self.bg, self.fg = bg, fg
        self.neon = neon
        self.board = board

    def moved(self, xf):
        p = xf.point((self.x, self.y, self.z))
        return SignRec(self.text, p[0], p[1], p[2], self.yaw + xf.yaw, self.w, self.h, self.bg,
                       self.fg, self.neon, self.board)


def yaw_facing(dx, dy):
    """Yaw that turns local -Y toward the direction (dx, dy)."""
    return math.atan2(dx, -dy)
