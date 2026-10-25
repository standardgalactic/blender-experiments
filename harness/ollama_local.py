#!/usr/bin/env python3
"""Generate local Blender submissions with installed Ollama models, then evaluate via v7 harness."""
import argparse, json, re, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def generate(model, prompt, endpoint, timeout, num_predict, temperature):
    payload={'model':model,'prompt':prompt,'stream':False,'options':{'temperature':temperature,'num_predict':num_predict}}
    req=urllib.request.Request(endpoint.rstrip('/')+'/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.load(response)

def extract(raw):
    blocks=re.findall(r'```(?:python|py)?\s*\n(.*?)```',raw,re.I|re.S)
    code=max(blocks,key=len).strip() if blocks else raw.strip()
    if code.startswith('```'): raise ValueError('Unrecognized fenced response')
    compile(code,'model_submission.py','exec')
    if not ('bpy' in code): raise ValueError('Response contains no Blender bpy code')
    return code+'\n'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--models',nargs='+',default=['granite4.1:3b','granite4.1:8b'])
    ap.add_argument('--tasks',nargs='+',default=['001','007','009'])
    ap.add_argument('--endpoint',default='http://127.0.0.1:11434')
    ap.add_argument('--timeout',type=int,default=300,help='Ollama request timeout per task')
    ap.add_argument('--blender-timeout',type=int,default=180)
    ap.add_argument('--num-predict',type=int,default=1200)
    ap.add_argument('--temperature',type=float,default=0.0)
    ap.add_argument('--generate-only',action='store_true')
    ap.add_argument('--api-guide',type=Path,default=None)
    args=ap.parse_args()
    manifest=[]; failures=[]
    out=ROOT/'model_submissions'/'local_ollama';out.mkdir(parents=True,exist_ok=True)
    for model in args.models:
        label='ollama_'+re.sub('[^a-zA-Z0-9_.-]','_',model)
        if args.api_guide:
            label += '_guided_fullspec'
        folder=out/label;folder.mkdir(exist_ok=True)
        for task in args.tasks:
            files=list((ROOT/'tasks').glob(task+'*.json'))
            if len(files)!=1: ap.error('Unknown or ambiguous task: '+task)
            spec=json.loads(files[0].read_text())
            # Never expose reference scripts, evaluators, or expected numerical scene data.
            prompt = ('Write a complete executable Blender 4.0 Python script.\n'
                      'Return ONLY executable Python code, without Markdown.\n'
                      'Import bpy. Do not render, save, or configure a camera.\n'
                      'Do not call bpy.ops.wm.read_factory_settings().\n'
                      'Use exact object names, locations, and dimensions.\n\n'
                      'TASK SPECIFICATION:\n' + json.dumps({k:v for k,v in spec.items() if k != 'id'}, indent=2) + '\n')
            if args.api_guide:
                guide = args.api_guide.read_text()
                prompt += (
                    "\n\nUse the following verified Blender API reference "
                    "when writing the script:\n\n" + guide
                )
            (folder/f'{task}.prompt.txt').write_text(prompt)
            started=time.monotonic()
            try:
                response=generate(model,prompt,args.endpoint,args.timeout,args.num_predict,args.temperature)
                (folder/f'{task}.response.json').write_text(json.dumps(response,indent=2))
                raw=response.get('response','')
                (folder/f'{task}.raw.txt').write_text(raw)
                code=extract(raw)
                (folder/f'{task}.py').write_text(code)
                manifest.append({'model':label,'task':task,'script':f'local_ollama/{label}/{task}.py'})
                print(f'{model} {task}: generated in {time.monotonic()-started:.1f}s',flush=True)
            except (ValueError,TimeoutError,urllib.error.URLError,OSError) as exc:
                failures.append({'model':model,'task':task,'error':str(exc)})
                print(f'{model} {task}: GENERATION FAILED: {exc}',file=sys.stderr,flush=True)
    manifest_path=ROOT/'model_submissions'/'manifest.local.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'generation_failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    print('Manifest:',manifest_path)
    if not manifest: return 1
    if not args.generate_only:
        cmd=[sys.executable,str(ROOT/'harness'/'model_batch.py'),str(manifest_path),'--timeout',str(args.blender_timeout)]
        result=subprocess.run(cmd)
        if result.returncode: print('Some Blender evaluations failed; inspect results/comparison.csv')
    return 1 if failures else 0

if __name__=='__main__':sys.exit(main())
