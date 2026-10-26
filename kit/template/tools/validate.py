"""Rule check of the edit in src/timeline/video.tsx. Run after every change; fix every ERROR before stills.

    python tools/validate.py [--hook 35]

ERROR: gaps/overlaps between scenes, last scene not ending at END, a clip missing or shorter than its scene,
       a missing photo/doc, banned layers (MapBlinds, TitleCard, Epigraph, Flash, Ribbon), burns on film->film,
       a picture change in the middle of a sentence (outside the hook), the same clip/photo twice after the hook,
       text-only screens (type with no film/print/doc/map/chart) over 5 % of the runtime or two in a row,
       camera keys outside scale 0.95-1.12 or zooming faster than 3 % per second,
       one picture held over 3+ sentences (> 8 s, outside the hook), a scene that opens on an empty backdrop
       (its first print/doc lands > 1 s after the cut), a chart whose first value lands > 4.5 s after its axis (WARN > 3 s),
       and from tools/repeats.py (frames compared by picture, cached in _cache/repeat_hashes.json): the same film shot
       or photo under another file name after the hook, the same setting (gate, crowd, room) again from another
       clip of one source film (_work/clips.tsv, written by cut.py), >= 1 s of blank (black/white/flat) film,
       a silent-film title card (intertitle) inside what a scene shows,
       a DocCard mark that is not on printed lines of its scan (OCR, tools/docmark.py: beside the text, cutting
       through a line, or running far past it), a date/number tag (DateTag, BigSerif, Highlight, LabelTape, BlackTag)
       landing > 0.6 s after the narrator says it, text (tags, tapes, type, quotes) that is not on screen for
       1 s (0.25 s per word if longer) after it has typed/faded on before its scene cuts, hook included,
       a shot whose only picture is one PhotoPrint of a wide photo that holds up full screen (aspect >= 1.3,
       enlarged <= 1.6x to cover 1920x1080) and is not a FullPhoto, a FullPhoto of a photo too small or tall for it,
       a free BlackTag in a shot with one print (it is the print's tag=), a print caption running off the frame,
       a free NameStrip in a shot with a print (it is the print's names=, hung under the photo), print names
       running off the frame, into the print's black caption, or far wider than the photo.
       a scene cut > 0.5 s before the narrator's voice starts (read from the audio, tools/voice.py; fix: tools/fixonset.py),
       and in a one-chat project (.onechat, tools/plancheck.py): no plan.md or a sentence without a row, a film line
       of plan.md showing film for under half its time without 3+ logged searches behind its "no film:", fewer than
       one archive.org search per 20 s of narration.
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
PYEXE = Path(sys.executable).as_posix()

s = (ROOT / a.file).read_text(encoding='utf8')
# sections may live in src/timeline/parts/s1.tsx, p2.tsx ... (imported by video.tsx, in order): check them as one cut
# (any letter prefix: the england-plain chat named them p*.tsx and the check silently read 1 empty scene)
if a.file == 'src/timeline/video.tsx':
    parts = [p for p in (ROOT / 'src/timeline/parts').glob('*.tsx') if re.fullmatch(r'[a-z]+\d+', p.stem)]
    s += ''.join(p.read_text(encoding='utf8') for p in sorted(parts, key=lambda p: int(re.sub(r'\D', '', p.stem))))
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
    for pm in re.finditer(r'(PhotoPrint|DocCard|FullPhoto)\s+(?:src|photo)="([^"]+)"', b):
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
    pics = len(re.findall(r'<(?:F|PhotoPrint|DocCard|FullPhoto)\b', b))
    # a sentence end counts when the next sentence starts on this picture (not the breath before the next cut)
    ends = [w for i, w in enumerate(W[:-1]) if fr + 0.3 < w['e'] and W[i + 1]['s'] < to - 0.3
            and re.search(r'[.!?]["\')\]]*$', w['w'])]
    if pics == 1 and to - fr > 8 and len(ends) >= 2 and fr >= a.hook and not re.search(r'<(DocMap|Chart)\b', b):
        held.append((sid, to - fr, f'{sid}: one picture for {to - fr:.1f} s over {len(ends) + 1} sentences; cut to a new '
                     f'shot on a sentence end (' + ', '.join(f"{w['e']:.2f}" for w in ends) + ')'))
    # an empty backdrop at the cut: every print/doc slides in later and nothing else is on screen
    ats = [float(x) for x in re.findall(r'<(?:PhotoPrint|DocCard)\b[^>]*?\bat=\{([\d.]+)\}', b)]
    if ats and not re.search(r'<(?:F|Film|FullPhoto|DocMap|Chart)\b', b) and min(ats) - fr > 1.0:
        E(f'{sid}: nothing on screen for {min(ats) - fr:.1f} s after the cut at {fr} (first print at {min(ats)}); '
          f'start the scene on a picture')
# an empty chart: the axis is up but its first bar/column/point lands > 3 s later (tax withholding s3/s4, 2026-10-24)
for sid, fr, to, en, b in scenes:
    cm = re.search(r'<Chart chart=\{\{(.*)\}\}', b, re.S)
    if not cm or re.search(r'<(?:F|Film|PhotoPrint|FullPhoto|DocCard|DocMap)\b', b):
        continue
    ap_ = re.search(r'appear:\s*([\d.]+)', cm.group(1))
    start = max(fr, float(ap_.group(1)) if ap_ else fr)
    ats = [float(x) for x in re.findall(r'\bat:\s*([\d.]+)', cm.group(1))]
    gap = min(ats) - start if ats else 0
    if gap > 3.0:
        (E if gap > 4.5 else Wn)(f'{sid}: empty chart for {gap:.1f} s (axis up at {start}, first value at {min(ats)}); '
                                 f'land the first value within 3 s or start the chart later')
# no slideshow: type alone on Black/ConcreteWall/Paper (no film, print, document, map or chart under it)
PIC = re.compile(r'<(F|Film|PhotoPrint|FullPhoto|DocCard|DocMap|Chart)\b')
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

# document marks sit on the printed words (Chipyong-ni 2026-10-25: two plaque boxes guessed by eye sat beside the
# text): every mark rect must hold OCR lines, not cut through one, and not run more than a line past them
import docmark  # noqa: E402

for sid, fr, to, en, b in scenes:
    for dm in re.finditer(r'<DocCard\b.*?photo="([^"]+)"(.*?)/>', b, re.S):
        doc, body = dm.groups()
        mk = re.search(r'marks=\{\[(.*)\]\}', body, re.S)
        if not mk:
            continue
        # a circle rings an area (a town on a map, a signature): only highlight/underline marks must sit on words
        quad = r'\[\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\s*\]'
        rects = [[float(v) for v in q] for o in re.findall(r'\{[^{}]*\}', mk.group(1)) if 'circle' not in o
                 for q in re.findall(quad, o)]
        if not rects:
            continue
        d = docmark.ocr(ROOT, doc)
        if d is None:
            Wn(f'{sid}: marks on {doc} not checked (no OCR: install ~/yt/.venv-ocr)')
            continue
        if len(d['lines']) < 2:
            Wn(f'{sid}: OCR reads no text on {doc}; a mark there cannot be checked (prefer a legible scan)')
            continue
        lh = sorted(ln['box'][3] - ln['box'][1] for ln in d['lines'])[len(d['lines']) // 2]
        lw = lh * d['h'] / d['w']
        # a box taller than 4 lines is a headline when it is wide and spells words, else a pencil stroke or a stamp
        def printed(ln):
            x0, y0, x1, y1 = ln['box']
            return y1 - y0 <= 4 * lh or ((x1 - x0) * d['w'] >= 2 * (y1 - y0) * d['h']
                                         and sum(c.isalnum() for c in ln['text']) >= 4)
        text_lines = [ln for ln in d['lines'] if printed(ln)]
        for r in rects:
            on, cut = [], []
            for ln in text_lines:
                x0, y0, x1, y1 = ln['box']
                hx = min(r[2], x1) - max(r[0], x0)
                if hx <= 0.3 * min(r[2] - r[0], x1 - x0):
                    continue
                v = (min(r[3], y1) - max(r[1], y0)) / max(y1 - y0, 1e-6)
                if v >= 0.6:  # docmark stops halfway into the overlap of tight lines
                    on.append(ln)
                elif v >= 0.25:
                    cut.append(ln)
            fix = f'run: {PYEXE} tools/docmark.py {doc} "the spoken words"'
            if not on:
                E(f'{sid}: mark {r} on {doc} is not on any printed line ({fix})')
                continue
            top, bot = min(ln['box'][1] for ln in on), max(ln['box'][3] for ln in on)
            for ln in cut:
                # OCR boxes of tall or tight type overlap their neighbours: only the part of the line the mark covers
                # beyond the lines it is on counts as cutting through it
                y0, y1 = max(r[1], ln['box'][1]), min(r[3], ln['box'][3])
                extra = max(0, min(y1, top) - y0) + max(0, y1 - max(y0, bot))
                if extra < 0.25 * (ln['box'][3] - ln['box'][1]):
                    continue
                E(f'{sid}: mark {r} on {doc} cuts through the line "{ln["text"][:40]}" ({fix})')
            left, right = min(ln['box'][0] for ln in on), max(ln['box'][2] for ln in on)
            if r[1] < top - lh or r[3] > bot + lh or r[0] < left - 2 * lw or r[2] > right + 2 * lw:
                E(f'{sid}: mark {r} on {doc} runs past its text (printed lines span {[left, top, right, bot]}; {fix})')

# a date or figure on screen lands when the narrator says it (Chipyong-ni 2026-10-25: "25 October 1950" appeared
# after the date was spoken, because the scene cut came after the sentence had started)
MONTHS = 'january february march april may june july august september october november december'.split()
TAGS = re.compile(r'<(DateTag|BigSerif|Highlight|LabelTape|BlackTag)\b([^>]*?)/?>(?:([^<]{1,80})</\1>)?', re.S)
for sid, fr, to, en, b in scenes:
    for tm in TAGS.finditer(b):
        kind, attrs, inner = tm.groups()
        txt = (re.search(r'\btext="([^"]+)"', attrs) or re.search(r"\btext='([^']+)'", attrs))
        txt = txt.group(1) if txt else (inner or '')
        at = re.search(r'\bat=\{([\d.]+)\}', attrs)
        if not at or not txt:
            continue
        at = float(at.group(1))
        keys = [k for k in (re.sub(r'[^\w]', '', t.lower().replace(',', '')) for t in txt.split())
                if (k.isdigit() and len(k) >= 2) or k in MONTHS]
        said = []
        for k in keys:
            hits = [w['s'] for w in W if fr - 2.5 <= w['s'] <= to and re.sub(r'[^\w]', '', w['w'].lower().replace(',', '')) == k]
            if hits:
                said.append(min(hits, key=lambda t: abs(t - at)))
        if not said:
            continue
        t = min(said)
        if at - t > 0.6:
            hint = (f'the sentence starts before the scene at {fr}: start this scene at that sentence' if t < fr
                    else f'set at={{{t:.2f}}}')
            E(f'{sid}: {kind} "{txt}" lands at {at} but the narrator says it at {t:.2f} ({at - t:.1f} s late; {hint})')

# text must stay on screen long enough to read once it has typed / faded on (Italy 2026-10-25: "11 days earlier" and
# "The referendum ballot / Republic or Monarchy" sat on a 1.24 s hook scene and the cut came while they were still
# typing). Applies in the hook too: a fast montage cuts pictures, not half-read words.
# seconds from at= until the text is fully on (matches the components in src/layers at 25 fps)
ON = {'DateTag': lambda n: (min(n * 1.2, 15) - 4) / 25, 'LabelTape': lambda n: (min(n, 15) - 3) / 25, 'BlackTag': lambda n: 5 / 25,
      'NameStrip': lambda n: 6 / 25, 'BigSerif': lambda n: 8 / 25, 'Highlight': lambda n: 6 / 25,
      'KraftNote': lambda n: 3 / 25}
READ = re.compile(r'<(DateTag|LabelTape|BlackTag|NameStrip|BigSerif|Highlight|KraftNote)\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)/?>', re.S)


def _q(a, k):
    m = re.search(rf"""\b{k}:\s*(?:'([^']*)'|"([^"]*)")""", a)
    return (m.group(1) if m.group(1) is not None else m.group(2)) if m else ''



