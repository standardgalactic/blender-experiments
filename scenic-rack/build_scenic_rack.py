"""Intermittent scenic rack inspired by Ratchet mechanism 6, Part 2,
p. 70 of Nguyen Duc Thang's 2100 Animated Mechanical Mechanisms.
Run with blender -b --python-exit-code 1 -t 4 -P build_scenic_rack.py.
"""
from pathlib import Path
from math import cos, sin, tau

import bpy
from mathutils import Matrix, Vector

OUTPUT = Path(__file__).resolve().parent
STEPS = 192
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



from math import atan2, pi, sqrt

PITCH = 1.12
R = PITCH/2
ROD = 1.52
CRANK_Z = 1.02
DRIVE_Y = -.72
RACK_Z = 1.51

block("Stage floor", (24, 15, .25), (0, 0, -.13), deck)


def bar(name, length, color):
    return block(name, (length+.16, .12, .13), (0, 0, 0), color, .026)


def pose_bar(obj, a, b, frame):
    d = b-a
    obj.location = (a+b)/2
    obj.rotation_euler.y = -atan2(d.z, d.x)
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_euler", frame=frame)


def keyed_location(obj, point, frame):
    obj.location = point
    obj.keyframe_insert("location", frame=frame)


def put(obj, parent, point):
    obj.parent = parent
    obj.location = point
    return obj


def saw_tooth(parent, x):
    width, height = .31, .20
    # Vertical drive face at the left, ramp on the reset side.
    verts = [(u+x, y, z) for y in (-.09, .09)
             for u, z in [(0, 0), (0, -height), (width, 0)]]
    mesh = bpy.data.meshes.new("Ratchet tooth")
    mesh.from_pydata(verts, [], [(2,1,0), (3,4,5), (0,1,4,3), (1,2,5,4), (2,0,3,5)])
    mesh.update()
    tooth = bpy.data.objects.new("Rack tooth", mesh)
    scene.collection.objects.link(tooth)
    tooth.data.materials.append(brass)
    put(tooth, parent, (0, 0, -.045))


def station(x, offset):
    block("Plinth", (5.7, 1.85, .24), (x, .35, .12), steel)
    for side in (-1, 1):
        block("Portal side flat", (2.14, .35, 1.52),
              (x+side*1.62, -.30, 2.41), steel)
        block("Aperture jamb", (.075, .10, 1.06),
              (x+side*.552, -.50, 2.41), cream, .012)
    for z in (1.87, 2.95):
        block("Aperture lintel", (1.17, .39, .17), (x, -.31, z), steel)
    block("Backdrop", (5.18, .14, 2.93), (x, .57, 1.73), steel)
    block("Crank base", (.40, .56, .88), (x-1.92, -.18, .68), steel)
    block("Pawl guide", (2.15, .18, .18), (x+.01, -.52, CRANK_Z), steel)
    block("Rack linear guide", (5.0, .14, .10), (x, -.27, RACK_Z), steel)

    rack = bpy.data.objects.new("Scenery and rack", None)
    scene.collection.objects.link(rack)
    put(block("Brass rack spine", (3.41, .17, .12), (0, 0, 0), brass),
        rack, (0, 0, 0))
    for index, color in enumerate((teal, red, cream)):
        px = (1-index)*PITCH
        put(block("Painted scenic panel", (1.08, .12, 1.05), (0, 0, 0), color),
            rack, (px, .76, .90))
        motif = pin("Scenic disc", (0, 0, 0), (.19, .27, .16)[index],
                    .045, cream if index != 2 else teal)
        put(motif, rack, (px+(.14, -.15, .04)[index], .68, 1.00))
        put(block("Horizon stripe", (1.03, .045, .07), (0, 0, 0), steel, .012),
            rack, (px, .68, .65))
    for n in range(-2, 2):
        saw_tooth(rack, n*PITCH+.42)

    center = Vector((x-1.92, DRIVE_Y, CRANK_Z))
    pin("Crank axle", (center.x, DRIVE_Y+.11, CRANK_Z), .155, .32)
    crank, rod = bar("Drive crank", R, brass), bar("Connecting rod", ROD, brass)
    wrist = pin("Crank pin", (0, 0, 0), .09, .22)
    shoe = block("Pawl carriage", (.24, .20, .24), (0, 0, 0), teal)
    pawl = block("Drive pawl", (.16, .13, .31), (0, 0, 0), red)
    pawl_tip = block("Pawl nose", (.14, .15, .10), (0, 0, 0), steel, .012)
    for sample in range(STEPS+1):
        frame = 1+sample-offset
        turns = 2*sample/STEPS
        cycle = min(int(turns), 1)
        local = turns-cycle
        angle = pi + tau*local
        crank_pin = center + Vector((R*cos(angle), 0, R*sin(angle)))
        slider = Vector((crank_pin.x+sqrt(ROD**2-(crank_pin.z-CRANK_Z)**2),
                         DRIVE_Y, CRANK_Z))
        stroke = slider.x-(center.x+ROD-R)
        engaged = local <= .5
        travel = stroke if engaged else PITCH
        assert abs((slider-crank_pin).length-ROD) < 1e-6
        assert -.000001 <= stroke <= PITCH+.000001
        # A prescribed lift clears the rack on the return stroke.
        drop = 0 if engaged else .28*sin(tau*(local-.5))**.45
        keyed_location(rack, (x+travel+(cycle-1)*PITCH, DRIVE_Y, RACK_Z), frame)
        pose_bar(crank, center, crank_pin, frame)
        # The crank angle stays unwrapped across both rotations.
        crank.rotation_euler.y = -angle-cycle*tau
        crank.keyframe_insert("rotation_euler", frame=frame)
        pose_bar(rod, crank_pin, slider, frame)
        keyed_location(wrist, crank_pin, frame)
        keyed_location(shoe, slider, frame)
        keyed_location(pawl, slider+Vector((.10, 0, .17-drop)), frame)
        keyed_location(pawl_tip, slider+Vector((.19, 0, .302-drop)), frame)
        if engaged:
            tooth_face = rack.location.x-cycle*PITCH+.42
            assert abs(tooth_face-(pawl_tip.location.x+.07)) < 1e-5

station(-3.25, 0)
station(3.25, 48)
for frame, label in [(25, "Advance 1"), (73, "Hold 1"),
                     (121, "Advance 2"), (169, "Hold 2")]:
    scene.timeline_markers.new("Left station | " + label, frame=frame)

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(1.7, -18, 6.0))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 1.54))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 13.8
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
scene.render.filepath = str(OUTPUT / "scenic-rack-preview.png")
scene.frame_set(25)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "scenic-rack.blend"))
bpy.ops.render.render(write_still=True)
