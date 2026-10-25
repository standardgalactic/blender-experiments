import bpy
import math

# Remove any existing objects that might be in the scene
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        bpy.data.objects.remove(obj, do_unlink=True)

# Create a cube named "CubeObject" at location (1.0, 2.0, 3.0)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, 2.0, 3.0))
obj = bpy.context.object
obj.name = "CubeObject"

# Create a UV Sphere named "UVSphereObject" at location (4.0, 2.0, 3.0)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(4.0, 2.0, 3.0))
obj = bpy.context.object
obj.name = "UVSphereObject"

# Create an Ico Sphere named "IcosphereObject" at location (7.0, 2.0, 3.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
obj = bpy.context.object
obj.name = "IcosphereObject"

# Create a Cylinder named "CylinderObject" at location (1.0, 4.0, 3.0)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.0, depth=2.0)
obj = bpy.context.object
obj.name = "CylinderObject"
obj.location = (1.0, 4.0, 3.0)

# Create a Cone named "ConeObject" at location (4.0, 4.0, 3.0)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.0, radius2=0.0, depth=2.0)
obj = bpy.context.object
obj.name = "ConeObject"
obj.location = (4.0, 4.0, 3.0)

# Create a Torus named "TorusObject" at location (7.0, 4.0, 3.0)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.25)
obj = bpy.context.object
obj.name = "TorusObject"
obj.location = (7.0, 4.0, 3.0)
