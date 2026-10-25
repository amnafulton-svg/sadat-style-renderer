"""Hang every free NameStrip of a shot with prints under the photo it names: <PhotoPrint ... names={[{text, sub,
at, fx}]} />.

PhotoPrint hangs its names in one row off its bottom edge, so each sits under its photo and moves with it
(producer, cannabis 6:00 2026-10-25: "the name tag on the right side feels messy and where does it belongs?", then
"the white tag should be under the image not on the face"). A strip goes to the print whose file is named after
that person (s7_ciampi.jpg), else to the nearest print; fx (where the editor
had put it across the photo, 0-1) orders the row left to right. Long rows get a smaller size. Run validate after.

    python tools/fixnames.py [--root .] [--dry-run]
"""
import argparse
import json
import pathlib
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root)

PRINT = re.compile(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\[.*?\]\}|\{\{.*?\}\}|\{[^{}]*\})*?)(\s*/?>)', re.S)
NS = re.compile(r'[ \t]*<NameStrip\b((?:[^>"{]|"[^"]*"|\{[^{}]*\})*?)/>[ \t]*\n?', re.S)
SCENE = re.compile(r"\{id:\s*'([^']+)'.*?(?=\n\s*\{id:\s*'|\Z)", re.S)


def num(s, k, d=None):
    m = re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', s)
    return float(m.group(1)) if m else d


def txt(s, k):
    m = re.search(rf'\b{k}="([^"]*)"', s)
    return m.group(1) if m else None


TITLES = {'king', 'queen', 'prince', 'princess', 'pope', 'president', 'general', 'colonel', 'duke', 'duchess',
          'saint', 'emperor', 'empress', 'family', 'house', 'lord', 'lady', 'count', 'baron', 'captain', 'admiral'}


def words(s):
    return set(re.findall('[a-z]+', (s or '').lower()))


def who(name):
    """the words of a person's name worth matching against a photo's file name"""
    return {v for v in words(name) if len(v) >= 4} - TITLES


def rect(attrs):
    """(left, top, right, bottom) px of a print, or None"""
    from PIL import Image
    x, y, w, asp, bd = num(attrs, 'x'), num(attrs, 'y'), num(attrs, 'w'), num(attrs, 'aspect'), num(attrs, 'border', 14)
    src = txt(attrs, 'src')
    if None in (x, y) or not src:
        return None
    if asp is None:
        try:
            iw, ih = Image.open(ROOT / 'public/photos' / src).size
            asp = iw / ih
        except Exception:
            asp = 1.4
    f = re.search(r"\{\.\.\.fit\('[^']*'(?:,\s*([\d.]+))?(?:,\s*([\d.]+))?", attrs)
    if w is None and f:  # w from the project's fit(src, maxW, maxH) helper in timeline/kit.tsx
        w = round(min(float(f.group(1) or 1200), (float(f.group(2) or 820) - 28) * asp + 28))
    if w is None:
        return None
    h = (w - 2 * bd) / asp + 2 * bd
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2


moved = 0
for p in sorted((ROOT / 'src/timeline/parts').glob('*.tsx')):
    s = open(p, encoding='utf8').read()
    out, last = [], 0
    for sm in SCENE.finditer(s):
        b = sm.group(0)
        pp = [pm for pm in PRINT.finditer(b) if 'names={' not in pm.group(1)]
        rs = [rect(pm.group(1)) for pm in pp]
        strips = list(NS.finditer(b))
        if not pp or not strips or None in rs:
            continue
        per = {i: [] for i in range(len(pp))}
        for st in strips:
            # the print whose file is named after the person wins (Quirinale: Ciampi's strip sat nearer the palace)
            hit = [i for i, pm in enumerate(pp) if who(txt(st.group(1), 'text')) & words(txt(pm.group(1), 'src'))]
            if len(hit) == 1:
                per[hit[0]].append(st)
                continue
            x, y = num(st.group(1), 'x', 960), num(st.group(1), 'y', 540)
            d = [max(r[0] - x, 0, x - r[2]) + max(r[1] - y, 0, y - r[3]) for r in rs]
            per[d.index(min(d))].append(st)
        nb = b
        # edit from the end so earlier offsets stay valid: prints and strips together, last first
        edits = []
        for i, pm in enumerate(pp):
            if not per[i]:
                continue
            r = rs[i]
            src = txt(pm.group(1), 'src')
            pw = r[2] - r[0]
            names = []
            for st in sorted(per[i], key=lambda t: num(t.group(1), 'x', 960)):
                at_, x = st.group(1), num(st.group(1), 'x', 960)
                n = {'text': txt(at_, 'text')}
                if txt(at_, 'sub'):
                    n['sub'] = txt(at_, 'sub')
                n['at'] = num(at_, 'at')
                n['fx'] = round(min(1, max(0, (x - r[0]) / pw)), 2)
                if num(at_, 'rot') is not None:
                    n['rot'] = num(at_, 'rot')
                n['size'] = min(34, num(at_, 'size', 34))
                names.append(n)
                edits.append((st.start(), st.end(), ''))
            # the whole row no wider than 1.4x the photo: smaller type, down to 24
            bw = lambda n, z: max(len(n['text']) * z * 0.5, len(n.get('sub', '')) * z * 0.26) + 52
            z = names[0]['size']
            while z > 24 and sum(bw(n, z) for n in names) + 16 * (len(names) - 1) > pw * 1.4:
                z -= 1
            for n in names:
                n['size'] = min(n['size'], z)
                if n['size'] == 34:
                    del n['size']
                print(f'{p.name} {sm.group(1)}: "{n["text"]}" -> under {src} (fx {n["fx"]})')
            js = lambda v: json.dumps(int(v) if isinstance(v, float) and v.is_integer() else v, ensure_ascii=False)
            lit = ', '.join('{' + ', '.join(f'{k}: {js(v)}' for k, v in n.items()) + '}' for n in names)
            edits.append((pm.end(1), pm.end(1), f' names={{[{lit}]}}'))
            moved += len(names)
        for st, en, rep in sorted(edits, reverse=True):
            nb = nb[:st] + rep + nb[en:]
        out.append(s[last:sm.start()] + nb)
        last = sm.end()
    if out and not a.dry_run:
        open(p, 'w', encoding='utf8').write(''.join(out) + s[last:])
print(f'{moved} free name strips hung under their photo' + (' (dry run)' if a.dry_run else ''))
