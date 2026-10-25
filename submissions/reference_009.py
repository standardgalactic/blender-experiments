import bpy
bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,0))
block=bpy.context.object;block.name='Perforated_Block';block.dimensions=(4,2,3)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=0.65,depth=4,rotation=(1.57079632679,0,0))
cutter=bpy.context.object
mod=block.modifiers.new('Through_hole','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
bpy.context.view_layer.objects.active=block
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter,do_unlink=True)
