"""Execute deliberately invalid real Blender scenes; success means rejection."""
import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
cases=[('007','007_uneven_posts.py'),('009','009_solid_block.py'),('010','010_variable_pitch.py')]
failed=[]
for tid,name in cases:
    cmd=[sys.executable,str(root/'harness'/'run.py'),tid,str(root/'calibration'/'negative'/name),'--model','negative_control']
    proc=subprocess.run(cmd)
    metrics=root/'results'/'negative_control'/tid/'metrics.json'
    if not metrics.exists():
        print(tid,'ERROR: no metrics');failed.append(tid);continue
    data=json.loads(metrics.read_text())
    if data['passed']:
        print(tid,'ESCAPED: invalid Blender scene accepted');failed.append(tid)
    else:print(tid,'DETECTED: invalid Blender scene rejected')
if failed:sys.exit(1)
