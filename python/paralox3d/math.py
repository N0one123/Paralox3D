"""Small, allocation-friendly math types for the public API."""
from __future__ import annotations
from dataclasses import dataclass
import math
@dataclass(slots=True)
class Vec3:
    x:float=0.0;y:float=0.0;z:float=0.0
    def __iter__(self):yield self.x;yield self.y;yield self.z
    def as_tuple(self):return (self.x,self.y,self.z)
    def copy(self):return Vec3(self.x,self.y,self.z)
    def __add__(self,o):return Vec3(self.x+o.x,self.y+o.y,self.z+o.z)
    def __sub__(self,o):return Vec3(self.x-o.x,self.y-o.y,self.z-o.z)
    def __mul__(self,n):return Vec3(self.x*n,self.y*n,self.z*n)
    __rmul__=__mul__
    def __truediv__(self,n):return Vec3(self.x/n,self.y/n,self.z/n)
    def length(self):return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)
    def normalized(self):
        n=self.length();return self/n if n else Vec3()
    def dot(self,o):return self.x*o.x+self.y*o.y+self.z*o.z
    def cross(self,o):return Vec3(self.y*o.z-self.z*o.y,self.z*o.x-self.x*o.z,self.x*o.y-self.y*o.x)
