"""Small, allocation-friendly math types for the public API."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def as_tuple(self):
        return (self.x, self.y, self.z)
