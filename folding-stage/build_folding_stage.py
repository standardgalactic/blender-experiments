"""Build with blender -b --python-exit-code 1 -t 4 -P build_folding_stage.py."""
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



from math import atan2

LENGTH = .86
HEIGHT = 2.12
HINGE_Z = (.62, 1.48, 2.36)
block("Stage floor", (26, 16, .25), (0, 0, -.13), deck)
for x, offset, label in [(-4.7, 0, "Extended"), (0, 40, "Folding"),
                         (4.7, 80, "Stacked")]:
    block(label + " plinth", (4.15, 2.30, .24), (x, .19, .12), steel)
    start = x-1.67
    block("Floor track", (3.63, .18, .065), (x, 0, .27), brass)
    block("Fixed hinge post", (.14, .17, 2.44), (start-.12, .04, 1.46), steel)
    block("Fixed hinge bracket", (.28, .17, .12), (start-.08, 0, 2.36), steel)
    panels = []
    hinges = []
    for i in range(4):
        leaf = block(f"{label} leaf {i+1}", (LENGTH-.045, .075, HEIGHT),
                     (0, 0, 0), steel, .022)
        inset = block("Painted inset", (LENGTH-.17, .035, HEIGHT-.19),
                      (0, 0, 0), teal if i % 2 == 0 else red, .016)
        inset.parent = leaf
        inset.location = (0, -.041, 0)
        for j in range(2):
            trim = block("Inset trim", (LENGTH-.24, .023, .027),
                         (0, 0, 0), cream, .007)
            trim.parent = leaf
            trim.location = (0, -.062, -.70+j*.15)
        panels.append(leaf)
    for i in range(5):
        axle = pin(f"Hinge {i+1}", (0, 0, 0), .034, HEIGHT+.04)
        axle.rotation_euler = (0, 0, 0)
        for z in HINGE_Z:
            sleeve = pin("Hinge knuckle", (0, 0, 0), .065, .19)
            sleeve.rotation_euler = (0, 0, 0)
            sleeve.parent = axle
            sleeve.location = (0, 0, z-1.46)
        hinges.append(axle)
    shoes = [block("Track carriage", (.21, .27, .16), (0, 0, .36), steel)
             for _ in range(3)]
    for frame in range(1, STEPS+2):
        angle = .075 + 1.315*(1-cos(tau*(frame-1+offset)/STEPS))/2
        dx = LENGTH*cos(angle)
        dy = LENGTH*sin(angle)
        joints = [Vector((start+i*dx, (i % 2)*dy, 1.46)) for i in range(5)]
        for leaf, a, b in zip(panels, joints, joints[1:]):
            delta = b-a
            assert abs(delta.length-LENGTH) < 1e-6
            leaf.location = (a+b)/2
            leaf.rotation_euler.z = atan2(delta.y, delta.x)
            leaf.keyframe_insert("location", frame=frame)
            leaf.keyframe_insert("rotation_euler", frame=frame)
        for axle, point in zip(hinges, joints):
            axle.location = point
            axle.keyframe_insert("location", frame=frame)
        for shoe, point in zip(shoes, joints[::2]):
            assert point.y == 0
            shoe.location.x = point.x
            shoe.keyframe_insert("location", frame=frame)

for frame, label in [(1, "Extended"), (41, "Half folded"), (81, "Stacked")]:
    scene.timeline_markers.new("Left wall | " + label, frame=frame)

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(3.5, -15, 9.4))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 1.3))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 15.4
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
scene.render.filepath = str(OUTPUT / "folding-stage-preview.png")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "folding-stage.blend"))
bpy.ops.render.render(write_still=True)
