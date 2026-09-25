"""First-class scenes with lifecycle and switching."""
import json
from pathlib import Path
class Scene:
    _current=None
    def __init__(self,name="Scene"):self.name=name;self.objects=[];self.on_enter=None;self.on_exit=None;Scene._current=self
    def add(self,obj):
        if obj not in self.objects:self.objects.append(obj)
        return obj
    def create(self,model="cube",**kwargs):
        from .entity import Object
        return self.add(Object(model=model,scene=self,**kwargs))
    def enter(self):Scene._current=self;self.on_enter() if self.on_enter else None;return self
    def exit(self):self.on_exit() if self.on_exit else None
    def save(self,path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"scene":self.name,"objects":[o._serialize() for o in self.objects]},indent=2),encoding="utf-8");return p
    @classmethod
    def load(cls,path,on_loaded=None):
        p=Path(path);d=json.loads(p.read_text(encoding="utf-8"));s=cls(d.get("scene",p.stem))
        for x in d.get("objects",[]):s.create(model=x.get("model","cube"),name=x.get("name"),position=tuple(x.get("position",(0,0,0))),rotation=tuple(x.get("rotation",(0,0,0))),scale=tuple(x.get("scale",(1,1,1))))
        s.enter();on_loaded(s) if on_loaded else None;return s
    @classmethod
    def switch(cls,scene,on_loaded=None):
        if cls._current and cls._current is not scene:cls._current.exit()
        if isinstance(scene,(str,Path)):scene=cls.load(scene,on_loaded)
        scene.enter();on_loaded(scene) if on_loaded else None;return scene
def current_scene():return Scene._current
