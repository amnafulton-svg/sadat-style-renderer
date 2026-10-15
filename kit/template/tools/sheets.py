"""Review sheets of everything in public/: 3 frames per clip (start / middle / end) and the photos and docs.

    python tools/sheets.py <out-dir>

Look at every sheet before building on it: wrong era, title cards, watermarks, black frames, AI-looking photos.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '_sheets'
fr = out / 'fr'
fr.mkdir(parents=True, exist_ok=True)


def font(n):
    for f in ('arial.ttf', 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/Library/Fonts/Arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


F = font(18)


def dur(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0


groups = {}
for f in sorted((ROOT / 'public/footage').glob('*.mp4')):
    n, d = f.stem, dur(f)
    tiles = []
    for k, t in enumerate([0.3, d / 2, max(0.3, d - 0.4)]):
        o = fr / f'{n}_{k}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(f), '-frames:v', '1', '-vf', 'scale=-2:150', str(o)])
        tiles.append(o)
    groups.setdefault(n.split('_')[0], []).append((n, d, tiles))
made = []
for g, items in groups.items():
    for p in range(0, len(items), 16):
        chunk = items[p:p + 16]
        im = Image.new('RGB', (3 * 268 + 10, len(chunk) * 176), 'white')
        dr = ImageDraw.Draw(im)
        for i, (n, d, tiles) in enumerate(chunk):
            for k, t in enumerate(tiles):
                try:
                    th = Image.open(t)
                    th.thumbnail((266, 150))
                    im.paste(th, (k * 268, i * 176 + 22))
                except OSError:
                    pass
            dr.text((2, i * 176 + 2), f'{n}  {d:.1f}s', fill='black', font=F)
        o = out / f'clips_{g}_{p // 16}.jpg'
        im.save(o, quality=80)
        made.append(o)
for folder in ('photos', 'docs'):
    ph = sorted(x for x in (ROOT / 'public' / folder).glob('*') if x.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'))
    for p in range(0, len(ph), 20):
        chunk = ph[p:p + 20]
        im = Image.new('RGB', (5 * 330, 4 * 300), 'white')
        dr = ImageDraw.Draw(im)
        for i, f in enumerate(chunk):
            th = Image.open(f).convert('RGB')
            th.thumbnail((320, 260))
            x, y = (i % 5) * 330, (i // 5) * 300
            im.paste(th, (x, y + 24))
            dr.text((x + 2, y + 2), f.name[:34], fill='black', font=F)
        o = out / f'{folder}_{p // 20}.jpg'
        im.save(o, quality=80)
        made.append(o)
for o in made:
    print(o)
