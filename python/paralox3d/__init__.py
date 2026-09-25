"""Paralox3D public API."""
from .engine import Engine,start,get_default_engine
from .entity import Object,Entity
from .math import Vec3
from .scene import Scene,current_scene
from .components import Component,Script,FPSController,CharacterController
from .input import key,held,any_held,pressed,bind,action,action_pressed,mouse
from .modes import modes
from .clock import dt
from .camera import camera,Camera
from .collision import Collider,Collision,raycast,boxcast,spherecast,overlap_box,overlap_sphere,RaycastHit\nfrom .timing import Timer,after,every,cancel
def find(name):return next((o for o in get_default_engine()._objects if o.name==name),None)
def find_all(name):return [o for o in get_default_engine()._objects if o.name==name]
def find_with_tag(tag):return [o for o in get_default_engine()._objects if tag in o.tags]
__all__=["Engine","start","get_default_engine","Object","Entity","Vec3","Scene","current_scene","Component","Script","FPSController","CharacterController","key","held","any_held","pressed","bind","action","action_pressed","mouse","modes","dt","camera","Camera","Collider","Collision","raycast","boxcast","spherecast","overlap_box","overlap_sphere","RaycastHit","Timer","after","every","cancel","find","find_all","find_with_tag"]
