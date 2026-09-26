"""Component helpers and built-in controllers."""
class Component:
    def __init__(self,owner=None):
        self.owner=owner
        self._enabled=True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self,value):
        value=bool(value)
        if value==self._enabled:
            return
        self._enabled=value
        if value:
            self.on_enable()
        else:
            self.on_disable()

    def on_start(self): pass
    def on_enable(self): pass
    def on_disable(self): pass
    def update(self): pass
    def on_destroy(self): pass


class Script(Component):
    def __init__(self,owner=None,update=None):
        super().__init__(owner)
        self._update=update

    def update(self):
        if self._update:
            self._update()


class FPSController(Component):
    """Low-level first/third-person controller used by FPS()."""
    def __init__(self,owner=None,speed=5.0,sprint=8.0,jump_speed=7.0,gravity=-18.0,
                 third_person=False,sensitivity=0.18,distance=6.0,height=2.0):
        super().__init__(owner)
        self.speed=float(speed)
        self.sprint=float(sprint)
        self.jump_speed=float(jump_speed)
        self.gravity=float(gravity)
        self.third_person=bool(third_person)
        self.sensitivity=float(sensitivity)
        self.distance=float(distance)
        self.height=float(height)
        self.velocity_y=0.0
        self.grounded=False
        self._pitch=0.0
        self._yaw=0.0

    def on_start(self):
        from .camera import camera
        from .input import mouse
        self._yaw=float(self.owner.rotation.y)
        self._pitch=0.0
        mouse.lock()

    def on_destroy(self):
        from .input import mouse
        mouse.unlock()

    def update(self):
        from .input import held, pressed, mouse
        from .clock import dt
        from .camera import camera
        from .collision import Collision

        frame_dt=float(dt)

        # Mouse look.
        self._yaw += mouse.dx*self.sensitivity
        self._pitch -= mouse.dy*self.sensitivity
        self._pitch=max(-89.0,min(89.0,self._pitch))
        self.owner.rotation=(0,self._yaw,0)

        # Horizontal movement follows camera/player yaw.
        x=(1 if held("d") else 0)-(1 if held("a") else 0)
        z=(1 if held("w") else 0)-(1 if held("s") else 0)
        move=self.owner.right*x+self.owner.forward*z
        if move.length():
            move=move.normalized()
            self.owner.translate(*(move*(self.sprint if held("shift") else self.speed)*frame_dt))

        # Gravity and jumping.
        if pressed("space") and self.grounded:
            self.velocity_y=self.jump_speed
            self.grounded=False
        self.velocity_y+=self.gravity*frame_dt
        self.owner.y+=self.velocity_y*frame_dt
        self.grounded=False

        for other in self.owner._engine._objects:
            if other is self.owner or not other.collider.enabled or other.collider.is_trigger:
                continue
            if Collision(self.owner,other) and self.velocity_y<=0:
                self.owner.y=other.collider.max.y+self.owner.collider.size.y*.5
                self.velocity_y=0.0
                self.grounded=True
                break

        # Camera is owned by the controller, so users never need camera boilerplate.
        target_y=self.owner.y+self.height
        if self.third_person:
            behind=self.owner.forward*-self.distance
            camera.position=(self.owner.x+behind.x,target_y+0.25,self.owner.z+behind.z)
            camera.look_at((self.owner.x,self.owner.y+self.height*.55,self.owner.z))
        else:
            camera.position=(self.owner.x,target_y,self.owner.z)
            camera.rotation=(self._pitch,self._yaw+180.0,0)


class CharacterController(FPSController):
    def __init__(self,owner=None,speed=5.0,jump_speed=6.0,gravity=-18.0):
        super().__init__(owner,speed=speed,jump_speed=jump_speed,gravity=gravity)


class FPS:
    """Convenience constructor for a ready-to-use FPS/third-person player."""
    def __new__(cls, model="cube", position=(0,0,0), rotation=(0,0,0),
                scale=(1,2,1), name="Player", engine=None, scene=None, parent=None,
                color=None, opacity=None, size=None, third_person=False,
                speed=5.0, sprint=8.0, jump_speed=7.0, gravity=-18.0,
                sensitivity=0.18, distance=6.0, height=2.0, **kwargs):
        from .entity import Object

        # Keep FPS() as an Object, not a separate wrapper type.
        obj=Object(model=model,position=position,rotation=rotation,scale=scale,
                   name=name,engine=engine,scene=scene,parent=parent)
        if color is not None:
            obj.color=color
        if opacity is not None:
            obj.opacity=opacity
        if size is not None:
            obj.collider.size=size

        controller=FPSController(
            obj,speed=speed,sprint=sprint,jump_speed=jump_speed,gravity=gravity,
            third_person=third_person,sensitivity=sensitivity,distance=distance,height=height
        )
        obj.add(controller)
        obj.fps_controller=controller
        return obj
