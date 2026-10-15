"""Cut one clip from a source film into public/footage/ (25 fps, 1080p, no sound) and refresh media.json.

    python tools/cut.py <source> <in-sec> <dur-sec> <name> [--crop "480:294:80:0"]

<name> is the footage file stem, e.g. canal_dredger -> public/footage/canal_dredger.mp4.
--crop removes a watermark / timecode strip only (PeriscopeFilm 640x360: 480:294:80:0). Never crop to zoom:
4:3 film is padded at render time (the F wrapper reads media.json).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('start', type=float); ap.add_argument('dur', type=float); ap.add_argument('name')
ap.add_argument('--crop')
a = ap.parse_args()

out = ROOT / 'public/footage' / f'{a.name}.mp4'
vf = (f'crop={a.crop},' if a.crop else '') + 'fps=25,scale=-2:1080:flags=lanczos,setsar=1'
r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.start), '-i', a.src, '-t', str(a.dur), '-an', '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', str(out)])
if r.returncode:
    sys.exit('ffmpeg failed')
print(out)
subprocess.run([sys.executable, str(ROOT / 'tools/media.py')], cwd=ROOT)
