"""Run with blender -b --python-exit-code 1 -t 4 -P build_stage.py."""
from pathlib import Path
from math import cos, sin, sqrt, tau

import bpy
from mathutils import Vector

OUTPUT = Path(__file__).resolve().parent
STEPS = 120
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_end = STEPS
scene.render.fps = 24

def material(name, color, metal=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = .33
    return mat

steel = material("Blue-black painted steel", (.034, .078, .10), .45)
brass = material("Satin brass", (.63, .30, .07), .65)
teal = material("Petrol blue scenic panels", (.045, .33, .31), .15)
red = material("Vermilion scenic panel", (.63, .10, .045), .12)
floor = material("Charcoal stage floor", (.065, .077, .085))

def block(name, size, xyz, mat, bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    edge = obj.modifiers.new("Rounded edges", "BEVEL")
    edge.width = bevel
    edge.segments = 3
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj

def pin(name, xyz, radius=.09):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=.19,
                                       location=xyz, rotation=(tau/4, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(brass)
    return obj

def end(x, y, z, length, angle):
    return Vector((x + length*cos(angle), y, z + length*sin(angle)))

def pose_bar(obj, a, b, frame):
    obj.location = (a + b)/2
    obj.rotation_mode = "QUATERNION"
    q = (b - a).to_track_quat("Z", "Y")
    if frame > 1:
        q.make_compatible(obj.rotation_quaternion)
    obj.rotation_quaternion = q
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_quaternion", frame=frame)

def move(obj, xyz, frame):
    obj.location = xyz
    obj.keyframe_insert("location", frame=frame)

block("Stage", (20, 14, .25), (0, 1, -.13), floor)
for x, width, label in [(-2.2, 3.5, "Louvers"), (2.1, 3.1, "Lift")]:
    for side in (-1, 1):
        block(label + " upright", (.18, .32, 3.8),
              (x + side*width/2, .15, 1.9), steel)
    for z in (.13, 3.75):
        block(label + " crossmember", (width, .35, .20), (x, .15, z), steel)
    block(label + " backdrop", (width, .13, 3.5), (x, .38, 1.92), steel)

AXIS = -0.42
DEPTH = -.66
LEVER = .39
LEVELS = [.79, 1.55, 2.31, 3.07]
slats, arms, joints = [], [], []
for index, z in enumerate(LEVELS, 1):
    slats.append(block(f"Louver {index}", (2.54, .16, .59), (-2.39, DEPTH, z), teal))
    arms.append(block(f"Louver lever {index}", (.11, .10, LEVER), (0, 0, 0), brass))
    joints.append(pin(f"Connecting bar pin {index}", (0, DEPTH, z), .065))
    joints[-1].rotation_euler = (0, tau/4, 0)
    pivot_pin = pin(f"Louver pivot {index}", (AXIS, DEPTH, z), .105)
    pivot_pin.rotation_euler = (0, tau/4, 0)
tie = block("Louver connecting bar", (.10, .10, LEVELS[-1]-LEVELS[0]), (0, 0, 0), brass)

CX, CY, CZ = 2.1, -.68, .77
RADIUS, ROD = .36, 1.40
lift = block("Sliding scenic panel", (2.61, .19, 1.02), (CX, -.07, 2.5), red)
for x in (CX-1.35, CX+1.35):
    block("Panel guide", (.095, .33, 2.1), (x, -.07, 2.52), brass)
base = Vector((CX, CY, CZ))
pin("Crank axle", base, .16)
crank = block("Crank arm", (.15, .13, RADIUS), base, brass)
rod = block("Connecting rod", (.115, .11, ROD), base, brass)
crank_pin = pin("Crank pin", base, .08)
slide_pin = pin("Slider wrist pin", base, .09)

for frame in range(1, STEPS+2):
    phase = tau*(frame-1)/STEPS
    tilt = .57 + .50*sin(phase)
    links = []
    for z, slat, arm, joint in zip(LEVELS, slats, arms, joints):
        slat.rotation_euler.x = tilt
        slat.keyframe_insert("rotation_euler", frame=frame)
        pivot = Vector((AXIS, DEPTH, z))
        tip = pivot + Vector((0, -LEVER*sin(tilt), LEVER*cos(tilt)))
        pose_bar(arm, pivot, tip, frame)
        move(joint, tip + Vector((.065, 0, 0)), frame)
        links.append(tip)
    pose_bar(tie, links[0], links[-1], frame)
    assert abs((links[-1]-links[0]).length - (LEVELS[-1]-LEVELS[0])) < 1e-5

    crank_end = end(*base, RADIUS, phase)
    slide_z = crank_end.z + sqrt(ROD**2 - (crank_end.x-CX)**2)
    slider = Vector((CX, CY, slide_z))
    assert abs((slider-crank_end).length - ROD) < 1e-5
    pose_bar(crank, base, crank_end, frame)
    pose_bar(rod, crank_end, slider, frame)
    move(crank_pin, crank_end + Vector((0, -.12, 0)), frame)
    move(slide_pin, slider + Vector((0, -.12, 0)), frame)
    move(lift, (CX, -.07, slide_z+.28), frame)

# Extend each louver's axle from the drive plane through the panel.
for z in LEVELS:
    axle = pin("Louver axle extension", (-.77, DEPTH, z), .055)
    axle.rotation_euler = (0, tau/4, 0)
    axle.scale.z = 3.9
    block("Louver bearing mount", (.18, .82, .17), (AXIS, -.27, z), steel)
block("Slider standoff", (.17, .63, .16), (CX, -.37, 2.05), brass)
standoff = bpy.context.object
standoff.parent = slide_pin
standoff.location = (0, .42, 0)

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(5.3, -14, 7.1))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 1.72))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 9.8
for name, xyz, energy, size, color in [
    ("Warm key", (-4, -6, 8), 1500, 6, (1, .82, .65)),
    ("Cool fill", (5, -4, 5), 1150, 5, (.54, .73, 1)),
    ("Top rim", (0, 3, 8), 1750, 5, (.78, .90, 1)),
]:
    bpy.ops.object.light_add(type="AREA", location=xyz)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    aim(light, (0, 0, 1.6))
scene.world = bpy.data.worlds.new("Stage ambient")
scene.world.color = (.16, .16, .16)
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x = 1000
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.filepath = "//stage-preview.png"
scene.frame_set(18)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "stage-mechanisms.blend"))
bpy.ops.render.render(write_still=True)
