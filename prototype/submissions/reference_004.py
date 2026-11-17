# Reference implementation, not a model submission.
import bpy
for name, location, dimensions in [('Step_00', [0, 0.0, 0.2], [2, 0.7, 0.4]), ('Step_01', [0, 0.7, 0.4], [2, 0.7, 0.4]), ('Step_02', [0, 1.4, 0.6000000000000001], [2, 0.7, 0.4]), ('Step_03', [0, 2.0999999999999996, 0.8], [2, 0.7, 0.4]), ('Step_04', [0, 2.8, 1.0], [2, 0.7, 0.4])]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
