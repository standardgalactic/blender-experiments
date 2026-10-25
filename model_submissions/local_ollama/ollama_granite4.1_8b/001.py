import bpy

# Clear the default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube named 'Cube1' at location (0, 0, 0) with dimensions (2, 2, 2)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube1 = bpy.context.active_object
cube1.name = 'Cube1'

# Create a sphere named 'Sphere1' at location (3, 0, 0) with radius 1.5
bpy.ops.sphere.add(radius=1.5, location=(3, 0, 0))
sphere1 = bpy.context.active_object
sphere1.name = 'Sphere1'

# Create a cylinder named 'Cylinder1' at location (6, 0, 0) with radius 1 and height 4
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=4, location=(6, 0, 0))
cylinder1 = bpy.context.active_object
cylinder1.name = 'Cylinder1'
