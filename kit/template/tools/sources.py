"""On-screen source numbers ("[17] Source in Description", top right) from the producer's sources list.

    python tools/sources.py <notion page link | sources .md/.txt/.csv> [--show]

The list is numbered claims in the order the narration makes them ([1] claim | link). Each claim is matched to the
spoken sentence that makes it (src/lib/words.json, in order, rare words and numbers weigh most) and the tag appears on
that sentence's first matching word. Writes src/lib/sources.json, which Main.tsx shows on top of every scene, plus
_work/sources_report.txt (claim -> the words it landed on, weak matches marked ??). --show prints the report.
Claims that land on the same sentence share one tag ("[17, 18]").
"""
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOLD = 3.6  # seconds a tag stays up (in + hold + out), shortened when the next tag comes sooner

STOP = set('''a an the and or but of to in on at by for with from as is was were be been are it its it's this that these
those he she his her him they them their we our you your i me my not no so than then there here what which who whom
whose when where why how all any some more most very can could would should will just only also into over under
after before about up down out off again once one two had has have did do does said says like even still each other
such own same too s t don't'''.split())
NUM = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
       'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
       'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
       'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90, 'hundred': 100}


def toks(s):
    out = []
    for w in re.findall(r"[a-z0-9]+(?:[:.,][0-9]+)*", s.lower().replace('’', "'")):
        w = w.replace(',', '')
        w = re.sub(r'(\d+)(st|nd|rd|th)$', r'\1', w)
        if w in NUM:
            w = str(NUM[w])
        if w in STOP or (len(w) < 3 and not w.isdigit()):
            continue
        if not w[0].isdigit():
            w = (w[:-1] if len(w) > 4 and w.endswith('s') else w)[:6]  # crude stem: tables/table, punctual/punctuality
        out.append(w)
    return out


def load_list(src):
    if src.startswith('http'):
        return notion(src)
    rows = []
    for line in Path(src).read_text(encoding='utf-8').splitlines():
        m = re.match(r'\s*\|?\s*\[?(\d+)\]?\s*[|.)\t,]\s*(.+)', line)
        if m:
            claim = re.split(r'\s*\|\s*|\s+https?://', m.group(2))[0]
            rows.append((int(m.group(1)), claim.strip()))
    return rows


def notion(url):
    m = re.search(r'([0-9a-f]{32})$', re.split(r'[?#]', url)[0].replace('-', ''))  # the id ends the path
    if not m:
        sys.exit('no page id in the Notion link')
    h = m.group(1)
    pid = f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}'
    host = re.match(r'https?://[^/]+', url).group(0)
    body = json.dumps({'pageId': pid, 'limit': 500, 'cursor': {'stack': []}, 'chunkNumber': 0,
                       'verticalColumns': False}).encode()
    req = urllib.request.Request(host + '/api/v3/loadPageChunk', body, {'content-type': 'application/json', 'user-agent': 'Mozilla/5.0'})
    blocks = json.load(urllib.request.urlopen(req, timeout=60))['recordMap']['block']

    def g(i):
        b = blocks.get(i, {}).get('value', {})
        return b.get('value', b)

    def text(b, key='title'):
        return ''.join(x[0] for x in b.get('properties', {}).get(key, []))

    rows = []
    for cid in g(pid).get('content', []):
        t = g(cid)
        if t.get('type') == 'table':
            cols = t['format']['table_block_column_order']
            for r in t.get('content', []):
                cells = [text(g(r), c) for c in cols]
                m = re.match(r'\[?(\d+)\]?$', cells[0].strip())
                if m and len(cells) > 1:
                    rows.append((int(m.group(1)), cells[1].strip()))
        else:  # a plain "[1] claim — link" list works too
            m = re.match(r'\s*\[?(\d+)\]?[.)\s]\s*(.+)', text(t))
            if m:
                rows.append((int(m.group(1)), re.split(r'\s+https?://', m.group(2))[0]))
    return rows


