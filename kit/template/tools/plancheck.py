"""The beat plan of a one-chat video (plan.md) against the cut and the searches (called by validate.py).

The zniti test (2026-10-26): the section workflow planned every sentence first and searched archive.org per line, and
found far better film; the one chat skipped the plan, searched a third as much and filled filmed moments with photos.
So a one-chat project (it has a `.onechat` file, written by kit/new_chat.py) must have plan.md:

    | # | Time | Line | Plane | Source ideas |
    | 1 | 0.00-6.42 | In 1944 the convoy left Murmansk ... | film | Arctic convoy 1944 newsreel; PQ-17 ships ice |
    | 7 | 41.10-47.80 | ... | film | no film: Kola inlet 1944; Murmansk harbour newsreel; Soviet port film |

one row per sentence (or spoken list), Time in seconds from `python tools/facts.py 0 99999`. Plane: film, named,
geography, document, numbers, list or argument. ERROR when:
  - plan.md is missing, or a spoken sentence falls in no row,
  - a film row shows film for under half of its time, unless its Source ideas say `no film: q1; q2; q3` and those
    3+ queries are in _work/searches.tsv (tools/source.py logs every search), at least one of them on archive.org,
  - archive.org was searched fewer times than once per 20 s of narration.
"""
import re
from pathlib import Path

PLANES = ('film', 'named', 'geography', 'document', 'numbers', 'list', 'argument')


def _sec(t):
    t = t.strip()
    if ':' in t:
        m, s = t.split(':', 1)
        return 60 * float(m) + float(s)
    return float(t)


def rows(text):
    """(row text, from, to, plane, source ideas) for every table row with a time range"""
    out = []
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if len(cells) < 5:
            continue
        m = re.fullmatch(r'([\d:.]+)\s*[-–]\s*([\d:.]+)', cells[1])
        if not m:
            continue
        try:
            a, b = _sec(m.group(1)), _sec(m.group(2))
        except ValueError:
            continue
        out.append((cells[0], a, b, cells[3].lower(), cells[4]))
    return out


def sentences(W):
    """(start, end, text) per sentence: a sentence ends on . ? or ! (as facts.py splits them)"""
    out, cur = [], []
    for i, w in enumerate(W):
        cur.append(w)
        if re.search(r"[.?!][\"')\]]*$", w['w']) or i == len(W) - 1:
            out.append((cur[0]['s'], w['e'], ' '.join(x['w'] for x in cur)))
            cur = []
    return out


def searches(root):
    """(kind, normalised query) per logged search"""
    p = root / '_work' / 'searches.tsv'
    out = []
    if p.exists():
        for ln in p.read_text(encoding='utf8').splitlines():
            f = ln.split('\t')
            if len(f) >= 3:
                out.append((f[1], _norm(f[2])))
    return out


def _norm(q):
    return ' '.join(re.sub(r'[^\w\s]', ' ', q.lower()).split())


def check(root, scenes, W):
    """ERROR lines for the plan (empty when the project is not a one-chat project)"""
    root = Path(root)
    if not (root / '.onechat').exists():
        return []
    errs = []
    plan = root / 'plan.md'
    if not plan.exists():
        return ['plan.md is missing: write the beat table (one row per sentence) before searching (see CLAUDE.md)']
    R = rows(plan.read_text(encoding='utf8'))
    if not R:
        return ['plan.md has no beat rows ("| # | Time | Line | Plane | Source ideas |", Time like 12.40-18.90)']
    miss = [(a, t) for a, b, t in sentences(W) if not any(ra - 0.3 <= (a + b) / 2 <= rb + 0.3 for _, ra, rb, _, _ in R)]
    for a, t in miss[:8]:
        errs.append(f'plan.md: no row for the sentence at {a:.2f} "{t[:70]}"')
    if len(miss) > 8:
        errs.append(f'plan.md: {len(miss) - 8} more sentences with no row')
    for n, a, b, plane, ideas in R:
        if not any(p in plane for p in PLANES):  # "filmed" is film; a film row is one whose plane starts with film
            errs.append(f'plan.md row {n}: plane "{plane}" is not one of {", ".join(PLANES)}')
    S = searches(root)
    logged = {q for _, q in S}
    archive = {q for k, q in S if k == 'archive'}
    film = [(fr, to) for sid, fr, to, en, blk in scenes if '<F src=' in blk]
    for n, a, b, plane, ideas in R:
        if not plane.startswith('film') or b - a < 0.5:
            continue
        shown = sum(max(0.0, min(b, to) - max(a, fr)) for fr, to in film)
        if shown >= 0.5 * (b - a):
            continue
        m = re.search(r'no film:\s*(.*)', ideas, re.I)
        qs = [_norm(q) for q in re.split(r'[;,]', m.group(1)) if q.strip()] if m else []
        done = [q for q in qs if q in logged]
        if not m:
            errs.append(f'plan.md row {n} ({a:.2f}-{b:.2f}) is a film line but the cut shows film for '
                        f'{shown:.1f} of {b - a:.1f} s: put film there, or write "no film: q1; q2; q3" with the searches '
                        f'that found nothing')
        elif len(done) < 3 or not any(q in archive for q in done):
            errs.append(f'plan.md row {n} ({a:.2f}-{b:.2f}): "no film" needs 3+ searches run through tools/source.py '
                        f'(at least one ia-search on archive.org); found {len(done)} of them in _work/searches.tsv'
                        + ('' if any(q in archive for q in done) else ', none on archive.org'))
    narration = W[-1]['e'] if W else 0
    need = int(narration // 20)
    if len(archive) < need:
        errs.append(f'only {len(archive)} different archive.org searches for {narration / 60:.1f} min of narration '
                    f'(at least {need}: one per 20 s; search archive.org first for every film line)')
    return errs
