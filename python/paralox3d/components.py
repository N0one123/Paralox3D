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
    """Built-in character controller with Ursina-style FPS movement."""

    def __init__(self,owner=None,height=2.0,speed=5.0,gravity=1.0,
                 jump_height=2.0,jump_duration=0.5,fall_after=0.35,
                 sensitivity=(0.25,0.25),third_person=False,distance=6.0,
                 eye_height=None,step_height=0.5,sprint=False,sprint_speed=None,
                 sprint_key="shift",jump_speed=None,mouse_sensitivity=None):
        super().__init__(owner)

        self.height=float(height)
        self.speed=float(speed)
        self.gravity=float(gravity)
        self.jump_height=float(jump_height)
        self.jump_duration=float(jump_duration)
        self.fall_after=float(fall_after)
        self.jump_speed=None if jump_speed is None else float(jump_speed)

        if mouse_sensitivity is not None:
            sensitivity=mouse_sensitivity
        if isinstance(sensitivity,(int,float)):
            self.mouse_sensitivity=(float(sensitivity),float(sensitivity))
        else:
            self.mouse_sensitivity=(float(sensitivity[0]),float(sensitivity[1]))

        self.third_person=bool(third_person)
        self.distance=float(distance)
        self.eye_height=float(self.height if eye_height is None else eye_height)
        self.step_height=max(0.0,float(step_height))

        self.sprint=bool(sprint)
        self.sprint_speed=float(self.speed*1.5 if sprint_speed is None else sprint_speed)
        self.sprint_key=str(sprint_key)

        self.grounded=False
        self.jumping=False
        self.air_time=0.0
        self.velocity_y=0.0
        self._yaw=0.0
        self._pitch=0.0

    def on_start(self):
        from .input import mouse

        # Controller yaw uses the camera's public yaw convention. The native
        # renderer applies the inverse camera rotation, while Object rotation
        # is a model rotation. Therefore the body's yaw is the inverse of the
        # camera yaw. This keeps the visible body facing exactly where the
        # camera looks.
        self._yaw=-float(self.owner.rotation.y)
        self._pitch=max(-90.0,min(90.0,float(self.owner.rotation.x)))
        self.owner.rotation=(0,-self._yaw,0)

        # The controller owns mouse capture while it is enabled.
        self.owner._engine._set_mouse_locked(True)
        self.owner._engine._set_fps_camera_active(True)
        mouse.lock()

        # Controllers use a simple upright body collider. Objects keep their
        # normal auto-sized collider unless the user explicitly changed it.
        if self.owner.collider._auto_size:
            radius=max(
                0.01,
                min(abs(self.owner.scale.x),abs(self.owner.scale.z))*0.5
            )
            self.owner.collider.size=(radius*2.0,self.height,radius*2.0)

        self._snap_to_ground()
        self._camera_update()

    def on_enable(self):
        from .input import mouse
        self.owner._engine._set_mouse_locked(True)
        self.owner._engine._set_fps_camera_active(True)
        mouse.lock()

    def on_disable(self):
        self._leave_mouse_mode()

    def on_destroy(self):
        self._leave_mouse_mode()

    def _leave_mouse_mode(self):
        from .input import mouse
        self.owner._engine._set_mouse_locked(False)
        self.owner._engine._set_fps_camera_active(False)
        mouse.unlock()

    def _is_solid(self,other):
        return (
            other is not self.owner
            and other.enabled
            and other.collider.enabled
            and not other.collider.is_trigger
        )

    def _ray(self,origin,direction,distance):
        from .collision import raycast
        return raycast(origin,direction,distance=distance,ignore=(self.owner,))

    def _colliding_solid(self):
        from .collision import Collision
        hits=[]
        for other in tuple(self.owner._engine._objects):
            if self._is_solid(other) and Collision(self.owner,other):
                hits.append(other)
        return hits

    def _snap_to_ground(self):
        from .math import Vec3

        hit=self._ray(
            self.owner.position+Vec3(0,self.height*0.5+0.05,0),
            Vec3(0,-1,0),
            self.height+1.0
        )
        if hit and hit.object and self._is_solid(hit.object) and hit.normal.y>0.7:
            self.owner.y=hit.point.y+self.owner.collider.size.y*0.5
            self.grounded=True
            self.air_time=0.0
            self.velocity_y=0.0

    def _horizontal_clear(self,position):
        """Test horizontal movement without treating the floor as a wall."""
        original=self.owner.position
        self.owner.position=position

        blocked=False
        player_min=self.owner.collider.min
        player_max=self.owner.collider.max

        for other in tuple(self.owner._engine._objects):
            if not self._is_solid(other):
                continue
            if not __import__("paralox3d").Collision(self.owner,other):
                continue

            other_min=other.collider.min
            other_max=other.collider.max
            vertical_overlap=min(player_max.y,other_max.y)-max(
                player_min.y,other_min.y
            )

            # A collider entirely below the character is the floor, not a
            # horizontal obstacle. This is what lets the player walk on planes.
            if vertical_overlap>0.05 and other_max.y>player_min.y+0.05:
                blocked=True
                break

        self.owner.position=original
        return not blocked

    def _try_step(self,amount):
        if not self.grounded or self.step_height<=0:
            return False

        from .math import Vec3

        original=self.owner.position
        raised=original+Vec3(0,self.step_height,0)
        if not self._horizontal_clear(raised+amount):
            return False

        self.owner.position=raised+amount

        # Snap to the top of the step. If there is no usable ground, restore.
        bottom=self.owner.collider.min.y
        hit=self._ray(
            Vec3(self.owner.x,bottom+0.08,self.owner.z),
            Vec3(0,-1,0),
            self.step_height+0.25
        )
        if hit and hit.object and self._is_solid(hit.object) and hit.normal.y>0.7:
            self.owner.y=hit.point.y+self.owner.collider.size.y*0.5
            return True

        self.owner.position=original
        return False

    def _move_horizontal(self,amount):
        if amount.length_squared()==0:
            return

        original=self.owner.position
        target=original+amount

        if self._horizontal_clear(target):
            self.owner.position=target
            return

        # Walk up small ledges before falling back to wall sliding.
        if self._try_step(amount):
            return

        # Try each horizontal axis independently for natural wall sliding.
        x_target=original+type(amount)(amount.x,0,0)
        if abs(amount.x)>0 and self._horizontal_clear(x_target):
            self.owner.position=x_target

        z_base=self.owner.position
        z_target=z_base+type(amount)(0,0,amount.z)
        if abs(amount.z)>0 and self._horizontal_clear(z_target):
            self.owner.position=z_target

    def _move_vertical(self,amount):
        """Move vertically and resolve the first blocking AABB."""
        if amount==0:
            return

        from .math import Vec3

        original=self.owner.position
        target=original+Vec3(0,amount,0)

        if self._horizontal_clear(target):
            self.owner.position=target
            return

        # The generic overlap test is enough here because horizontal movement
        # already excludes the floor from its wall test.
        self.owner.position=target
        hits=self._colliding_solid()

        if not hits:
            self.owner.position=original
            return

        if amount<0:
            # Landing: put the body directly on the highest surface below it.
            candidates=[
                o for o in hits
                if o.collider.max.y<=original.y+self.owner.collider.size.y*0.5+0.05
            ]
            if candidates:
                top=max(o.collider.max.y for o in candidates)
                self.owner.y=top+self.owner.collider.size.y*0.5
            else:
                self.owner.position=original
            self.grounded=True
            self.jumping=False
            self.velocity_y=0.0
        else:
            # Ceiling hit.
            candidates=[
                o for o in hits
                if o.collider.min.y>=original.y-self.owner.collider.size.y*0.5-0.05
            ]
            if candidates:
                bottom=min(o.collider.min.y for o in candidates)
                self.owner.y=bottom-self.owner.collider.size.y*0.5
            else:
                self.owner.position=original
            self.velocity_y=0.0
            self.jumping=False

    def _ground_check(self):
        from .math import Vec3

        bottom=self.owner.collider.min.y
        hit=self._ray(
            Vec3(self.owner.x,bottom+0.08,self.owner.z),
            Vec3(0,-1,0),
            self.step_height+0.18
        )
        if hit and hit.object and self._is_solid(hit.object) and hit.normal.y>0.7:
            self.owner.y=hit.point.y+self.owner.collider.size.y*0.5
            return True
        return False

    def _jump(self):
        if not self.grounded:
            return

        import math

        # Equivalent to v² = 2gh. The public jump_speed option can override it.
        g=max(0.01,self.gravity*10.0)
        self.velocity_y=(
            self.jump_speed
            if self.jump_speed is not None
            else math.sqrt(2.0*g*self.jump_height)
        )
        self.grounded=False
        self.jumping=True
        self.air_time=0.0

    def _vectors(self):
        # Do not duplicate the engine's rotation math here. Object.forward
        # and Object.right are the single source of truth for movement.
        return self.owner.forward, self.owner.right

    def _camera_update(self):
        from .camera import camera

        forward,_=self._vectors()
        if self.third_person:
            behind=forward*-self.distance
            camera.position=(
                self.owner.x+behind.x,
                self.owner.y+self.eye_height*0.5,
                self.owner.z+behind.z
            )
            camera.look_at((
                self.owner.x,
                self.owner.y+self.height*0.5,
                self.owner.z
            ))
        else:
            camera.position=(
                self.owner.x,
                self.owner.y+self.eye_height*0.5,
                self.owner.z
            )
            camera.rotation=(self._pitch,self._yaw,0)

    def update(self):
        from .input import held,pressed,mouse
        from .clock import dt
        from .math import Vec3

        frame_dt=max(0.0,float(dt))

        # Escape releases FPS mode. Re-enabling the component captures it again.
        if pressed("escape"):
            self.enabled=False
            return

        sx,sy=self.mouse_sensitivity
        # Native relative mouse X is opposite to the camera yaw direction
        # expected by the FPS controller. Invert it so moving the mouse left
        # turns the view left and moving it right turns the view right.
        self._yaw-=mouse.dx*sx
        self._pitch-=mouse.dy*sy
        self._pitch=max(-90.0,min(90.0,self._pitch))
        # Object rotation is the model/body rotation, so it is the inverse
        # of the camera's public yaw convention.
        self.owner.rotation=(0,-self._yaw,0)

        forward,right=self._vectors()
        move=forward*((1 if held("w") else 0)-(1 if held("s") else 0))
        move=move+right*((1 if held("d") else 0)-(1 if held("a") else 0))

        if move.length_squared():
            move=move.normalized()
            current_speed=self.speed
            if self.sprint and held(self.sprint_key):
                current_speed=self.sprint_speed
            self._move_horizontal(move*current_speed*frame_dt)

        if pressed("space"):
            self._jump()

        if self.gravity:
            gravity_strength=max(0.01,self.gravity*10.0)
            self.velocity_y-=gravity_strength*frame_dt
            self._move_vertical(self.velocity_y*frame_dt)

            if self.velocity_y<=0 and self._ground_check():
                self.grounded=True
                self.jumping=False
                self.air_time=0.0
                self.velocity_y=0.0
            elif self.grounded:
                # Keep grounded only while there is still a surface below us.
                self.grounded=False
            else:
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
