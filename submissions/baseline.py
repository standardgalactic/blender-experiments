# Reference submission for task 001. Models should generate their own scripts.
import bpy
for name,location,dimensions in [
    ('Base',(0,0,0),(4,4,1)),
    ('Column',(0,0,1.5),(1,1,2)),
    ('Cap',(0,0,2.75),(2,2,0.5)),
]:
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
