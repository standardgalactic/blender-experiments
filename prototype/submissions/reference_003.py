# Reference implementation, not a model submission.
import bpy
for name, location, dimensions in [('Beam', [0, 0, 3], [6, 1, 0.5]), ('Left', [-2.5, 0, 1.5], [0.5, 0.5, 3]), ('Right', [2.5, 0, 1.5], [0.5, 0.5, 3])]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
