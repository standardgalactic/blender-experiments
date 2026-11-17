"""Model-authored pilot: apply a through-hole Boolean to a solid rectangular block."""
import bpy
from math import pi

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
block = bpy.context.object
block.name = 'Perforated_Block'
block.dimensions = (4.0, 2.0, 3.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# A cylinder aligned with the Y axis and extending beyond both block faces.
bpy.ops.mesh.primitive_cylinder_add(
    vertices=64,
    radius=0.65,
    depth=4.0,
    location=(0, 0, 0),
    rotation=(pi / 2, 0, 0),
)
cutter = bpy.context.object
cutter.name = 'Temporary_Hole_Cutter'

modifier = block.modifiers.new(name='Aperture', type='BOOLEAN')
modifier.operation = 'DIFFERENCE'
modifier.object = cutter
bpy.context.view_layer.objects.active = block
block.select_set(True)
cutter.select_set(False)
bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.data.objects.remove(cutter, do_unlink=True)
