"""Paralox3D: a low-boilerplate Python 3D engine."""
from .engine import Engine,start
from .entity import Object,Entity
from .math import Vec3
from .scene import Scene,current_scene
from .components import Component,Script
from .input import key,pressed
__all__=["Engine","start","Object","Entity","Vec3","Scene","current_scene","Component","Script","key","pressed"]
