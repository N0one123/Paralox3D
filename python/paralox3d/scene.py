"""First-class, JSON-serializable Paralox3D scenes."""

import json
from pathlib import Path
from .entity import Object

class Scene:
    _current=None
    def __init__(self,name="Scene"):
        self.name=name; self.objects=[]; Scene._current=self
    def add(self,obj):
        if obj not in self.objects: self.objects.append(obj)
        return obj
    def create(self,model="cube",**kwargs):
        return self.add(Object(model=model,scene=self,**kwargs))
    def save(self,path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"scene":self.name,"objects":[o._serialize() for o in self.objects]},indent=2),encoding="utf-8")
        return path
    @classmethod
    def load(cls,path):
        path=Path(path); data=json.loads(path.read_text(encoding="utf-8"))
        scene=cls(data.get("scene",path.stem))
        for item in data.get("objects",[]):
            scene.create(model=item.get("model","cube"),name=item.get("name"),
                position=tuple(item.get("position",(0,0,0))),
                rotation=tuple(item.get("rotation",(0,0,0))),
                scale=tuple(item.get("scale",(1,1,1))))
        return scene

def current_scene(): return Scene._current
