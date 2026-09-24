# Paralox3D

A performance-first Python 3D engine designed from the ground up for desktop and mobile.

**[Read the Documentation](https://n0one123.github.io/Paralox3D/)**

## API philosophy

Paralox3D should feel like writing a game, not manually operating an engine.

- Automatic/default engine context.
- No mandatory Engine object for simple games.
- Built-in transform properties: x, y, z, position, rotation, scale.
- Simple components.
- QoL-first input helpers.
- First-class Scenes for storing and loading levels.
- Native C++ core for performance-critical work.
- No lighting system in this milestone.

## Example

```python
from paralox3d import *

cube = Object("cube", position=(0, 0, -5))

def update():
    cube.x += 0.5 * dt

start()
```

## Scenes

Scenes are first-class levels. They are intended to replace repeatedly rebuilding large worlds in Python files.

```python
from paralox3d import *

scene = Scene("Level1")
scene.create("cube", position=(0, 0, -5))
scene.create("cube", position=(2, 0, -5))

scene.save("scenes/Level1.scene")
```

Later:

```python
scene = Scene.load("scenes/Level1.scene")
```

The current scene format is readable JSON, making it easy to inspect and version-control. The public Scene API is deliberately independent of the file format.

## Architecture

```
Python game code
      │
      ▼
Paralox3D Python API
      │
      ▼
C ABI boundary
      │
      ▼
Native C++ engine
      │
      ├── Scene / entities
      ├── Transforms
      ├── visibility / culling
      └── renderer backends
             ├── Desktop
             ├── Android
             └── iOS / Metal
```

Lighting is deliberately postponed. When it is introduced, it must be designed for low overhead and older hardware rather than assuming expensive directional lighting is acceptable.

## Native builds

The native core is built without CMake.

For a source checkout:

```text
python -m paralox3d build
```

The build system currently supports Windows, Linux, and macOS native targets. Android and iOS targets are reserved for future platform toolchains.

When building a wheel for distribution, the native library is built and bundled into the wheel.

## Status

🚧 Early development — API and native core are being built together.

## License

MIT
