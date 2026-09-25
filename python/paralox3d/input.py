"""Keyboard, mouse and action input."""
_KEY_CODES={**{chr(c).lower():c for c in range(ord("A"),ord("Z")+1)},**{str(c):0x30+c for c in range(10)},"space":0x20,"enter":0x0D,"escape":0x1B,"tab":0x09,"backspace":0x08,"shift":0x10,"ctrl":0x11,"alt":0x12,"left":0x25,"up":0x26,"right":0x27,"down":0x28}
class Input:
    def __init__(self):self._keys=set();self._pressed=set();self._bindings={}
    def _set_key(self,k,d):
        k=str(k).lower()
        if d and k not in self._keys:self._pressed.add(k)
        if d:self._keys.add(k)
        else:self._keys.discard(k)
    def _sync(self,query):
        for n,c in _KEY_CODES.items():self._set_key(n,bool(query(c)))
    def held(self,*keys):return all(str(k).lower() in self._keys for k in keys)
    def any_held(self,*keys):return any(str(k).lower() in self._keys for k in keys)
    def pressed(self,k):return str(k).lower() in self._pressed
    def bind(self,action,*keys):self._bindings[str(action)]=tuple(str(k).lower() for k in keys);return action
    def action_held(self,action):return self.held(*self._bindings.get(str(action),()))
    def action_pressed(self,action):return any(self.pressed(k) for k in self._bindings.get(str(action),()))
    def _end_frame(self):self._pressed.clear()
_default_input=Input()
held=lambda *keys:_default_input.held(*keys)
any_held=lambda *keys:_default_input.any_held(*keys)
pressed=lambda k:_default_input.pressed(k)
key=lambda k:held(k)
bind=lambda action,*keys:_default_input.bind(action,*keys)
action=lambda name:_default_input.action_held(name)
action_pressed=lambda name:_default_input.action_pressed(name)
class Mouse:
    def __init__(self):self._x=self._y=self._dx=self._dy=0.0;self._left=self._right=self._middle=False;self._pressed=set();self.visible=True;self.locked=False
    x=property(lambda s:s._x);y=property(lambda s:s._y);position=property(lambda s:(s._x,s._y));dx=property(lambda s:s._dx);dy=property(lambda s:s._dy)
    left=property(lambda s:s._left);right=property(lambda s:s._right);middle=property(lambda s:s._middle)
    def pressed(self,b):return str(b).lower() in self._pressed
    def _sync(self,state):
        x,y,l,r,m=state;self._dx=x-self._x;self._dy=y-self._y;self._x=x;self._y=y
        for n,d in (("left",l),("right",r),("middle",m)):
            if d and not getattr(self,"_"+n):self._pressed.add(n)
            setattr(self,"_"+n,d)
    def _end_frame(self):self._pressed.clear();self._dx=0.0;self._dy=0.0
    def lock(self):self.locked=True
    def unlock(self):self.locked=False
mouse=Mouse()
