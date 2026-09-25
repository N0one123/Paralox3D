"""AABB collision, triggers, layers and ray queries."""
from .math import Vec3
import math
class Collider:
    __slots__=("owner","enabled","_size","_offset","is_trigger","layer","collides_with")
    def __init__(self,owner,size=None,offset=(0,0,0),enabled=True,is_trigger=False,layer="default",collides_with=None):
        self.owner=owner;self.enabled=bool(enabled);self._size=Vec3(*(size if size is not None else owner.scale));self._offset=Vec3(*offset);self.is_trigger=is_trigger;self.layer=layer;self.collides_with=set(collides_with or {"default"})
    size=property(lambda s:s._size,lambda s,v:setattr(s,"_size",Vec3(*v)))
    offset=property(lambda s:s._offset,lambda s,v:setattr(s,"_offset",Vec3(*v)))
    @property
    def position(self):return self.owner.position+self._offset
    @property
    def min(self):p=self.position;return Vec3(p.x-abs(self._size.x)/2,p.y-abs(self._size.y)/2,p.z-abs(self._size.z)/2)
    @property
    def max(self):p=self.position;return Vec3(p.x+abs(self._size.x)/2,p.y+abs(self._size.y)/2,p.z+abs(self._size.z)/2)
def _overlaps(a,b):
    if not a.enabled or not b.enabled or (b.layer not in a.collides_with and a.layer not in b.collides_with):return False
    A,aM=a.min,a.max;B,bM=b.min,b.max
    return A.x<=bM.x and aM.x>=B.x and A.y<=bM.y and aM.y>=B.y and A.z<=bM.z and aM.z>=B.z
def Collision(a,b=None):
    if not hasattr(a,"collider"):raise TypeError("Collision() expects an Object.")
    if b is not None:return _overlaps(a.collider,b.collider)
    return [o for o in a._engine._objects if o is not a and _overlaps(a.collider,o.collider)]
class RaycastHit:
    __slots__=("object","point","normal","distance")
    def __init__(self,obj,point,normal,distance):self.object=obj;self.point=point;self.normal=normal;self.distance=distance
def _ray(origin,direction,mn,mx,distance):
    t0,t1=0.0,distance
    for o,d,a,b in ((origin.x,direction.x,mn.x,mx.x),(origin.y,direction.y,mn.y,mx.y),(origin.z,direction.z,mn.z,mx.z)):
        if abs(d)<1e-8:
            if o<a or o>b:return None
        else:
            u,v=(a-o)/d,(b-o)/d
            if u>v:u,v=v,u
            t0=max(t0,u);t1=min(t1,v)
            if t0>t1:return None
    return t0
def raycast(origin,direction,distance=1000,ignore=()):
    from .engine import get_default_engine
    origin=origin if isinstance(origin,Vec3) else Vec3(*origin);direction=(direction if isinstance(direction,Vec3) else Vec3(*direction)).normalized();best=None
    for o in get_default_engine()._objects:
        if o in ignore:continue
        t=_ray(origin,direction,o.collider.min,o.collider.max,distance)
        if t is not None and (best is None or t<best.distance):best=RaycastHit(o,origin+direction*t,direction,t)
    return best
def boxcast(center,size,direction,distance=1,**kwargs):return raycast(center,direction,distance,kwargs.get("ignore",()))
def spherecast(center,radius,direction,distance=1,**kwargs):return boxcast(center,(radius*2,)*3,direction,distance,**kwargs)
