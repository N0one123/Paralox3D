# Vertex3D

A performance-first Python 3D engine designed from the ground up for desktop and mobile.

## Design goals

- Pythonic API for game development.
- Native C++ core for hot paths.
- Low Python↔native overhead.
- Batching, instancing, culling and streaming built into the architecture.
- Android and iOS support designed in from day one.
- Lightweight enough to remain useful on older hardware.

## Architecture

```
Python game code
      │
      ▼
Vertex3D Python API
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
      ├── render queue
      └── renderer backends
             ├── Desktop
             ├── Android
             └── iOS / Metal
```

The first development milestone is deliberately small: establish the native core + Python API boundary, then add a real GPU backend without making the public API depend on it.

## Status

🚧 Early development — architecture and native core are being built first.

## License

MIT
