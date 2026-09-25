"""First-class scenes with lifecycle and JSON persistence."""
import json
from pathlib import Path
class Scene:
    _current=None
    def __init__(self,name="Scene"):self.name=name;self.objects=[];self.on_enter=None;self.on_exit=None
    def add(self,obj):
        if obj not in self.objects:self.objects.append(obj)
        return obj
    def create(self,model="cube",**kwargs):
        from .entity import Object
        return self.add(Object(model=model,scene=self,**kwargs))
    def enter(self):Scene._current=self;self.on_enter() if self.on_enter else None;return self
    def exit(self):
        if self.on_exit:self.on_exit()
    def clear(self,keep_persistent=True):
        for o in tuple(self.objects):
            if keep_persistent and o.persistent:continue
            o.destroy()
        self.objects=[o for o in self.objects if o.persistent];return self
    def save(self,path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"scene":self.name,"objects":[o._serialize() for o in self.objects if not o.persistent]},indent=2),encoding="utf-8");return p
    @classmethod
    def load(cls,path,on_loaded=None):
        p=Path(path);d=json.loads(p.read_text(encoding="utf-8"));s=cls(d.get("scene",p.stem))
        for x in d.get("objects",[]):
            o=s.create(model=x.get("model","cube"),name=x.get("name"),position=tuple(x.get("position",(0,0,0))),rotation=tuple(x.get("rotation",(0,0,0))),scale=tuple(x.get("scale",(1,1,1))))
            o.tags.update(x.get("tags",[]));o.persistent=bool(x.get("persistent",False))
        if on_loaded:on_loaded(s)
        return s
    @classmethod
    def switch(cls,scene,on_loaded=None):
        if cls._current and cls._current is not scene:cls._current.exit()
        if isinstance(scene,(str,Path)):scene=cls.load(scene)
        scene.enter()
        if on_loaded:on_loaded(scene)
        return scene
def current_scene():return Scene._current
