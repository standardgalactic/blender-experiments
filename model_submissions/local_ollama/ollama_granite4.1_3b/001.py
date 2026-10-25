import bpy

bpy.context.scene.world.background_image.enable = False
bpy.data.scenes['Scene'].clear()  # Clear the default scene

# Construct three named primitives with specified dimensions and locations
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0), name='Cube')
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=3, location=(-2, 1, -1), name='Cylinder')
bpy.ops.mesh.primitive_sphere_add(radius=1.5, location=(1, -2, 2), name='Sphere')
