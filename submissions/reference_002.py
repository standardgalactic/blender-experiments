# Reference implementation, not a model submission.
import bpy
for name, location, dimensions in [('A', [2, 0, 0], [1, 1, 1]), ('B', [0, 3, 0], [1, 1, 1]), ('C', [-2, -1, 1], [1, 1, 1])]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
