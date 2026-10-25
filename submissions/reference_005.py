# Reference implementation, not a model submission.
import bpy
for name, location, dimensions in [('Support_L', [-2, 0, 1.5], [0.5, 0.5, 3]), ('Support_R', [2, 0, 1.5], [0.5, 0.5, 3]), ('Crossbar', [0, 0, 3.25], [4.5, 0.6, 0.5])]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
