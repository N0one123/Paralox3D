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
def held(*keys):return _default_input.held(*keys)
def pressed(k):return _default_input.pressed(k)
def key(k):return held(k)
def bind(action,*keys):return _default_input.bind(action,*keys)
def action(name):return _default_input.action_held(name)
def action_pressed(name):return _default_input.action_pressed(name)
class Mouse:
    x=property(lambda s:0);y=property(lambda s:0);position=property(lambda s:(0,0));dx=property(lambda s:0);dy=property(lambda s:0)
    left=property(lambda s:False);right=property(lambda s:False);middle=property(lambda s:False)
    def pressed(self,button):return False
    def lock(self):pass
    def unlock(self):pass
    visible=True
mouse=Mouse()
