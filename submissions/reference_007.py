import bpy, math
for i in range(8):
    a=2*math.pi*i/8
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=0.18,depth=1.5,location=(3*math.cos(a),3*math.sin(a),0.75))
    bpy.context.object.name=f'Post_{i:02d}'
