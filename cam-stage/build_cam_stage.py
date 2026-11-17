"""Build an animated cam-driven reveal and render its three poses.

Run with blender -b --python-exit-code 1 -t 4 -P build_cam_stage.py.
"""
from pathlib import Path
from math import cos, sin, tau

import bpy
from mathutils import Matrix, Vector

OUTPUT = Path(__file__).resolve().parent
STEPS = 160
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
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
cream = material("Cream scenic panel", (.62, .52, .33), .08)
deck = material("Charcoal stage floor", (.065, .077, .085))


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


def pin(name, xyz, radius=.09, depth=.19, mat=None):
    """Cylinder whose axis runs along Y, the stage depth axis."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth,
                                       location=xyz, rotation=(tau/4, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat or brass)
    return obj


def stage_frame(label, x, width, height):
    for side in (-1, 1):
        block(label + " upright", (.18, .32, height),
              (x + side*width/2, .15, height/2), steel)
    for z in (.13, height - .05):
        block(label + " crossmember", (width, .35, .20), (x, .15, z), steel)
    block(label + " backdrop", (width, .13, height - .3), (x, .38, height/2 + .02), steel)


block("Stage", (26, 14, .25), (0, 1, -.13), deck)


BASE_RADIUS = .63
ROLLER_RADIUS = .14
TRAVEL = .78
AXLE_Z = 1.51
CAM_Y = -.67
SAMPLES = 720


def follower(phase):
    """Return the follower displacement and its derivative per drive radian."""
    turn = (phase / tau) % 1
    if turn < .125 or turn >= .875:
        return 0, 0
    if .375 <= turn < .625:
        return TRAVEL, 0
    rising = turn < .375
    start = .125 if rising else .625
    u = (turn - start) / .25
    position = u - sin(tau*u)/tau
    slope = (1 - cos(tau*u)) / (.25*tau)
    if rising:
        return TRAVEL*position, TRAVEL*slope
    return TRAVEL*(1-position), -TRAVEL*slope


def cam_point(theta):
    """Offset the roller-centre pitch curve inward along its unit normal."""
    height, slope = follower(theta)
    radius = BASE_RADIUS + ROLLER_RADIUS + height
    s, c = sin(theta), cos(theta)
    pitch = Vector((radius*s, radius*c))
    tangent = Vector((slope*s + radius*c, slope*c - radius*s))
    normal = Vector((-tangent.y, tangent.x)).normalized()
    return pitch - ROLLER_RADIUS*normal


rim = [cam_point(tau*i/SAMPLES) for i in range(SAMPLES)]
assert AXLE_Z > max(p.length for p in rim)


def cam(x):
    depth = .23
    vertices = [(p.x, y, p.y) for y in (-depth/2, depth/2) for p in rim]
    faces = [tuple(reversed(range(SAMPLES))), tuple(range(SAMPLES, 2*SAMPLES))]
    for i in range(SAMPLES):
        j = (i+1) % SAMPLES
        faces.append((i, j, SAMPLES+j, SAMPLES+i))
    mesh = bpy.data.meshes.new("Roller-compensated cam profile")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Plate cam", mesh)
    scene.collection.objects.link(obj)
    obj.location = (x, CAM_Y, AXLE_Z)
    obj.data.materials.append(brass)
    return obj


for x, label, offset in [
    (-4.1, "Low dwell", 0),
    (0, "Rising", 40),
    (4.1, "High dwell", 80),
]:
    stage_frame(label, x, 3.65, 4.70)
    for rail_x in (x-.85, x+.85):
        block("Vertical gate guide", (.095, .28, 1.92), (rail_x, -.23, 3.41), steel)
    block("Scenic opening lining", (1.59, .08, .74), (x, .12, 2.93), cream)
    block("Inset landscape", (1.43, .10, .60), (x, .07, 2.93), red)
    block("Horizon", (1.40, .09, .11), (x, .005, 2.75), cream, .014)
    panel = block("Scenic reveal gate", (1.62, .20, .83), (x, -.24, 0), teal)
    stem = block("Follower stem", (.12, .16, .50), (x, CAM_Y, 0), steel)
    bridge = block("Gate bracket", (.20, .45, .11), (x, -.46, 0), steel)
    roller = pin("Roller follower", (x, CAM_Y, 0), ROLLER_RADIUS, .30, cream)
    plate = cam(x)
    pin("Cam axle", (x, -.39, AXLE_Z), .115, .97, steel)
    witness = pin("Cam phase mark", (0, 0, 0), .046, .035, cream)
    witness.parent = plate
    witness.location = (0, -.123, .41)

    for frame in range(1, STEPS+2):
        theta = tau*(frame-1+offset)/STEPS
        r = BASE_RADIUS + ROLLER_RADIUS + follower(theta)[0]
        roller_z = AXLE_Z + r
        plate.rotation_euler.y = -theta
        plate.keyframe_insert("rotation_euler", frame=frame)
        for obj, z in ((roller, roller_z), (stem, roller_z+.30),
                       (bridge, roller_z+.53), (panel, roller_z+.65)):
            obj.location.z = z
            obj.keyframe_insert("location", frame=frame)
        pitch = Vector((r*sin(theta), r*cos(theta)))
        assert abs((cam_point(theta)-pitch).length - ROLLER_RADIUS) < 1e-6
        assert min((p-pitch).length for p in rim) >= ROLLER_RADIUS - .0001

for frame, label in [(1, "Left gate at low dwell"), (41, "Left gate rising"),
                     (81, "Left gate at high dwell"), (121, "Left gate returning")]:
    scene.timeline_markers.new(label, frame=frame)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(1.6, -16, 6.1))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 2.30))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 14.0
for name, xyz, energy, size, color in [
    ("Warm key", (-7, -6, 8), 2100, 7, (1, .82, .65)),
    ("Cool fill", (8, -4, 5), 1700, 6, (.54, .73, 1)),
    ("Top rim", (0, 3, 8), 2400, 7, (.78, .90, 1)),
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
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x = 1400
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.filepath = str(OUTPUT / "cam-stage-preview.png")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "cam-stage.blend"))
bpy.ops.render.render(write_still=True)
