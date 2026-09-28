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
        self.speed=float(speed); self.sprint=float(sprint); self.jump_speed=float(jump_speed)
        self.gravity=float(gravity); self.third_person=bool(third_person)
        self.sensitivity=float(sensitivity); self.distance=float(distance); self.height=float(height)
        self.velocity_y=0.0; self.grounded=False; self._pitch=0.0; self._yaw=0.0

    def on_start(self):
        from .input import mouse
        self._yaw=float(self.owner.rotation.y)
        self._pitch=max(-89.0,min(89.0,float(self.owner.rotation.x)))
        self.owner.rotation=(0,self._yaw,0)
        self.owner._engine._set_mouse_locked(True)
        self.owner._engine._set_fps_camera_active(True)
        mouse.lock()

    def on_destroy(self):
        from .input import mouse
        self.owner._engine._set_mouse_locked(False)
        self.owner._engine._set_fps_camera_active(False)
        mouse.unlock()

    def _vectors(self):
        import math
        from .math import Vec3
        yaw=math.radians(self._yaw)
        return Vec3(math.sin(yaw),0,-math.cos(yaw)), Vec3(math.cos(yaw),0,math.sin(yaw))

    def _blocked(self):
        from .collision import Collision
        for other in tuple(self.owner._engine._objects):
            if other is self.owner or not other.collider.enabled or other.collider.is_trigger:
                continue
            if Collision(self.owner,other):
                return True
        return False

    def _move_horizontal(self,dx,dz):
        start=self.owner.position.copy()
        if dx:
            self.owner.position=(start.x+dx,start.y,start.z)
            if self._blocked(): self.owner.position=start
        if dz:
            current=self.owner.position.copy()
            self.owner.position=(current.x,current.y,current.z+dz)
            if self._blocked(): self.owner.position=current

    def update(self):
        from .input import held,pressed,mouse
        from .clock import dt
        from .camera import camera
        from .collision import Collision

        frame_dt=max(0.0,float(dt))

        self._yaw += mouse.dx*self.sensitivity
        self._pitch -= mouse.dy*self.sensitivity
        self._pitch=max(-89.0,min(89.0,self._pitch))

        # Body follows camera yaw, while pitch stays camera-only.
        self.owner.rotation=(0,self._yaw,0)
        forward,right=self._vectors()

        x=(1 if held("d") else 0)-(1 if held("a") else 0)
        z=(1 if held("w") else 0)-(1 if held("s") else 0)
        move=right*x+forward*z
        if move.length():
            move=move.normalized()
            speed=self.sprint if held("shift") else self.speed
            self._move_horizontal(move.x*speed*frame_dt,move.z*speed*frame_dt)

        if pressed("space") and self.grounded:
            self.velocity_y=self.jump_speed
            self.grounded=False

        old_y=self.owner.y
        self.velocity_y+=self.gravity*frame_dt
        self.owner.y=old_y+self.velocity_y*frame_dt
        self.grounded=False

        if self._blocked():
            # Resolve vertical contact. The existing floor behavior is preserved,
            # while ceilings are prevented from letting the player pass through.
            if self.velocity_y <= 0:
                best=None
                for other in tuple(self.owner._engine._objects):
                    if other is self.owner or not other.collider.enabled or other.collider.is_trigger:
                        continue
                    if Collision(self.owner,other):
                        top=other.collider.max.y
                        if best is None or top>best: best=top
                if best is not None:
                    self.owner.y=best+self.owner.collider.size.y*.5
                    self.velocity_y=0.0
                    self.grounded=True
                else:
                    self.owner.y=old_y
            else:
                self.owner.y=old_y
                self.velocity_y=0.0
        else:
            # Downward probe prevents grounded state from flickering between frames.
            self.owner.y-=0.03
            for other in tuple(self.owner._engine._objects):
                if other is self.owner or not other.collider.enabled or other.collider.is_trigger:
                    continue
                if Collision(self.owner,other) and self.velocity_y<=0:
                    self.owner.y=other.collider.max.y+self.owner.collider.size.y*.5
                    self.velocity_y=0.0
                    self.grounded=True
                    break
            else:
                self.owner.y+=0.03

        target_y=self.owner.y+self.height
        if self.third_person:
            behind=forward*-self.distance
            camera.position=(self.owner.x+behind.x,target_y+0.25,self.owner.z+behind.z)
            camera.look_at((self.owner.x,self.owner.y+self.height*.55,self.owner.z))
        else:
            camera.position=(self.owner.x,target_y,self.owner.z)
            camera.rotation=(self._pitch,self._yaw,0)


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
