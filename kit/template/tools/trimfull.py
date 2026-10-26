"""Crop a scan's own borders (black bars, paper margins, scanner strips) off every FullPhoto: python tools/trimfull.py [--root .]

A print on the wall hides them; full screen they show as bars at the sides (America 2026-10-26: the account book
pillarboxed in black, the Lowell engraving on its cream paper). The trimmed copy is written next to the original as
<name>_trim.jpg and the scene points at it, so the original stays for prints.
"""
import argparse
import pathlib
import re

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry', action='store_true', help='only list what would be trimmed')
A = ap.parse_args()
R = pathlib.Path(A.root)
PH = R / 'public/photos'


def depth(line, axis_len, flip):
    """rows (or cols) in from one side that are flat and the same tone as the outermost one"""
    n = 0
    ref = None
    for i in range(int(axis_len * 0.15)):
        v = line(axis_len - 1 - i if flip else i)
        m, s = float(v.mean()), float(v.std())
        if ref is None:
            ref = m
        if s > 9 or abs(m - ref) > 12:
            break
        n = i + 1
    return n


def edge(g, axis_len, line, flip):
    """border depth on one side, or 0. A border ends on a straight line all along the side; a clear sky or a plain
    wall is flat too, but it ends on a roofline or a horizon that wanders, so it stays (s14 Capitol, s8 Caserta)."""
    full = line(0)
    k = len(full) // 8
    ns = [depth(lambda i, a=a: line(i)[a * k:(a + 1) * k], axis_len, flip) for a in range(8)]
    n = min(ns)
    if n < max(4, axis_len * 0.006) or max(ns) - n > 4 or n >= int(axis_len * 0.15) - 1:
        return 0
    return n


def trim(src):
    im = Image.open(PH / src).convert('RGB')
    g = np.asarray(im.convert('L'), dtype=np.float32)
    h, w = g.shape
    top = edge(g, h, lambda i: g[i, w // 10: -w // 10], False)
    bot = edge(g, h, lambda i: g[i, w // 10: -w // 10], True)
    left = edge(g, w, lambda i: g[h // 10: -h // 10, i], False)
    right = edge(g, w, lambda i: g[h // 10: -h // 10, i], True)
    if not (top or bot or left or right):
        return None
    pad = 3  # a hair more, so no soft seam is left
    box = (left + pad if left else 0, top + pad if top else 0, w - (right + pad if right else 0), h - (bot + pad if bot else 0))
    out = pathlib.Path(src).stem + '_trim.jpg'
    if not A.dry:
        im.crop(box).save(PH / out, quality=93)
    return out, (top, bot, left, right)


done = 0
for p in sorted((R / 'src/timeline/parts').glob('*.tsx')):
    s = p.read_text(encoding='utf8')
    new = s
    for src in sorted(set(re.findall(r'<FullPhoto src="([^"]+)"', s))):
        if src.endswith('_trim.jpg') or not (PH / src).exists():
            continue
        r = trim(src)
        if r:
            new = new.replace(f'<FullPhoto src="{src}"', f'<FullPhoto src="{r[0]}"')
            done += 1
            print(f'{p.name}: {src} trimmed top/bottom/left/right {r[1]} -> {r[0]}')
    if new != s and not A.dry:
        p.write_text(new, encoding='utf8')
print(f'{done} full-screen photos trimmed')
