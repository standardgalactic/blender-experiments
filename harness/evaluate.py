import json, math, sys
from pathlib import Path

def ray_hits(mesh, origin, direction=(0.,1.,0.)):
    """Count intersections with a triangulated mesh using Moller-Trumbore.
    Works on world-space vertices and indices from scene.json.
    """
    vs=mesh.get('mesh_vertices',[])
    hits=[]
    def sub(a,b):return [x-y for x,y in zip(a,b)]
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    for tri in mesh.get('triangles',[]):
        if len(tri)!=3 or any(i<0 or i>=len(vs) for i in tri):continue
        a,b,c=(vs[i] for i in tri)
        e1=sub(b,a);e2=sub(c,a);h=cross(direction,e2);det=dot(e1,h)
        if abs(det)<1e-9:continue
        inv=1./det;v=sub(origin,a);u=inv*dot(v,h)
        if u < -1e-7 or u > 1+1e-7:continue
        q=cross(v,e1);w=inv*dot(direction,q)
        if w < -1e-7 or u+w > 1+1e-7:continue
        t=inv*dot(e2,q)
        if t>1e-6:hits.append(t)
    # Collapse duplicate intersections along shared triangle edges.
    unique=[]
    for t in sorted(hits):
        if not unique or abs(t-unique[-1])>1e-5:unique.append(t)
    return unique

def boolean_aperture_ok(obj):
    if not obj or obj.get('type')!='MESH' or not obj.get('triangles'):return False
    # Opening follows Y axis. Central rays must miss the block entirely;
    # offset rays must cross its front and back solid faces.
    for x,z in ((0.,0.),(0.25,0.),(0.,0.25)):
        if ray_hits(obj,(x,-3.,z)):return False
    for x,z in ((1.5,0.),(-1.5,0.),(0.,1.0),(0.,-1.0)):
        if len(ray_hits(obj,(x,-3.,z)))<2:return False
    return True

def evaluate(task,scene):
    objects={o['name']:o for o in scene['objects']}
    checks=[]
    for spec in task.get('expected',[]):
        obj=objects.get(spec['name'])
        if obj is None:
            checks.append({'object':spec['name'],'pass':False,'reason':'missing'})
            continue
        failures=[]
        if obj['type']!=spec.get('type',obj['type']): failures.append('type')
        for field in ('location','dimensions'):
            if field in spec and any(abs(a-b)>spec.get('tolerance',0.01) for a,b in zip(obj[field],spec[field])):
                failures.append(field)
        checks.append({'object':spec['name'],'pass':not failures,'reason':','.join(failures)})
    if task.get('preserve_unmodified'):
        initial=scene.get('initial',{})
        expected_names={e['name'] for e in task.get('expected',[])}
        for name,before in initial.items():
            if name not in expected_names:
                checks.append({'object':name,'pass':False,'reason':'unaccounted original object'})
                continue
            target=next(e for e in task['expected'] if e['name']==name)
            changed=any(abs(a-b)>1e-5 for field in ('location','dimensions') for a,b in zip(before[field],target[field]))
            if not changed:
                after=objects.get(name)
                ok=bool(after and all(abs(a-b)<1e-5 for field in ('location','dimensions') for a,b in zip(before[field],after[field]))
                     and len(before['mesh_vertices'])==len(after.get('mesh_vertices',[]))
                     and all(all(abs(a-b)<1e-5 for a,b in zip(v,w)) for v,w in zip(before['mesh_vertices'],after.get('mesh_vertices',[]))))
                checks.append({'object':name+' preservation','pass':ok,'reason':'' if ok else 'original changed'})
    kind=task.get('geometry_test')
    if kind:
        import math
        if kind=='radial':
            posts=[o for o in scene['objects'] if o['name'].startswith('Post_') and o['type']=='MESH']
            ok=len(posts)==8 and all(abs(math.hypot(*o['location'][:2])-3)<0.03 for o in posts)
            angles=sorted(math.atan2(o['location'][1],o['location'][0])%(2*math.pi) for o in posts)
            if len(angles)==8:
                gaps=[(angles[(i+1)%8]-angles[i])%(2*math.pi) for i in range(8)]
                ok=ok and all(abs(g-2*math.pi/8)<0.025 for g in gaps)
            else:ok=False
        elif kind=='arch':
            obj=next((o for o in scene['objects'] if o['name']=='Arch' and o['type']=='MESH'),None)
            vs=obj.get('mesh_vertices',[]) if obj else []
            ok=len(vs)>=26 and max(v[2] for v in vs)-min(v[2] for v in vs)>2.5 and (max(v[0] for v in vs)-min(v[0] for v in vs)>5)
            # Reference arch follows upper semicircle x^2+(z-0.5)^2=9.
            ok=ok and all(abs(v[0]**2+(v[2]-0.5)**2-9)<0.12 for v in vs)
        elif kind=='boolean':
            obj=next((o for o in scene['objects'] if o['name']=='Perforated_Block' and o['type']=='MESH'),None)
            ok=boolean_aperture_ok(obj)
        elif kind=='helix':
            obj=next((o for o in scene['objects'] if o['name']=='Helix' and o['type']=='CURVE'),None)
            pts=obj.get('curve_points',[]) if obj else []
            if len(pts)>=100:
                angles=[math.atan2(p[1],p[0]) for p in pts]
                total=sum((angles[i]-angles[i-1]+math.pi)%(2*math.pi)-math.pi for i in range(1,len(angles)))
                ok=abs(abs(total)-8*math.pi)<0.3 and max(p[2] for p in pts)-min(p[2] for p in pts)>3.8
                ok=ok and all(abs(math.hypot(p[0],p[1])-1.5)<0.05 for p in pts)
                # Uniform pitch: z increases linearly with unwrapped angle.
                if abs(total)>1e-9:
                    accum=0.
                    for i in range(1,len(pts)):
                        accum+=(angles[i]-angles[i-1]+math.pi)%(2*math.pi)-math.pi
                        expected=pts[0][2]+4*accum/total
                        if abs(pts[i][2]-expected)>0.08:ok=False;break
            else: ok=False
        else: ok=False
        checks.append({'object':kind,'pass':bool(ok),'reason':'' if ok else 'geometry constraint failed'})
    return {'passed':bool(checks) and all(c['pass'] for c in checks),'checks':checks}

def main():
    task=json.loads(Path(sys.argv[1]).read_text())
    folder=Path(sys.argv[2]); scene=json.loads((folder/'scene.json').read_text())
    result=evaluate(task,scene)
    (folder/'metrics.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    sys.exit(0 if result['passed'] else 1)

if __name__=='__main__':main()
