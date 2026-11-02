"""10,000 visible-cube rendering benchmark.

Run with: python benchmarks/scene_10k.py
Close the game window to stop. The console reports measured update-loop FPS.
"""
from time import perf_counter

from paralox3d import Engine, Object, camera, modes

COUNT = 10_000
modes.low_quality = True
modes.camera = True

engine = Engine(title="Paralox3D 10K Benchmark", width=1280, height=720)
camera.position = (50, 50, 150)
camera.look_at((50, 50, 0))

print("Creating 10,000 cubes...")
for x in range(100):
    for y in range(100):
        Object("cube", position=(x, y, 0), scale=0.8)

print("Scene ready. Measuring frame-loop rate; close the window to stop.")
frames = 0
started = perf_counter()
last_report = started

def update():
    global frames, started, last_report
    frames += 1
    now = perf_counter()
    elapsed = now - last_report
    if elapsed >= 1.0:
        print("Measured update FPS: {:.1f} | objects: {:,}".format(frames / elapsed, COUNT))
        frames = 0
        last_report = now

engine.start(update)
