"""Place each handwritten note (HandNote) clear of faces and aim its arrow at the face's edge.

Producer 2026-11-23 (Kim Jong-un 2:06, 4:24, 8:37): the words sat on faces and every arrow left the words from their
left side and ended in an eye or a mouth. This looks at a still of each note's picture just before the words come,
finds the faces, and:
  - if the words would cover a face, moves them to the calmest free spot around the person the arrow points at
    (right, left, above, below or a corner, whichever is quietest and fits the frame), so the side changes shot to shot;
  - when the arrow points into a face, moves its tip to the face's edge on the words' side;
  - drops `from=`: HandNote starts the arrow on whichever side of the words faces its target.
Notes on pictures with no face found are left where they are. Run it after the pictures and notes are placed and
BEFORE tools/fixink.py (which picks the colours for the new places).

    python tools/fixarrow.py [--root .] [--dry-run]
"""
import argparse
import pathlib
import re
import shutil
import subprocess

import cv2

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve()
EL = re.compile(r'<HandNote\b((?:[^>"\'{]|"[^"]*"|\'[^\']*\'|\{\[[^\]]*\]\}|\{[^{}]*\})*?)/>', re.S)
W, H = 1920, 1080
TOP, BOTTOM, SIDE = 150, 860, 80  # date tag above, quote bar / captions below


def num(s, k, d=None):
    m = re.search(r'\b' + k + r'=\{(-?[\d.]+)\}', s)
    return float(m.group(1)) if m else d


def raw(s, k):
    m = re.search(r'\b' + k + r'=(?:"([^"]*)"|\'([^\']*)\'|\{"([^"]*)"\})', s)
    return next((g for g in m.groups() if g is not None), None) if m else None


def pair(s, k):
    m = re.search(r'\b' + k + r'=\{\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]\}', s)
    return (float(m.group(1)), float(m.group(2))) if m else None


notes = []
for f in sorted((ROOT / 'src/timeline').rglob('*.tsx')):
    src = f.read_text(encoding='utf8')
    for m in EL.finditer(src):
        s = m.group(1)
        text, t, x, y = raw(s, 'text'), num(s, 'at'), num(s, 'x'), num(s, 'y')
        if text is None or t is None or x is None or y is None:
            continue
        starts = re.findall(r'\bfrom:\s*([\d.]+)', src[:m.start()])
        start = float(starts[-1]) if starts else 0.0
        z = num(s, 'size', 120)
        sub = raw(s, 'sub') or ''
        bw = max(len(text) * z * 0.33, len(sub) * z * 0.62 * 0.33 + 12) + 30  # + the small tilt
        bh = z * 0.9 + (z * 0.62 * 1.25 + 6 if sub else 0) + 20
        notes.append(dict(file=f, el=m.group(0), text=text, at=t, x=x, y=y, bw=bw, bh=bh, to=pair(s, 'to'),
                          ring='ring=' in s, time=round(max(start + 0.04, t - 0.24), 2)))

if not notes:
    print('fixarrow: no HandNote in the timeline')
    raise SystemExit(0)

