"""AABB collision and lightweight spatial query helpers."""
from .math import Vec3
from .modes import modes

class Collider:
    __slots__=("owner","enabled","_size","_offset","is_trigger","layer","collides_with","_auto_size")
    def __init__(self,owner,size=None,offset=(0,0,0),enabled=True,is_trigger=False,layer="default",collides_with=None):
        self.owner=owner
        self.enabled=bool(enabled)
        self._auto_size=size is None
        self._size=Vec3(*(size if size is not None else owner.scale))
        self._offset=Vec3(*offset)
        self.is_trigger=bool(is_trigger)
        self.layer=str(layer)
        self.collides_with=set(collides_with or {"*"})

    @property
    def size(self): return self._size
    @size.setter
    def size(self,v):
        self._size=Vec3(*v)
        self._auto_size=False

    offset=property(lambda s:s._offset,lambda s,v:setattr(s,"_offset",Vec3(*v)))

    @property
    def position(self): return self.owner.position+self._offset

    @property
    def min(self):
        p=self.position
        return Vec3(p.x-abs(self._size.x)/2,p.y-abs(self._size.y)/2,p.z-abs(self._size.z)/2)

    @property
    def max(self):
        p=self.position
        return Vec3(p.x+abs(self._size.x)/2,p.y+abs(self._size.y)/2,p.z+abs(self._size.z)/2)

    def sync_to_scale(self):
        if self._auto_size:
            self._size=self.owner.scale.copy()

def _compatible(a,b):
    return a.enabled and b.enabled and (
        "*" in a.collides_with or "*" in b.collides_with
        or b.layer in a.collides_with or a.layer in b.collides_with
    )

def _overlaps(a,b):
    if not _compatible(a,b): return False
    A,aM=a.min,a.max
    B,bM=b.min,b.max
    return A.x<=bM.x and aM.x>=B.x and A.y<=bM.y and aM.y>=B.y and A.z<=bM.z and aM.z>=B.z

def _collision_collider(obj, argument_name):
    if not hasattr(obj, "collider"):
        raise TypeError(f"Collision() expects an Object for {argument_name}.")
    collider = getattr(obj, "collider", None)
    if collider is None:
        name = getattr(obj, "name", argument_name)
        if getattr(obj, "_destroyed", False):
            raise RuntimeError(
                f"Collision() cannot use destroyed Object '{name}' for {argument_name}."
            )
        raise RuntimeError(
            f"Collision() cannot use Object '{name}' because its collider is missing."
        )
    return collider

def Collision(a,b=None):
    a_collider = _collision_collider(a, "a")
    if b is not None:
        b_collider = _collision_collider(b, "b")
        return _overlaps(a_collider,b_collider)
    return [o for o in a._engine._objects if o is not a and o.collider is not None and _overlaps(a_collider,o.collider)]

