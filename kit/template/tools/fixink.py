"""Pick the colour of plain type and of a note's arrow from the picture behind it.

The big typewriter line (BigSerif) and the handwritten note (HandNote) carry no outline, box or shadow (producer,
Japan oil 2026-11-15), so they must change colour to stay visible: off-white on a dark picture, dark ink on a
bright one. This looks at a still of each one's scene just before the words appear, measures how bright the picture
is under the words and along the arrow, and writes the choice to src/lib/ink.json (key "text|at"), which the two
components read. On a grey or patchy picture a note stays warm white and gets a soft dark patch behind it. The arrow keeps the pen's colour where that shows along its whole way and at its tip; otherwise it
takes the other tone, and red when neither shows. Nothing in the timeline is edited. Run it after the pictures and
the notes' places are settled, and again after moving a note or changing its picture.

    python tools/fixink.py [--root .] [--dry-run]
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve()
W, H = 480, 270  # stills are measured at a quarter size
K = W / 1920
EL = re.compile(r'<(HandNote|BigSerif)\b((?:[^>"\'{]|"[^"]*"|\'[^\']*\'|\{\[[^\]]*\]\}|\{[^{}]*\})*?)/>', re.S)
LIGHT, DARK = 0.95, 0.07


def num(s, k, d=None):
    m = re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', s)
    return float(m.group(1)) if m else d


def raw(s, k):
    """the attribute's value exactly as the component receives it (string) and as written (for the key)"""
    m = re.search(rf"""\b{k}=(?:"([^"]*)"|\{{\s*'((?:[^'\\]|\\.)*)'\s*\}}|\{{\s*"((?:[^"\\]|\\.)*)"\s*\}})""", s)
    if not m:
        return None
    return next(g for g in m.groups() if g is not None)


def pair(s, k):
    m = re.search(rf'\b{k}=\{{\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]\s*\}}', s)
    return (float(m.group(1)), float(m.group(2))) if m else None


def jsnum(v):
    """a number as JavaScript prints it in a template string: 32.06 -> '32.06', 38.0 -> '38'"""
    return str(int(v)) if v == int(v) else repr(v)


def arrow_start(box, to):
    """where HandNote's arrow leaves its words (noteArrowStart in Print.tsx)"""
    if not to:
        return None
    x0, y0, x1, y1 = box
    bx, by, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    dx, dy = to[0] - bx, to[1] - by
    k = min((bw / 2 + 26) / max(abs(dx), 1e-3), (bh / 2 + 26) / max(abs(dy), 1e-3))
    return (bx + dx * k, by + dy * k) if k < 0.85 else None


def arrow_bend(s, e, box, bend):
    """the curve's control point, bowed away from the words (noteArrowBend in Print.tsx)"""
    bx, by = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    ln = max(1.0, ((e[0] - s[0]) ** 2 + (e[1] - s[1]) ** 2) ** 0.5)
    nx, ny = -(e[1] - s[1]) / ln, (e[0] - s[0]) / ln
    amt = min(bend, ln * 0.22)
    mx, my = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
    d = lambda k: (mx + nx * amt * k - bx) ** 2 + (my + ny * amt * k - by) ** 2
    k = 1 if d(1) >= d(-1) else -1
    return mx + nx * amt * k, my + ny * amt * k


items = []
for f in sorted((ROOT / 'src/timeline').rglob('*.tsx')):
    src = f.read_text(encoding='utf8')
    for m in EL.finditer(src):
        kind, at_ = m.group(1), m.group(2)
        text, t, x, y = raw(at_, 'text'), num(at_, 'at'), num(at_, 'x'), num(at_, 'y')
        if text is None or t is None or x is None or y is None:
            continue
        starts = re.findall(r'\bfrom:\s*([\d.]+)', src[:m.start()])
        start = float(starts[-1]) if starts else 0.0
        sub = raw(at_, 'sub') or ''
        if kind == 'HandNote':
            z = num(at_, 'size', 120)
            w = max(len(text) * z * 0.33, len(sub) * z * 0.62 * 0.33 + 12)  # Kalam ~0.33 em a letter
            h = z * 0.9 + (z * 0.62 * 1.25 + 6 if sub else 0)
            box = (x, y, x + w, y + h)
        else:
            z = min(num(at_, 'size', 260) * 0.8, 160)
            w = max(len(text) * z * 0.62, len(sub) * 26)
            h = z * 1.1 + (z * 0.6 if sub else 0)
            an = raw(at_, 'anchor') or 'center'
            left = x - w / 2 if an == 'center' else x if an == 'left' else x - w
            box = (left, y - h / 2, left + w, y + h / 2)
        items.append(dict(kind=kind, key=f'{text}|{jsnum(t)}', text=text, box=box, frm=pair(at_, 'from'), to=pair(at_, 'to'),
                          bend=num(at_, 'bend', 50), time=round(max(start + 0.04, t - 0.24), 2), file=f.name))

