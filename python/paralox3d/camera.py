"""Simple built-in camera for Paralox3D."""

from .math import Vec3
import math


class Camera:
    """Default camera. Left-drag rotates; right-drag pans."""

    def __init__(self):
        self._position = Vec3()
        self._rotation = Vec3()
        self._dirty = True

    def _mark_dirty(self):
        self._dirty = True

    def _clear_dirty(self):
        self._dirty = False

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = Vec3(*value)
        self._mark_dirty()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = Vec3(*value)
        self._mark_dirty()

    @property
    def x(self):
        return self._position.x

    @x.setter
    def x(self, value):
        self._position.x = float(value)
        self._mark_dirty()

    @property
    def y(self):
        return self._position.y

    @y.setter
    def y(self, value):
        self._position.y = float(value)
        self._mark_dirty()

    @property
    def z(self):
        return self._position.z

    @z.setter
    def z(self, value):
        self._position.z = float(value)
        self._mark_dirty()

    @property
    def pitch(self):
        return self._rotation.x

    @pitch.setter
    def pitch(self, value):
        self._rotation.x = float(value)
        self._mark_dirty()

    @property
    def yaw(self):
        return self._rotation.y

    @yaw.setter
    def yaw(self, value):
        self._rotation.y = float(value)
        self._mark_dirty()

    @property
    def roll(self):
        return self._rotation.z

    @roll.setter
    def roll(self, value):
        self._rotation.z = float(value)
        self._mark_dirty()

    def move(self, x=0.0, y=0.0, z=0.0):
        self.x += x
        self.y += y
        self.z += z

    def _update_controls(self, mouse):
        """Update the built-in click-and-drag camera controls."""
        if mouse.left:
            self.yaw += mouse.dx * 0.25
            self.pitch += mouse.dy * 0.25
            self.pitch = max(-89.0, min(89.0, self.pitch))

        if mouse.wheel:
            yaw = math.radians(self.yaw)
            pitch = math.radians(self.pitch)
            forward = Vec3(
                math.sin(yaw) * math.cos(pitch),
                math.sin(pitch),
                -math.cos(yaw) * math.cos(pitch),
            )
            self.position = self.position + forward * (mouse.wheel * 0.5)

        if mouse.right:
            yaw = math.radians(self.yaw)
            pitch = math.radians(self.pitch)
            roll = math.radians(self.roll)

            cy, sy = math.cos(yaw), math.sin(yaw)
            cp, sp = math.cos(pitch), math.sin(pitch)
            cr, sr = math.cos(roll), math.sin(roll)

            right = Vec3(
                cy * cr + sy * sp * sr,
                cp * sr,
                -sy * cr + cy * sp * sr,
            )
            up = Vec3(
                -cy * sr + sy * sp * cr,
                cp * cr,
                sy * sr + cy * sp * cr,
            )

            pan_speed = 0.0065
            self.position = self.position - right * (mouse.dx * pan_speed)
            self.position = self.position + up * (mouse.dy * pan_speed)

    def look_at(self, target):
        # Accept either Vec3 or a plain (x, y, z) tuple/list.
        if not hasattr(target, "x"):
            target = Vec3(*target)

        dx = target.x - self.x
        dy = target.y - self.y
        dz = target.z - self.z

        # Camera convention: yaw=0 looks along -Z.
        self.yaw = math.degrees(math.atan2(dx, -dz))
        self.pitch = math.degrees(math.atan2(dy, math.hypot(dx, dz)))


camera = Camera()
