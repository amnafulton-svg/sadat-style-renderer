"""Move the free BlackTag of every one-print shot onto its print: <PhotoPrint ... tag={{line1, line2, at}} />.

PhotoPrint sticks the caption on its own bottom-left edge, so it always sits under the photo it names and moves with
it (producer, cannabis 2026-10-25: "why the text in the black box is not under the image?"). validate errors on a free
BlackTag next to a shot's only print; this does the move for all of them at once. Only the first free tag of a shot
is moved (a second one is the editor's call). Afterwards run validate: a caption that would run off the frame needs
the print raised or made smaller.

    python tools/fixtags.py [--root .] [--dry-run]
"""
import argparse
import pathlib
import re

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root)

PRINT = re.compile(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\{.*?\}\}|\{[^{}]*\})*?)(\s*/?>)', re.S)
TAG = re.compile(r'[ \t]*<BlackTag\b((?:[^>"{]|"[^"]*"|\{[^{}]*\})*?)/>[ \t]*\n?', re.S)
SCENE = re.compile(r"\{id:\s*'([^']+)'.*?(?=\n\s*\{id:\s*'|\Z)", re.S)


def val(attrs, k):
    m = re.search(rf'\b{k}=(?:"([^"]*)"|\{{\s*([\d.]+)\s*\}})', attrs)
    return None if not m else (m.group(1) if m.group(1) is not None else m.group(2))


moved = 0
for p in sorted((ROOT / 'src/timeline/parts').glob('*.tsx')):
    s = open(p, encoding='utf8').read()
    out, last = [], 0
    for sm in SCENE.finditer(s):
        b = sm.group(0)
        pp = list(PRINT.finditer(b))
        tm = TAG.search(b)
        if len(pp) != 1 or not tm or 'tag={{' in pp[0].group(1):
            continue
        t = tm.group(1)
        l1, l2, at, size = val(t, 'line1'), val(t, 'line2'), val(t, 'at'), val(t, 'size')
        if not l1:
            continue
        parts = [f'line1: "{l1}"'] + ([f'line2: "{l2}"'] if l2 else []) + ([f'at: {at}'] if at else [])
        if size and float(size) < 38:
            parts.append(f'size: {size}')
        pm = pp[0]
        nb = b[:pm.end(1)] + ' tag={{' + ', '.join(parts) + '}}' + b[pm.end(1):]
        tm2 = TAG.search(nb, pm.end(1))  # the tag after the edit (the print may come before or after it)
        tm2 = tm2 if tm2 and tm2.group(1) == t else TAG.search(nb)
        nb = nb[:tm2.start()] + nb[tm2.end():]
        out.append(s[last:sm.start()] + nb)
        last = sm.end()
        moved += 1
        print(f'{p.name} {sm.group(1)}: "{l1}" -> print caption')
    if out and not a.dry_run:
        open(p, 'w', encoding='utf8').write(''.join(out) + s[last:])
print(f'{moved} free tags moved onto their print' + (' (dry run)' if a.dry_run else ''))
