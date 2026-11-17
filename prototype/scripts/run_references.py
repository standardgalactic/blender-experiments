#!/usr/bin/env python3
"""Run all thirteen reference scripts and rebuild the gallery. Requires Blender on PATH."""
import argparse, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--blender',default='blender');args=p.parse_args()
failures=[]
for n in range(1,14):
    task=f'{n:03d}'
    script=root/'submissions'/('baseline.py' if n==1 else f'reference_{task}.py')
    command=[sys.executable,str(root/'harness'/'run.py'),task,str(script),'--model','reference','--blender',args.blender]
    print('Running',task,flush=True)
    if subprocess.run(command).returncode:failures.append(task)
subprocess.run([sys.executable,str(root/'harness'/'gallery.py')],check=True)
print('Failed tasks:',', '.join(failures) if failures else 'none')
sys.exit(bool(failures))
