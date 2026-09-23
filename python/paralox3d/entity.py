"""High-level scene objects with low-boilerplate properties."""

from .math import Vec3

class Object:
    __slots__=("_engine","_handle","_model","_position","_rotation","_scale","_components","name")
    def __init__(self,model="cube",position=(0,0,0),rotation=(0,0,0),scale=(1,1,1),name=None,engine=None,scene=None):
        from .engine import get_default_engine
        from .scene import current_scene
        self._engine=engine or get_default_engine()
        self._handle=self._engine._create_entity()
        self._model=model; self._position=Vec3(*position); self._rotation=Vec3(*rotation); self._scale=Vec3(*scale)
        self._components=[]; self.name=name or model
        self._engine._set_position(self._handle,self._position)
        self._engine.register(self)
        target=scene or current_scene()
        if target is not None: target.add(self)
    @property
    def model(self): return self._model
    @property
    def position(self): return self._position
    @position.setter
    def position(self,value):
        self._position=Vec3(*value); self._engine._set_position(self._handle,self._position)
    @property
    def x(self): return self._position.x
    @x.setter
    def x(self,value): self.position=(value,self.y,self.z)
    @property
    def y(self): return self._position.y
    @y.setter
    def y(self,value): self.position=(self.x,value,self.z)
    @property
    def z(self): return self._position.z
    @z.setter
    def z(self,value): self.position=(self.x,self.y,value)
    @property
    def rotation(self): return self._rotation
    @rotation.setter
    def rotation(self,value): self._rotation=Vec3(*value)
    @property
    def scale(self): return self._scale
    @scale.setter
    def scale(self,value): self._scale=Vec3(*value)
    def move(self,x=0,y=0,z=0):
        self.position=(self.x+x,self.y+y,self.z+z); return self
    def add(self,component):
        component.owner=self; self._components.append(component); component.on_start(); return component
    def _update_components(self):
        for component in self._components: component.update()
    def _serialize(self):
        return {"name":self.name,"model":self.model,"position":list(self.position),"rotation":list(self.rotation),"scale":list(self.scale)}

Entity=Object