_TITLES = {'king', 'queen', 'prince', 'princess', 'pope', 'president', 'general', 'colonel', 'duke', 'duchess',
           'saint', 'emperor', 'empress', 'family', 'house', 'lord', 'lady', 'count', 'baron', 'captain', 'admiral'}


def _fitw(pa, asp):
    """a print's w: its w={..}, or from the project's {...fit(src, maxW, maxH)} helper (timeline/kit.tsx)"""
    m = re.search(r'\bw=\{\s*([\d.]+)\s*\}', pa)
    if m:
        return float(m.group(1))
    f = re.search(r"\{\.\.\.fit\('[^']*'(?:,\s*([\d.]+))?(?:,\s*([\d.]+))?", pa)
    if f and asp:
        return round(min(float(f.group(1) or 1200), (float(f.group(2) or 820) - 28) * asp + 28))
    return None

def attr(attrs, k):
    m = re.search(rf'\b{k}=(?:"([^"]*)"|\'([^\']*)\'|\{{\s*([\d.]+)\s*\}})', attrs)
    return None if not m else (m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else m.group(3))


for sid, fr, to, en, b in scenes:
    items = []
    for tm in READ.finditer(b):
        kind, attrs = tm.groups()
        txt = ' '.join(x for x in (attr(attrs, k) for k in ('text', 'title', 'line1', 'line2', 'sub')) if x)
        at = attr(attrs, 'at')
        if at is None or not txt:
            continue
        out = attr(attrs, 'out')
        items.append((kind, txt, float(at), float(out) if out else to))
    for pm in re.finditer(r'<PhotoPrint\b((?:[^>"]|"[^"]*")*?)\btag=\{\{(.*?)\}\}', b, re.S):
        tg = pm.group(2)
        txt = ' '.join(m.group(1) or m.group(2) for m in re.finditer(r"""line[12]:\s*(?:'([^']*)'|"([^"]*)")""", tg))
        ta = re.search(r'\bat:\s*([\d.]+)', tg)
        pa = attr(pm.group(1), 'at')
        if txt and (ta or pa):
            items.append(('BlackTag', txt, float(ta.group(1)) if ta else float(pa) + 0.2, to))
    for nm in re.finditer(r'<PhotoPrint\b(?:[^>"]|"[^"]*")*?\bnames=\{\[(.*?)\]\}', b, re.S):
        for e in re.finditer(r'\{([^{}]*)\}', nm.group(1)):
            t, na = _q(e.group(1), 'text'), re.search(r'\bat:\s*([\d.]+)', e.group(1))
            if t and na:
                items.append(('NameStrip', ' '.join(x for x in (t, _q(e.group(1), 'sub')) if x), float(na.group(1)), to))
    # QuoteText / ListWords: the line is on once its last word has popped in
    for qm in re.finditer(r'<(QuoteText|ListWords)\b[^>]*?(?:words|items)=\{\[(.*?)\]\}', b, re.S):
        ws = re.findall(r"""\{\s*w:\s*(?:'([^']*)'|"([^"]*)")\s*,\s*at:\s*([\d.]+)""", qm.group(2))
        if ws:
            items.append((qm.group(1), ' '.join(x or y for x, y, _ in ws), max(float(t) for *_, t in ws), to))
    for kind, txt, at, end in items:
        on = max(fr, at + ON.get(kind, lambda n: 5 / 25)(len(txt)))
        need = max(1.0, 0.25 * len(txt.split()))
        if min(end, to) - on < need - 0.02:
            left = min(end, to) - on
            E(f'{sid}: {kind} "{txt[:50]}" is fully on at {on:.2f} but the scene cuts at {min(end, to):.2f} '
              f'({max(left, 0):.2f} s to read, needs {need:.1f} s): hold the scene to {on + need:.2f} on the next sentence '
              f'end/pause, cue it earlier, or move/drop the tag (hook included; python tools/fixread.py does the first two)')

