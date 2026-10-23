"""The editor's free chore runner: several source commands in ONE call, run side by side, short answer.

    python tools/batch.py "python tools/source.py commons 'James Watt portrait' s5_watt" "python tools/source.py ia-search 'beam engine'" ...
    (or one command per line on stdin)

Every editor turn re-sends its whole chat, so ten small steps cost ten re-reads. Put a whole chore's commands here
in one call instead: searches, ia-files, downloads, sheets, facts. Only `python tools/source.py`, `python tools/sheets.py`
and `python tools/facts.py` commands run. Lines naming media another section already logged in _work/used.tsv
are marked [USED sN]; rights-reserved archive.org results are dropped. No model, costs nothing.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ALLOWED = ("tools/source.py", "tools/sheets.py", "tools/facts.py")
MAX_LINES = 25
ROOT = Path.cwd()


def used_index():
    idx = []
    try:
        for line in (ROOT / "_work" / "used.tsv").read_text(encoding="utf8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 2:
                idx.append((parts[0], parts[1]))
    except OSError:
        pass
    return idx


def mark(line, idx):
    words = [w for w in re.findall(r"[\w.\-()&',]{8,}", line)]
    for sec, src in idx:
        for w in words:
            if w in src:
                return f"{line}  [USED {sec}]"
    return line


def run(cmd, idx):
    argv = shlex.split(cmd)
    if argv and argv[0] in ("python", "python3"):
        argv = argv[1:]
    if not argv or argv[0] not in ALLOWED:
        return cmd, f"refused: only {', '.join(ALLOWED)} commands", 0
    env = dict(os.environ, PATH=f"{ROOT / '_work' / 'bin'}:{os.environ.get('PATH', '')}")
    t0 = time.time()
    try:
        r = subprocess.run(["python", *argv], cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=300)
        out = (r.stdout + ("\n" + r.stderr.strip().splitlines()[-1] if r.returncode and r.stderr.strip() else "")).strip()
    except subprocess.TimeoutExpired:
        out = "timed out after 300 s"
    lines, dropped = [], 0
    for line in out.splitlines():
        if "ALL RIGHTS RESERVED" in line:
            dropped += 1
            continue
        lines.append(mark(line, idx))
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"... {len(lines) - MAX_LINES} more lines"]
    if dropped:
        lines.append(f"({dropped} rights-reserved results dropped)")
    return cmd, "\n".join(lines) or "(no output)", time.time() - t0


def main():
    cmds = [c for c in sys.argv[1:] if c.strip()] or [l.strip() for l in sys.stdin if l.strip()]
    if not cmds:
        sys.exit(__doc__)
    idx = used_index()
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(lambda c: run(c, idx), cmds))
    for cmd, out, _ in results:
        print(f"## {cmd}\n{out}")
    try:
        with (ROOT / "_work" / "batch_log.jsonl").open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "n": len(cmds),
                                "sec": round(time.time() - t0, 1), "cmds": [c[:150] for c in cmds]}) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
