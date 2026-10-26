"""Fix validate's "N s to read" errors: text that is still typing when the scene cuts.

For each one, in this order:
  1. cue it earlier: at= moves back by what is missing (at most 1.2 s, never before the scene starts);
  2. hold the scene: its cut moves to the next pause (>= 0.25 s between words) after the text has been read, and the
     next scene starts there, if that scene keeps >= 2.5 s;
  3. otherwise it is listed for the editor (drop the tag or rework the shot).
Producer, Italy 2026-10-25: the scene "appears and disappears fast while the text is still typing".
Runs validate itself and repeats until nothing more can be fixed. Run validate after.

    python tools/fixread.py [--root .] [--dry-run]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve()
W = json.loads((ROOT / 'src/lib/words.json').read_text(encoding='utf8'))
ERR = re.compile(r'^ERROR (\S+): (\w+) "(.*?)" is fully on at ([\d.]+) but the scene cuts at ([\d.]+) '
                 r'\(([\d.]+) s to read, needs ([\d.]+) s\)')
HEAD = re.compile(r"\{id:\s*'([^']+)',\s*from:\s*([\d.]+),\s*to:\s*([\d.]+)")
MAX_EARLY = 1.2


def parts():
    return {p: p.read_text(encoding='utf8') for p in sorted((ROOT / 'src/timeline/parts').glob('*.tsx'))}


def errors():
    r = subprocess.run([sys.executable, str(ROOT / 'tools/validate.py'), '--root', str(ROOT)], capture_output=True,
                       text=True, encoding='utf8', errors='replace')
    return [m.groups() for m in map(ERR.match, r.stdout.splitlines()) if m]


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def scene_span(s, sid):
    """(start, end) offsets of scene sid's text in s"""
    m = re.search(r"\{id:\s*'" + re.escape(sid) + r"'", s)
    if not m:
        return None
    n = re.compile(r"\n\s*\{id:\s*'").search(s, m.end())
    return m.start(), n.start() if n else len(s)


def at_spots(b, kind, text):
    """the (start, end) of the at number(s) that cue this text in scene text b"""
    t0 = text.split(' ')[0]
    spots = []
    if kind == 'NameStrip':  # a print's names=[{text, at}] or a free NameStrip
        for m in re.finditer(r'\{text:\s*"([^"]*)"[^{}]*?\bat:\s*([\d.]+)', b):
            if text.startswith(m.group(1)):
                spots.append(m.span(2))
    if kind == 'BlackTag':  # a print's tag={{line1, at}}
        for m in re.finditer(r'tag=\{\{([^{}]*)\}\}', b):
            l1 = re.search(r"""line1:\s*(?:'([^']*)'|"([^"]*)")""", m.group(1))
            if l1 and text.startswith((l1.group(1) or l1.group(2) or '')[:40]):
                am = re.search(r'\bat:\s*([\d.]+)', m.group(1))
                if am:
                    spots.append((m.start(1) + am.start(1), m.start(1) + am.end(1)))
    for m in re.finditer(r'<' + kind + r'\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)/?>', b, re.S):
        vals = re.findall(r"""\b(?:text|title|line1)=(?:"([^"]*)"|'([^']*)')""", m.group(1))
        if any(text.startswith((x or y)[:40]) for x, y in vals) or (not vals and t0):
            am = re.search(r'\bat=\{\s*([\d.]+)\s*\}', m.group(1))
            if am and vals:
                spots.append((m.start(1) + am.start(1), m.start(1) + am.end(1)))
    return spots


def pause_after(t):
    """the first cut point >= t on a pause between words (or a sentence end)"""
    for i, w in enumerate(W[:-1]):
        if w['e'] >= t - 0.02 and (W[i + 1]['s'] - w['e'] >= 0.25 or w['w'].rstrip('"\'').endswith(('.', '?', '!'))):
            return round(max(t, (w['e'] + W[i + 1]['s']) / 2), 2)
    return None


