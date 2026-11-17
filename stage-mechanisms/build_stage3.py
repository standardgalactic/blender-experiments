"""Run with blender -b --python-exit-code 1 -t 4 -P build_stage3.py.

Third bank of animated set mechanisms, after entries in Nguyen Duc Thang's
catalog "2100 Animated Mechanical Mechanisms": a Peaucellier-Lipkin straight
line linkage (Part 3, 16.1), a disc cam with roller follower and dwells
(Part 2, 3.3) and a double toggle riser (Part 3, 12). Every pose is solved from
the geometry and baked to keyframes, with assertions on every frame.
"""
from pathlib import Path
from math import atan2, cos, hypot, pi, radians, sin, sqrt, tau

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


# ------------------------------------------------ Peaucellier-Lipkin linkage
def peaucellier(xc):
    """Exact straight-line linkage: a scenic flat rises with no slide guiding the linkage."""
    r, long_len, side = .7, 1.9, 1.0
    theta_max = radians(30)
    k = (long_len**2 - side**2)/(2*r)       # distance of the straight line from O
    width, height = 4.2, 4.4
    stage_frame("Line", xc, width, height)
    o = Vector((xc - 1.7, 0, 2.2))
    p = o + Vector((r, 0, 0))
    line_x = o.x + k
    panel_x = line_x + .85
    y_crank, y_long, y_a, y_b, y_tie = -.36, -.50, -.64, -.78, -.95

    for pt, name in ((o, "O"), (p, "P")):
        pin(f"Line pivot {name}", (pt.x, -.2, pt.z), .11, 1.0)
    crank = block("Line crank", (.14, .12, r + .22), (0, 0, 0), brass)
    long_links = [block("Line long link", (.13, .10, long_len + .22), (0, 0, 0), brass) for _ in range(2)]
    rhombus = {n: block(f"Line rhombus {n}", (.13, .10, side + .22), (0, 0, 0), brass)
               for n in ("AC", "BD", "AD", "BC")}
    joints = {n: pin(f"Line joint {n}", (0, 0, 0), .08, .40) for n in "ABD"}
    joints["C"] = pin("Line joint C", (0, 0, 0), .08, .56)
    tie = block("Line tie bar", (.85, .10, .14), (0, 0, 0), brass)
    panel = block("Rising scenic flat", (1.0, .12, .9), (0, 0, 0), red)
    for sx in (-.62, .62):
        block("Line rail", (.095, .30, 3.4), (panel_x + sx, y_tie, o.z), brass)
        for sz in (-1.75, 1.75):
            block("Line rail bracket", (.20, 1.30, .16), (panel_x + sx, -.30, o.z + sz), steel)

    def step(frame, phase):
        theta = theta_max*sin(phase)
        t = 2*theta
        d_pt = p + Vector((r*cos(t), 0, r*sin(t)))
        e = (d_pt - o).normalized()
        dist = (d_pt - o).length
        c_pt = o + e*((long_len**2 - side**2)/dist)
        mid = (d_pt + c_pt)/2
        half = (c_pt - d_pt).length/2
        n = Vector((-e.z, 0, e.x))
        h = sqrt(side**2 - half**2)
        a_pt, b_pt = mid + n*h, mid - n*h
        assert abs((d_pt - p).length - r) < 1e-5
        assert abs((a_pt - o).length - long_len) < 1e-5 and abs((b_pt - o).length - long_len) < 1e-5
        for q in (a_pt, b_pt):
            assert abs((q - d_pt).length - side) < 1e-5 and abs((q - c_pt).length - side) < 1e-5
        assert abs(c_pt.x - line_x) < 1e-5, "output left its straight line"
        assert panel_x - .62 - .0475 - (max(a_pt.x, b_pt.x, c_pt.x) + .09) > .02, "linkage hits rail"
        pose_bar(crank, lift(p, y_crank), lift(d_pt, y_crank), frame)
        pose_bar(long_links[0], lift(o, y_long), lift(a_pt, y_long), frame)
        pose_bar(long_links[1], lift(o, y_long), lift(b_pt, y_long), frame)
        pose_bar(rhombus["AC"], lift(a_pt, y_a), lift(c_pt, y_a), frame)
        pose_bar(rhombus["BD"], lift(b_pt, y_a), lift(d_pt, y_a), frame)
        pose_bar(rhombus["AD"], lift(a_pt, y_b), lift(d_pt, y_b), frame)
        pose_bar(rhombus["BC"], lift(b_pt, y_b), lift(c_pt, y_b), frame)
        move(joints["A"], lift(a_pt, -.64), frame)
        move(joints["B"], lift(b_pt, -.64), frame)
        move(joints["D"], lift(d_pt, -.57), frame)
        move(joints["C"], lift(c_pt, -.78), frame)
        move(tie, (line_x + .42, y_tie, c_pt.z), frame)
        move(panel, (panel_x, y_tie, c_pt.z), frame)

    return step


