"""Free fact sheet for a section editor (no model): the sentences spoken in a time range, with the safe cut points.

    python tools/facts.py <from> <to>

Prints one line per sentence: start-end, the gap to the next word, the text, and marks gaps >= 0.3 s as CUT.
Run it once per section instead of grepping/awking _work/sentences.md or transcript.txt line by line.
"""
import json
import re
import sys
from pathlib import Path


def sentences():
    """_work/sentences.md, made from src/lib/words.json the first time (a sentence ends on . ? or !)."""
    out = Path("_work/sentences.md")
    if not out.exists():
        words = json.loads(Path("src/lib/words.json").read_text())
        rows, cur = [], []
        for i, w in enumerate(words):
            cur.append(w)
            if re.search(r"[.?!][\"')\]]*$", w["w"]) or i == len(words) - 1:
                nxt = words[i + 1]["s"] - w["e"] if i + 1 < len(words) else 0.0
                rows.append(f"{cur[0]['s']:8.2f}-{w['e']:8.2f} (next +{max(nxt, 0):.2f}) "
                            + " ".join(x["w"] for x in cur))
                cur = []
        out.parent.mkdir(exist_ok=True)
        out.write_text("# sentences: start-end (gap to next word)\n" + "\n".join(rows) + "\n")
    return out.read_text().splitlines()


lo, hi = float(sys.argv[1]), float(sys.argv[2])
rx = re.compile(r"\s*([\d.]+)-\s*([\d.]+) \(next \+([\d.]+)\) (.*)")
print(f"# sentences {lo}-{hi} (CUT = sentence end with >= 0.3 s pause: a picture may change there)")
for line in sentences():
    m = rx.match(line)
    if not m:
        continue
    a, b, gap, text = float(m[1]), float(m[2]), float(m[3]), m[4]
    if b < lo - 0.01 or a > hi + 0.01:
        continue
    print(f"{a:7.2f}-{b:7.2f} {'CUT' if gap >= 0.3 else '   '} +{gap:.2f} {text}")