left, fixed_early, held = {}, 0, 0
for rnd in range(4):
    errs = errors()
    if not errs:
        break
    src = parts()
    changed = False
    done = set()
    for sid, kind, text, on, cut, have, need in errs:
        on, cut, have, need = map(float, (on, cut, have, need))
        miss = need - have + 0.04
        for p, s in src.items():
            sp = scene_span(s, sid)
            if not sp or (p, sid) in done:
                continue
            b = s[sp[0]:sp[1]]
            h = HEAD.search(b)
            fr, to = float(h.group(2)), float(h.group(3))
            spots = at_spots(b, kind, text)
            ok = False
            if len(spots) == 1 and cut >= to - 0.01:
                at = float(b[spots[0][0]:spots[0][1]])
                new = round(at - miss, 2)
                lead = on - at  # how long it takes to come on
                if at - new <= MAX_EARLY and new + max(lead, 0) >= fr + 0.04 and new >= fr:
                    b = b[:spots[0][0]] + fmt(new) + b[spots[0][1]:]
                    fixed_early += 1
                    ok = True
                    print(f'{p.name} {sid}: {kind} "{text[:40]}" cued earlier, at {fmt(at)} -> {fmt(new)}')
            if not ok and cut < to - 0.01:  # it leaves on its own out=: leave later, before the next label comes on
                for m in re.finditer(r'<' + kind + r'\b((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)/?>', b, re.S):
                    om = re.search(r'\bout=\{\s*([\d.]+)\s*\}', m.group(1))
                    if om and abs(float(om.group(1)) - cut) < 0.02 and text[:20] in m.group(1):
                        own = re.search(r'\bat=\{\s*([\d.]+)', m.group(1))
                        own = float(own.group(1)) if own else cut
                        later = [float(x) for x in re.findall(r'\bat(?:=\{|:)\s*([\d.]+)', b) if float(x) > own + 0.01]
                        new = round(cut + miss, 2)
                        if new <= min([to - 0.1] + [x - 0.1 for x in later]):
                            o0, o1 = m.start(1) + om.start(1), m.start(1) + om.end(1)
                            b = b[:o0] + fmt(new) + b[o1:]
                            ok = True
                            fixed_early += 1
                            print(f'{p.name} {sid}: {kind} "{text[:40]}" leaves later, out {fmt(cut)} -> {fmt(new)}')
                        break
            if not ok and cut >= to - 0.01:
                t = pause_after(on + need)
                nxt = re.compile(r"\{id:\s*'([^']+)',\s*from:\s*" + re.escape(h.group(3)) + r",\s*to:\s*([\d.]+)").search(s, sp[1])
                if t and nxt and float(nxt.group(2)) - t >= 2.5 and t - to <= 1.5:
                    b = b[:h.start(3)] + fmt(t) + b[h.end(3):]
                    s2 = s[:sp[0]] + b + s[sp[1]:]
                    nx = re.compile(r"(\{id:\s*'" + re.escape(nxt.group(1)) + r"',\s*from:\s*)([\d.]+)").search(s2)
                    s2 = s2[:nx.start(2)] + fmt(t) + s2[nx.end(2):]
                    src[p] = s2
                    held += 1
                    done.add((p, sid))
                    changed = True
                    print(f'{p.name} {sid}: held to {fmt(t)} (was {fmt(to)}) for {kind} "{text[:40]}"; '
                          f'{nxt.group(1)} starts there')
                    break
            if ok:
                src[p] = s[:sp[0]] + b + s[sp[1]:]
                done.add((p, sid))
                changed = True
            else:
                left[(sid, text)] = f'{sid}: {kind} "{text[:50]}" needs {miss:.2f} s more (cut at {cut})'
            break
    if not changed:
        break
    if a.dry_run:
        break
    for p, s in src.items():
        p.write_text(s, encoding='utf8')
    left = {}

still = errors() if not a.dry_run else []
print(f'{fixed_early} cued earlier or left later, {held} scenes held; {len(still)} left for the editor' + (' (dry run)' if a.dry_run else ''))
for e in still:
    print(f'  {e[0]}: {e[1]} "{e[2][:50]}" ({e[5]} s to read, needs {e[6]} s)')
