"""Rule check of the edit in src/timeline/video.tsx. Run after every change; fix every ERROR before stills.

    python tools/validate.py [--hook 35]

ERROR: gaps/overlaps between scenes, last scene not ending at END, a clip missing or shorter than its scene,
       a missing photo/doc, banned layers (MapBlinds, TitleCard, Epigraph, Flash, Ribbon), burns on film->film,
       a picture change in the middle of a sentence (outside the hook), the same clip/photo twice after the hook.
WARN:  holds under 2.5 s outside the hook, burn count outside 3-6, film stills over 9 s with nothing new.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--hook', type=float, default=35, help='seconds of fast hook montage at the start (relaxed rules)')
ap.add_argument('--file', default='src/timeline/video.tsx')
ap.add_argument('--root', default=str(ROOT), help='project folder (default: this one)')
a = ap.parse_args()
ROOT = Path(a.root)

s = (ROOT / a.file).read_text(encoding='utf8')
M = json.loads((ROOT / 'src/lib/media.json').read_text())
W = json.loads((ROOT / 'src/lib/words.json').read_text(encoding='utf8'))
OV = {'cut': 0, 'dissolve': 22, 'whip': 6, 'whipL': 6, 'torn': 12, 'rack': 0}
errs, warns = [], []
E = errs.append
Wn = warns.append

m = re.search(r'export const END = ([\d.]+)', s)
END = float(m.group(1)) if m else 0
if W and END < W[-1]['e'] + 1:
    E(f'END {END} is before the last word ends ({W[-1]["e"]}) + 1 s')

for bad in ('MapBlinds', 'TitleCard', 'Epigraph', 'Flash', 'Ribbon'):
    if re.search(rf'<{bad}\b', s):
        E(f'banned layer <{bad}> (Sadat-style rules: no title intro, no red-line blinds map, no white flash, no light ribbons)')


def word_at(t):
    """(is mid-sentence, gap before) for a cut at t: a cut is fine on a sentence end or a pause >= 0.3 s"""
    prev = [w for w in W if w['e'] <= t + 0.05]
    nxt = [w for w in W if w['s'] >= t - 0.05]
    if not prev or not nxt:
        return False
    p, n = prev[-1], nxt[0]
    if p is n:
        return True
    gap = n['s'] - p['e']
    # sentence end, a pause >= 0.3 s, or a comma break (list items cut per item, the Sadat rhythm)
    return not (re.search(r'[.!?;:,]["\')]?$', p['w']) or gap >= 0.3)


scenes = []
for b in re.split(r"(?=\{id: ')", s)[1:]:
    m = re.match(r"\{id: '([\w-]+)', from: (-?[\d.]+), to: ([\d.]+|END), enter: '(\w+)'", b)
    if not m:
        continue
    to = END if m.group(3) == 'END' else float(m.group(3))
    scenes.append((m.group(1), float(m.group(2)), to, m.group(4), b))
if not scenes:
    E('no scenes found')

seen = {}
prev_to = 0.0
for sid, fr, to, en, b in scenes:
    if abs(prev_to - fr) > 0.001:
        E(f'{sid}: gap/overlap, previous scene ends {prev_to}, this starts {fr}')
    prev_to = to
    if to - fr < 2.5 and fr >= a.hook:
        Wn(f'{sid}: holds {to - fr:.2f} s (< 2.5 s outside the hook)')
    if fr >= a.hook and W and word_at(fr):
        E(f'{sid}: starts mid-sentence at {fr} (cut on a sentence end or a pause >= 0.3 s)')
    need = to - fr + OV.get(en, 0) / 25
    has_film = False
    for fm in re.finditer(r'<F src="([^"]+)" start=\{([\d.]+)\}(?:[^>]*?rate=\{([\d.]+)\})?', b):
        has_film = True
        src, st, rate = fm.group(1), float(fm.group(2)), float(fm.group(3) or 1)
        if src not in M:
            E(f'{sid}: clip {src} not in media.json (missing file, or run tools/media.py)')
            continue
        if (M[src]['d'] - st) / rate < need:
            E(f'{sid}: clip {src} too short: needs {need:.2f} s from {st}, has {(M[src]["d"] - st) / rate:.2f}')
        key = (src, round(st))
        if src in seen and fr >= a.hook:
            E(f'{sid}: clip {src} already used in {seen[src][0]} (no repeats after the hook)')
        seen.setdefault(src, (sid, fr, key))
    for pm in re.finditer(r'(PhotoPrint|DocCard)\s+(?:src|photo)="([^"]+)"', b):
        kind, src = pm.groups()
        folder = 'docs' if kind == 'DocCard' else 'photos'
        if 'film={' in b[pm.start():pm.start() + 400] and kind == 'PhotoPrint':
            folder = 'footage'
        if not (ROOT / 'public' / folder / src).exists():
            E(f'{sid}: missing public/{folder}/{src}')
        if src in seen and seen[src][0] != sid and fr >= a.hook:
            E(f'{sid}: {src} already shown in {seen[src][0]} (no repeats after the hook)')
        seen.setdefault(src, (sid, fr, src))
    if has_film and to - fr > 9 and b.count('<F ') == 1 and 'PhotoPrint' not in b and fr >= a.hook:
        Wn(f'{sid}: one film shot for {to - fr:.1f} s; split it on a phrase end if the narration moves on')
if scenes and abs(prev_to - END) > 0.001:
    E(f'last scene ends {prev_to}, END is {END}')

# film burns: only where the picture changes layer (film <-> print/graphic), never film -> film
bm = re.search(r'export const BURNS[^=]*=\s*\[(.*?)\];', s, re.S)
burns = [(float(x), int(n)) for x, n in re.findall(r'at:\s*([\d.]+),\s*n:\s*(\d+)', bm.group(1))] if bm else []
if not 3 <= len(burns) <= 6:
    Wn(f'{len(burns)} film burns (house rule: 3-6, at the big turns)')
for at, n in burns:
    if n not in (1, 4, 5, 6, 11, 12, 13):
        E(f'burn n={n} at {at}: only 1, 4, 5, 6, 11, 12, 13 exist in public/transitions')
    i = next((k for k, sc in enumerate(scenes) if abs(sc[1] - at) < 0.05), None)
    if i is None or i == 0:
        E(f'burn at {at} is not on a scene start')
        continue
    film = lambda b: b.lstrip().find('<F ') != -1 and '<Desk' not in b and '<Paper' not in b and '<DocMap' not in b and '<Chart' not in b and '<DocCard' not in b
    if film(scenes[i - 1][4]) and film(scenes[i][4]):
        E(f'burn at {at}: film -> film ({scenes[i - 1][0]} -> {scenes[i][0]}); burns only on a layer change')

for w in warns:
    print('WARN ', w)
for e in errs:
    print('ERROR', e)
print(f'{len(scenes)} scenes, END {END}, {len(burns)} burns: {len(errs)} errors, {len(warns)} warnings')
raise SystemExit(1 if errs else 0)
