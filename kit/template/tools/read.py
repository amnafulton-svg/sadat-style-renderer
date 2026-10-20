"""The editor's reader: a Haiku helper reads long text and answers with only what the editor asked for.

    python tools/read.py "<question>" <file> [<file> ...]
    <command> | python tools/read.py "<question>"

Long outputs (JSON, logs, transcripts, search results, loop output, example code) stay in the editing session's
context and are paid for again on every later turn (2026-10-17 measure: ~20% of a video's cost). This sends the
text to a separate headless Claude (Haiku) and prints its short answer. Short text (< 4000 chars) is printed as is.
Read exact lines directly (sed -n) only when you are about to edit them. Logged to _work/read_log.jsonl.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

MODEL = "claude-haiku-5-5"
SHORT = 4000
CHUNK = 350_000  # chars per Haiku call

RULES = """You read text for a documentary editor and answer their question. The editor sees only your answer.
- Answer only what was asked, as short as possible: exact values, file names, seconds, ids, line numbers.
- Quote the relevant lines exactly (with their line number or key) when the editor will act on them.
- If the text does not contain the answer, say so plainly. Never guess or invent.
- No intro, no summary of the rest."""



def account_env():
    """The environment for the helper's claude call. On the producer's server it uses the Claude account picked on the
    Videos page (claude_accounts.py), like the chat itself: the chat's account token does not reach tool shells, so
    the helpers used the server's own login instead (account 1, weekly-limited 2026-10-19: every look.py call answered
    UNSURE while the chats ran on account 2). Anywhere else: the environment as it is."""
    env = dict(os.environ)
    acc = Path.home() / "yt" / "archive-remotion-factory" / "claude_accounts.py"
    if acc.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("claude_accounts", acc)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            env = mod.env(env, mod.active() or mod.accounts()[0])
        except Exception:  # noqa: BLE001 - a broken switch must never stop the helper
            pass
    return env

def ask(question, text):
    claude = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    prompt = f"{RULES}\n\nQuestion: {question}\n\n<text>\n{text}\n</text>"
    cmd = [claude, "-p", "--model", MODEL, "--output-format", "json", "--tools", ""]
    err = ""
    for _ in range(2):
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600,
                           env=account_env())
        try:
            out = json.loads(r.stdout)
            if not out.get("is_error") and out.get("result", "").strip():
                return out["result"].strip(), out.get("total_cost_usd") or 0
            err = out.get("result", "")
        except ValueError:
            err = r.stderr or r.stdout
    return f"read.py failed ({err.strip()[:300]}): read the text directly with head/sed -n", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    if a.files:
        parts = []
        for f in a.files:
            p = Path(f)
            if not p.is_file():
                sys.exit(f"not found: {f}")
            lines = p.read_text(errors="replace").splitlines()
            parts.append(f"=== {f} ===\n" + "\n".join(f"{i + 1}: {l}" for i, l in enumerate(lines)))
        text = "\n\n".join(parts)
    else:
        text = sys.stdin.read()
    if len(text) < SHORT:
        print(text)
        return
    t0 = time.time()
    chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]
    usd = 0
    for i, c in enumerate(chunks):
        ans, cost = ask(a.question + (f" (part {i + 1} of {len(chunks)})" if len(chunks) > 1 else ""), c)
        usd += cost
        print(ans)
    try:
        log = Path.cwd() / "_work" / "read_log.jsonl"
        log.parent.mkdir(exist_ok=True)
        with log.open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "chars": len(text), "usd": round(usd, 4),
                                "sec": round(time.time() - t0, 1), "q": a.question[:120]}) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
