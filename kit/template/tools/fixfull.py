"""Turn validate's "the only picture is a print of X, which holds up full screen" scenes into <FullPhoto>.

One good wide photo plays full screen with a slow zoom in, not as a print on the wall (producer, Italy throne room
2026-10-25). The print's grade carries over; its black caption (tag=) becomes a free BlackTag and its names= become
free NameStrips, put in the first corner/band clear of the scene's other labels (bottom-left, top-left, bottom-right,
top-right). Run validate after, and look at stills of the changed scenes: a caption must not cover a face.

    python tools/fixfull.py [--root .] [--dry-run]
"""
import argparse
import pathlib
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve()
ERR = re.compile(r'^ERROR (\S+): the only picture is a print of (\S+), which holds up full screen')
PRINT = re.compile(r'<PhotoPrint\b((?:[^>"{]|"[^"]*"|\{\[.*?\]\}|\{\{.*?\}\}|\{[^{}]*\})*?)/>', re.S)
LABEL = re.compile(r'<(LabelTape|Highlight|BlackTag|DateTag|BigSerif|NameStrip|KraftNote)\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)/?>', re.S)


def errors():
    r = subprocess.run([sys.executable, str(ROOT / 'tools/validate.py'), '--root', str(ROOT)], capture_output=True,
                       text=True, encoding='utf8', errors='replace')
    return [m.groups() for m in map(ERR.match, r.stdout.splitlines()) if m]


def num(s, k, d=None):
    m = re.search(rf'\b{k}=\{{\s*(-?[\d.]+)\s*\}}', s)
    return float(m.group(1)) if m else d


def val(s, k):
    """a JSX attribute or an object key's string value"""
    m = re.search(rf"""\b{k}(?:=|:\s*)(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""", s)
    return None if not m else (m.group(1) if m.group(1) is not None else m.group(2))


def box(kind, at_):
    """(left, top, right, bottom) px of a label, as validate estimates it"""
    x, y = num(at_, 'x'), num(at_, 'y')
    if x is None or y is None:
        return None
    t = val(at_, 'text') or val(at_, 'line1') or ''
    z = num(at_, 'size')
    if kind == 'LabelTape':
        z = z or 40
        w, h = len(t) * (z * 0.6 + 4) + 52, z * 1.2 + 20
    elif kind in ('Highlight', 'BigSerif'):
        z = z or (64 if kind == 'Highlight' else 120)
        w, h = len(t) * z * 0.55 + 40, z * 1.3
    elif kind == 'NameStrip':
        z = z or 44
        w, h = max(len(t) * z * 0.5, len(val(at_, 'sub') or '') * z * 0.26) + 52, z * 1.9
    else:  # black tags, date tags and notes start at their x/y
        z = z or (46 if kind == 'DateTag' else 38)
        w, h = len(t) * z * 0.55 + 56, z * 1.25 + 28
        x, y = x + w / 2, y + h / 2
    anc = re.search(r'\banchor="(left|right)"', at_)
    if anc and kind in ('LabelTape', 'Highlight'):
        x += w / 2 if anc.group(1) == 'left' else -w / 2
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2


def hits(r, taken, pad=24):
    return any(r[0] < o[2] + pad and o[0] < r[2] + pad and r[1] < o[3] + pad and o[1] < r[3] + pad for o in taken)


def q(v):
    return '"' + v.replace('"', '\\"') + '"'


done = 0
want = {}
for sid, src in errors():
    want[sid] = src
