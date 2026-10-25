"""Mutation-test the structural evaluator against saved reference scenes.
No Blender invocation or rendering is required. Existing reference scenes must be
regenerated if task specifications or inspection formats have changed.
"""
import argparse, copy, csv, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('benchmark_evaluator', ROOT/'harness'/'evaluate.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def variants(task, scene):
    objs=scene.get('objects',[])
    if not objs:return
    first=objs[0]['name']
    s=copy.deepcopy(scene);s['objects']=[o for o in s['objects'] if o['name']!=first]
    yield 'remove_object',s,True
    s=copy.deepcopy(scene);s['objects'][0]['location'][0]+=1.0
    yield 'move_object',s,True if any(e.get('name')==first and 'location' in e for e in task.get('expected',[])) or task.get('geometry_test')=='radial' else None
    s=copy.deepcopy(scene);s['objects'][0]['dimensions'][0]+=1.0
    yield 'resize_object',s,True if any(e.get('name')==first and 'dimensions' in e for e in task.get('expected',[])) else None
    if task.get('preserve_unmodified') and scene.get('initial'):
        names={e['name'] for e in task.get('expected',[])}
        for name,original in scene['initial'].items():
            target=next((e for e in task.get('expected',[]) if e['name']==name),None)
            if target and all(abs(a-b)<1e-5 for field in ('location','dimensions') for a,b in zip(original[field],target[field])):
                s=copy.deepcopy(scene)
                for obj in s['objects']:
                    if obj['name']==name and obj.get('mesh_vertices'):
                        obj['mesh_vertices'][0][0]+=0.25
                        yield 'tamper_preserved_mesh',s,True
                        break
                break
    if task.get('geometry_test')=='radial':
        s=copy.deepcopy(scene)
        posts=sorted((o for o in s['objects'] if o['name'].startswith('Post_')),key=lambda o:o['name'])
        if len(posts)==8:
            import math
            a=math.atan2(posts[1]['location'][1],posts[1]['location'][0])+0.2
            posts[1]['location'][:2]=[3*math.cos(a),3*math.sin(a)]
            yield 'distort_angular_spacing',s,True
    if task.get('geometry_test')=='arch':
        s=copy.deepcopy(scene)
        obj=next((o for o in s['objects'] if o['name']=='Arch'),None)
        if obj and obj.get('mesh_vertices'):
            obj['mesh_vertices'][len(obj['mesh_vertices'])//2][2]+=0.7
            yield 'distort_arch_curvature',s,True
    if task.get('geometry_test')=='helix':
        s=copy.deepcopy(scene)
        obj=next((o for o in s['objects'] if o['name']=='Helix'),None)
        if obj and obj.get('curve_points'):
            for i,p in enumerate(obj['curve_points']):
                p[2]+=0.5*__import__('math').sin(2*__import__('math').pi*i/(len(obj['curve_points'])-1))
            yield 'distort_helix_pitch',s,True
    if task.get('geometry_test')=='boolean':
        s=copy.deepcopy(scene)
        # An intentionally invalid topology that retains counts. The current
        # Boolean heuristic cannot distinguish it from a valid through-hole.
        for o in s['objects']:
            if o['name']=='Perforated_Block':
                o['mesh_vertices']=[[0.0,0.0,0.0] for _ in o.get('mesh_vertices',[])]
                yield 'collapse_boolean_vertices',s,True
                break
    if task.get('geometry_test')=='helix':
        s=copy.deepcopy(scene)
        for o in s['objects']:
            if o['name']=='Helix':
                o['curve_points']=[[0.0,0.0,p[2]] for p in o.get('curve_points',[])]
                yield 'flatten_helix_radius',s,True
                break

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',default='reference');ap.add_argument('--strict',action='store_true');args=ap.parse_args()
    rows=[]
    for file in sorted((ROOT/'tasks').glob('*.json')):
        task=json.loads(file.read_text());tid=task['id']
        scene_file=ROOT/'results'/args.model/tid/'scene.json'
        if not scene_file.exists():
            rows.append(dict(task=tid,mutation='reference_missing',expected='PASS',observed='MISSING',detected='',status='MISSING'))
            continue
        scene=json.loads(scene_file.read_text())
        baseline=module.evaluate(task,scene)['passed']
        rows.append(dict(task=tid,mutation='reference',expected='PASS',observed='PASS' if baseline else 'FAIL',detected='',status='OK' if baseline else 'BASELINE_FAIL'))
        if not baseline:continue
        for name,mutant,should_reject in variants(task,scene):
            passed=module.evaluate(task,mutant)['passed']
            status=('DETECTED' if not passed else 'ESCAPED') if should_reject is True else 'UNCLASSIFIED'
            rows.append(dict(task=tid,mutation=name,expected='FAIL' if should_reject else 'UNCLASSIFIED',observed='PASS' if passed else 'FAIL',detected=str(not passed),status=status))
    destination=ROOT/'calibration'/'report.csv'
    with destination.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['task','mutation','expected','observed','detected','status']);writer.writeheader();writer.writerows(rows)
    for row in rows:print(f"{row['task']} {row['mutation']:<29} {row['status']}")
    from collections import Counter
    print('\nSummary:',dict(Counter(row['status'] for row in rows)))
    print('Report:',destination)
    if args.strict and any(row['status'] in ('ESCAPED','BASELINE_FAIL','MISSING') for row in rows):sys.exit(1)

if __name__=='__main__':main()
