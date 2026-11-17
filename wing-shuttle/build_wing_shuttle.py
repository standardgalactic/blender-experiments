"""Run with blender -b --python-exit-code 1 -t 4 -P build_wing_shuttle.py.

A Hoeken linkage (crank-rocker with the coupler extended to twice its length)
drives a scenic wing along a track. The foot pin rides a vertical slot in the wing,
so the wing follows only the x motion of the foot, which is a straight run for
about half of each crank turn (speed along that run is not constant).
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
# Palette: oxblood wall, umber floor, mustard wing, cream trim, satin brass hardware.
wall_mat = material("Oxblood backdrop", (.10, .016, .022), 0, .7)
floor_mat = material("Umber floor", (.045, .032, .028), 0, .55)
brass = material("Satin brass", (.70, .42, .12), .8, .3)
mustard = material("Mustard wing", (.78, .50, .06), 0, .5)
cream = material("Cream trim", (.80, .72, .52), 0, .6)
ink = material("Ink steel", (.02, .025, .03), .5, .35)

block("Floor", (30, 16, .3), (0, -2, -.15), floor_mat, 0)
block("Backdrop", (16, .2, 8), (0, .4, 3.7), wall_mat, 0)

# Hoeken linkage, scaled 0.55: crank 1, ground 2, coupler 2.5, rocker 2.5, foot at twice the coupler.
K = .55
crank_len, ground, coupler_len, rocker_len, reach = 1*K, 2*K, 2.5*K, 2.5*K, 2.0
a_pt = Vector((-1.4, 0, .75))
d_pt = a_pt + Vector((ground, 0, 0))
y_crank, y_coupler, y_wing = -.30, -.45, -.80
slot_w, slot_lo, slot_hi = .16, 2.85, 3.55
wing_z0, wing_h = 1.9, 2.8

for pt, name in ((a_pt, "crank"), (d_pt, "rocker")):
    pin(f"Wing {name} pivot", (pt.x, -.1, pt.z), .10, 1.0, brass)
crank = block("Wing crank", (.14, .12, crank_len + .22), (0, 0, 0), brass)
rocker = block("Wing rocker", (.14, .12, rocker_len + .22), (0, 0, 0), brass)
coupler = block("Wing coupler", (.14, .12, coupler_len*reach + .25), (0, 0, 0), brass)
joint_b = pin("Wing crank joint", (0, 0, 0), .085, .30, brass)
joint_c = pin("Wing rocker joint", (0, 0, 0), .085, .30, brass)
foot = pin("Wing foot pin", (0, 0, 0), .06, .56, brass)

# The wing is a frame of four pieces around a vertical slot that the foot pin rides in.
wing = empty("Shuttle wing", (0, y_wing, wing_z0 + wing_h/2))
mid_z = wing_z0 + wing_h/2
half_w = .9
for sx in (-1, 1):
    side = block("Wing side", (half_w - slot_w/2, .12, wing_h), (0, 0, 0), mustard, .02)
    adopt(side, wing, (sx*(slot_w/2 + (half_w - slot_w/2)/2), 0, 0))
cap = block("Wing slot cap", (slot_w, .12, wing_z0 + wing_h - slot_hi), (0, 0, 0), mustard, .02)
adopt(cap, wing, (0, 0, (slot_hi + wing_z0 + wing_h)/2 - mid_z))
sill = block("Wing slot sill", (slot_w, .12, slot_lo - wing_z0), (0, 0, 0), mustard, .02)
adopt(sill, wing, (0, 0, (wing_z0 + slot_lo)/2 - mid_z))
for z, mat in ((1.12, cream), (-1.12, cream)):
    band = block("Wing band", (2*half_w + .04, .14, .22), (0, 0, 0), mat, .02)
    adopt(band, wing, (0, 0, z))
disc = pin("Wing disc", (0, 0, 0), .36, .16, cream)
adopt(disc, wing, (-.5, 0, .45))

# Track: two rails with end posts to the backdrop.
for z in (wing_z0 - .12, wing_z0 + wing_h + .12):
    block("Wing rail", (7.0, .30, .14), (0, y_wing, z), ink, .02)
for sx in (-3.5, 3.5):
    block("Wing rail post", (.22, 1.3, 3.2), (sx, -.25, 3.3), ink, .02)


def foot_point(t):
    b_pt = a_pt + Vector((crank_len*cos(t), 0, crank_len*sin(t)))
    d = d_pt - b_pt
    dist = d.length
    a = (coupler_len**2 - rocker_len**2 + dist**2)/(2*dist)
    h = sqrt(coupler_len**2 - a**2)
    mid = b_pt + d*(a/dist)
    n = Vector((-d.z, 0, d.x))/dist
    c1, c2 = mid + n*h, mid - n*h
    c_pt = c1 if c1.z > c2.z else c2
    return b_pt, c_pt, b_pt + (c_pt - b_pt)*reach


track = []
for frame in range(1, STEPS + 2):
    t = tau*CYCLES*(frame - 1)/STEPS
    b_pt, c_pt, p_pt = foot_point(t)
    assert abs((c_pt - b_pt).length - coupler_len) < 1e-5
    assert abs((c_pt - d_pt).length - rocker_len) < 1e-5
    assert abs((p_pt - b_pt).length - coupler_len*reach) < 1e-5
    assert slot_lo + .08 < p_pt.z < slot_hi - .08, "foot pin leaves its slot"
    pose_bar(crank, lift(a_pt, y_crank), lift(b_pt, y_crank), frame)
    pose_bar(rocker, lift(d_pt, y_crank), lift(c_pt, y_crank), frame)
    pose_bar(coupler, lift(b_pt, y_coupler), lift(p_pt, y_coupler), frame)
    move(joint_b, lift(b_pt, -.375), frame)
    move(joint_c, lift(c_pt, -.375), frame)
    move(foot, lift(p_pt, -.62), frame)
    move(wing, (p_pt.x, y_wing, mid_z), frame)
    track.append((p_pt.x, p_pt.z))

# Report how steady the wing speed is on the flat stretch of the foot path.
zs = [z for _, z in track]
flat = [i for i, z in enumerate(zs[:-1]) if z < min(zs) + .01*(max(zs) - min(zs))]
span = [abs(track[i + 1][0] - track[i][0]) for i in flat]
mean = sum(span)/len(span)
print(f"flat stretch: {len(flat)/ (STEPS)*100:.0f} percent of the loop, "
      f"speed spread {100*(max(span) - min(span))/mean:.1f} percent of mean, "
      f"foot height variation {max(zs[i] for i in flat) - min(zs[i] for i in flat):.4f}")

bpy.ops.object.camera_add(location=(-6.2, -11.5, 3.4))
scene.camera = bpy.context.object
aim(scene.camera, (-.3, 0, 2.3))
scene.camera.data.lens = 42
for name, kind, xyz, energy, color, size in [
    ("Warm key", "SPOT", (-4, -8, 9), 3600, (1, .78, .55), .8),
    ("Cool kicker", "AREA", (8, -5, 4), 900, (.55, .7, 1), 5),
    ("Wall wash", "AREA", (0, -4, 8.5), 400, (1, .6, .45), 6),
]:
    bpy.ops.object.light_add(type=kind, location=xyz)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.color = color
    if kind == "SPOT":
        light.data.spot_size = radians(60)
        light.data.spot_blend = .6
        light.data.shadow_soft_size = size
    else:
        light.data.shape = "DISK"
        light.data.size = size
    aim(light, (0, 0, 2.6))
scene.world = bpy.data.worlds.new("Dark house")
scene.world.color = (.02, .02, .025)
render_setup("wing-shuttle-preview.png", "wing-shuttle.blend", 50)
