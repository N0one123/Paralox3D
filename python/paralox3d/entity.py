"""Lightweight Python-side entity handles."""

from __future__ import annotations

from .math import Vec3


class Entity:
    __slots__ = ("_engine", "_handle", "_position")

    def __init__(self, engine, model=None, position=(0.0, 0.0, 0.0)):
        self._engine = engine
        self._handle = engine._create_entity()
        self._position = Vec3(*position)
        engine._set_position(self._handle, self._position)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = Vec3(*value)
        self._engine._set_position(self._handle, self._position)
