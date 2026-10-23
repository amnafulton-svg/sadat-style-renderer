"""Rule check of the edit in src/timeline/video.tsx. Run after every change; fix every ERROR before stills.

    python tools/validate.py [--hook 35]

ERROR: gaps/overlaps between scenes, last scene not ending at END, a clip missing or shorter than its scene,
       a missing photo/doc, banned layers (MapBlinds, TitleCard, Epigraph, Flash, Ribbon), burns on film->film,
       a picture change in the middle of a sentence (outside the hook), the same clip/photo twice after the hook,
       text-only screens (type with no film/print/doc/map/chart) over 5 % of the runtime or two in a row,
       camera keys outside scale 0.95-1.12 or zooming faster than 3 % per second,
       one picture held over 3+ sentences (> 8 s, outside the hook), a scene that opens on an empty backdrop
       (its first print/doc lands > 1 s after the cut),
       and from tools/repeats.py (frames compared by picture, cached in _cache/repeat_hashes.json): the same film shot
       or photo under another file name after the hook, the same setting (gate, crowd, room) again from another
       clip of one source film (_work/clips.tsv, written by cut.py), >= 1 s of blank (black/white/flat) film.
WARN:  holds under 2.5 s outside the hook, burn count outside 3-6, smeared/out-of-focus film (repeats.py),
       DocMaps zoomed past what world.jpg / their basemaps can show sharply (tools/mapres.py: add a Sentinel-2
       basemap or pull the camera back).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--hook', type=float, default=35, help='seconds of fast hook montage at the start (relaxed rules)')
ap.add_argument('--file', default='src/timeline/video.tsx')
ap.add_argument('--root', default=str(ROOT), help='project folder (default: this one)')
ap.add_argument('--no-repeats', action='store_true', help='skip the picture-repeat check (needs ffmpeg, PIL, numpy)')
ap.add_argument('--repeat-cache', help='hash cache file (default _cache/repeat_hashes.json)')
a = ap.parse_args()
ROOT = Path(a.root)

s = (ROOT / a.file).read_text(encoding='utf8')
# sections may live in src/timeline/parts/s*.tsx (imported by video.tsx, in order): check them as one cut
if a.file == 'src/timeline/video.tsx':
    s += ''.join(p.read_text(encoding='utf8') for p in sorted((ROOT / 'src/timeline/parts').glob('s*.tsx'), key=lambda p: int(p.stem[1:])))
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
held = []  # (scene, seconds, line): reported after repeats.py measured the cuts inside film
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
    # one picture under three or more sentences reads as a stuck shot (producer, Britain test 2026-10-23)
    pics = len(re.findall(r'<(?:F|PhotoPrint|DocCard)\b', b))
    ends = [w for w in W if fr + 0.3 < w['e'] < to - 0.3 and re.search(r'[.!?]["\')\]]*$', w['w'])]
    if pics == 1 and to - fr > 8 and len(ends) >= 2 and fr >= a.hook and not re.search(r'<(DocMap|Chart)\b', b):
        held.append((sid, to - fr, f'{sid}: one picture for {to - fr:.1f} s over {len(ends) + 1} sentences; cut to a new '
                     f'shot on a sentence end (' + ', '.join(f"{w['e']:.2f}" for w in ends) + ')'))
    # an empty backdrop at the cut: every print/doc slides in later and nothing else is on screen
    ats = [float(x) for x in re.findall(r'<(?:PhotoPrint|DocCard)\b[^>]*?\bat=\{([\d.]+)\}', b)]
    if ats and not re.search(r'<(?:F|Film|DocMap|Chart)\b', b) and min(ats) - fr > 1.0:
        E(f'{sid}: nothing on screen for {min(ats) - fr:.1f} s after the cut at {fr} (first print at {min(ats)}); '
          f'start the scene on a picture')
# no slideshow: type alone on Black/ConcreteWall/Paper (no film, print, document, map or chart under it)
PIC = re.compile(r'<(F|Film|PhotoPrint|DocCard|DocMap|Chart)\b')
bare = [(sid, fr, to) for sid, fr, to, en, b in scenes if not PIC.search(b)]
for (s1, f1, t1), (s2, f2, t2) in zip(bare, bare[1:]):
    if abs(t1 - f2) < 0.001:
        E(f'{s1} -> {s2}: two text-only screens in a row at {f1:.1f} s (put real film or a photo under the type)')
bare_s = sum(t - f for _, f, t in bare)
if END and bare_s > 0.05 * END:
    E(f'text-only screens are {bare_s:.0f} s = {100 * bare_s / END:.0f} % of the video (max 5 %: it looks like a '
      f'slideshow). Replace with real film/photos: ' + ', '.join(f'{sid}@{f:.0f}s' for sid, f, _ in bare))
elif bare:
    Wn(f'{len(bare)} text-only screens, {bare_s:.0f} s ({100 * bare_s / max(END, 1):.1f} %): '
       + ', '.join(sid for sid, _, _ in bare))
if scenes and abs(prev_to - END) > 0.001:
    E(f'last scene ends {prev_to}, END is {END}')

# camera: a slow drift, never a punch-in (producer 2026-10-21): scale 0.95-1.12, at most 3 % per second.
# Camera clamps bold keys at render time anyway; this tells the editor the move they wrote is not what plays.
num = lambda e: float(eval(e, {'__builtins__': {}})) if re.fullmatch(r'[\d.+\- ]+', e.strip()) else None
for sid, fr, to, en, b in scenes:
    for cm in re.finditer(r'<Camera keys=\{\[(.*?)\]\}', b, re.S):
        ks = [(num(t), float(z)) for t, z in re.findall(r'at:\s*([^,]+),[^}]*?\bs:\s*([\d.]+)', cm.group(1))]
        ks = [k for k in ks if k[0] is not None]
        if any(not 0.95 <= z <= 1.12 for _, z in ks):
            E(f'{sid}: camera scale {max(z for _, z in ks)} (keep 0.95-1.12: a slow drift, never a zoom into a detail; '
              f'show the detail as its own print or crop instead)')
        for (t0, z0), (t1, z1) in zip(ks, ks[1:]):
            if abs(z1 - z0) > 0.03 * max(t1 - t0, 0.04) + 1e-6:
                E(f'{sid}: camera {z0}->{z1} in {t1 - t0:.1f} s at {t0:.1f} (max 3 % per second: a drift, not a zoom)')
                break

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

# the same shot under two file names (cut twice from one archive film, a photo saved twice), blank film: ERROR;
# smeared film and blocky maps: WARN
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mapres  # noqa: E402
warns += mapres.check(ROOT, scenes, s)
if not a.no_repeats:
    try:
        import repeats  # noqa: E402
        for lv, msg in repeats.check(ROOT, scenes, a.hook, a.repeat_cache, M):
            (E if lv == 'ERROR' else Wn)(msg)
    except ImportError as ex:
        Wn(f'picture-repeat check skipped ({ex}): run with the python that has PIL and numpy')
# a held film clip that has its own cuts inside (an edited archive film) is not a stuck shot
shot_len = sys.modules['repeats'].SHOT_LEN if 'repeats' in sys.modules else {}
for sid, dur, line in held:
    if not (sid in shot_len and shot_len[sid] < dur - 1 and shot_len[sid] <= 8):
        E(line)

for w in warns:
    print('WARN ', w)
for e in errs:
    print('ERROR', e)
print(f'{len(scenes)} scenes, END {END}, {len(burns)} burns: {len(errs)} errors, {len(warns)} warnings')
raise SystemExit(1 if errs else 0)
