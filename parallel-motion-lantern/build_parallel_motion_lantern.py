"""Run with blender -b -t 4 -P build_parallel_motion_lantern.py."""
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

from math import cos, pi, sin

block('Base', (0, 0, -.12), (7.7, 2.7, .24), floor)
block('Ground', (0, 0, -.26), (200, 200, .1), floor)
block('Fixed bearing stand', (0, .13, .40), (1.55, .5, .8), steel)
barrier = block('Barrier', (0, -.57, .66), (1.16, .65, 1.32), steel)

def pin(name, x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.13, depth=.36,
                                        location=(x,y,z), rotation=(pi/2,0,0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(bronze)
    return obj

length = 2.65
pivot_height = .72
spacing = 1.2
arms = []
for x in (-spacing/2, spacing/2):
    pin('Fixed pivot', x, .02, pivot_height)
    pivot = bpy.data.objects.new('Arm pivot', None)
    scene.collection.objects.link(pivot)
    pivot.location = (x, .04, pivot_height)
    rail = block('Equal-length arm', (0,0,length/2), (.18,.22,length+.12), bronze)
    rail.parent = pivot
    arms.append(pivot)

carrier = bpy.data.objects.new('Level carrier', None)
scene.collection.objects.link(carrier)
block('Carrier crossbar', (0,0,0), (1.47,.24,.17), steel).parent = carrier
for x in (-spacing/2, spacing/2):
    pin('Moving pivot', x, .01, 0).parent = carrier

glass = material('Warm luminous panel', (.83,.43,.09))
shader = glass.node_tree.nodes.get('Principled BSDF')
shader.inputs['Emission Color'].default_value = (1,.42,.075,1)
shader.inputs['Emission Strength'].default_value = 2
block('Lantern pane', (0,-.57,-.47), (.42,.4,.46), glass).parent = carrier
block('Lantern bracket', (0,-.27,-.12), (.14,.67,.14), steel).parent = carrier
for z in (-.72,-.22):
    block('Lantern cap', (0,-.57,z), (.55,.51,.10), steel).parent = carrier
for x in (-.22,.22):
    for y in (-.77,-.37):
        block('Lantern frame', (x,y,-.47), (.055,.055,.52), steel, .012).parent = carrier

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
minimum_clearance = float('inf')
for frame in range(1,121):
    progress = (frame-1)/119
    angle = -1.08*cos(pi*progress)
    for arm in arms:
        arm.rotation_euler.y = angle
        arm.keyframe_insert(data_path='rotation_euler', index=1, frame=frame)
    carrier.location = (length*sin(angle), .04, pivot_height+length*cos(angle))
    carrier.keyframe_insert(data_path='location', frame=frame)
    if abs(carrier.location.x) <= (.55+1.16)/2:
        minimum_clearance = min(minimum_clearance, carrier.location.z-.77-1.32)
assert minimum_clearance > 0
print(f'Minimum sampled lantern clearance: {minimum_clearance:.3f} scene units')
for frame, name in [(1,'LEFT'),(60,'OVER BARRIER'),(120,'RIGHT')]:
    scene.timeline_markers.new(name, frame=frame)

def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.camera_add(location=(3.1,-12,5.1))
camera = bpy.context.object
aim(camera,(0,0,1.59))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 8.2
scene.camera = camera
for position, power, size in [((-3,-4,7),1400,6),((4,2,6),1550,5)]:
    bpy.ops.object.light_add(type='AREA', location=position)
    lamp = bpy.context.object
    lamp.data.energy, lamp.data.size = power,size
    aim(lamp,(0,0,1.5))

scene.world = bpy.data.worlds.new('Studio')
scene.world.color = (.25,.25,.25)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1100, 660
scene.render.resolution_percentage = 100
scene.render.filepath = '//parallel-motion-lantern-preview.png'
scene.frame_set(49)
bpy.ops.wm.save_as_mainfile(filepath=str(output/'parallel-motion-lantern.blend'))
bpy.ops.render.render(write_still=True)
