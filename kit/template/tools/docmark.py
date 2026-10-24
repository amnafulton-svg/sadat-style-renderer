"""Where the printed words are on a document scan (OCR), so a DocCard mark sits exactly on them.

    python tools/docmark.py <doc>                  numbered OCR lines with their boxes
    python tools/docmark.py <doc> "the words"      the rects of those words -> paste as the mark's lines: [...]
    python tools/docmark.py <doc> --rows 3-6       the rects of whole lines 3 to 6

<doc> is a file in public/docs (name or path). Rects are [x0, y0, x1, y1] fractions of the scan, one per printed line:
    marks={[{lines: [[0.12, 0.31, 0.88, 0.36], [0.12, 0.37, 0.64, 0.42]], at: 478.9, until: 480.4}]}
Never guess a mark box by eye (Chipyong-ni 2026-10-25: two plaque marks sat beside the text); validate.py checks every
mark against this OCR. OCR runs in ~/yt/.venv-ocr (RapidOCR) and is cached in _cache/ocr/.
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_PY = Path.home() / 'yt/.venv-ocr/bin/python'
WORKER = Path(__file__).resolve().parent / 'ocr_worker.py'


# reading order: by the line's centre height (bins split tight lines out of order), then left to right
BY_ROW = lambda ln: (round((ln['box'][1] + ln['box'][3]) * 50), ln['box'][0])


def ocr(root, name):
    """{'w', 'h', 'lines': [{'text', 'box' (fractions), 'words': [{'text', 'box'}]}]} or None when OCR is unavailable"""
    p = Path(name)
    if not p.is_file():
        p = Path(root) / 'public/docs' / Path(name).name
    if not p.is_file():
        return None
    cache = Path(root) / '_cache/ocr' / (p.stem + '.json')
    st = p.stat()
    key = f'{st.st_size}:{int(st.st_mtime)}'
    if cache.is_file():
        d = json.loads(cache.read_text(encoding='utf8'))
        if d.get('key') == key:
            d['lines'].sort(key=BY_ROW)
            return d
    if not OCR_PY.is_file():
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    raw = cache.with_suffix('.raw.json')
    r = subprocess.run([str(OCR_PY), str(WORKER), str(p), str(raw)], capture_output=True, text=True)
    if r.returncode or not raw.is_file():
        print(r.stderr[-800:], file=sys.stderr)
        return None
    d = json.loads(raw.read_text(encoding='utf8'))
    raw.unlink()
    W, H = d['w'], d['h']
    fr = lambda b: [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]
    lines = [{'text': ln['text'], 'box': fr(ln['box']), 'words': [{'text': w['text'], 'box': fr(w['box'])} for w in ln['words']]}
             for ln in d['lines'] if ln['score'] >= 0.5 and ln['text'].strip()]
    lines.sort(key=BY_ROW)
    out = {'key': key, 'w': W, 'h': H, 'lines': lines}
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding='utf8')
    return out


norm = lambda t: re.sub(r'[^\w]', '', t.lower())


def tokens(d):
    """(line no, text, box) per word; a line without word boxes is split by character count"""
    out = []
    for i, ln in enumerate(d['lines']):
        ws = [w for w in ln['words'] if norm(w['text'])]
        # RapidOCR gives Latin words or single CJK characters; rebuild words from the line text when they disagree
        if not ws or len(ws) > len(ln['text']):
            x0, y0, x1, y1 = ln['box']
            parts = ln['text'].split() or [ln['text']]
            n, pos = sum(len(p) + 1 for p in parts), 0
            ws = []
            for p in parts:
                ws.append({'text': p, 'box': [x0 + (x1 - x0) * pos / n, y0, x0 + (x1 - x0) * (pos + len(p)) / n, y1]})
                pos += len(p) + 1
        out += [(i, w['text'], w['box']) for w in ws]
    return out


def pad(b, d):
    """a little air around the printed letters (an eighth of the line height), never into the line above or below"""
    lh = b[3] - b[1]
    h = lh * 0.12
    wx = h * d['h'] / d['w']
    y0, y1 = b[1] - h, b[3] + h
    for ln in d['lines']:
        o = ln['box']
        if min(b[2], o[2]) - max(b[0], o[0]) <= 0:
            continue
        # a neighbouring line: stop at it, or halfway into the overlap when tall tight type makes the boxes overlap
        if o[1] < b[1] and o[3] <= b[1] + 0.5 * lh:
            y0 = max(y0, o[3] if o[3] <= b[1] else (o[3] + b[1]) / 2)
        if o[3] > b[3] and o[1] >= b[3] - 0.5 * lh:
            y1 = min(y1, o[1] if o[1] >= b[3] else (o[1] + b[3]) / 2)
    return [round(max(0, b[0] - wx), 3), round(max(0, y0), 3), round(min(1, b[2] + wx), 3), round(min(1, y1), 3)]


def find(d, phrase):
    """(score, rects per line, matched text) of the best run of OCR words for phrase"""
    toks = tokens(d)
    want = norm(phrase)
    n = max(1, len(phrase.split()))
    best = (0, [], '')
    for i in range(len(toks)):
        for k in range(max(1, n - 2), n + 3):
            run = toks[i:i + k]
            if len(run) < k:
                break
            got = ''.join(norm(t[1]) for t in run)
            sc = difflib.SequenceMatcher(None, want, got).ratio()
            if sc > best[0]:
                by = {}
                for ln, _, b in run:
                    r = by.setdefault(ln, list(b))
                    r[0], r[1], r[2], r[3] = min(r[0], b[0]), min(r[1], b[1]), max(r[2], b[2]), max(r[3], b[3])
                best = (sc, [pad(by[ln], d) for ln in sorted(by)], ' '.join(t[1] for t in run))
    return best


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = ocr(ROOT, sys.argv[1])
    if d is None:
        sys.exit(f'no OCR for {sys.argv[1]} (file missing or ~/yt/.venv-ocr not installed)')
    if not d['lines']:
        sys.exit('OCR found no printed text on this scan: do not mark it (pick a scan whose words are legible)')
    if len(sys.argv) == 2:
        for i, ln in enumerate(d['lines'], 1):
            print(f'{i:3}  {ln["box"]}  {ln["text"]}')
    elif sys.argv[2] == '--rows':
        a, _, b = sys.argv[3].partition('-')
        rows = d['lines'][int(a) - 1:int(b or a)]
        print('lines: ' + json.dumps([pad(ln['box'], d) for ln in rows]))
        for ln in rows:
            print('   ', ln['text'])
    else:
        sc, rects, got = find(d, ' '.join(sys.argv[2:]))
        print(f'match {sc:.2f}: {got}')
        if sc < 0.6:
            print('weak match: check the numbered lines (no phrase) and use --rows')
        print('lines: ' + json.dumps(rects))