# ------------------------------------------------------------------ disc cam
def disc_cam(xc):
    """Cycloidal disc cam with dwells at both ends, raising a scenic flat."""
    base, lift_h, roller = .7, .5, .18
    steps = 360
    width, height = 3.4, 4.6
    zc, y_cam, y_stem = 1.4, -.64, -.48
    stage_frame("Cam", xc, width, height)

    def rise(w):
        w %= tau
        q = pi/2
        if w < q:
            u = w/q
            return lift_h*(u - sin(tau*u)/tau)
        if w < 2*q:
            return lift_h
        if w < 3*q:
            u = (w - 2*q)/q
            return lift_h*(1 - (u - sin(tau*u)/tau))
        return 0.0

    # Pitch curve of the roller centre, then the cam surface offset inward by the roller radius.
    pitch = []
    for i in range(steps):
        phi = tau*i/steps
        rad = base + rise(pi/2 - phi)
        pitch.append(Vector((rad*cos(phi), rad*sin(phi))))
    surface = []
    for i in range(steps):
        tan = pitch[(i + 1) % steps] - pitch[i - 1]
        nrm = Vector((tan.y, -tan.x)).normalized()
        surface.append(pitch[i] - nrm*roller)
    assert min(v.length for v in surface) > .3, "cam profile undercut"

    half = .06
    mesh = bpy.data.meshes.new("Cam profile")
    verts = [(v.x, -half, v.y) for v in surface] + [(v.x, half, v.y) for v in surface]
    faces = [list(range(steps)), list(range(2*steps - 1, steps - 1, -1))]
    faces += [[i, (i + 1) % steps, steps + (i + 1) % steps, steps + i] for i in range(steps)]
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    cam = bpy.data.objects.new("Disc cam", mesh)
    scene.collection.objects.link(cam)
    cam.data.materials.append(teal)
    for poly in cam.data.polygons:
        poly.use_smooth = False

    spinner = bpy.data.objects.new("Cam spinner", None)
    spinner.location = (xc, y_cam, zc)
    scene.collection.objects.link(spinner)
    adopt(cam, spinner, (0, 0, 0))
    mark = pin("Cam marker", (0, 0, 0), .06, .18)
    adopt(mark, spinner, (.32, -.08, 0))
    hub = pin("Cam hub", (0, 0, 0), .13, .20)
    adopt(hub, spinner, (0, -.08, 0))
    pin("Cam axle", (xc, -.2, zc), .09, 1.0)

    stem = block("Follower stem", (.10, .10, 1.3), (0, 0, 0), brass)
    wheel = pin("Follower roller", (0, 0, 0), roller, .14)
    roller_pin = pin("Follower roller pin", (0, 0, 0), .05, .31)
    flat = block("Cam scenic flat", (1.6, .12, .7), (0, 0, 0), cream)
    for sx in (-.17, .17):
        block("Follower guide", (.10, .24, .30), (xc + sx, -.40, 2.8), steel)
    block("Follower bracket", (.6, .66, .14), (xc, 0, 3.02), steel)

    def step(frame, phase):
        omega = phase
        z_r = zc + base + rise(omega)
        spin(spinner, omega, frame)
        move(stem, (xc, y_stem, z_r + .65), frame)
        move(wheel, (xc, y_cam, z_r), frame)
        move(roller_pin, (xc, -.585, z_r), frame)
        move(flat, (xc, y_stem, z_r + 1.3), frame)
        # Contact check: roller must touch the rotated cam outline without cutting into it.
        centre = Vector((xc, zc + base + rise(omega)))
        gaps = []
        for v in surface:
            wx = v.x*cos(omega) - v.y*sin(omega)
            wz = v.x*sin(omega) + v.y*cos(omega)
            gaps.append((Vector((xc + wx, zc + wz)) - centre).length)
        assert min(gaps) > roller - .004, f"roller cuts the cam at frame {frame}"
        assert min(gaps) < roller + .004, f"roller loses the cam at frame {frame}"

    return step


