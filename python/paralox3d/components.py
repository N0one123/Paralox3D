"""Component helpers and built-in controllers."""
class Component:
    def __init__(self,owner=None):self.owner=owner;self.enabled=True
    def on_start(self):pass
    def update(self):pass
    def on_destroy(self):pass
class Script(Component):
    def __init__(self,owner=None,update=None):super().__init__(owner);self._update=update
    def update(self):
        if self._update:self._update()
class FPSController(Component):
    def __init__(self,owner=None,speed=5.0,sprint=8.0):super().__init__(owner);self.speed=speed;self.sprint=sprint
    def update(self):
        from .input import held
        from .clock import dt
        x=(1 if held("d") else 0)-(1 if held("a") else 0);z=(1 if held("w") else 0)-(1 if held("s") else 0)
        move=self.owner.right*x+self.owner.forward*z
        if move.length():self.owner.translate(*(move.normalized()*(self.sprint if held("shift") else self.speed)*float(dt)))
class CharacterController(FPSController):
    def __init__(self,owner=None,speed=5.0,jump_speed=6.0,gravity=-18.0):super().__init__(owner,speed);self.jump_speed=jump_speed;self.gravity=gravity;self.velocity_y=0.0;self.grounded=False
    def update(self):
        super().update()
        from .input import pressed
        from .clock import dt
        if pressed("space") and self.grounded:self.velocity_y=self.jump_speed;self.grounded=False
        self.velocity_y+=self.gravity*float(dt);self.owner.y+=self.velocity_y*float(dt)
        from .collision import Collision
        for o in self.owner._engine._objects:
            if o is not self.owner and not o.collider.is_trigger and Collision(self.owner,o) and self.velocity_y<=0:
                self.owner.y=o.collider.max.y+self.owner.collider.size.y*.5;self.velocity_y=0;self.grounded=True
