"""ffprobe every clip in public/footage -> src/lib/media.json {name: {w, h, d}}. The F wrapper pads 4:3 film from it,
and validate.py checks clip lengths against it. cut.py runs this by itself; run it after adding clips by hand.

    python tools/media.py
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = {}
for f in sorted((ROOT / 'public/footage').glob('*.mp4')):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
                        '-of', 'json', str(f)], capture_output=True, text=True)
    j = json.loads(r.stdout or '{}')
    if not j.get('streams'):
        print('unreadable:', f.name)
        continue
    s = j['streams'][0]
    out[f.name] = {'w': s['width'], 'h': s['height'], 'd': round(float(j['format']['duration']), 2)}
json.dump(out, open(ROOT / 'src/lib/media.json', 'w'), indent=0)
pad = [k for k, v in out.items() if v['w'] / v['h'] < 1.7]
print(f'{len(out)} clips -> src/lib/media.json; {len(pad)} padded (narrower than 1.7:1)')
