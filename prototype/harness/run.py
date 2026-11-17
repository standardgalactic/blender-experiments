import argparse, subprocess, sys, json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('task',help='Task ID, e.g. 001')
    parser.add_argument('submission',type=Path)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--repair',type=Path,help='Optional second script to run after the first; use only for explicit repair trials')
    parser.add_argument('--model',default='baseline')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    tasks=sorted((root/'tasks').glob(args.task+'*.json'))
    if len(tasks)!=1: parser.error('Task ID must match exactly one task')
    output=root/'results'/args.model/args.task
    output.mkdir(parents=True,exist_ok=True)
    submission=args.submission.resolve()
    if args.repair:
        repair=args.repair.resolve()
        if not submission.is_file() or not repair.is_file():parser.error('Both scripts must exist')
        combined=output/'combined_submission.py'
        combined.write_text(submission.read_text()+"\n# ---- corrective pass ----\n"+repair.read_text())
        submission=combined
    cmd=[args.blender,'--background','--python',str(root/'harness'/'scene.py'),'--',str(tasks[0]),str(output),str(submission)]
    with (output/'execution.log').open('w') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print('Blender failed; see',output/'execution.log')
        if (output/'error.txt').exists():
            print((output/'error.txt').read_text()[-2500:])
        sys.exit(result.returncode)
    if not (output/'scene.json').is_file():
        print('Blender exited without scene.json; see',output/'execution.log')
        if (output/'error.txt').exists():
            print((output/'error.txt').read_text()[-2500:])
        sys.exit(1)
    result=subprocess.run([sys.executable,str(root/'harness'/'evaluate.py'),str(tasks[0]),str(output)])
    print('Artifacts:',output)
    sys.exit(result.returncode)

if __name__=='__main__':main()
