from paralox3d import *
import math

# ============================================================
# PARALOX3D — VISUAL FEATURE SHOWCASE
# ============================================================

modes.developer = True
modes.camera = True

camera.position = (0, 3, 14)
camera.look_at((0, 0, -2))

scene = Scene("Paralox3D Visual Feature Showcase")
scene.enter()

center = Object("cube", position=(0, 0, 0), scale=2, name="Center")
center.color = electric_blue

red_cube = Object("cube", position=(-4, 0, 0), scale=1.5, name="Player")
red_cube.color = crimson

green_cube = Object("cube", position=(4, 0, 0), scale=1.5, name="Enemy")
green_cube.color = neon_green

parent = Object("cube", position=(0, 3, -2), scale=.7, name="Parent")
parent.color = gold
child = Object("cube", position=(2, 0, 0), scale=.5, name="Child", parent=parent)
child.color = hot_pink

ground = Object("cube", position=(0, -3, -2), scale=(14, 1, 10), name="Ground")
ground.color = dark_gray
ground.collider.layer = "ground"

red_cube.add_tag("player").add_tag("actors")
green_cube.add_tag("enemy").add_tag("actors")

print("=== TAGS / GROUPS ===")
print("Player objects:", find_with_tag("player"))
print("Enemy objects:", find_with_tag("enemy"))
print("Actor group:", find_with_tag("actors"))
print("Player has tag:", red_cube.has_tag("player"))
print("Enemy has tag:", green_cube.has_tag("enemy"))

red_cube.collider.layer = "player"
red_cube.collider.collides_with = {"ground", "enemy"}
green_cube.collider.layer = "enemy"
green_cube.collider.collides_with = {"player"}

target = Object("cube", position=(0, 0, -5), scale=2, name="CastTarget")
target.color = orange

ray_visual = Object("cube", position=(0, 0, 1), scale=(.08, .08, 10), name="RayVisual")
ray_visual.color = red
box_visual = Object("cube", position=(2.7, 0, 1), scale=(1.0, 1.0, 8), name="BoxCastVisual")
box_visual.color = yellow
sphere_visual = Object("cube", position=(-2.7, 0, 1), scale=(1.2, 1.2, 8), name="SphereCastVisual")
sphere_visual.color = magenta

red_cube.position = (0, -1.5, 0)
print("=== COLLISION ===")
print("Collision(red_cube, ground):", Collision(red_cube, ground))
print("Collisions(red_cube):", Collision(red_cube))
red_cube.position = (-4, 0, 0)

print("=== CASTS ===")
hit = raycast((0, 0, 6), (0, 0, -1), distance=20)
print("Raycast:", hit.object.name if hit else None)
hit = boxcast((2.7, 0, 6), (1, 1, 1), (0, 0, -1), distance=20)
print("Boxcast:", hit.object.name if hit else None)
hit = spherecast((-2.7, 0, 6), .5, (0, 0, -1), distance=20)
print("Spherecast:", hit.object.name if hit else None)
print("Overlap box:", [o.name for o in overlap_box((0, 0, 0), (5, 5, 5))])
print("Overlap sphere:", [o.name for o in overlap_sphere((0, 0, 0), 4)])

bind("move_left", "a")
bind("move_right", "d")
bind("jump", "space")
print("=== INPUT ===")
print("Actions registered: move_left=A, move_right=D, jump=SPACE")

counter = 0
def delayed_message():
    print("after() TIMER WORKED!")
after(2.0, delayed_message)

def repeating_timer():
    global counter
    counter += 1
    print("every() tick:", counter)
    if counter >= 5:
        repeating.cancel()
        print("Repeating timer cancelled.")
repeating = every(1.0, repeating_timer)

elapsed = 0.0
print("=== VISUAL DEMO ===")
print("WASD moves the parent. SPACE reports jump. Mouse camera is active.")
print("Center color pulses; the three cast visuals stay visible.")

def update():
    global elapsed
    elapsed += dt
    center.rotation = (elapsed * 25, elapsed * 55, elapsed * 15)
    parent.rotation = (0, -elapsed * 45, 0)
    red_cube.rotation = (elapsed * 50, elapsed * 30, 0)
    green_cube.rotation = (0, -elapsed * 40, elapsed * 20)
    red_cube.x = -4 + math.sin(elapsed) * .8
    green_cube.x = 4 + math.cos(elapsed) * .8

    center.color = (
        .15 + .75 * (math.sin(elapsed) + 1) / 2,
        .15 + .75 * (math.sin(elapsed + 2.1) + 1) / 2,
        .15 + .75 * (math.sin(elapsed + 4.2) + 1) / 2,
    )

    if action("move_left"):
        parent.x -= 3 * dt
    if action("move_right"):
        parent.x += 3 * dt
    if action_pressed("jump"):
        print("Jump action pressed!")
    if mouse.dx or mouse.dy:
        print("Mouse:", mouse.position, "delta:", (mouse.dx, mouse.dy))

start()
