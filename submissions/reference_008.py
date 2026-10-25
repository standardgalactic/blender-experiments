import bpy, math
verts=[]; faces=[]
n=24
for i in range(n+1):
    a=math.pi*i/n
    x=3*math.cos(a); z=0.5+3*math.sin(a)
    verts.extend([(x,-0.3,z),(x,0.3,z)])
for i in range(n):
    k=2*i; faces.append((k,k+1,k+3,k+2))
mesh=bpy.data.meshes.new('ArchMesh');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('Arch',mesh);bpy.context.collection.objects.link(obj)
