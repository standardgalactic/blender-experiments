"""Build with blender -b --python-exit-code 1 -t 4 -P build_hoberman_ring.py."""
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



from math import pi, atan2

CELLS = 10
HALF = pi/CELLS
K = .49
ARM = K/cos(HALF)
BEND = K*sin(HALF)/cos(HALF)
Z = 1.94

block("Stage floor", (26, 16, .25), (0, 0, -.13), deck)


def radial(radius, angle):
    return Vector((radius*cos(angle), 0, radius*sin(angle)))


def bent_link():
    # Local X follows the chord. Local Z points from chord midpoint to pivot.
    obj = bpy.data.objects.new("Rigid bent link", None)
    scene.collection.objects.link(obj)
    for side in (-1, 1):
        a, b = Vector((side*K, 0, 0)), Vector((0, 0, BEND))
        arm = block("Bent link arm", (ARM+.095, .085, .115), (0, 0, 0), teal if side == 1 else red, .028)
        arm.parent = obj
        arm.location = (a+b)/2
        arm.rotation_euler.y = -atan2(b.z-a.z, b.x-a.x)
    return obj


for x, offset, label in [(-4, 0, "Contracted"), (0, 40, "Intermediate"),
                         (4, 80, "Expanded")]:
    center = Vector((x, 0, Z))
    block(label + " plinth", (3.60, 1.30, .21), (x, .40, .105), steel)
    cells = []
    for i in range(CELLS):
        links = [bent_link(), bent_link()]
        pins = [pin("Common elbow pivot", (0, 0, 0), .071, .29)]
        pins.extend(pin("Radial joint", (0, 0, 0), .060, .29) for _ in range(2))
        cells.append((links, pins))
    for frame in range(1, STEPS+2):
        phase = tau*(frame-1+offset)/STEPS
        t = .18 + .86*(1+cos(phase))/2
        mean = K*cos(t)/sin(HALF)
        gap = K*sin(t)/cos(HALF)
        radii = (mean-gap, mean+gap)
        for i, (links, pins) in enumerate(cells):
            angle = tau*i/CELLS
            elbow = center + radial(mean/cos(HALF), angle+HALF)
            anchors = [center + radial(radius, angle) for radius in radii]
            for j, link in enumerate(links):
                a = anchors[j]
                b = center + radial(radii[1-j], angle+2*HALF)
                mid = (a+b)/2
                chord = b-a
                assert abs(chord.length-2*K) < 1e-6
                assert abs((elbow-a).length-ARM) < 1e-6
                assert abs((elbow-b).length-ARM) < 1e-6
                assert abs((elbow-mid).length-BEND) < 1e-6
                # Align local X to the chord and local Z toward the elbow.
                u = chord.normalized()
                w = (elbow-mid).normalized()
                v = w.cross(u)
                link.rotation_mode = "QUATERNION"
                q = Matrix((u, v, w)).transposed().to_quaternion()
                if frame > 1:
                    q.make_compatible(link.rotation_quaternion)
                link.rotation_quaternion = q
                link.location = mid + Vector((0, (-1)**j*.063, 0))
                link.keyframe_insert("location", frame=frame)
                link.keyframe_insert("rotation_quaternion", frame=frame)
            for obj, point in zip(pins, [elbow, *anchors]):
                obj.location = point
                obj.keyframe_insert("location", frame=frame)

for frame, label in [(1, "Contracted"), (41, "Intermediate"), (81, "Expanded")]:
    scene.timeline_markers.new("Left ring | " + label, frame=frame)

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(2.2, -16, 6.9))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 1.98))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 13.2
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
scene.render.filepath = str(OUTPUT / "hoberman-ring-preview.png")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "hoberman-ring.blend"))
bpy.ops.render.render(write_still=True)
