"""Run with blender -b -t 4 -P build_walking_beam.py."""
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

pitch = 2.15
stations = [(i - 1.5) * pitch for i in range(4)]
block('Bed', (0, 0, -.12), (9.1, 3.15, .24), floor)
block('Ground', (0, 0, -.29), (200, 200, .1), floor)

# Two outer pads support each load. The moving beam passes between them.
for i, x in enumerate(stations, 1):
    for y in (-.43, .43):
        block(f'Cradle {i} post', (x, y, .37), (.5, .22, .74), steel)
        block(f'Cradle {i} pad', (x, y, .84), (.84, .23, .2), steel)

beam = block('Walking beam', (-pitch / 2, 0, .48), (5.28, .36, .32), bronze)
loads = [
    block(f'Load {i + 1}', (x, 0, 1.23), (.72, 1.2, .58), mat, .075)
    for i, (x, mat) in enumerate(zip(stations, payloads))
]

def key(obj, frame, x, z):
    obj.location.x, obj.location.z = x, z
    obj.keyframe_insert(data_path='location', frame=frame)

# Beam top starts at .64. Cradle tops and load bottoms are both .94.
# The contact keys at 24 and 85 make the change of support explicit.
for frame, dx, top, carried in [
    (1, 0, .64, 0), (12, 0, .64, 0), (24, 0, .94, 0),
    (40, 0, 1.44, .50), (68, pitch, 1.44, .50),
    (85, pitch, .94, 0), (97, pitch, .64, 0), (120, 0, .64, 0),
]:
    key(beam, frame, -pitch / 2 + dx, top - .16)
    for obj, x in zip(loads, stations):
        # Once deposited, the loads stay behind as the empty beam returns.
        load_dx = pitch if frame >= 85 else dx
        key(obj, frame, x + load_dx, 1.23 + carried)

# The same linear interpolation on the contact segments keeps the beam
# and loads in exact contact while they move together.
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
for obj in [beam, *loads]:
    action = obj.animation_data.action
    curves = getattr(action, 'fcurves', None)
    if curves is None:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        curves = action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves
    for curve in curves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'

for frame, label in [(12, 'LIFT'), (24, 'PICKUP'), (40, 'ADVANCE'),
                     (68, 'LOWER'), (85, 'DEPOSIT'), (97, 'RETURN')]:
    scene.timeline_markers.new(label, frame=frame)

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.camera_add(location=(3.8, -12, 5.1))
camera = bpy.context.object
aim(camera, (0, 0, .7))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 10.4
scene.camera = camera

for position, power, size in [((-3, -4, 7), 1600, 7), ((4, 2, 6), 1800, 5)]:
    bpy.ops.object.light_add(type='AREA', location=position)
    lamp = bpy.context.object
    lamp.data.energy, lamp.data.size = power, size
    aim(lamp, (0, 0, .5))

scene.world = bpy.data.worlds.new('Studio')
scene.world.color = (.25, .25, .25)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1100, 620
scene.render.resolution_percentage = 100
bpy.context.preferences.filepaths.save_version = 0
scene.frame_set(52)
scene.render.filepath = '//walking-beam-preview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'walking-beam.blend'))
bpy.ops.render.render(write_still=True)
