"""Run with blender -b --python-exit-code 1 -t 4 -P build_stage2.py.

Second bank of animated set mechanisms: a four-bar swinging flat, a scissor
lift and a Geneva indexer. Every pose is solved from the linkage geometry and
baked to keyframes, with assertions that link lengths and the Geneva pin
constraint hold on every frame.
"""
from pathlib import Path
from math import atan2, cos, floor, pi, sin, sqrt, tau, asin

import bpy
from mathutils import Matrix, Vector

OUTPUT = Path(__file__).resolve().parent
STEPS = 240
CYCLES = 2
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


def lift(v, y):
    return Vector((v.x, y, v.z))


def pose_bar(obj, a, b, frame):
    """Place a block whose long axis is local Z so it spans point a to point b.

    The local Y axis stays on world Y (stage depth), so flat plates keep
    their broad face toward the camera whatever the bar angle.
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


def spin(empty, angle, frame):
    """Turn an empty counter-clockwise (as seen from the camera) by angle."""
    empty.rotation_euler = (0, -angle, 0)
    empty.keyframe_insert("rotation_euler", frame=frame)


def adopt(child, parent, local_xyz, rotation=None):
    child.parent = parent
    child.location = local_xyz
    if rotation is not None:
        child.rotation_euler = rotation
    return child


def stage_frame(label, x, width, height):
    for side in (-1, 1):
        block(label + " upright", (.18, .32, height),
              (x + side*width/2, .15, height/2), steel)
    for z in (.13, height - .05):
        block(label + " crossmember", (width, .35, .20), (x, .15, z), steel)
    block(label + " backdrop", (width, .13, height - .3), (x, .38, height/2 + .02), steel)


block("Stage", (26, 14, .25), (0, 1, -.13), deck)


# ---------------------------------------------------------------- four-bar
def four_bar(xc):
    """Crank-rocker whose coupler carries a swinging scenic flat."""
    ground, crank_len, coupler_len, rocker_len = 2.0, .5, 2.2, 1.6
    assert crank_len + coupler_len < ground + rocker_len, "crank would not turn fully"
    zc = .95
    width, height = 4.2, 3.9
    stage_frame("Swing", xc, width, height)
    o2 = Vector((xc - .43 - .3, 0, zc))
    o4 = o2 + Vector((ground, 0, 0))
    y_crank, y_coupler, y_panel, y_joint = -.46, -.61, -.76, -.54

    block("Swing ground link", (ground + .5, .10, .16), ((o2.x + o4.x)/2, -.30, zc), steel)
    for p, name in ((o2, "crank"), (o4, "rocker")):
        pin(f"Swing {name} pivot", (p.x, -.17, p.z), .11, .95)
    crank = block("Swing crank", (.14, .12, crank_len + .22), (0, 0, 0), brass)
    rocker = block("Swing rocker", (.14, .12, rocker_len + .22), (0, 0, 0), brass)
    coupler = block("Swing coupler", (.14, .12, coupler_len + .22), (0, 0, 0), brass)
    panel = block("Swinging scenic flat", (1.0, .10, 1.9), (0, 0, 0), red)
    joint_p = pin("Swing crank joint", (0, 0, 0), .09, .34)
    joint_q = pin("Swing rocker joint", (0, 0, 0), .09, .34)
    studs = [pin("Swing flat stud", (0, 0, 0), .06, .26) for _ in range(2)]

    lo_x, hi_x = xc - width/2 + .15, xc + width/2 - .15
    lo_z, hi_z = .35, height - .2
    extent = [10, -10, 10, -10]

    def step(frame, phase):
        p = o2 + Vector((crank_len*cos(phase), 0, crank_len*sin(phase)))
        d = o4 - p
        dist = d.length
        a = (coupler_len**2 - rocker_len**2 + dist**2)/(2*dist)
        h = sqrt(coupler_len**2 - a**2)
        mid = p + d*(a/dist)
        n = Vector((-d.z, 0, d.x))/dist
        q1, q2 = mid + n*h, mid - n*h
        q = q1 if q1.z > q2.z else q2
        assert abs((q - p).length - coupler_len) < 1e-6
        assert abs((q - o4).length - rocker_len) < 1e-6
        pose_bar(crank, lift(o2, y_crank), lift(p, y_crank), frame)
        pose_bar(rocker, lift(o4, y_crank), lift(q, y_crank), frame)
        pose_bar(coupler, lift(p, y_coupler), lift(q, y_coupler), frame)
        u = (q - p).normalized()
        up = Vector((-u.z, 0, u.x))
        pose_bar(panel, lift(p + up*.62, y_panel), lift(q + up*.62, y_panel), frame)
        move(joint_p, lift(p, y_joint), frame)
        move(joint_q, lift(q, y_joint), frame)
        for stud, t in zip(studs, (.2, .8)):
            move(stud, lift(p + (q - p)*t, -.69), frame)
        centre = (p + q)/2 + up*.62
        for su in (-1, 1):
            for sv in (-1, 1):
                corner = centre + u*(.95*su) + up*(.5*sv)
                assert lo_x < corner.x < hi_x and lo_z < corner.z < hi_z, "flat leaves frame"
                extent[0] = min(extent[0], corner.x)
                extent[1] = max(extent[1], corner.x)
                extent[2] = min(extent[2], corner.z)
                extent[3] = max(extent[3], corner.z)

    return step


# ------------------------------------------------------------- scissor lift
def scissor_lift(xc):
    """Symmetric scissor stack: bottom and top node pairs both slide."""
    link, stages = 1.3, 3
    width, height = 3.6, 4.4
    stage_frame("Lift", xc, width, height)
    zb, yc = .78, -.45
    y_a, y_b = yc - .075, yc + .075

    block("Lift base plinth", (3.0, .50, .47), (xc, -.35, .235), steel)
    block("Lift base rail", (2.7, .22, .10), (xc, yc, .52), steel)
    bottom_sliders = [block("Lift base slider", (.38, .34, .14), (0, 0, 0), brass) for _ in range(2)]
    top_sliders = [block("Lift top slider", (.38, .34, .14), (0, 0, 0), brass) for _ in range(2)]
    plate = block("Lift platform", (3.1, .90, .16), (0, 0, 0), teal)
    rail = block("Lift platform rail", (2.7, .22, .10), (0, 0, 0), steel)
    prop = block("Lift prop", (.60, .50, .45), (0, 0, 0), cream)
    a_links = [block(f"Lift link up-right {k}", (.13, .10, link + .2), (0, 0, 0), brass)
               for k in range(stages)]
    b_links = [block(f"Lift link up-left {k}", (.13, .10, link + .2), (0, 0, 0), brass)
               for k in range(stages)]
    node_pins = {(k, s): pin(f"Lift node {k}{'LR'[s > 0]}", (0, 0, 0), .07, .34)
                 for k in range(stages + 1) for s in (-1, 1)}
    centre_pins = [pin(f"Lift centre pin {k}", (0, 0, 0), .07, .34) for k in range(stages)]

    def step(frame, phase):
        sine = .42 + .17*sin(phase - pi/2)
        alpha = asin(sine)
        w, h = link*cos(alpha), link*sin(alpha)
        node = lambda k, s: Vector((xc + s*w/2, yc, zb + k*h))
        for k in range(stages):
            pose_bar(a_links[k], lift(node(k, -1), y_a), lift(node(k + 1, 1), y_a), frame)
            pose_bar(b_links[k], lift(node(k, 1), y_b), lift(node(k + 1, -1), y_b), frame)
            assert abs((node(k + 1, 1) - node(k, -1)).length - link) < 1e-6
            assert abs((node(k + 1, -1) - node(k, 1)).length - link) < 1e-6
            move(centre_pins[k], (xc, yc, zb + k*h + h/2), frame)
        for (k, s), obj in node_pins.items():
            move(obj, node(k, s), frame)
        z_top = zb + stages*h
        for s, slider in zip((-1, 1), bottom_sliders):
            move(slider, (xc + s*w/2, yc, zb - .14), frame)
        for s, slider in zip((-1, 1), top_sliders):
            move(slider, (xc + s*w/2, yc, z_top + .14), frame)
        move(rail, (xc, yc, z_top + .27), frame)
        move(plate, (xc, -.10, z_top + .40), frame)
        move(prop, (xc - .55, -.10, z_top + .48 + .225), frame)
        assert z_top + .48 + .45 < height - .22, "prop reaches the top crossmember"

    return step


# -------------------------------------------------------------- Geneva drive
def geneva_indexer(xc):
    """Four-slot external Geneva drive indexing a scenic square by 90 degrees."""
    slots, centre = 4, 1.4
    r_pin = centre*sin(pi/slots)
    width, height = 4.0, 3.6
    stage_frame("Index", xc, width, height)
    zc, y_wheel = 1.8, -.62
    o1 = Vector((xc - .7, y_wheel, zc))
    o2 = Vector((xc + .7, y_wheel, zc))

    for p, name in ((o1, "driver"), (o2, "driven")):
        pin(f"Index {name} axle", (p.x, -.35, p.z), .09, 1.35)
        pin(f"Index {name} cap", (p.x, -1.08 if name == "driven" else -.9, p.z), .13, .06)

    driver = bpy.data.objects.new("Index driver", None)
    driven = bpy.data.objects.new("Index driven", None)
    for emp, p in ((driver, o1), (driven, o2)):
        emp.location = p
        emp.rotation_mode = "XYZ"
        scene.collection.objects.link(emp)

    # Driver: locking disc with a window, carrier arm and the drive pin.
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.70, depth=.14,
                                       rotation=(tau/4, 0, 0))
    disc = bpy.context.object
    disc.name = "Index lock disc"
    disc.data.materials.append(steel)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(.26 + .45, 0, 0))
    cutter = bpy.context.object
    cutter.dimensions = (.9, .6, 1.18)
    window = disc.modifiers.new("Window", "BOOLEAN")
    window.operation = "DIFFERENCE"
    window.object = cutter
    window.solver = "EXACT"
    bpy.context.view_layer.objects.active = disc
    bpy.ops.object.modifier_apply(modifier=window.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    adopt(disc, driver, (0, 0, 0))
    carrier = block("Index carrier arm", (r_pin + .10, .12, .17), (0, 0, 0), brass)
    adopt(carrier, driver, (r_pin/2, -.15, 0))
    drive_pin = pin("Index drive pin", (0, 0, 0), .06, .32)
    adopt(drive_pin, driver, (r_pin, -.05, 0))

    # Driven wheel: hub plus four slotted arms, and the scenic square.
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.30, depth=.14,
                                       rotation=(tau/4, 0, 0))
    hub = bpy.context.object
    hub.name = "Index hub"
    hub.data.materials.append(steel)
    adopt(hub, driven, (0, 0, 0))
    slot_gap, flank = .17, .18
    for k in range(slots):
        ang = k*tau/slots
        u = Vector((cos(ang), 0, sin(ang)))
        v = Vector((-sin(ang), 0, cos(ang)))
        spin_rot = (0, -ang, 0)
        for side in (-1, 1):
            f = block(f"Index arm {k} flank", (.69, .14, flank), (0, 0, 0), steel)
            adopt(f, driven, u*.675 + v*side*(slot_gap/2 + flank/2), spin_rot)
        b = block(f"Index arm {k} bridge", (.11, .14, slot_gap + 2*flank), (0, 0, 0), steel)
        adopt(b, driven, u*.275, spin_rot)
    square = block("Index scenic square", (.80, .10, .80), (0, 0, 0), red)
    adopt(square, driven, (0, -.38, 0))
    mark = block("Index square mark", (1.0, .06, .10), (0, 0, 0), brass)
    adopt(mark, driven, (0, -.46, 0))
    tip = block("Index square tag", (.20, .06, .20), (0, 0, 0), cream)
    adopt(tip, driven, (.30, -.46, .30))
    tip2 = block("Index square tag", (.20, .06, .20), (0, 0, 0), cream)
    adopt(tip2, driven, (-.30, -.46, -.30))

    def wheel_angle(theta):
        m = floor((theta + pi/4)/tau)
        loc = theta - tau*m
        if loc <= pi/4:
            s = atan2(r_pin*sin(loc), centre - r_pin*cos(loc)) + pi/4
        else:
            s = pi/2
        return pi/4 - m*pi/2 - s, loc

    def step(frame, phase):
        theta = phase            # two driver turns per loop, a half turn of the square
        rho, loc = wheel_angle(theta)
        spin(driver, theta, frame)
        spin(driven, rho, frame)
        if abs(loc) <= pi/4:     # pin must sit on the centreline of an engaged slot
            pin_pos = o1 + Vector((r_pin*cos(theta), 0, r_pin*sin(theta)))
            rel = pin_pos - o2
            best = 9.0
            for k in range(slots):
                a = k*tau/slots + rho
                ua = Vector((cos(a), 0, sin(a)))
                if ua.dot(rel) > 0:
                    best = min(best, abs(ua.x*rel.z - ua.z*rel.x))
            assert best < 1e-6, f"pin left the slot at frame {frame}"
            assert .33 < rel.length < 1.02

    return step


mechanisms = [four_bar(-5.2), scissor_lift(0.0), geneva_indexer(5.3)]
for frame in range(1, STEPS + 2):
    phase = tau*CYCLES*(frame - 1)/STEPS
    for mech in mechanisms:
        mech(frame, phase)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.camera_add(location=(3.2, -14, 7.1))
scene.camera = bpy.context.object
aim(scene.camera, (0, 0, 1.9))
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 16.2
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
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x = 1800
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.filepath = str(OUTPUT / "stage2-preview.png")
scene.frame_set(120)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "stage-mechanisms-2.blend"))
bpy.ops.render.render(write_still=True)