for p in sorted((ROOT / 'src/timeline/parts').glob('*.tsx')):
    s = p.read_text(encoding='utf8')
    out = s
    for sid, src in want.items():
        m = re.search(r"\{id:\s*'" + re.escape(sid) + r"'", out)
        if not m:
            continue
        n = re.compile(r"\n\s*\{id:\s*'").search(out, m.end())
        st, en = m.start(), n.start() if n else len(out)
        b = out[st:en]
        if '<RedCircle' in b:
            print(f'{p.name} {sid}: skipped, a RedCircle is drawn on the print')
            continue
        pm = next((x for x in PRINT.finditer(b) if val(x.group(1), 'src') == src), None)
        if not pm:
            print(f'{p.name} {sid}: skipped, could not read the print of {src}')
            continue
        pa = pm.group(1)
        grade = val(pa, 'grade')
        taken = [r for r in (box(k, la) for k, la in LABEL.findall(b)) if r]
        new = [f'<FullPhoto src={q(src)}' + (f' grade={q(grade)}' if grade else '') + ' />']
        tm = re.search(r'tag=\{\{(.*?)\}\}', pa, re.S)
        if tm:
            l1, l2 = val(tm.group(1), 'line1') or '', val(tm.group(1), 'line2')
            tat = re.search(r'\bat:\s*([\d.]+)', tm.group(1))
            tat = float(tat.group(1)) if tat else num(pa, 'at', 0) + 0.2
            z = 42
            w = max(len(l1) * z * 0.7, len(l2 or '') * z * 0.29) + 44
            h = z * 1.1 + (z * 0.58 * 1.2 + 4 if l2 else 0) + 24
            spots = [(70, 1010 - h, 'left'), (70, 70, 'left'), (1850, 1010 - h, 'right'), (1850, 70, 'right')]
            for x, y, al in spots:
                r = (x, y, x + w, y + h) if al == 'left' else (x - w, y, x, y + h)
                if not hits(r, taken):
                    break
            taken.append(r)
            new.append(f'<BlackTag at={{{tat:g}}} x={{{x}}} y={{{round(y)}}} line1={q(l1)}' + (f' line2={q(l2)}' if l2 else '')
                       + (" align=\"right\"" if al == 'right' else '') + f' size={{{z}}} />')
        nm = re.search(r'names=\{\[(.*?)\]\}', pa, re.S)
        if nm:
            ns = [x.group(1) for x in re.finditer(r'\{([^{}]*)\}', nm.group(1))]
            for yrow in (950, 130):
                strips = []
                for k, e in enumerate(sorted(ns, key=lambda e: float(re.search(r'fx:\s*([\d.]+)', e).group(1)) if 'fx:' in e else 0.5)):
                    fx = re.search(r'fx:\s*([\d.]+)', e)
                    x = round(260 + (float(fx.group(1)) if fx else 0.5) * 1400)
                    t, sub = val(e, 'text') or '', val(e, 'sub')
                    nat = re.search(r'\bat:\s*([\d.]+)', e)
                    attrs = f'text={q(t)}' + (f' sub={q(sub)}' if sub else '') + f' at={{{nat.group(1) if nat else 0}}} x={{{x}}} y={{{yrow}}}'
                    strips.append((attrs, box('NameStrip', attrs)))
                if not any(hits(r, taken, 0) for _, r in strips):
                    break
            for attrs, r in strips:
                taken.append(r)
                new.append(f'<NameStrip {attrs} />')
        b2 = b[:pm.start()] + ''.join(new) + b[pm.end():]
        out = out[:st] + b2 + out[en:]
        done += 1
        print(f'{p.name} {sid}: {src} full screen' + (' + caption' if tm else '') + (' + names' if nm else ''))
    for name, mod in (('FullPhoto', '../../layers/Film'), ('BlackTag', '../../layers/Print'), ('NameStrip', '../../layers/Print')):
        if f'<{name}' not in out or re.search(r'import\s*\{[^}]*\b' + name + r'\b[^}]*\}', out):
            continue
        im = re.search(r"import\s*\{([^}]*)\}\s*from\s*'" + re.escape(mod) + "';", out)
        if im:
            names = sorted({x.strip() for x in im.group(1).split(',') if x.strip()} | {name}, key=str.lower)
            out = out[:im.start(1)] + ', '.join(names) + out[im.end(1):]
        else:
            last = list(re.finditer(r"^import .*?;\n", out, re.M | re.S))[-1]
            out = out[:last.end()] + f"import {{{name}}} from '{mod}';\n" + out[last.end():]
    if out != s and not a.dry_run:
        p.write_text(out, encoding='utf8')
print(f'{done} single prints turned into full-screen photos' + (' (dry run)' if a.dry_run else ''))
