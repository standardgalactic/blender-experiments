#!/usr/bin/env python3
"""Evaluate existing model-generated Blender scripts. Does not call an LLM."""
import argparse, csv, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ['model','task','attempt','status','passed','checks_passed','checks_total','seconds','script','result_dir']

def safe_label(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', str(value)) or value in ('.','..'):
        raise ValueError('Unsafe model or task label: '+str(value))
    return str(value)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest',type=Path,help='JSON file listing model submissions')
    ap.add_argument('--blender',default='blender')
    ap.add_argument('--timeout',type=int,default=180,help='Maximum seconds per Blender attempt')
    ap.add_argument('--repair',action='store_true',help='Run optional repair scripts only when initial attempt fails')
    args=ap.parse_args()
    if args.timeout<1: ap.error('--timeout must be positive')
    manifest=args.manifest.resolve()
    records=json.loads(manifest.read_text())
    if not isinstance(records,list): ap.error('Manifest must contain a JSON array')
    report=[]
    def execute(model,task,script,attempt,repair_script=None):
        # Distinct output directories per attempt, so initial results are never overwritten.
        label=model if attempt=='initial' else model+'__repair'
        output=ROOT/'results'/label/task
        output.mkdir(parents=True,exist_ok=True)
        for stale in ('scene.json','metrics.json','render.png','scene.blend','error.txt'):
            (output/stale).unlink(missing_ok=True)
        cmd=[sys.executable,str(ROOT/'harness'/'run.py'),task,str(script),'--model',label,'--blender',args.blender]
        if repair_script:cmd+=['--repair',str(repair_script)]
        t=time.monotonic();status='error'
        try:
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=args.timeout)
            status='completed' if proc.returncode==0 else 'failed'
            (output/'runner.log').write_text(proc.stdout+'\n'+proc.stderr)
        except subprocess.TimeoutExpired:
            status='timeout';(output/'runner.log').write_text('Timed out after '+str(args.timeout)+' seconds\n')
        elapsed=round(time.monotonic()-t,3)
        metrics={}
        if (output/'metrics.json').exists():
            try: metrics=json.loads((output/'metrics.json').read_text())
            except (ValueError,OSError):pass
        checks=metrics.get('checks',[])
        row=dict(model=model,task=task,attempt=attempt,status=status,
                 passed=metrics.get('passed') if status!='timeout' else None,
                 checks_passed=sum(bool(c.get('pass')) for c in checks),checks_total=len(checks),
                 seconds=elapsed,script=str(script),result_dir=str(output.relative_to(ROOT)))
        report.append(row)
        print(f'{model} {task} {attempt}: {status}, pass={row["passed"]}, {elapsed:.1f}s',flush=True)
        return row
    for item in records:
        if not isinstance(item,dict):ap.error('Each manifest entry must be an object')
        try: model=safe_label(item['model']);task=safe_label(item['task'])
        except (KeyError,ValueError) as exc:ap.error(str(exc))
        if model in ('reference','negative_control') or model.endswith('__repair'):
            ap.error('Reserved model label: '+model)
        if len(list((ROOT/'tasks').glob(task+'*.json')))!=1:ap.error('Unknown task: '+task)
        script=(manifest.parent/item['script']).resolve()
        if not script.is_file():ap.error('Missing submission: '+str(script))
        first=execute(model,task,script,'initial')
        if args.repair and first['passed'] is not True and item.get('repair'):
            fix=(manifest.parent/item['repair']).resolve()
            if not fix.is_file():ap.error('Missing repair: '+str(fix))
            execute(model,task,script,'repair',fix)
    output=ROOT/'results'/'comparison.csv';output.parent.mkdir(exist_ok=True)
    with output.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(report)
    subprocess.run([sys.executable,str(ROOT/'harness'/'gallery.py')],check=True)
    print('Comparison:',output)
    print('Model submissions evaluated:',len([r for r in report if r['attempt']=='initial']))
    print('Initial passes:',sum(r['passed'] is True for r in report if r['attempt']=='initial'))
    print('Repair passes:',sum(r['passed'] is True for r in report if r['attempt']=='repair'))
    return 0 if all(r['passed'] is True for r in report if r['attempt']=='initial') else 1

if __name__=='__main__':sys.exit(main())
