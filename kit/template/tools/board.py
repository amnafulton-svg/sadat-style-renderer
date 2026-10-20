"""Review boards: stills of the cut in a 3x4 grid, each with the words spoken over it, for the editor's own eyes.

    python tools/board.py [--from S] [--to S] [--out _review]

One still per scene (mid-scene) plus the end frame of every DocMap, Chart and DocCard, rendered in one go with
tools/stills.mjs, then tiled 12 per board with the scene id, time and the narration under each tile. Prints the
board paths.

Why (producer, 2026-10-20): after 10-17 the editors stopped looking at pictures themselves (look.py described them
instead) and the cuts stopped feeling "synced": a screen model passes a well-made shot that is the wrong shot for the
words. Picture-to-words judgement is the editor's job again; these boards make that cheap (one image = 12 scenes
with their lines, ~3k tokens) instead of one full-size still per scene.
"""
import argparse
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path.cwd()
COLS, ROWS, TW, TH, CAP = 3, 4, 512, 288, 84
END_FRAME = ("<DocMap", "<Chart", "<DocCard")


def font(n):
    for f in ('DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'arial.ttf', '/Library/Fonts/Arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def scenes():
    s = (ROOT / 'src/timeline/video.tsx').read_text(encoding='utf8')
    blocks = re.split(r"(?=\{id: ')", s)[1:]
    out = []
    for b in blocks:
        m = re.match(r"\{id: '([\w-]+)', from: (-?[\d.]+), to: ([\d.]+|END)", b)
        if not m:
            continue
        out.append({'id': m.group(1), 'from': float(m.group(2)),
                    'to': None if m.group(3) == 'END' else float(m.group(3)),
                    'end': any(k in b for k in END_FRAME)})
    return out


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='lo', type=float, default=0)
    ap.add_argument('--to', dest='hi', type=float, default=1e9)
    ap.add_argument('--out', default='_review')
    a = ap.parse_args()
    words = json.loads((ROOT / 'src/lib/words.json').read_text(encoding='utf8'))
    last = max(w['e'] for w in words) + 2
    shots = []  # (time, scene id, label, from, to)
    for sc in scenes():
        fr, to = sc['from'], sc['to'] if sc['to'] is not None else last
        if to <= a.lo or fr >= a.hi:
            continue
        shots.append(((fr + to) / 2, sc['id'], 'mid', fr, to))
        if sc['end'] and to - fr > 1.5:
            shots.append((to - 0.3, sc['id'], 'end frame', fr, to))
    if not shots:
        raise SystemExit('no scenes in that range')
    out = ROOT / a.out
    frames = out / 'frames'
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    ts = [f"{t:.2f}" for t, *_ in shots]
    r = subprocess.run(['node', 'tools/stills.mjs', str(frames), *ts], capture_output=True, text=True)
    files = [Path(x) for x in r.stdout.split() if x.endswith('.jpg')]
    if len(files) != len(shots):
        raise SystemExit(f'stills.mjs made {len(files)} of {len(shots)} stills:\n{r.stderr[-1500:]}')
    for old in out.glob('board_*.jpg'):
        old.unlink()
    f1, f2 = font(17), font(15)
    per = COLS * ROWS
    made = []
    for b in range(0, len(shots), per):
        chunk = list(zip(shots[b:b + per], files[b:b + per]))
        im = Image.new('RGB', (COLS * (TW + 8), ROWS * (TH + CAP + 8)), 'white')
        dr = ImageDraw.Draw(im)
        for i, ((t, sid, label, fr, to), f) in enumerate(chunk):
            x, y = (i % COLS) * (TW + 8), (i // COLS) * (TH + CAP + 8)
            th = Image.open(f).convert('RGB').resize((TW, TH))
            im.paste(th, (x, y))
            spoken = ' '.join(w['w'] for w in words if fr - 0.05 <= w['s'] < to)
            dr.text((x + 2, y + TH + 2), f"#{b + i + 1} {sid}  {mmss(fr)}-{mmss(to)}  ({label} @{mmss(t)})",
                    fill=(170, 30, 20), font=f1)
            for k, line in enumerate(textwrap.wrap(f'"{spoken}"', 62)[:3]):
                dr.text((x + 2, y + TH + 24 + k * 19), line, fill='black', font=f2)
        o = out / f'board_{b // per + 1:02d}.jpg'
        im.save(o, quality=82)
        made.append(o)
    print(f'{len(shots)} stills on {len(made)} boards ({mmss(shots[0][3])}-{mmss(shots[-1][4])}):')
    for o in made:
        print(o.relative_to(ROOT))


if __name__ == '__main__':
    main()
