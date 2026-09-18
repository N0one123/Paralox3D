"""Simple, frame-friendly input helpers."""

from __future__ import annotations

class Input:
    def __init__(self):
        self._keys=set()
        self._pressed=set()
    def _set_key(self,key,down):
        key=str(key).lower()
        if down:
            if key not in self._keys: self._pressed.add(key)
            self._keys.add(key)
        else: self._keys.discard(key)
    def held(self,key): return str(key).lower() in self._keys
    def pressed(self,key): return str(key).lower() in self._pressed
    def _end_frame(self): self._pressed.clear()

_default_input=Input()

def key(name): return _default_input.held(name)
def pressed(name): return _default_input.pressed(name)
