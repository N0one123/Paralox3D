"""High-level scene objects with low-boilerplate properties."""
from __future__ import annotations
import math
from .math import Vec3
from .collision import Collider

def _vec(v): return v if isinstance(v,Vec3) else Vec3(*v)
def _rotate(v,r):
    yaw,pitch,roll=map(math.radians,(r.y,r.x,r.z))
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch); cr,sr=math.cos(roll),math.sin(roll)
    x=v.x*cy+v.z*sy; z=-v.x*sy+v.z*cy
    y2=v.y*cp-z*sp; z2=v.y*sp+z*cp
    return Vec3(x*cr-y2*sr,x*sr+y2*cr,z2)

class Object:
    __slots__=("__dict__","_id","_engine","_handle","_model","_position","_rotation","_scale","_components","name","collider","parent","_children","_enabled","_visible","tags","persistent","_local_position","_local_rotation","_local_scale","_color","texture","_opacity")
    def __init__(self,model="cube",position=(0,0,0),rotation=(0,0,0),scale=(1,1,1),name=None,engine=None,scene=None,parent=None):
        from .engine import get_default_engine
        from .scene import current_scene
        self._engine=engine or get_default_engine(); self._id=self._engine._next_object_id(); self._handle=self._engine._create_entity()
        self._model=model; self._local_position=Vec3(*position); self._local_rotation=Vec3(*rotation)
        s=(scale,scale,scale) if isinstance(scale,(int,float)) else scale; self._local_scale=Vec3(*s)
        self._position=self._local_position.copy(); self._rotation=self._local_rotation.copy(); self._scale=self._local_scale.copy()
        self._components=[]; self.name=name or model; self.parent=None; self._children=[]
        self._enabled=True; self._visible=True; self.tags=set(); self.persistent=False; self._color=(1.0,1.0,1.0); self.texture=None; self._opacity=1.0
        self.collider=Collider(self); self._engine.register(self); self._push()
        if parent is not None:self.set_parent(parent)
        target=scene or current_scene()
        if target is not None:target.add(self)
    def _push(self):
        self._engine._set_position(self._handle,self._position); self._engine._set_rotation(self._handle,self._rotation); self._engine._set_scale(self._handle,self._scale)
        if hasattr(self._engine,"_set_enabled"):self._engine._set_enabled(self._handle,self._enabled,self._visible)
        if hasattr(self._engine,"_set_color"):self._engine._set_color(self._handle,*self._color,self._opacity)
    @property
    def id(self):return self._id
    @property
    def enabled(self):return self._enabled
    @enabled.setter
    def enabled(self,v):self._enabled=bool(v);self._push()
    @property
    def visible(self):return self._visible
    @visible.setter
    def visible(self,v):self._visible=bool(v);self._push()
    @property
    def color(self):return self._color
    @color.setter
    def color(self,v):
        if len(v)!=3:raise ValueError("color must be an RGB 3-tuple.")
        self._color=tuple(max(0.0,min(1.0,float(x))) for x in v);self._push()
    @property
    def opacity(self):return self._opacity
    @opacity.setter
    def opacity(self,v):self._opacity=max(0.0,min(1.0,float(v)));self._push()
    @property
    def model(self):return self._model
    @property
    def position(self):return self._position
    @position.setter
    def position(self,v):self._local_position=_vec(v);self._recompute_world()
    @property
    def x(self):return self._position.x
    @x.setter
    def x(self,v):self.position=(v,self.y,self.z)
    @property
    def y(self):return self._position.y
    @y.setter
    def y(self,v):self.position=(self.x,v,self.z)
    @property
    def z(self):return self._position.z
    @z.setter
    def z(self,v):self.position=(self.x,self.y,v)
    @property
    def rotation(self):return self._rotation
    @rotation.setter
    def rotation(self,v):self._local_rotation=_vec(v);self._recompute_world()
    @property
    def scale(self):return self._scale
    @scale.setter
    def scale(self,v):self._local_scale=Vec3(*((v,v,v) if isinstance(v,(int,float)) else v));self._recompute_world()
    @property
    def local_position(self):return self._local_position
    @local_position.setter
    def local_position(self,v):self._local_position=_vec(v);self._recompute_world()
    @property
    def local_rotation(self):return self._local_rotation
    @local_rotation.setter
    def local_rotation(self,v):self._local_rotation=_vec(v);self._recompute_world()
    @property
    def local_scale(self):return self._local_scale
    @local_scale.setter
    def local_scale(self,v):self._local_scale=_vec(v);self._recompute_world()
    @property
    def forward(self):return _rotate(Vec3(0,0,1),self._rotation).normalized()
    @property
    def right(self):return _rotate(Vec3(1,0,0),self._rotation).normalized()
    @property
    def up(self):return _rotate(Vec3(0,1,0),self._rotation).normalized()
    def _recompute_world(self):
        if self.parent:
            self._position=self.parent._position+_rotate(self._local_position,self.parent._rotation)
            self._rotation=self.parent._rotation+self._local_rotation
            self._scale=Vec3(self.parent._scale.x*self._local_scale.x,self.parent._scale.y*self._local_scale.y,self.parent._scale.z*self._local_scale.z)
        else:self._position=self._local_position.copy();self._rotation=self._local_rotation.copy();self._scale=self._local_scale.copy()
        self._push()
        for c in tuple(self._children):c._recompute_world()
    def set_parent(self,parent):
        if parent is self:raise ValueError("An Object cannot be its own parent.")
        if self.parent and self in self.parent._children:self.parent._children.remove(self)
        self.parent=parent
        if parent and self not in parent._children:parent._children.append(self)
        self._recompute_world();return self
    def detach(self):return self.set_parent(None)
    @property
    def children(self):return tuple(self._children)
    @property
    def components(self):return tuple(self._components)
    def add_tag(self,tag):self.tags.add(str(tag));return self
    def remove_tag(self,tag):self.tags.discard(str(tag));return self
    def has_tag(self,tag):return str(tag) in self.tags
    def move(self,x=0,y=0,z=0):return self.translate(x,y,z)
    def translate(self,x=0,y=0,z=0):self._local_position=self._local_position+Vec3(x,y,z);self._recompute_world();return self
    def rotate(self,x=0,y=0,z=0):self._local_rotation=self._local_rotation+Vec3(x,y,z);self._recompute_world();return self
    def scale_by(self,x=1,y=None,z=None):
        y=x if y is None else y;z=x if z is None else z;self._local_scale=Vec3(self._local_scale.x*x,self._local_scale.y*y,self._local_scale.z*z);self._recompute_world();return self
    def look_at(self,target):
        d=_vec(target.position if hasattr(target,"position") else target)-self.position;flat=math.hypot(d.x,d.z)
        self.rotation=(math.degrees(math.atan2(d.y,flat)),math.degrees(math.atan2(d.x,d.z)),0);return self
    def distance_to(self,target):return (_vec(target.position if hasattr(target,"position") else target)-self.position).length()
    def move_forward(self,distance):return self.translate(*(self.forward*distance))
    def move_right(self,distance):return self.translate(*(self.right*distance))
    def move_up(self,distance):return self.translate(*(self.up*distance))
    def add(self,component):component.owner=self;self._components.append(component);component.on_start();return component
    def get(self,component_type):return next((c for c in self._components if isinstance(c,component_type)),None)
    def remove(self,component):
        if component in self._components:self._components.remove(component);component.on_destroy();component.owner=None
    def destroy(self):
        if self not in self._engine._objects:return
        for c in tuple(self._children):c.destroy()
        if self.parent and self in self.parent._children:self.parent._children.remove(self)
        for c in tuple(self._components):c.on_destroy()
        self._components.clear();self.enabled=False;self.visible=False;self._engine.unregister(self);self._push()
    def _update_components(self):
        if self.enabled:
            for c in tuple(self._components):
                if c.enabled:c.update()
    def _serialize(self):return {"id":self.id,"name":self.name,"model":self.model,"position":list(self.position),"rotation":list(self.rotation),"scale":list(self.scale),"tags":sorted(self.tags),"persistent":self.persistent}
Entity=Object