tmp = ROOT / 'out' / '_arrow'
shutil.rmtree(tmp, ignore_errors=True)
times = sorted({n['time'] for n in notes})
r = subprocess.run(['node', 'tools/stills.mjs', str(tmp), *[f'{t:.2f}' for t in times]], cwd=ROOT, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(f'fixarrow: stills failed\n{r.stderr[-1500:]}')

MODEL = pathlib.Path.home() / '.cache/fixarrow/yunet.onnx'  # OpenCV's YuNet face model (opencv_zoo, 230 KB)
if not MODEL.exists():
    import urllib.request
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve('https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/'
                               'face_detection_yunet_2023mar.onnx', MODEL)
DET = cv2.FaceDetectorYN.create(str(MODEL), '', (W, H), 0.6, 0.3, 50)


def faces(img):
    _, r = DET.detect(img)
    return [tuple(int(v) for v in f[:4]) for f in (r if r is not None else []) if f[2] >= 40]


def grow(b, k):
    x, y, w, h = b
    return (x - w * k, y - h * k, x + w * (1 + k), y + h * (1 + k))


def over(p, q):
    return max(0, min(p[2], q[2]) - max(p[0], q[0])) * max(0, min(p[3], q[3]) - max(p[1], q[1]))


def head(f):
    """the face box plus a little hair and ears"""
    x, y, w, h = f
    return (x - w * 0.08, y - h * 0.15, x + w * 1.08, y + h * 1.04)


def body(f):
    """the shoulders and chest under a face"""
    x, y, w, h = f
    return (x - w * 0.45, y + h * 1.05, x + w * 1.45, H)


def arrow_len(box, to):
    bx, by, bw, bh = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, box[2] - box[0], box[3] - box[1]
    dx, dy = to[0] - bx, to[1] - by
    k = min((bw / 2 + 26) / max(abs(dx), 1e-3), (bh / 2 + 26) / max(abs(dy), 1e-3))
    return None if k >= 0.85 else (1 - k) * (dx * dx + dy * dy) ** 0.5


def busy(g, b):
    x0, y0, x1, y1 = (int(max(0, v)) for v in b)
    patch = g[y0:min(H, y1), x0:min(W, x1)]
    return float(patch.std()) if patch.size else 99.0


edits = {}
for n in notes:
    p = tmp / ('t' + f"{n['time']:.2f}".rjust(7, '0') + '.jpg')
    img = cv2.imread(str(p))
    if img is None:
        print(f"  {n['text']}: no still, left as is")
        continue
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fs = faces(img)
    words = (n['x'], n['y'], n['x'] + n['bw'], n['y'] + n['bh'])
    heads = [head(f) for f in fs]
    to = n['to']
    target = None
    if to and fs:
        near = sorted(fs, key=lambda b: (b[0] + b[2] / 2 - to[0]) ** 2 + (b[1] + b[3] / 2 - to[1]) ** 2)[0]
        cxf, cyf = near[0] + near[2] / 2, near[1] + near[3] / 2
        if ((cxf - to[0]) ** 2 + (cyf - to[1]) ** 2) ** 0.5 < max(260, near[2] * 1.5):
            target = near
    nx, ny, nto, why = n['x'], n['y'], to, []
    nz = None
    if target and not n['ring']:
        Hd = head(target)

        def tip_for(px, py, bw, bh):  # the head's edge on the words' side
            fcx, fcy = (Hd[0] + Hd[2]) / 2, (Hd[1] + Hd[3]) / 2
            wx, wy = px + bw / 2 - fcx, py + bh / 2 - fcy
            k = min((Hd[2] - Hd[0]) / 2 / max(abs(wx), 1e-3), (Hd[3] - Hd[1]) / 2 / max(abs(wy), 1e-3))
            return (round(fcx + wx * k), round(fcy + wy * k))

        def ok(px, py, bw, bh):
            b = (px, py, px + bw, py + bh)
            if any(over(b, h) > 0 for h in heads) or any(over(b, bd) > 0 for bd in others):
                return None  # never on a face, never on someone else's body
            L = arrow_len(b, tip_for(px, py, bw, bh))
            return L if L and 90 <= L <= 320 else None

        others = [body(f) for f in fs if f != target]
        own = body(target)
        bw, bh = n['bw'], n['bh']
        if ok(nx, ny, bw, bh) is None:
            best = None
            for sc in (1.0, 0.85, 0.72):  # a smaller note before a bad place
                sbw, sbh = (n['bw'] - 30) * sc + 30, (n['bh'] - 20) * sc + 20
                hcy = (Hd[1] + Hd[3]) / 2
                cands = []
                for gap in (90, 140, 200, 260):
                    cands += [(Hd[2] + gap, hcy - sbh / 2, 0), (Hd[0] - gap - sbw, hcy - sbh / 2, 0),  # beside the head
                              (Hd[2] + gap, Hd[1] - sbh * 0.3, 0), (Hd[0] - gap - sbw, Hd[1] - sbh * 0.3, 0),
                              ((Hd[0] + Hd[2]) / 2 - sbw / 2, Hd[1] - gap - sbh, 10),  # above
                              (Hd[2] + gap * 0.6, Hd[1] - gap * 0.7 - sbh, 4), (Hd[0] - gap * 0.6 - sbw, Hd[1] - gap * 0.7 - sbh, 4),
                              (Hd[2] + gap * 0.8, Hd[3] - sbh * 0.3, 14), (Hd[0] - gap * 0.8 - sbw, Hd[3] - sbh * 0.3, 14)]  # chin level
                for cx_, cy_, pen in cands:
                    cx_ = min(max(cx_, SIDE), W - SIDE - sbw)
                    cy_ = min(max(cy_, TOP), BOTTOM - sbh)
                    L = ok(cx_, cy_, sbw, sbh)
                    if L is None:
                        continue
                    sb = (cx_, cy_, cx_ + sbw, cy_ + sbh)
                    score = busy(g, sb) + pen + abs(L - 170) * 0.03 + (25 if over(sb, own) > 0 else 0)
                    if best is None or score < best[0]:
                        best = (score, round(cx_), round(cy_), sc, sbw, sbh)
                if best:
                    break
            if best:
                nx, ny, bw, bh = best[1], best[2], best[4], best[5]
                if best[3] < 1:
                    nz = round(num(n['el'], 'size', 120) * best[3])
                why.append(f'words moved to ({nx}, {ny})' + (f' at size {nz}' if nz else ''))
            else:
                why.append('no free spot beside the head: check this note by eye')
        nto = tip_for(nx, ny, bw, bh)
        if not to or abs(nto[0] - to[0]) + abs(nto[1] - to[1]) > 6:
            why.append(f'arrow tip to the head edge {nto}')
    elif any(over(words, h) > 0 for h in heads):
        why.append('words cover a face: check this note by eye')
    el = n['el']
    new = re.sub(r'\s+from=\{\[[^\]]*\]\}', '', el)
    new = re.sub(r'\bx=\{-?[\d.]+\}', f'x={{{nx:g}}}', new, 1)
    new = re.sub(r'\by=\{-?[\d.]+\}', f'y={{{ny:g}}}', new, 1)
    if nz:
        new = re.sub(r'\s+size=\{-?[\d.]+\}', '', new).replace('<HandNote', f'<HandNote size={{{nz}}}', 1)
    if nto and nto != to:
        new = re.sub(r'\bto=\{\[[^\]]*\]\}', f'to={{[{nto[0]:g}, {nto[1]:g}]}}', new, 1)
    print(f"  {n['text'][:28]:28} faces {len(fs)}  " + ('; '.join(why) if why else 'fine'))
    if new != el:
        edits.setdefault(n['file'], []).append((el, new))

for f, ch in edits.items():
    src = f.read_text(encoding='utf8')
    for old, new in ch:
        src = src.replace(old, new, 1)
    if not a.dry_run:
        f.write_text(src, encoding='utf8')
print(f"fixarrow: {sum(len(c) for c in edits.values())} notes changed" + (' (dry run)' if a.dry_run else ''))
shutil.rmtree(tmp, ignore_errors=True)
