from paralox3d import *

cube=Object("cube",position=(0,0,-5))

def update(dt):
    cube.x += 0.5 * dt

start()
