"""Simple axis-aligned colliders and collision queries."""

from .math import Vec3


class Collider:
    """An axis-aligned bounding box attached to an Object."""

    __slots__ = ("owner", "enabled", "_size", "_offset")

    def __init__(self, owner, size=None, offset=(0, 0, 0), enabled=True):
        self.owner = owner
        self.enabled = bool(enabled)
        self._size = Vec3(*(size if size is not None else owner.scale))
        self._offset = Vec3(*offset)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = Vec3(*value)

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = Vec3(*value)

    @property
    def position(self):
        return Vec3(
            self.owner.x + self._offset.x,
            self.owner.y + self._offset.y,
            self.owner.z + self._offset.z,
        )

    @property
    def min(self):
        p = self.position
        return Vec3(
            p.x - abs(self._size.x) * 0.5,
            p.y - abs(self._size.y) * 0.5,
            p.z - abs(self._size.z) * 0.5,
        )

    @property
    def max(self):
        p = self.position
        return Vec3(
            p.x + abs(self._size.x) * 0.5,
            p.y + abs(self._size.y) * 0.5,
            p.z + abs(self._size.z) * 0.5,
        )


def _overlaps(a, b):
    if not a.enabled or not b.enabled:
        return False

    amin, amax = a.min, a.max
    bmin, bmax = b.min, b.max

    return (
        amin.x <= bmax.x and amax.x >= bmin.x and
        amin.y <= bmax.y and amax.y >= bmin.y and
        amin.z <= bmax.z and amax.z >= bmin.z
    )


def Collision(object1, object2=None):
    """Check one collision, or return every object colliding with object1."""

    if object1 is None or not hasattr(object1, "collider"):
        raise TypeError("Collision() expects an Object as object1.")

    if object2 is not None:
        if not hasattr(object2, "collider"):
            raise TypeError("Collision() expects an Object as object2.")
        return _overlaps(object1.collider, object2.collider)

    return [
        other
        for other in object1._engine._objects
        if other is not object1 and _overlaps(object1.collider, other.collider)
    ]