def _dispatch_collision_events(engine):
    """Grid broadphase: only test objects sharing one or more spatial cells."""
    from collections import defaultdict

    cell_size = 4.0
    max_cells_per_object = 64
    grid = defaultdict(list)
    oversized = []
    active = []
    bounds = {}

    for obj in engine._objects:
        collider = obj.collider
        if not obj.enabled or collider is None or not collider.enabled:
            continue
        mn, mx = collider.min, collider.max
        active.append(obj)
        bounds[obj] = (mn, mx)
        x0, y0, z0 = (int(v // cell_size) for v in (mn.x, mn.y, mn.z))
        x1, y1, z1 = (int(v // cell_size) for v in (mx.x, mx.y, mx.z))
        cells = (x1-x0+1) * (y1-y0+1) * (z1-z0+1)
        if cells > max_cells_per_object:
            oversized.append(obj)
            continue
        for x in range(x0, x1+1):
            for y in range(y0, y1+1):
                for z in range(z0, z1+1):
                    grid[(x, y, z)].append(obj)

    candidates = set()
    for bucket in grid.values():
        if len(bucket) < 2:
            continue
        for i, a in enumerate(bucket):
            for b in bucket[i+1:]:
                if a.id < b.id:
                    candidates.add((a, b))
                else:
                    candidates.add((b, a))

    # Very large colliders are deliberately kept out of the grid to avoid
    # inserting thousands of cells; compare them against active objects.
    if oversized:
        for a in oversized:
            for b in active:
                if a is not b:
                    candidates.add((a, b) if a.id < b.id else (b, a))

    current = set()
    for a, b in candidates:
        if not _compatible(a.collider, b.collider):
            continue
        amin, amax = bounds[a]
        bmin, bmax = bounds[b]
        if not (amin.x <= bmax.x and amax.x >= bmin.x
                and amin.y <= bmax.y and amax.y >= bmin.y
                and amin.z <= bmax.z and amax.z >= bmin.z):
            continue
        pair = (a.id, b.id)
        current.add(pair)
        if pair not in engine._collision_pairs:
            callback = getattr(a, "on_enter", None)
            if callback:
                callback(b)
            callback = getattr(b, "on_enter", None)
            if callback:
                callback(a)
        callback = getattr(a, "on_collision", None)
        if callback:
            callback(b)
        callback = getattr(b, "on_collision", None)
        if callback:
            callback(a)

    if engine._collision_pairs - current:
        by_id = {obj.id: obj for obj in engine._objects}
        for aid, bid in engine._collision_pairs - current:
            a, b = by_id.get(aid), by_id.get(bid)
            if a is not None:
                callback = getattr(a, "on_exit", None)
                if callback:
                    callback(b)
            if b is not None:
                callback = getattr(b, "on_exit", None)
                if callback:
                    callback(a)
    engine._collision_pairs = current

class RaycastHit:
    __slots__=("object","entity","point","normal","distance")
    def __init__(self,obj,point,normal,distance):
        self.object=obj.object
        self.entity=obj
        self.point=point
        self.normal=normal
        self.distance=distance

def _ray_bounds(origin,direction,min_x,min_y,min_z,max_x,max_y,max_z,distance):
    t0,t1=0.0,float(distance)
    normal=Vec3()
    for axis,(o,d,lo,hi) in enumerate(((origin.x,direction.x,min_x,max_x),(origin.y,direction.y,min_y,max_y),(origin.z,direction.z,min_z,max_z))):
        if abs(d)<1e-8:
            if o<lo or o>hi: return None
        else:
            u,v=(lo-o)/d,(hi-o)/d
            if u>v: u,v=v,u
            if u>t0:
                t0=u
                normal=Vec3(-1 if d>0 else 1,0,0) if axis==0 else Vec3(0,-1 if d>0 else 1,0) if axis==1 else Vec3(0,0,-1 if d>0 else 1)
            t1=min(t1,v)
            if t0>t1: return None
    return t0,normal

def raycast(origin,direction,distance=1000,ignore=()):
    """Return the closest collider hit by a ray.

    origin may be an Object, Collider, an Object.position Vec3, or a 3-tuple.
    The origin object's own collider is always excluded.
    """
    from .engine import get_default_engine

    origin_owner = None
    if isinstance(origin, Vec3):
        origin_owner = origin.owner
        origin_position = origin
    elif hasattr(origin, "position"):
        origin_owner = origin if hasattr(origin, "_engine") else getattr(origin, "owner", None)
        origin_position = origin.position
    else:
        origin_position = origin

    origin_position = origin_position if isinstance(origin_position, Vec3) else Vec3(*origin_position)
    direction = direction if isinstance(direction, Vec3) else Vec3(*direction)
    distance = float(distance)
    if distance < 0:
        raise ValueError("raycast() distance must be non-negative.")
    length_sq = direction.length_squared()
    if length_sq == 0:
        return None
    direction = direction * (1.0 / (length_sq ** 0.5))

    if ignore is None:
        ignored = set()
    elif isinstance(ignore, (tuple, list, set, frozenset)):
        ignored = set(ignore)
    else:
        ignored = {ignore}
    if origin_owner is not None:
        ignored.add(origin_owner)

    engine = getattr(origin_owner, "_engine", None) or get_default_engine()
    best = None
    for obj in engine._objects:
        if obj in ignored or not obj.enabled:
            continue
        collider = obj.collider
        if collider is None or not collider.enabled:
            continue

        p = collider.owner._position
        off = collider._offset
        size = collider._size
        cx, cy, cz = p.x + off.x, p.y + off.y, p.z + off.z
        hx, hy, hz = abs(size.x) * 0.5, abs(size.y) * 0.5, abs(size.z) * 0.5
        hit = _ray_bounds(
            origin_position, direction,
            cx-hx, cy-hy, cz-hz, cx+hx, cy+hy, cz+hz, distance
        )
        if hit is not None and (best is None or hit[0] < best.distance):
            best = RaycastHit(
                obj, origin_position + direction * hit[0], hit[1], hit[0]
            )

    if modes.developer:
        end = best.point if best is not None else origin_position + direction * distance
        engine._debug_raycast(origin_position, end, origin_owner)
    return best

def boxcast(center,size,direction,distance=1,ignore=()):
    c = center if isinstance(center, Vec3) else Vec3(*center)
    s = size if isinstance(size, Vec3) else Vec3(*size)
    d = direction if isinstance(direction, Vec3) else Vec3(*direction)
    length_sq = d.length_squared()
    if length_sq == 0:
        return None
    d = d * (1.0 / (length_sq ** 0.5))
    ignored = set(ignore or ())
    best = None
    engine = __import__("paralox3d").get_default_engine()
    for obj in engine._objects:
        collider = obj.collider
        if obj in ignored or not obj.enabled or collider is None or not collider.enabled:
            continue
        p, off, size3 = collider.owner._position, collider._offset, collider._size
        cx, cy, cz = p.x + off.x, p.y + off.y, p.z + off.z
        hx, hy, hz = abs(size3.x)*0.5+s.x*0.5, abs(size3.y)*0.5+s.y*0.5, abs(size3.z)*0.5+s.z*0.5
        hit = _ray_bounds(c, d, cx-hx, cy-hy, cz-hz, cx+hx, cy+hy, cz+hz, distance)
        if hit is not None and (best is None or hit[0] < best.distance):
            best = RaycastHit(obj, c + d*hit[0], hit[1], hit[0])
    return best

def spherecast(center,radius,direction,distance=1,ignore=()):
    return boxcast(center,(radius*2,radius*2,radius*2),direction,distance,ignore)

def overlap_box(center,size,ignore=()):
    c=center if isinstance(center,Vec3) else Vec3(*center)
    s=size if isinstance(size,Vec3) else Vec3(*size)
    out=[]
    for o in __import__("paralox3d").get_default_engine()._objects:
        if o in ignore or not o.enabled or not o.collider.enabled: continue
        mn,mx=o.collider.min,o.collider.max
        if c.x-s.x/2<=mx.x and c.x+s.x/2>=mn.x and c.y-s.y/2<=mx.y and c.y+s.y/2>=mn.y and c.z-s.z/2<=mx.z and c.z+s.z/2>=mn.z:
            out.append(o)
    return out

def overlap_sphere(center,radius,ignore=()):
    c=center if isinstance(center,Vec3) else Vec3(*center)
    r=float(radius)
    out=[]
    for o in __import__("paralox3d").get_default_engine()._objects:
        if o in ignore or not o.enabled or not o.collider.enabled: continue
        mn,mx=o.collider.min,o.collider.max
        q=(min(max(c.x,mn.x),mx.x),min(max(c.y,mn.y),mx.y),min(max(c.z,mn.z),mx.z))
        if (c.x-q[0])**2+(c.y-q[1])**2+(c.z-q[2])**2<=r*r:
            out.append(o)
    return out
