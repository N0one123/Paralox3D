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


class ControllerComponent(Component):
    """Ursina-style character controller with first-person camera control."""

    def __init__(self,owner=None,height=2.0,speed=5.0,gravity=1.0,
                 jump_height=2.0,jump_duration=0.5,fall_after=0.35,
                 sensitivity=(40.0,40.0),third_person=False,distance=6.0,
                 eye_height=None,step_height=0.5):
        super().__init__(owner)
        self.height=float(height)
        self.speed=float(speed)
        self.gravity=float(gravity)
        self.jump_height=float(jump_height)
        self.jump_duration=float(jump_duration)
        self.fall_after=float(fall_after)
        if isinstance(sensitivity,(int,float)):
            self.mouse_sensitivity=float(sensitivity)
        else:
            self.mouse_sensitivity=(float(sensitivity[0]),float(sensitivity[1]))
        self.third_person=bool(third_person)
        self.distance=float(distance)
        self.eye_height=float(self.height if eye_height is None else eye_height)
        self.step_height=float(step_height)

        self.grounded=False
        self.jumping=False
        self.air_time=0.0
        self.velocity_y=0.0
        self._yaw=0.0
        self._pitch=0.0

    def on_start(self):
        from .input import mouse
        self._yaw=float(self.owner.rotation.y)
        self._pitch=max(-90.0,min(90.0,float(self.owner.rotation.x)))
        self.owner.rotation=(0,self._yaw,0)

        # Controller owns the camera while enabled. The native layer only
        # hides the cursor, it never captures or recenters the OS mouse.
        self.owner._engine._set_mouse_locked(True)
        self.owner._engine._set_fps_camera_active(True)
        mouse.lock()

        # Make the controller collider match the character height.
        if self.owner.collider._auto_size:
            radius=max(0.01,min(abs(self.owner.scale.x),abs(self.owner.scale.z))*0.5)
            self.owner.collider.size=(radius*2.0,self.height,radius*2.0)

        self._snap_to_ground()

    def _leave_mouse_mode(self):
        from .input import mouse
        self.owner._engine._set_mouse_locked(False)
        self.owner._engine._set_fps_camera_active(False)
        mouse.unlock()

    def on_enable(self):
        self.owner._engine._set_mouse_locked(True)
        self.owner._engine._set_fps_camera_active(True)
        from .input import mouse
        mouse.lock()

    def on_disable(self):
        self._leave_mouse_mode()

    def on_destroy(self):
        self._leave_mouse_mode()

    def _is_solid(self,other):
        return (other is not self.owner and other.enabled and
                other.collider.enabled and not other.collider.is_trigger)

    def _ray(self,origin,direction,distance):
        from .collision import raycast
        return raycast(origin,direction,distance=distance,ignore=(self.owner,))

    def _snap_to_ground(self):
        from .math import Vec3
        hit=self._ray(self.owner.position+Vec3(0,self.height*0.5+0.05,0),
                      Vec3(0,-1,0),self.height+1.0)
        if hit and hit.object and self._is_solid(hit.object) and hit.normal.y>0.7:
            self.owner.y=hit.point.y+self.owner.collider.size.y*0.5
            self.grounded=True
            self.air_time=0.0
            self.velocity_y=0.0

    def _horizontal_clear(self,position):
        from .collision import Collision
        original=self.owner.position
        self.owner.position=position
        blocked=False
        for other in tuple(self.owner._engine._objects):
            if not self._is_solid(other):
                continue
            if Collision(self.owner,other):
                # Contact with the floor is allowed. What blocks movement is
                # an obstacle overlapping the character's vertical body.
                overlap=min(self.owner.collider.max.y,other.collider.max.y)-max(
                    self.owner.collider.min.y,other.collider.min.y)
                if overlap>0.05:
                    blocked=True
                    break
        self.owner.position=original
        return not blocked

    def _move(self,amount):
        # Try the full movement first, then each axis separately. This gives
        # natural wall sliding instead of stopping both axes at once.
        if amount.length_squared()==0:
            return
        target=self.owner.position+amount
        if self._horizontal_clear(target):
            self.owner.position=target
            return

        x_target=self.owner.position+type(amount)(amount.x,0,0)
        if abs(amount.x)>0 and self._horizontal_clear(x_target):
            self.owner.position=x_target

        z_target=self.owner.position+type(amount)(0,0,amount.z)
        if abs(amount.z)>0 and self._horizontal_clear(z_target):
            self.owner.position=z_target

    def _ground_check(self):
        from .math import Vec3
        bottom=self.owner.collider.min.y
        hit=self._ray(Vec3(self.owner.x,bottom+0.08,self.owner.z),
                      Vec3(0,-1,0),self.step_height+0.18)
        if hit and hit.object and self._is_solid(hit.object) and hit.normal.y>0.7:
            self.owner.y=hit.point.y+self.owner.collider.size.y*0.5
            return True
        return False

    def _jump(self):
        if not self.grounded:
            return
        # v² = 2gh. gravity is deliberately positive here and applied down.
        import math
        g=max(0.01,self.gravity*10.0)
        self.velocity_y=math.sqrt(2.0*g*self.jump_height)
        self.grounded=False
        self.jumping=True
        self.air_time=0.0

    def _vectors(self):
        import math
        from .math import Vec3
        yaw=math.radians(self._yaw)
        forward=Vec3(math.sin(yaw),0,-math.cos(yaw))
        right=Vec3(math.cos(yaw),0,math.sin(yaw))
        return forward,right

    def _camera_update(self):
        from .camera import camera
        forward,_=self._vectors()
        eye=self.owner.position.y+self.eye_height*0.5
        if self.third_person:
            behind=forward*-self.distance
            camera.position=(self.owner.x+behind.x,eye,self.owner.z+behind.z)
            camera.look_at((self.owner.x,self.owner.y+self.height*0.5,self.owner.z))
        else:
            camera.position=(self.owner.x,eye,self.owner.z)
            camera.rotation=(self._pitch,self._yaw,0)

    def update(self):
        from .input import held,pressed,mouse
        from .clock import dt
        from .math import Vec3
        import math

        frame_dt=max(0.0,float(dt))

        if pressed("escape"):
            self.enabled=False
            return

        # Ursina-style mouse look. dx/dy are true per-frame relative motion,
        # so there is no fake return-to-zero camera movement.
        sx,sy=self.mouse_sensitivity
        self._yaw += mouse.dx*sx
        self._pitch -= mouse.dy*sy
        self._pitch=max(-90.0,min(90.0,self._pitch))
        self.owner.rotation=(0,self._yaw,0)

        forward,right=self._vectors()
        move=forward*((1 if held("w") else 0)-(1 if held("s") else 0))
        move=move+right*((1 if held("d") else 0)-(1 if held("a") else 0))
        if move.length_squared():
            move=move.normalized()*self.speed*frame_dt
            self._move(move)

        if pressed("space"):
            self._jump()

        if self.gravity:
            gravity_strength=max(0.01,self.gravity*10.0)
            self.velocity_y-=gravity_strength*frame_dt

            vertical=self.velocity_y*frame_dt
            if vertical!=0:
                target=self.owner.position+Vec3(0,vertical,0)
                if self._horizontal_clear(target):
                    self.owner.position=target
                else:
                    if self.velocity_y<0:
                        self.grounded=True
                        self.jumping=False
                        self.velocity_y=0.0
                    else:
                        self.velocity_y=0.0

            if self._ground_check():
                self.grounded=True
                self.jumping=False
                self.air_time=0.0
                self.velocity_y=min(0.0,self.velocity_y)
            else:
                self.grounded=False
                self.air_time+=frame_dt

        self._camera_update()


class CharacterController(ControllerComponent):
    """Compatibility name for the character controller component."""
    pass


class Controller:
    """Convenience constructor for a ready-to-use controlled Object."""
    def __new__(cls,model="cube",position=(0,1,0),rotation=(0,0,0),
                scale=(1,2,1),name="Player",engine=None,scene=None,parent=None,
                color=None,opacity=None,size=None,**kwargs):
        from .entity import Object
        obj=Object(model=model,position=position,rotation=rotation,scale=scale,
                   name=name,engine=engine,scene=scene,parent=parent,color=color,
                   opacity=1.0 if opacity is None else opacity)
        controller=ControllerComponent(obj,**kwargs)
        if size is not None:
            obj.collider.size=size
        obj.add(controller)
        obj.controller=controller
        return obj
