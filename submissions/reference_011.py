import bpy
assert 'Anchor' in bpy.data.objects
for name,location,dimensions in [('Bridge',(1.5,0,1),(2,.5,.4)),('Terminal',(3,0,.5),(1,1,1))]:
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