# one photo alone on the wall, shot after shot, feels templated (producer, Italy 2026-10-25): when a shot's only
# picture is a photo that holds up full screen, it plays full screen with a slow zoom in (FullPhoto); a photo too
# small or too tall for that stays a print
try:
    from PIL import Image
except ImportError:
    Image = None
    Wn('full-screen photo check skipped: run with the python that has PIL')


def fill_fit(src):
    """(aspect, enlargement to cover 1920x1080) of public/photos/src, or None"""
    try:
        w, h = Image.open(ROOT / 'public/photos' / src).size
    except Exception:
        return None
    return w / h, max(1920 / w, 1080 / h)


for sid, fr, to, en, b in scenes if Image else []:
    pics = re.findall(r'<(?:F|Film|PhotoPrint|FullPhoto|DocCard|DocMap|Chart)\b', b)
    for fm in re.finditer(r'<FullPhoto\s+src="([^"]+)"', b):
        f = fill_fit(fm.group(1))
        if f and (f[0] < 1.25 or f[1] > 2.0):
            E(f'{sid}: FullPhoto {fm.group(1)} is too {"tall" if f[0] < 1.25 else "small"} for full screen '
              f'(aspect {f[0]:.2f}, enlarged {f[1]:.1f}x); find a bigger copy or use a PhotoPrint')
    pp = re.findall(r'<PhotoPrint\s+src="([^"]+)"((?:[^>"]|"[^"]*")*?)(/?)>', b)
    if len(pics) != 1 or len(pp) != 1 or 'film=' in pp[0][1] or not pp[0][2] or '<RedCircle' in b or to - fr < 2:
        continue  # several pictures, moving film in a print, or annotations drawn on the print (a zoom slides it from under a ring)
    f = fill_fit(pp[0][0])
    if f and f[0] >= 1.3 and f[1] <= 1.6:
        E(f'{sid}: the only picture is a print of {pp[0][0]}, which holds up full screen (aspect {f[0]:.2f}, '
          f'enlarged {f[1]:.1f}x): use <FullPhoto src="{pp[0][0]}" /> (slow zoom in) instead of PhotoPrint on a wall '
          f'(python tools/fixfull.py converts them all, caption and names included)')

