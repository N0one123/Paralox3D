from paralox3d import Engine, Entity

engine = Engine(title="Paralox3D Hello", width=1280, height=720)

cube = Entity(
    engine,
    model="cube",
    position=(0.0, 0.0, 5.0),
)

engine.run()
