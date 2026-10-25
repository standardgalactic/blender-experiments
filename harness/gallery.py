#!/usr/bin/env python3
"""Build a standalone, offline HTML index of result PNGs and metrics."""
import argparse, json, html
from pathlib import Path
from urllib.parse import quote

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    root=args.root.resolve()
    rows=[]
    for image in sorted((root/'results').glob('*/*/render.png')):
        folder=image.parent
        metrics={}
        try: metrics=json.loads((folder/'metrics.json').read_text())
        except (FileNotFoundError,ValueError): pass
        rows.append({'model':folder.parent.name,'task':folder.name,'passed':metrics.get('passed'),
                     'checks':metrics.get('checks',[]),
                     'image':image.relative_to(root).as_posix(),
                     'scene':(folder/'scene.blend').relative_to(root).as_posix(),
                     'log':(folder/'execution.log').relative_to(root).as_posix()})
    template=(root/'viewer'/'template.html').read_text()
    output=template.replace('/*__GALLERY_DATA__*/',json.dumps(rows).replace('</','<\/'))
    destination=root/'index.html'
    destination.write_text(output,encoding='utf-8')
    print(f'Gallery: {destination} ({len(rows)} renders)')
if __name__=='__main__':main()