# a print's caption sits under the print it names (producer, cannabis 2026-10-25: "why the text in the black box is
# not under the image?"; 14-78 hand-placed BlackTags per video sat across the frame from their print): in a shot with
# one print the caption is that print's tag={{line1, line2}}, which PhotoPrint sticks on its bottom-left edge
for sid, fr, to, en, b in scenes:
    pp = list(re.finditer(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\[.*?\]\}|\{\{.*?\}\}|\{[^{}]*\})*?)/?>', b, re.S))
    if len(pp) == 1:
        for tm in re.finditer(r'<BlackTag\b[^>]*?line1="([^"]*)"', b):
            E(f'{sid}: BlackTag "{tm.group(1)}" floats free beside the shot\'s only print: make it the print\'s caption, '
              f'<PhotoPrint ... tag={{{{line1: \'{tm.group(1)}\', line2: \'...\'}}}} /> (sits under the photo, moves with it; python tools/fixtags.py moves them all)')
    for pm in pp:
        pa = pm.group(1)
        tg = re.search(r'\btag=\{\{(.*?)\}\}', pa, re.S)
        if not tg or Image is None:
            continue
        g = lambda k, d=None: (lambda m: float(m.group(1)) if m else d)(re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', pa))
        src = re.search(r'\bsrc="([^"]+)"', pa)
        x, y, asp, bd = g('x'), g('y'), g('aspect'), g('border', 14)
        if None in (x, y) or not src:
            continue
        if asp is None and 'film=' not in pa:
            try:
                iw, ih = Image.open(ROOT / 'public/photos' / src.group(1)).size
                asp = iw / ih
            except Exception:
                continue
        w = _fitw(pa, asp)
        if not asp or not w:
            continue
        t = tg.group(1)
        sz = (lambda m: float(m.group(1)) if m else 38)(re.search(r'\bsize:\s*([\d.]+)', t))
        l1, l2 = _q(t, 'line1'), _q(t, 'line2')
        th = sz * 1.1 + (sz * 0.58 * 1.1 + 4 if l2 else 0) + 24
        bottom = y + (w / asp + 2 * bd) / 2 + 0.4 * th
        right = x - w / 2 + 28 + max(len(l1) * sz * 0.5, len(l2) * sz * 0.29) + 44
        if bottom > 1060:
            E(f'{sid}: the caption "{l1}" under {src.group(1)} runs off the bottom of the frame (to y {bottom:.0f}): '
              f'raise the print (y) or make it smaller (w)')
        if right > 1900:
            E(f'{sid}: the caption "{l1}" on {src.group(1)} runs off the right edge (to x {right:.0f}): '
              f'move the print left or shorten the line')

# a name hangs under the photo it names (producer, cannabis 6:00 2026-10-25: "the name tag on the right side feels
# messy and where does it belongs?"; 105 of 135 NameStrips in shots with prints sat > 80 px off the photo; then
# "the white tag should be under the image not on the face"): in a shot with a print every name is that print's
# names=[{text, sub, at, fx}], one row hung off its bottom edge, people left to right by fx
for sid, fr, to, en, b in scenes:
    pp = list(re.finditer(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\[.*?\]\}|\{\{.*?\}\}|\{[^{}]*\})*?)/?>', b, re.S))
    if not pp:
        continue
    for nm in re.finditer(r'<NameStrip\b[^>]*?text="([^"]*)"', b):
        E(f'{sid}: NameStrip "{nm.group(1)}" floats free in a shot with a print: hang it under its photo, '
          f'<PhotoPrint ... names={{[{{text: "{nm.group(1)}", at: .., fx: ..}}]}} /> (fx = where that person stands, '
          f'0-1, orders the row; python tools/fixnames.py moves them all)')
    for pm in pp:
        pa = pm.group(1)
        nb = re.search(r'\bnames=\{\[(.*?)\]\}', pa, re.S)
        src = re.search(r'\bsrc="([^"]+)"', pa)
        if not nb or not src:
            continue
        g = lambda k, d=None: (lambda m: float(m.group(1)) if m else d)(re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', pa))
        x, y, bd, asp = g('x'), g('y'), g('border', 14), g('aspect')
        if asp is None and 'film=' not in pa and Image is not None:
            try:
                iw, ih = Image.open(ROOT / 'public/photos' / src.group(1)).size
                asp = iw / ih
            except Exception:
                pass
        w = _fitw(pa, asp)
        if None in (x, y, w) or not asp:
            continue
        ws, hs, ts = [], [], []
        for e in re.finditer(r'\{([^{}]*)\}', nb.group(1)):
            t, sub = _q(e.group(1), 'text'), _q(e.group(1), 'sub')
            sz = (lambda m: float(m.group(1)) if m else 34)(re.search(r'\bsize:\s*([\d.]+)', e.group(1)))
            ws.append(max(len(t) * sz * 0.5, len(sub) * sz * 0.26) + 52)
            hs.append(sz * 1.05 + 22 + (sz * 0.55 if sub else 0))
            ts.append(t)
        row = sum(ws) + 16 * (len(ws) - 1)
        names = ' + '.join(f'"{t}"' for t in ts)
        # the name goes under that person's own photo (Quirinale: Ciampi's name hung under the palace)
        stems = {q: set(re.findall('[a-z]+', q.lower())) for q in
                 (o.group(1) for o in (re.search('src="([^"]+)"', z.group(1)) for z in pp) if o)}
        for t in ts:
            tw = {v for v in re.findall('[a-z]+', t.lower()) if len(v) >= 4} - _TITLES
            other = [k for k, v in stems.items() if k != src.group(1) and tw & v]
            if other and not tw & stems.get(src.group(1), set()):
                E(f"{sid}: the name \"{t}\" hangs under {src.group(1)}, but {other[0]} is that person's photo: "
                  f"move it to that print's names=")
        edge = y + ((w - 2 * bd) / asp + 2 * bd) / 2  # the row hangs 55 % below the print's bottom edge
        bottom = edge + 0.55 * max(hs)
        if bottom > 1060:
            E(f'{sid}: the name {names} under {src.group(1)} runs off the bottom of the frame (to y {bottom:.0f}): '
              f'raise the print (y) or make it smaller (w)')
        tg = re.search(r'\btag=\{\{(.*?)\}\}', pa, re.S)
        if tg:  # the row sits right-aligned, beside the black caption in the bottom-left corner
            t = tg.group(1)
            tsz = (lambda m: float(m.group(1)) if m else 38)(re.search(r'\bsize:\s*([\d.]+)', t))
            cap = 28 + max(len(_q(t, 'line1')) * tsz * 0.5, len(_q(t, 'line2')) * tsz * 0.29) + 44
            left, right = x + w / 2 - 18 - row, x + w / 2 - 18
            if left < x - w / 2 + cap + 10:
                E(f'{sid}: the name {names} under {src.group(1)} runs into the print\'s black caption: shorten one '
                  f'(drop the name\'s sub, or a smaller size), or widen the print (w)')
        else:
            left, right = x - row / 2, x + row / 2
        if row > w * 1.5:
            E(f'{sid}: the names {names} under {src.group(1)} are much wider than the photo ({row:.0f} px vs {w:.0f}): '
              f'shorten them (sub), set a smaller size or widen the print')
        for lb in re.finditer(r'<(LabelTape|Highlight|BlackTag|DateTag)\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)/?>', b, re.S):
            la = lb.group(2)
            lx, ly = (re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', la) for k in ('x', 'y'))
            if not lx or not ly:
                continue
            lx, ly = float(lx.group(1)), float(ly.group(1))
            lt = next((m.group(1) for k in ('text', 'line1') for m in [re.search(rf'\b{k}="([^"]*)"', la)] if m), '') or _q(la, 'text') or _q(la, 'line1')
            lsz = (lambda m: float(m.group(1)) if m else None)(re.search(r'\bsize=\{\s*([\d.]+)', la))
            if lb.group(1) == 'LabelTape':
                lsz = lsz or 40
                lw, lh = len(lt) * (lsz * 0.6 + 4) + 52, lsz * 1.2 + 20
            elif lb.group(1) == 'Highlight':
                lsz = lsz or 64
                lw, lh = len(lt) * lsz * 0.55 + 40, lsz * 1.3
            else:  # black tags start at their x/y
                lsz = lsz or (46 if lb.group(1) == 'DateTag' else 38)
                lw, lh = len(lt) * lsz * 0.55 + 56, lsz * 1.25 + 28
                lx, ly = lx + lw / 2, ly + lh / 2
            anc = re.search(r'\banchor="(left|right)"', la)
            if anc and lb.group(1) in ('LabelTape', 'Highlight'):
                lx += lw / 2 if anc.group(1) == 'left' else -lw / 2
            if abs(lx - (left + right) / 2) < (lw + right - left) / 2 and abs(ly - (edge + 0.05 * max(hs))) < (lh + max(hs)) / 2:
                E(f'{sid}: the name {names} under {src.group(1)} runs into the {lb.group(1)} "{lt}": move that label '
                  f'away from the photo\'s bottom edge (the names hang there)')
        if left < 20 or right > 1900:
            E(f'{sid}: the name {names} under {src.group(1)} runs off the {"left" if left < 20 else "right"} edge: '
              f'move the print in or shorten the name')

# the same shot under two file names (cut twice from one archive film, a photo saved twice), blank film: ERROR;
# smeared film and blocky maps: WARN
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mapres  # noqa: E402
# a cut > 0.5 s before the narrator speaks (whisper glues the breath to the first word: Hitler's generals 2:12)
try:
    import voice  # noqa: E402
    _db = voice.levels(ROOT)
    for sid, fr, to, en, b in scenes[1:]:
        o = voice.onset(_db, fr)
        if o is not None and o - fr > 0.5:
            E(f'{sid}: cuts {o - fr:.2f} s before the voice (speech starts {o:.2f}, the cut is {fr}): '
              f'run tools/fixonset.py')
except Exception as ex:  # noqa: BLE001
    Wn(f'voice-start check skipped ({ex}): needs numpy + ffmpeg')
warns += mapres.check(ROOT, scenes, s)
import plancheck  # noqa: E402
errs += plancheck.check(ROOT, scenes, W)
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
