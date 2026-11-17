import bpy
bpy.ops.mesh.primitive_cube_add(size=2)
o=bpy.context.object;o.name='Perforated_Block';o.dimensions=(4,2,3)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
# Deliberately no aperture.
