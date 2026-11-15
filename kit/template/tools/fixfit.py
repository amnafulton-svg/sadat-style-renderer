"""Keep the big typewriter line (BigSerif) clear of the prints in its shot.

The typewriter number is wide, and a line placed beside a print can end up with its first letters lying on the
print's edge (producer, Japan oil 6:34, 2026-11-15: the "$" of "$30 million" sat on the photo's border). For every
BigSerif whose words cross the edge of a PhotoPrint in the same shot, this moves the line into the free wall beside
the print (the nearest side), and makes it smaller only when the free wall is too narrow; when even that leaves no
room it makes the print a little smaller, away from the words. A line that lies wholly inside a print is left alone
(it was put on the picture on purpose). It rewrites x / y / size (and the print's w / x / y) in the timeline.
tools/validate.py errors on what is left.

    python tools/fixfit.py [--root .] [--dry-run]
"""
import pathlib
import re
import subprocess

GAP = 40  # clear wall the fixer leaves between the words and a print, px
NEAR = 16  # closer than this counts as lying on the print
EDGE = 50  # clear frame edge, px
SCENE = re.compile(r"\{id:\s*'([^']+)',\s*from:\s*([\d.]+),\s*to:\s*([\d.]+)")
PRINT = re.compile(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\[.*?\]\}|\{\{.*?\}\}|\{[^{}]*\})*?)/?>', re.S)
BIG = re.compile(r'<BigSerif\b((?:[^>"\'{]|"[^"]*"|\'[^\']*\'|\{[^{}]*\})*?)/>', re.S)
_asp = {}


def num(s, k, d=None):
    m = re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', s)
    return float(m.group(1)) if m else d


def txt(s, k):
    m = re.search(rf"""\b{k}=(?:"([^"]*)"|\{{\s*'((?:[^'\\]|\\.)*)'\s*\}}|\{{\s*"((?:[^"\\]|\\.)*)"\s*\}})""", s)
    return next(g for g in m.groups() if g is not None) if m else None


def aspect(root, src):
    if src not in _asp:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
                            str(root / 'public/photos' / src)], capture_output=True, text=True).stdout.strip().split(',')
        try:
            _asp[src] = float(r[0]) / float(r[1])
        except Exception:
            _asp[src] = None
    return _asp[src]


def print_rect(root, pa):
    """(left, top, right, bottom) px a print can cover: its tilt and slow drift included"""
    import math
    x, y, w, asp, bd = num(pa, 'x'), num(pa, 'y'), num(pa, 'w'), num(pa, 'aspect'), num(pa, 'border', 14)
    src = txt(pa, 'src')
    if None in (x, y) or not src:
        return None
    if asp is None and 'film=' not in pa:
        asp = aspect(root, src)
    f = re.search(r"\{\.\.\.fit\('[^']*'(?:,\s*([\d.]+))?(?:,\s*([\d.]+))?", pa)
    if w is None and f and asp:
        w = round(min(float(f.group(1) or 1200), (float(f.group(2) or 820) - 28) * asp + 28))
    if not w or not asp:
        return None
    h = (w - 2 * bd) / asp + 2 * bd
    a = math.radians(abs(num(pa, 'rot', 0)))
    hw = (w * math.cos(a) + h * math.sin(a)) / 2
    hh = (w * math.sin(a) + h * math.cos(a)) / 2
    d = num(pa, 'drift', 18)
    return x - hw - d, y - hh - d, x + hw + d, y + hh + d


def text_size(text, sub, size):
    """(width, height) px of a BigSerif block, as src/layers/Type.tsx draws it (Special Elite)"""
    big = min(size * 0.8, 160)
    w = len(text) * big * 0.58
    h = big * 1.1
    if sub:
        fs = min(max(big * 0.4, 36), max(30, 680 / (len(sub) * 0.62)))
        w = max(w, len(sub) * (fs * 0.55 + 2))
        h += big * 0.12 + fs * 1.2
    return w, h


def text_box(x, y, w, h, anchor):
    left = x - w / 2 if anchor == 'center' else x if anchor == 'left' else x - w
    return left, y - h / 2, left + w, y + h / 2


def crosses(b, r, gap=NEAR):
    """the words touch the print (or its margin) without lying wholly inside it"""
    near = b[0] < r[2] + gap and b[2] > r[0] - gap and b[1] < r[3] + gap and b[3] > r[1] - gap
    inside = b[0] >= r[0] and b[2] <= r[2] and b[1] >= r[1] and b[3] <= r[3]
    return near and not inside


def scenes(src):
    ms = list(SCENE.finditer(src))
    for i, m in enumerate(ms):
        yield m.group(1), m.start(), (ms[i + 1].start() if i + 1 < len(ms) else len(src))


def clashes(root):
    """[(file, scene id, text, print src)] for every BigSerif lying across a print's edge"""
    root = pathlib.Path(root)
    out = []
    for f in sorted((root / 'src/timeline').rglob('*.tsx')):
        src = f.read_text(encoding='utf8')
        for sid, a, b in scenes(src):
            body = src[a:b]
            prints = [(txt(m.group(1), 'src'), print_rect(root, m.group(1))) for m in PRINT.finditer(body)]
            prints = [p for p in prints if p[1]]
            for m in BIG.finditer(body) if prints else []:
                at_ = m.group(1)
                text, x, y = txt(at_, 'text'), num(at_, 'x'), num(at_, 'y')
                if text is None or x is None or y is None:
                    continue
                w, h = text_size(text, txt(at_, 'sub') or '', num(at_, 'size', 260))
                bx = text_box(x, y, w, h, txt(at_, 'anchor') or 'center')
                for ps, r in prints:
                    if crosses(bx, r):
                        out.append((f.name, sid, text, ps))
                        break
    return out


