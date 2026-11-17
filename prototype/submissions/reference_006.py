# Reference implementation, not a model submission.
import bpy
for name, location, dimensions in [('Tier_00', [0, 0, 0.25], [4.0, 4.0, 0.5]), ('Tier_01', [0, 0, 0.75], [3.25, 3.25, 0.5]), ('Tier_02', [0, 0, 1.25], [2.5, 2.5, 0.5]), ('Tier_03', [0, 0, 1.75], [1.75, 1.75, 0.5])]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
