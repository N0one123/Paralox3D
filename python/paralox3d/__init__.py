"""Paralox3D: a low-boilerplate Python 3D engine."""
from .engine import Engine,start
from .entity import Object,Entity
from .math import Vec3
from .scene import Scene,current_scene
from .components import Component,Script
from .input import key,held,pressed
from .modes import modes
from .clock import dt
from .camera import camera, Camera
from .collision import Collider, Collision
__all__=["Engine","start","Object","Entity","Vec3","Scene","current_scene","Component","Script","key","held","pressed","modes","dt","camera","Camera","Collider","Collision"]
