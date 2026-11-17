"""Run with blender -b -t 4 -P build_geneva_turntable.py."""
from pathlib import Path
import bpy
from mathutils import Vector

output = Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 120
scene.render.fps = 24

def material(name, color, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = .32
    return mat

steel = material('Slate enamel', (.055, .13, .17), .45)
bronze = material('Amber enamel', (.78, .28, .055), .3)
floor = material('Graphite', (.035, .041, .049))
payloads = [material(name, color) for name, color in [
    ('Ivory', (.8, .7, .49)), ('Ceramic green', (.14, .56, .41)),
    ('Ceramic blue', (.16, .38, .73))]]

def block(name, position, size, mat, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    edge = obj.modifiers.new('Rounded edges', 'BEVEL')
    edge.width, edge.segments = bevel, 3
    obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj

from math import atan2, cos, pi, sin, sqrt

def cylinder(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    edge = obj.modifiers.new('Rounded rim', 'BEVEL')
    edge.width, edge.segments = .025, 3
    obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj

def pivot(name, location):
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.location = location
    return obj

def attach(obj, parent):
    obj.parent = parent
    return obj

distance = 2.4
throw = distance / sqrt(2)
scene.frame_end = 144
block('Base', (.85, 0, -.1), (6.8, 4.5, .22), floor)
block('Ground', (0, 0, -.27), (200, 200, .1), floor)
cylinder('Driven bearing', (0, 0, .3), .46, .58, steel)
cylinder('Driver bearing', (distance, 0, .23), .52, .44, steel)
wheel = pivot('Geneva wheel', (0, 0, 0))
driver = pivot('Continuous crank', (distance, 0, 0))
attach(cylinder('Driver disc', (0, 0, .47), .49, .16, bronze), driver)
attach(block('Crank arm', (-throw / 2, 0, .45), (throw + .19, .19, .13), bronze), driver)
attach(cylinder('Drive pin', (-throw, 0, .66), .077, .43, bronze), driver)

# Four open radial slots with parallel walls, measured perpendicular
# to the slot centreline. The outer wheel edge is circular.
outer_radius = 1.47
half_slot = .115
hub_radius = .58
from math import asin
for quadrant in range(4):
    start = -pi / 4 + quadrant * pi / 2
    inner_angle = asin(half_slot / hub_radius)
    outer_angle = asin(half_slot / outer_radius)
    arc = [start + outer_angle + i * (pi / 2 - 2 * outer_angle) / 32 for i in range(33)]
    outline = [(hub_radius * cos(start + inner_angle), hub_radius * sin(start + inner_angle))]
    outline += [(outer_radius * cos(a), outer_radius * sin(a)) for a in arc]
    stop = start + pi / 2 - inner_angle
    outline.append((hub_radius * cos(stop), hub_radius * sin(stop)))
    outline.append((0, 0))
    n = len(outline)
    vertices = [(x, y, z) for z in (.61, .81) for x, y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
    mesh = bpy.data.meshes.new('Slotted sector')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    part = bpy.data.objects.new(f'Wheel sector {quadrant+1}', mesh)
    scene.collection.objects.link(part)
    attach(part, wheel)
    mesh.materials.append(steel)

attach(cylinder('Hub cap', (0, 0, .85), .55, .12, bronze), wheel)
for i, (x, y, width, height, mat) in enumerate([
    (.83, 0, .26, .46, payloads[0]), (0, .83, .40, .19, payloads[1]),
    (-.83, 0, .32, .30, payloads[2]), (0, -.83, .21, .59, bronze)
]):
    attach(block(f'Scenery {i+1}', (x, y, .81+height/2), (width, width, height), mat), wheel)

# The drive pin starts left of its axle at crank angle zero. Its
# bearing as seen from the driven axle sets the slot angle during engagement.
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
for frame in range(1, 145):
    angle = (frame - 1) * 2*pi / 143 - pi
    driver.rotation_euler.z = -angle
    contact = min(pi/4, max(-pi/4, angle))
    wheel.rotation_euler.z = atan2(throw*sin(contact), distance-throw*cos(contact)) + pi/4
    driver.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
    wheel.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)

for frame, name in [(1, 'DWELL'), (55, 'PIN ENTERS'), (73, 'MID INDEX'), (91, 'DWELL')]:
    scene.timeline_markers.new(name, frame=frame)

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.camera_add(location=(4.1, -5.4, 10))
camera = bpy.context.object
aim(camera, (.75, 0, .42))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 7.6
scene.camera = camera
for position, power, size in [((-3, -4, 7), 1250, 5), ((4, 2, 6), 1500, 5)]:
    bpy.ops.object.light_add(type='AREA', location=position)
    lamp = bpy.context.object
    lamp.data.energy, lamp.data.size = power, size
    aim(lamp, (.7, 0, .4))
scene.world = bpy.data.worlds.new('Studio')
scene.world.color = (.25, .25, .25)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1050, 700
scene.render.resolution_percentage = 100
scene.render.filepath = '//geneva-turntable-preview.png'
bpy.context.preferences.filepaths.save_version = 0
scene.frame_set(73)
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'geneva-turntable.blend'))
bpy.ops.render.render(write_still=True)
