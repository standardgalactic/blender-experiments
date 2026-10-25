import bpy,math
curve=bpy.data.curves.new('HelixPath','CURVE');curve.dimensions='3D';curve.bevel_depth=0.07
s=curve.splines.new('POLY');n=160;s.points.add(n)
for i,p in enumerate(s.points):
 t=8*math.pi*i/n;f=i/n
 p.co=(1.5*math.cos(t),1.5*math.sin(t),4*f+0.5*math.sin(2*math.pi*f),1)
obj=bpy.data.objects.new('Helix',curve);bpy.context.collection.objects.link(obj)
