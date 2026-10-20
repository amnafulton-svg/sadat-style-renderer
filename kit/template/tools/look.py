"""The editor's eyes: a Sonnet helper looks at images and answers in one line per image (or per tile).

    python tools/look.py "<what to judge>" <image> [<image> ...] [--note "<context, e.g. the narration lines>"]

Opening sheets and stills in the editing session keeps every picture in its context, and every later turn pays to
read it again (2026-10-17 measure: images = ~41% of a video's cost). This runs a separate headless Claude (Sonnet)
that looks once and prints short verdicts; the editor reads only those lines. Batches of 6 images, 3 at a time.
Every call is logged to _work/look_log.jsonl (images, seconds, $).

Lean session (2026-10-17): the helper gets its own short system prompt, only the Read tool, and no settings, MCP,
skills or hooks. Claude Code's default system prompt + tool list cost ~21k cache-write tokens per call (bunker video:
440 calls = 9.2M tokens, $46) and says nothing about judging pictures; verdicts were compared side by side on the
bunker sheets before the switch.
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

MODEL = "claude-sonnet-5-5"
BATCH = 6

SYSTEM = ("You check images for a documentary editor. You have one tool, Read, which opens an image file. Open "
          "every image you are given before answering; never answer from file names. Follow the answer format in the "
          "message exactly: one short line per image, and for contact sheets one line per tile range.")

RULES = """You are the eyes of a documentary editor who cannot see images. Open every image listed below with the Read
tool, then answer the editor's question for each one. The editor acts on your words alone, so be exact.

Answer format, nothing else (no intro, no summary):
- One line per image, starting with its file name: `<name>: <verdict>`.
- For a contact sheet (a grid of numbered or timed tiles), one line per usable or problem tile/range, e.g.
  `<name> t12-18: clean, steam train leaving a station, 1920s, fits "the railways carried coal"`.
- Say what is actually shown (subject, era, framing), then the verdict. Keep each line under ~30 words.
- Flag problems plainly: watermark, stock-site or TV logo, burned-in timecode, title card, black/blank/blurry,
  AI-made look, modern people/reenactment/actors, wrong era for the line, clipped or colliding text, unreadable label,
  4:3 film stretched or zoomed instead of padded.
- Real period photos and scans naturally contain printed text, captions and signs: that is fine, not a flaw.
- If you are not sure (small, ambiguous, could be either), write `UNSURE:` and why, so the editor looks itself.
  Never guess a pass."""



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


def claude_bin():
    return shutil.which("claude") or str(Path.home() / ".local/bin/claude")


def ask(question, note, imgs, cwd):
    prompt = (f"{RULES}\n\nEditor's question: {question}\n"
              + (f"\nContext from the editor:\n{note}\n" if note else "")
              + "\nImages:\n" + "\n".join(str(p) for p in imgs))
    cmd = [claude_bin(), "-p", "--model", MODEL, "--output-format", "json", "--permission-mode", "default",
           "--system-prompt", SYSTEM, "--tools", "Read", "--allowedTools", "Read", "--setting-sources", "",
           "--strict-mcp-config", "--disable-slash-commands", "--add-dir", str(cwd)]
    for d in {p.parent for p in imgs}:
        cmd += ["--add-dir", str(d)]
    t0 = time.time()
    for attempt in range(2):
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd, timeout=900,
                           env=account_env())
        try:
            out = json.loads(r.stdout)
            if not out.get("is_error") and out.get("result", "").strip():
                return out["result"].strip(), out.get("total_cost_usd") or 0, time.time() - t0
        except ValueError:
            out = {}
        err = (out.get("result") or r.stderr or r.stdout or "").strip()[:300]
    return "\n".join(f"{p.name}: UNSURE: checker failed ({err}) - open it yourself" for p in imgs), 0, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    cwd = Path.cwd()
    imgs = [Path(p).resolve() for p in a.images]
    missing = [str(p) for p in imgs if not p.is_file()]
    if missing:
        sys.exit("not found: " + ", ".join(missing))
    batches = [imgs[i:i + BATCH] for i in range(0, len(imgs), BATCH)]
    with cf.ThreadPoolExecutor(3) as ex:
        results = list(ex.map(lambda b: ask(a.question, a.note, b, cwd), batches))
    for text, _, _ in results:
        print(text)
    usd = sum(r[1] for r in results)
    log = cwd / "_work" / "look_log.jsonl"
    try:
        log.parent.mkdir(exist_ok=True)
        with log.open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "images": len(imgs), "usd": round(usd, 4),
                                "sec": round(max(r[2] for r in results), 1), "q": a.question[:120]}) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
