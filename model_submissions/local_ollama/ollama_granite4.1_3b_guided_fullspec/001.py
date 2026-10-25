import bpy
import math

# Create Base (Cube)
bpy.ops.mesh.primitive_cube_add(size=4.0, location=(0, 0, 0))
obj = bpy.context.object
obj.name = "Base"

# Create Column (Cylinder)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.5, depth=2.0)
column_obj = bpy.context.object
column_obj.location = (0, 0, 1.5)

# Scale Column to match dimensions [1, 1, 2]
scale_factor = 4.0 / 2.0  # original size is diameter * depth / actual desired size
column_obj.scale *= scale_factor

# Create Cap (Cylinder)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.5, depth=0.25)
cap_obj = bpy.context.object
cap_obj.location = (0, 0, 2.75)

# Scale Cap to match dimensions [2, 2, 0.5]
scale_factor = 4.0 / 0.25  # original size is diameter * depth / actual desired size
cap_obj.scale *= scale_factor

# Optional: Align Caps orientation if needed (not required by task)
# cap_obj.rotation_euler = (math.pi/2, 0, 0)