def sentences(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r'[.!?]["”’)]*$', w['w']) or len(cur) > 45:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not args:
        sys.exit(__doc__)
    claims = sorted(load_list(args[0]))
    if not claims:
        sys.exit('no numbered claims found in ' + args[0])
    words = json.loads((ROOT / 'src/lib/words.json').read_text(encoding='utf-8'))
    if not words:
        sys.exit('src/lib/words.json is empty: run tools/words.py first')
    sents = sentences(words)
    # a claim often spans two short sentences, so a sentence's neighbours count a little too (score)
    stoks = [toks(' '.join(words[i]['w'] for i in s)) for s in sents]
    df = {}
    for ts in stoks:
        for t in set(ts):
            df[t] = df.get(t, 0) + 1
    idf = lambda t: math.log((len(sents) + 1) / (df.get(t, 0) + 0.5))
    ctoks = [toks(c) for _, c in claims]

    def score(ci, sj):
        have = set(stoks[sj])
        near = {t for k in (sj - 1, sj + 1) if 0 <= k < len(sents) for t in stoks[k]}
        s = 0.0
        for t in set(ctoks[ci]):
            if t in have:
                s += idf(t)
            elif t in near:
                s += 0.35 * idf(t)
        return s

    # monotonic alignment: claim order = narration order; several claims may share a sentence
    n, m = len(claims), len(sents)
    sc = [[score(i, j) for j in range(m)] for i in range(n)]
    best = [[0.0] * m for _ in range(n)]
    back = [[0] * m for _ in range(n)]
    for i in range(n):
        run, arg = -1e9, 0
        for j in range(m):
            if i == 0:
                prev, pj = 0.0, 0
            else:
                if best[i - 1][j] > run:
                    run, arg = best[i - 1][j], j
                prev, pj = run, arg
            best[i][j] = sc[i][j] + prev
            back[i][j] = pj
    j = max(range(m), key=lambda k: best[n - 1][k])
    pick = [0] * n
    for i in range(n - 1, -1, -1):
        pick[i] = j
        j = back[i][j]

    # the list is only roughly in narration order ([56] Ugaki's cry came after [57] the Betty's armour): a clearly
    # better sentence close to the in-order pick wins
    for i in range(n):
        lo, hi = max(0, pick[i] - 10), min(m, pick[i] + 11)
        j = max(range(lo, hi), key=lambda k: sc[i][k])
        if sc[i][j] > 1.5 * sc[i][pick[i]] + 1.0:
            pick[i] = j

    report, tags = [], []
    for i, (num, claim) in sorted(enumerate(claims), key=lambda x: (pick[x[0]], x[1][0])):
        s = sents[pick[i]]
        want = {t for t in ctoks[i] if idf(t) > 1.0}
        at = words[s[0]]['s']
        for wi in s:  # the first rare claim word said in that sentence
            if set(toks(words[wi]['w'])) & want:
                at = words[wi]['s']
                break
        top = sum(sorted((idf(t) for t in set(ctoks[i])), reverse=True)[:4]) or 1
        weak = sc[i][pick[i]] < 0.35 * top
        report.append(f"{'??' if weak else '  '} [{num}] {at:7.1f}s  {claim[:70]}\n"
                      f"            -> {' '.join(words[k]['w'] for k in s)[:150]}")
        if tags and pick[i] == tags[-1]['sent']:
            tags[-1]['n'].append(num)
        else:
            tags.append({'n': [num], 'at': round(at, 2), 'sent': pick[i]})
    for a, b in zip(tags, tags[1:]):
        if b['at'] - a['at'] < 1.2:  # two sentences in a breath: one tag
            b['n'] = a['n'] + b['n']
            b['at'] = a['at']
            a['n'] = []
    tags = [t for t in tags if t['n']]
    out = []
    for k, t in enumerate(tags):
        nxt = tags[k + 1]['at'] if k + 1 < len(tags) else 1e9
        out.append({'n': t['n'], 'from': t['at'], 'to': round(min(t['at'] + HOLD, nxt - 0.15), 2)})
    (ROOT / 'src/lib/sources.json').write_text(json.dumps(out))
    (ROOT / '_work').mkdir(exist_ok=True)
    rep = '\n'.join(report)
    (ROOT / '_work/sources_report.txt').write_text(rep + '\n', encoding='utf-8')
    weak = rep.count('??')
    print(f'{len(claims)} claims -> {len(out)} tags in src/lib/sources.json; {weak} weak matches (?? in '
          f'_work/sources_report.txt)')
    if '--show' in sys.argv:
        print(rep)


if __name__ == '__main__':
    main()