if not items:
    print('fixink: no HandNote or BigSerif in the timeline')
    raise SystemExit(0)

tmp = ROOT / 'out' / '_ink'
shutil.rmtree(tmp, ignore_errors=True)
times = sorted({i['time'] for i in items})
r = subprocess.run(['node', 'tools/stills.mjs', str(tmp), *[f'{t:.2f}' for t in times]], cwd=ROOT, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(f'fixink: stills failed\n{r.stderr[-1500:]}')


def gray(t):
    p = tmp / f't{t:.2f}'.replace('t', 't', 1)
    p = tmp / ('t' + f'{t:.2f}'.rjust(7, '0') + '.jpg')
    b = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(p), '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                       capture_output=True).stdout
    if len(b) != W * H:
        raise SystemExit(f'fixink: could not read {p}')
    return b


def area(g, x0, y0, x1, y1):
    """mean brightness 0..1 of a frame-pixel rectangle"""
    xa, xb = max(0, int(x0 * K)), min(W, int(x1 * K) + 1)
    ya, yb = max(0, int(y0 * K)), min(H, int(y1 * K) + 1)
    if xb <= xa or yb <= ya:
        return 0.5
    tot = sum(sum(g[y * W + xa:y * W + xb]) for y in range(ya, yb))
    return tot / ((xb - xa) * (yb - ya)) / 255


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(len(v) * q))]


out, cache = {}, {}
for it in items:
    g = cache.get(it['time']) or cache.setdefault(it['time'], gray(it['time']))
    lum = area(g, *it['box'])
    # warm white is the house colour and holds wherever the picture is not plainly bright; dark ink only on a bright one
    ink = lum > 0.62
    e = {'ink': ink}
    note = f"{it['kind']:8} {it['text'][:28]:28} picture {lum:.2f} -> {'dark ink' if ink else 'warm white'}"
    if not ink and it['kind'] == 'HandNote':
        # a grey or patchy picture: the note keeps its warm white and gets a soft, edgeless dark patch behind the words
        # (producer chose this over a colour or a letter shadow, 2026-11-15). The typewriter line dims the frame itself.
        x0, y0, x1, y1 = it['box']
        cw, ch = (x1 - x0) / 6, (y1 - y0) / 3
        cells = [area(g, x0 + i * cw, y0 + j * ch, x0 + (i + 1) * cw, y0 + (j + 1) * ch) for i in range(6) for j in range(3)]
        if lum > 0.33 or max(cells) > 0.55:
            e['soft'] = 'grad'
            note += ' + soft dark patch'
    st = arrow_start(it['box'], it['to']) if it['kind'] == 'HandNote' else it['frm']
    if st and it['to']:
        # same path as HandNote draws: from the side of the words facing the target, bowed away from them
        (fx, fy), (tx, ty) = st, it['to']
        cx, cy = arrow_bend(st, it['to'], it['box'], it['bend'])
        way = []
        for i in range(5, 25):  # the first fifth sits by the words, which the note moves clear of
            u = i / 24
            px = (1 - u) ** 2 * fx + 2 * u * (1 - u) * cx + u * u * tx
            py = (1 - u) ** 2 * fy + 2 * u * (1 - u) * cy + u * u * ty
            way.append(area(g, px - 8, py - 8, px + 8, py + 8))
        ux, uy = (tx - cx), (ty - cy)
        ul = max(1.0, (ux * ux + uy * uy) ** 0.5)
        tip = [area(g, tx + ux / ul * d - 10, ty + uy / ul * d - 10, tx + ux / ul * d + 10, ty + uy / ul * d + 10) for d in (-14, 0, 16)]

        def shows(tone):
            return pct([abs(tone - v) for v in way], 0.15) >= 0.26 and min(abs(tone - v) for v in tip) >= 0.26

        pen, other = (DARK, LIGHT) if ink else (LIGHT, DARK)
        if shows(pen):
            note += ', arrow as the pen'
        elif shows(other):
            e['arrow'] = '#14110d' if other == DARK else '#f4f1e8'
            note += f", arrow {'dark' if other == DARK else 'white'} (the pen's colour is lost on the way or at the tip)"
        else:
            e['arrow'] = '#d0302f'
            note += ', arrow red (neither tone shows all the way)'
    out[it['key']] = e
    print(note)

if not a.dry_run:
    (ROOT / 'src/lib/ink.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
    print(f'fixink: {len(out)} written to src/lib/ink.json')
shutil.rmtree(tmp, ignore_errors=True)
