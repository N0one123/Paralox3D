"""Small component helpers for Paralox3D objects."""

class Component:
    def __init__(self, owner=None): self.owner=owner
    def on_start(self): pass
    def update(self): pass

class Script(Component):
    def __init__(self, owner=None, update=None):
        super().__init__(owner); self._update=update
    def update(self):
        if self._update: self._update()
