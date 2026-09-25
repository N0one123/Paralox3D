"""AABB collision and lightweight spatial query helpers."""
from .math import Vec3
class Collider:
    __slots__=("owner","enabled","_size","_offset","is_trigger","layer","collides_with","_auto_size")
    def __init__(self,owner,size=None,offset=(0,0,0),enabled=True,is_trigger=False,layer="default",collides_with=None):
        self.owner=owner;self.enabled=bool(enabled);self._auto_size=size is None;self._size=Vec3(*(size if size is not None else owner.scale));self._offset=Vec3(*offset);self.is_trigger=bool(is_trigger);self.layer=str(layer);self.collides_with=set(collides_with or {"*"})
    @property
    def size(self):return self._size
    @size.setter
    def size(self,v):self._size=Vec3(*v);self._auto_size=False
    offset=property(lambda s:s._offset,lambda s,v:setattr(s,"_offset",Vec3(*v)))
    @property
    def position(self):return self.owner.position+self._offset
    @property
    def min(self):p=self.position;return Vec3(p.x-abs(self._size.x)/2,p.y-abs(self._size.y)/2,p.z-abs(self._size.z)/2)
    @property
    def max(self):p=self.position;return Vec3(p.x+abs(self._size.x)/2,p.y+abs(self._size.y)/2,p.z+abs(self._size.z)/2)
    def sync_to_scale(self):
        if self._auto_size:self._size=self.owner.scale.copy()
def _compatible(a,b):return a.enabled and b.enabled and ("*" in a.collides_with or "*" in b.collides_with or b.layer in a.collides_with or a.layer in b.collides_with)
def _overlaps(a,b):
    if not _compatible(a,b):return False
    A,aM=a.min,a.max;B,bM=b.min,b.max
    return A.x<=bM.x and aM.x>=B.x and A.y<=bM.y and aM.y>=B.y and A.z<=bM.z and aM.z>=B.z
def Collision(a,b=None):
    if not hasattr(a,"collider"):raise TypeError("Collision() expects an Object.")
    if b is not None:
        if not hasattr(b,"collider"):raise TypeError("Collision() expects Objects.")
        return _overlaps(a.collider,b.collider)
    return [o for o in a._engine._objects if o is not a and _overlaps(a.collider,o.collider)]
class RaycastHit:
    __slots__=("object","point","normal","distance")
    def __init__(self,obj,point,normal,distance):self.object=obj;self.point=point;self.normal=normal;self.distance=distance
def _ray(origin,direction,mn,mx,distance):
    t0,t1=0.0,float(distance);normal=Vec3()
    for axis,(o,d,a,b) in enumerate(((origin.x,direction.x,mn.x,mx.x),(origin.y,direction.y,mn.y,mx.y),(origin.z,direction.z,mn.z,mx.z))):
        if abs(d)<1e-8:
            if o<a or o>b:return None
        else:
            u,v=(a-o)/d,(b-o)/d
            if u>v:u,v=v,u
            if u>t0:t0=u;normal=Vec3(-1 if d>0 else 1,0,0) if axis==0 else Vec3(0,-1 if d>0 else 1,0) if axis==1 else Vec3(0,0,-1 if d>0 else 1)
            t1=min(t1,v)
            if t0>t1:return None
    return t0,normal
def raycast(origin,direction,distance=1000,ignore=()):
    from .engine import get_default_engine
    origin=origin if isinstance(origin,Vec3) else Vec3(*origin);direction=(direction if isinstance(direction,Vec3) else Vec3(*direction)).normalized()
    if direction.length_squared()==0:return None
    best=None
    for o in get_default_engine()._objects:
        if o in ignore or not o.collider.enabled:continue
        hit=_ray(origin,direction,o.collider.min,o.collider.max,distance)
        if hit and (best is None or hit[0]<best.distance):best=RaycastHit(o,origin+direction*hit[0],hit[1],hit[0])
    return best
def boxcast(center,size,direction,distance=1,ignore=()):
    c=center if isinstance(center,Vec3) else Vec3(*center);s=size if isinstance(size,Vec3) else Vec3(*size);d=(direction if isinstance(direction,Vec3) else Vec3(*direction)).normalized();best=None
    for o in __import__("paralox3d").get_default_engine()._objects:
        if o in ignore or not o.collider.enabled:continue
        hit=_ray(c,d,o.collider.min-s*.5,o.collider.max+s*.5,distance)
        if hit and (best is None or hit[0]<best.distance):best=RaycastHit(o,c+d*hit[0],hit[1],hit[0])
    return best
def spherecast(center,radius,direction,distance=1,ignore=()):return boxcast(center,(radius*2,radius*2,radius*2),direction,distance,ignore)
def overlap_box(center,size,ignore=()):
    c=center if isinstance(center,Vec3) else Vec3(*center);s=size if isinstance(size,Vec3) else Vec3(*size);out=[]
    for o in __import__("paralox3d").get_default_engine()._objects:
        if o in ignore:continue
        mn,mx=o.collider.min,o.collider.max
        if c.x-s.x/2<=mx.x and c.x+s.x/2>=mn.x and c.y-s.y/2<=mx.y and c.y+s.y/2>=mn.y and c.z-s.z/2<=mx.z and c.z+s.z/2>=mn.z:out.append(o)
    return out
def overlap_sphere(center,radius,ignore=()):
    c=center if isinstance(center,Vec3) else Vec3(*center);r=float(radius);out=[]
    for o in __import__("paralox3d").get_default_engine()._objects:
        if o in ignore or not o.collider.enabled:continue
        mn,mx=o.collider.min,o.collider.max;q=(min(max(c.x,mn.x),mx.x),min(max(c.y,mn.y),mx.y),min(max(c.z,mn.z),mx.z))
        if (c.x-q[0])**2+(c.y-q[1])**2+(c.z-q[2])**2<=r*r:out.append(o)
    return out
