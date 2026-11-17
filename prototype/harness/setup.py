"""Deterministic initial scenes for editing and repair tasks."""
import bpy

def cube(name,location,dimensions):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    o=bpy.context.object;o.name=name;o.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def build(kind):
    if kind=='anchor':cube('Anchor',(0,0,0.5),(1,1,1))
    elif kind=='supports':
        cube('LeftSupport',(-2,0,1.5),(.5,.5,3))
        cube('RightSupport',(2.8,0,1.5),(.5,.5,3))
    elif kind=='stairs':
        for i in range(5):cube(f'Step_{i:02d}',(0.9 if i==2 else 0,i*.7,i*.2+.2),(2,.7,.4))
    else:raise ValueError('Unknown setup: '+str(kind))