def refit(x, y, size, text, sub, anchor, rects):
    """a place (x, y, size) for the line clear of every print, nearest to where it was; None if the wall has none"""
    big0 = min(size * 0.8, 160)
    big = big0
    while big >= 56:
        w, h = text_size(text, sub, big / 0.8)
        ax = 0 if anchor == 'center' else w / 2 if anchor == 'left' else -w / 2  # anchor x -> centre x
        cx, best = x + ax, None
        cands = [(cx, y)]
        for r in rects:
            for lo, hi in ((r[2] + GAP, 1920 - EDGE), (EDGE, r[0] - GAP)):  # wall right / left of this print
                if hi - lo >= w:
                    cands.append((min(max(cx, lo + w / 2), hi - w / 2), y))
            for lo, hi in ((r[3] + GAP, 1080 - EDGE), (EDGE, r[1] - GAP)):  # wall below / above it
                if hi - lo >= h:
                    cands.append((cx, min(max(y, lo + h / 2), hi - h / 2)))
        for nx, ny in cands:
            bx = (nx - w / 2, ny - h / 2, nx + w / 2, ny + h / 2)
            if bx[0] < EDGE - 1 or bx[2] > 1920 - EDGE + 1 or bx[1] < EDGE - 1 or bx[3] > 1080 - EDGE + 1:
                continue
            if any(crosses(bx, r, GAP - 2) or (bx[0] >= r[0] and bx[2] <= r[2] and bx[1] >= r[1] and bx[3] <= r[3]) for r in rects):
                continue
            d = abs(nx - cx) + abs(ny - y)
            if best is None or d < best[0]:
                best = (d, nx - ax, ny)
        if best:
            return round(best[1]), round(best[2]), (size if big == big0 else round(big / 0.8))
        big *= 0.94
    return None


def setnum(at_, k, v):
    if re.search(rf'\b{k}=\{{[^{{}}]*\}}', at_):
        return re.sub(rf'\b{k}=\{{[^{{}}]*\}}', f'{k}={{{v}}}', at_, count=1)
    return at_.rstrip() + f' {k}={{{v}}} '


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()
    moved = stuck = 0
    for f in sorted((root / 'src/timeline').rglob('*.tsx')):
        src = f.read_text(encoding='utf8')
        edits = []
        for sid, s0, s1 in scenes(src):
            body = src[s0:s1]
            pms = [(m, print_rect(root, m.group(1))) for m in PRINT.finditer(body)]
            pms = [(m, r) for m, r in pms if r]
            rects = [r for _, r in pms]
            for m in BIG.finditer(body) if rects else []:
                at_ = m.group(1)
                text, x, y, size = txt(at_, 'text'), num(at_, 'x'), num(at_, 'y'), num(at_, 'size', 260)
                if text is None or x is None or y is None:
                    continue
                sub, anchor = txt(at_, 'sub') or '', txt(at_, 'anchor') or 'center'
                w, h = text_size(text, sub, size)
                if not any(crosses(text_box(x, y, w, h, anchor), r) for r in rects):
                    continue
                fit = refit(x, y, size, text, sub, anchor, rects)
                bx0 = text_box(x, y, w, h, anchor)
                hit = [i for i, r in enumerate(rects) if crosses(bx0, r)]
                pm, r0 = pms[hit[0]]
                pa, pw = pm.group(1), num(pm.group(1), 'w')
                k = 0.96
                while not fit and len(hit) == 1 and pw and k >= 0.7:  # no wall: the print gives way, its far edge stays put
                    np_ = setnum(pa, 'w', round(pw * k))
                    r1 = print_rect(root, np_)
                    tcx, tcy = (bx0[0] + bx0[2]) / 2, (bx0[1] + bx0[3]) / 2
                    ox, oy = tcx - (r0[0] + r0[2]) / 2, tcy - (r0[1] + r0[3]) / 2
                    if abs(oy) / (r0[3] - r0[1]) >= abs(ox) / (r0[2] - r0[0]):
                        np_ = setnum(np_, 'y', round(num(pa, 'y') + (r0[3] - r1[3] if oy < 0 else r0[1] - r1[1])))
                    else:
                        np_ = setnum(np_, 'x', round(num(pa, 'x') + (r0[2] - r1[2] if ox < 0 else r0[0] - r1[0])))
                    rs = [print_rect(root, np_) if i == hit[0] else r for i, r in enumerate(rects)]
                    fit = refit(x, y, size, text, sub, anchor, rs)
                    if fit:
                        edits.append((s0 + pm.start(1), s0 + pm.end(1), np_))
                        print(f'{f.name} {sid}: print {txt(pa, "src")} w {pw:.0f}->{round(pw * k)}')
                    k -= 0.04
                if not fit:
                    stuck += 1
                    print(f'{f.name} {sid}: "{text}" has no clear wall beside the print - move or shrink the print')
                    continue
                nx, ny, nz = fit[0], fit[1], round(fit[2])
                new = at_
                for k, old, v in (('x', x, nx), ('y', y, ny), ('size', size, nz)):
                    if v != old:
                        new = setnum(new, k, int(v) if float(v).is_integer() else v)
                edits.append((s0 + m.start(1), s0 + m.end(1), new))
                moved += 1
                print(f'{f.name} {sid}: "{text}" x {x:.0f}->{nx} y {y:.0f}->{ny} size {size:.0f}->{nz}')
        if edits and not a.dry_run:
            for st, en, rep in sorted(edits, reverse=True):
                src = src[:st] + rep + src[en:]
            f.write_text(src, encoding='utf8')
    print(f'{moved} big lines moved clear of a print' + (f', {stuck} need the print moved' if stuck else '') + (' (dry run)' if a.dry_run else ''))


if __name__ == '__main__':
    main()