# -------------------------------------------------------------- toggle riser
def toggle_riser(xt):
    """Double toggle: the ram nearly stops as the links straighten, twice per crank turn."""
    link_a = link_b = 1.1
    crank_r, rod_len = .7, 1.7
    width, height = 4.0, 4.6
    stage_frame("Riser", xt, width, height)
    f = Vector((xt + .75, 0, .55))
    oc = Vector((f.x - 1.7, 0, f.z + link_a))
    y_l1, y_l2, y_rod, y_disc, y_ram = -.40, -.55, -.70, -.50, -.40

    block("Riser post", (.34, .44, .45), (f.x, -.18, .40), steel)
    pin("Riser fixed pivot", (f.x, -.2, f.z), .11, 1.0)
    pin("Riser crank axle", (oc.x, -.2, oc.z), .10, 1.0)
    spinner = bpy.data.objects.new("Riser crank", None)
    spinner.location = (oc.x, y_disc, oc.z)
    scene.collection.objects.link(spinner)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.82, depth=.10, rotation=(tau/4, 0, 0))
    disc = bpy.context.object
    disc.name = "Riser crank disc"
    disc.data.materials.append(steel)
    adopt(disc, spinner, (0, 0, 0))
    crank_pin = pin("Riser crank pin", (0, 0, 0), .08, .36)
    adopt(crank_pin, spinner, (crank_r, -.075, 0))

    link1 = block("Riser toggle link 1", (.14, .10, link_a + .22), (0, 0, 0), brass)
    link2 = block("Riser toggle link 2", (.14, .10, link_b + .22), (0, 0, 0), brass)
    rod = block("Riser drive rod", (.13, .10, rod_len + .22), (0, 0, 0), brass)
    ram = block("Riser ram", (.14, .10, 1.05), (0, 0, 0), brass)
    knee = pin("Riser knee pin", (0, 0, 0), .08, .42)
    foot = pin("Riser ram pin", (0, 0, 0), .08, .26)
    plate = block("Riser platform", (1.5, .45, .14), (0, 0, 0), teal)
    prop = block("Riser prop", (.6, .40, .35), (0, 0, 0), cream)
    for sx in (-.17, .17):
        block("Riser guide", (.10, .30, .40), (f.x + sx, -.40, 2.9), steel)
    block("Riser bracket", (.6, .66, .14), (f.x, 0, 3.17), steel)

    def step(frame, phase):
        t = phase
        spin(spinner, t, frame)
        c_pt = oc + Vector((crank_r*cos(t), 0, crank_r*sin(t)))
        d = f - c_pt
        dist = d.length
        a = (rod_len**2 - link_a**2 + dist**2)/(2*dist)
        h = sqrt(rod_len**2 - a**2)
        mid = c_pt + d*(a/dist)
        n = Vector((-d.z, 0, d.x))/dist
        k1, k2 = mid + n*h, mid - n*h
        k = k1 if k1.z > k2.z else k2
        dx = k.x - f.x
        assert abs(dx) < link_b
        r_pt = Vector((f.x, 0, k.z + sqrt(link_b**2 - dx**2)))
        assert abs((k - c_pt).length - rod_len) < 1e-5
        assert abs((k - f).length - link_a) < 1e-5
        assert abs((r_pt - k).length - link_b) < 1e-5
        pose_bar(link1, lift(f, y_l1), lift(k, y_l1), frame)
        pose_bar(link2, lift(k, y_l2), lift(r_pt, y_l2), frame)
        pose_bar(rod, lift(c_pt, y_rod), lift(k, y_rod), frame)
        move(ram, (f.x, y_ram, r_pt.z + .425), frame)
        move(knee, lift(k, -.55), frame)
        move(foot, (f.x, -.47, r_pt.z), frame)
        move(plate, (f.x, y_ram, r_pt.z + .95 + .07), frame)
        move(prop, (f.x, y_ram, r_pt.z + .95 + .14 + .175), frame)

    return step


mechanisms = [peaucellier(-5.4), disc_cam(0.0), toggle_riser(5.4)]
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
scene.render.filepath = str(OUTPUT / "stage3-preview.png")
scene.frame_set(45)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "stage-mechanisms-3.blend"))
bpy.ops.render.render(write_still=True)
