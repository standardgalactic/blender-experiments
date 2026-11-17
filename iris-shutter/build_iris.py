"""Run with blender -b --python-exit-code 1 -t 4 -P build_iris.py.

A twelve blade iris, after the opening and closing mechanisms of the catalog (Part 3, 21).
Each blade hinges on a fixed plate and carries a drive pin in a radial slot of a rotating
ring. The blade angle drives the ring angle, and every frame asserts that each pin lies on
its slot centreline and inside the slot length.
"""
from pathlib import Path
from math import atan2, cos, pi, radians, sin, sqrt, tau

import bpy
import bmesh
from mathutils import Matrix, Vector

OUTPUT = Path(__file__).resolve().parent
STEPS = 240
CYCLES = 2
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = STEPS
scene.render.fps = 24


def material(name, color, metal=0.0, rough=.4, glow=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = rough
    if glow:
        shader.inputs["Emission Color"].default_value = (*color, 1)
        shader.inputs["Emission Strength"].default_value = glow
    return mat


def block(name, size, xyz, mat, bevel=.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        edge = obj.modifiers.new("Rounded edges", "BEVEL")
        edge.width = bevel
        edge.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def pin(name, xyz, radius, depth, mat):
    """Cylinder whose axis runs along Y, the stage depth axis."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth,
                                       location=xyz, rotation=(tau/4, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def lift(v, y):
    return Vector((v.x, y, v.z))


def pose_bar(obj, a, b, frame):
    """Place a block whose long axis is local Z so it spans point a to point b.

    Local Y stays on world Y so flat plates keep their broad face to the camera.
    """
    obj.location = (a + b)/2
    obj.rotation_mode = "QUATERNION"
    z_axis = (b - a).normalized()
    y_axis = Vector((0, 1, 0))
    x_axis = y_axis.cross(z_axis)
    q = Matrix((x_axis, y_axis, z_axis)).transposed().to_quaternion()
    if frame > 1:
        q.make_compatible(obj.rotation_quaternion)
    obj.rotation_quaternion = q
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_quaternion", frame=frame)


def move(obj, xyz, frame):
    obj.location = xyz
    obj.keyframe_insert("location", frame=frame)


def spin(obj, angle, frame):
    """Turn an object counter-clockwise, as seen from the camera, by angle."""
    obj.rotation_euler = (0, -angle, 0)
    obj.keyframe_insert("rotation_euler", frame=frame)


def adopt(child, parent, local_xyz, rotation=None):
    child.parent = parent
    child.location = local_xyz
    if rotation is not None:
        child.rotation_euler = rotation
    return child


def empty(name, xyz):
    obj = bpy.data.objects.new(name, None)
    obj.location = xyz
    scene.collection.objects.link(obj)
    return obj


def prism(name, outline, thickness, mat):
    """Extrude a convex or simple (x, z) outline along Y, front face toward the camera."""
    n = len(outline)
    half = thickness/2
    verts = [(x, -half, z) for x, z in outline] + [(x, half, z) for x, z in outline]
    faces = [list(range(n)), list(range(2*n - 1, n - 1, -1))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_setup(png, blend, preview_frame, samples=48):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT / png)
    scene.frame_set(preview_frame)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / blend))
    bpy.ops.render.render(write_still=True)
# Palette: ink plate, brass ring, oxblood blades, a warm lamp behind the aperture.
ink = material("Ink plate", (.02, .022, .028), .5, .4)
brass = material("Satin brass", (.70, .42, .12), .8, .3)
blade_mat = material("Oxblood blade", (.38, .035, .045), .1, .45)
lamp = material("Warm lamp", (1.0, .62, .28), 0, .5, glow=14)

BLADES = 12
HINGE_R, DRIVE_L, TAIL, TIP_LEN = 1.25, .85, 1.05, 1.9
HALF_HINGE, HALF_TIP, HALF_TAIL = .30, .16, .20
RING_IN, RING_OUT = 1.38, 2.55
SLOT_LO, SLOT_HI, SLOT_W = 1.46, 2.20, .12
KAPPA_MID, KAPPA_AMP = radians(43), radians(35)
Y_PLATE, Y_RING, Y_BLADE0, Y_STEP = -.20, -.31, -.43, -.032


def boolean(target, cutter):
    mod = target.modifiers.new("Cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


# Fixed plate with a round opening just inside the hinge circle.
plate = block("Iris plate", (9.0, .12, 6.2), (0, Y_PLATE, 0), ink, 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.0, depth=.6, location=(0, Y_PLATE, 0),
                                   rotation=(tau/4, 0, 0))
boolean(plate, bpy.context.object)

# Actuator ring with twelve radial slots, one per blade.
ring_spin = empty("Iris ring", (0, Y_RING, 0))
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=RING_OUT, depth=.08, rotation=(tau/4, 0, 0))
ring = bpy.context.object
ring.name = "Iris ring body"
ring.data.materials.append(brass)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=RING_IN, depth=.4, rotation=(tau/4, 0, 0))
boolean(ring, bpy.context.object)
for i in range(BLADES):
    phi = tau*i/BLADES
    mid = (SLOT_LO + SLOT_HI)/2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(mid*cos(phi), 0, mid*sin(phi)))
    cut = bpy.context.object
    cut.dimensions = (SLOT_HI - SLOT_LO, .4, SLOT_W)
    cut.rotation_euler = (0, -phi, 0)
    boolean(ring, cut)
adopt(ring, ring_spin, (0, 0, 0))

# Blades, hinge pins and drive pins.
blades, drive_pins = [], []
for i in range(BLADES):
    phi = tau*i/BLADES
    y = Y_BLADE0 + i*Y_STEP
    outline = [(-TAIL, -HALF_TAIL), (0, -HALF_HINGE), (TIP_LEN, -HALF_TIP),
               (TIP_LEN, HALF_TIP), (0, HALF_HINGE), (-TAIL, HALF_TAIL)]
    blade = prism(f"Iris blade {i}", outline, .028, blade_mat)
    blade.rotation_mode = "XYZ"
    blades.append(blade)
    hinge = Vector((HINGE_R*cos(phi), y, HINGE_R*sin(phi)))
    pin(f"Iris hinge pin {i}", (hinge.x, -.38, hinge.z), .06, .36, brass)
    drive_pins.append(pin(f"Iris drive pin {i}", (0, 0, 0), .045, .30, brass))

# Backlight behind the plate.
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.9, depth=.05, location=(0, .45, 0),
                                   rotation=(tau/4, 0, 0))
glow = bpy.context.object
glow.name = "Iris lamp"
glow.data.materials.append(lamp)

s_values = []
for frame in range(1, STEPS + 2):
    phase = tau*CYCLES*(frame - 1)/STEPS
    kappa = KAPPA_MID + KAPPA_AMP*sin(phase)
    # Blade direction is phi + 90 deg + kappa; the drive pin sits DRIVE_L behind the hinge.
    pin_r = HINGE_R + DRIVE_L*sin(kappa)
    pin_t = -DRIVE_L*cos(kappa)
    beta = atan2(pin_t, pin_r)          # slot angle relative to the hinge direction
    s = sqrt(pin_r**2 + pin_t**2)
    s_values.append(s)
    assert SLOT_LO + .05 < s < SLOT_HI - .05, "drive pin leaves its slot"
    spin(ring_spin, beta, frame)
    for i in range(BLADES):
        phi = tau*i/BLADES
        y = Y_BLADE0 + i*Y_STEP
        hinge = Vector((HINGE_R*cos(phi), y, HINGE_R*sin(phi)))
        blades[i].location = hinge
        blades[i].rotation_euler = (0, -(phi + tau/4 + kappa), 0)
        blades[i].keyframe_insert("location", frame=frame)
        blades[i].keyframe_insert("rotation_euler", frame=frame)
        # Drive pin position from the blade, then check it lies on the ring slot centreline.
        direction = Vector((cos(phi + tau/4 + kappa), 0, sin(phi + tau/4 + kappa)))
        pin_pos = Vector((hinge.x, y, hinge.z)) - direction*DRIVE_L
        slot_dir = Vector((cos(phi + beta), 0, sin(phi + beta)))
        off_line = abs(slot_dir.x*pin_pos.z - slot_dir.z*pin_pos.x)
        assert off_line < 1e-5, f"pin off slot centreline at frame {frame}"
        move(drive_pins[i], (pin_pos.x, -.46 + i*Y_STEP*.5, pin_pos.z), frame)

bpy.ops.object.camera_add(location=(0, -17, .3))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 0))
scene.camera.data.lens = 50
bpy.ops.object.light_add(type="AREA", location=(-3.5, -6, 4.5))
key = bpy.context.object
key.name = "Soft key"
key.data.energy = 650
key.data.shape = "DISK"
key.data.size = 4
key.data.color = (1, .85, .7)
aim(key, (0, 0, 0))
scene.world = bpy.data.worlds.new("Dark house")
scene.world.color = (.012, .012, .016)
render_setup("iris-preview.png", "iris.blend", 75)
