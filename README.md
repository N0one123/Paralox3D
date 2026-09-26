# Paralox3D

A performance-first Python 3D engine designed from the ground up for desktop and mobile.

**[Read the Documentation](https://n0one123.github.io/Paralox3D/)**

## 0.1.1

Paralox3D 0.1.1 is a major API expansion focused on making everyday game code easier.

### Core API

- Automatic/default engine context — simple games do not need an Engine object.
- Automatic game loop with `start()`.
- Universal `dt` available directly inside `update()`; no `dt` parameter is required.
- Built-in transform properties: `x`, `y`, `z`, `position`, `rotation`, `scale`.
- Local/world transforms and parent-child hierarchy.
- Direction helpers: `forward`, `right`, `up`.
- Convenience methods: `move()`, `translate()`, `rotate()`, `scale_by()`, `look_at()`, `distance_to()`, `move_forward()`, `move_right()`, `move_up()`.
- Object lifecycle: `enabled`, `visible`, `destroy()`.
- Object lookup: `find()`, `find_all()`, `find_with_tag()`, `find_by_id()`.
- Stable per-engine Object IDs through `object.id`.
- Tags with `add_tag()`, `remove_tag()`, and `has_tag()`.
- Components and controller helpers with start, enable/disable, update, and destroy lifecycle hooks.
- Expanded `Vec3` math.

### Input

Keyboard input supports held and pressed states plus named actions:

```python
from paralox3d import *

bind("move", "w", "up")

def update():
    if action("move"):
        player.z -= 5 * dt

    if action_pressed("jump"):
        print("Jump!")

start()
```

Mouse state is available through `mouse.position`, `mouse.x`, `mouse.y`, `mouse.dx`, `mouse.dy`, `mouse.left`, `mouse.right`, `mouse.middle`, and `mouse.pressed(...)`. The native camera can also use mouse controls when `modes.camera = True`.

### Camera

```python
modes.camera = True
camera.position = (0, 2, 8)
camera.look_at((0, 0, 0))
```

The camera exposes position, pitch, yaw, roll, and `look_at()`. Native camera controls support left-drag rotation and right-drag panning.

### Object appearance

Object visual state is reactive:

```python
cube.color = hot_pink
cube.opacity = 0.8
cube.visible = True
cube.enabled = True
cube.rotation = (0, 45, 0)
```

RGB tuples remain supported, with values clamped to 0..1.

0.1.1 includes a large set of named RGB colors such as `red`, `orange`, `yellow`, `green`, `lime`, `cyan`, `sky_blue`, `blue`, `purple`, `violet`, `magenta`, `pink`, `brown`, `white`, `gray`, plus game-friendly names such as `electric_blue`, `neon_green`, `neon_pink`, `neon_purple`, `fire`, `poison`, and `energy`.

```python
cube.color = electric_blue
enemy.color = neon_green
pickup.color = gold
```

### Collision and spatial queries

Every Object has a configurable `Collider`.

```python
player.collider.size = (1, 2, 1)
player.collider.offset = (0, 0.1, 0)
player.collider.layer = "player"
player.collider.collides_with = {"enemy", "ground"}
```

Use `Collision(a, b)` for a pair or `Collision(a)` to find all compatible overlaps.

Spatial queries include:

- `raycast(origin, direction, distance=...)`
- `boxcast(center, size, direction, distance=...)`
- `spherecast(center, radius, direction, distance=...)`
- `overlap_box(center, size)`
- `overlap_sphere(center, radius)`
- Collision callbacks: `on_collision`, `on_enter`, and `on_exit` can be assigned to Objects.

Each cast returns a `RaycastHit` containing `object`, `point`, `normal`, and `distance`, or `None`.\n\nAssign collision callbacks directly to an Object for per-frame and enter/exit events:\n\n```python\nplayer.on_enter = lambda other: print("Entered:", other.name)\nplayer.on_collision = lambda other: print("Touching:", other.name)\nplayer.on_exit = lambda other: print("Left:", other.name)\n```

### Timers

Frame-driven timers are available without building your own counters:

```python
after(2.0, lambda: print("Done!"))

timer = every(1.0, lambda: print("Tick"))
timer.cancel()
```

The `Timer` class also provides `done`, `cancel()`, and `reset()`. Use `cancel(timer)` for the global helper.

### Scenes

Scenes are first-class worlds/levels:

```python
scene = Scene("Level1")
scene.create("cube", position=(0, 0, -5))
scene.enter()

scene.save("scenes/Level1.scene")
loaded = Scene.load("scenes/Level1.scene")
Scene.switch(loaded)
```

Scenes support lifecycle callbacks, clearing, JSON persistence, loading, and switching.

### Developer mode

```python
modes.developer = True
```

Developer mode enables diagnostic information and visual collider bounds.

## Example

```python
from paralox3d import *

modes.camera = True

player = Object("cube", position=(0, 0, 0), name="Player")
player.color = electric_blue

bind("left", "a")
bind("right", "d")

def update():
    if action("left"):
        player.x -= 4 * dt
    if action("right"):
        player.x += 4 * dt

start()
```

## Native builds

The native core is built without CMake:

```text
python -m paralox3d build
```

The build system currently supports Windows, Linux, and macOS native targets. Android and iOS targets are reserved for future platform toolchains.

When building a wheel for distribution, the native library is built and bundled into the wheel.

## Architecture

```
Python game code
      |
      v
Paralox3D Python API
      |
      v
C ABI boundary
      |
      v
Native C++ engine
      |
      +-- scene / entities
      +-- transforms / visibility
      +-- collision queries
      +-- input / camera
      +-- renderer
```

Lighting is deliberately postponed. When it is introduced, it should be designed for low overhead and older hardware.

## Status

🚧 Early development — 0.1.1 is an API expansion milestone and the Python/native layers are still evolving together.

## License

MIT
