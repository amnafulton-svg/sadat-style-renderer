"""PostToolUse hook: keeps section editors (subagents) short so they don't re-read a huge context on every turn.

Counts tool calls per subagent (agent_id) in _work/turns/. At SOFT calls it tells the editor to wrap up and write
its hand-off; from HARD on it repeats that every 5 calls. The main chat then starts a fresh editor that reads the
hand-off (SKILL.md, section editors). 2026-10-17 measure: one coal section editor ran 264 turns = 74M cache reads.
The main chat (no agent_id) is not counted.
"""
import json
import os
import sys
from pathlib import Path

SOFT = int(os.environ.get("TURN_GUARD_SOFT", 80))
HARD = int(os.environ.get("TURN_GUARD_HARD", 100))


def main():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return
    agent = d.get("agent_id")
    if not agent:
        return
    folder = Path(d.get("cwd") or ".") / "_work" / "turns"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        f = folder / agent
        n = int(f.read_text() or 0) + 1 if f.exists() else 1
        f.write_text(str(n))
    except (OSError, ValueError):
        return
    msg = None
    if n == SOFT:
        msg = (f"[turn guard] You have made {n} tool calls. Your context is getting expensive to re-read. Finish only "
               "the step in hand, then write your hand-off to _parts/<your section>/HANDOFF.md: what is done and where "
               "(files, clip in-points, picks), what is left in order, open problems. Then end with your result plus "
               "the line `HANDOFF: _parts/<your section>/HANDOFF.md`. A fresh editor will carry on from it.")
    elif n >= HARD and (n - HARD) % 5 == 0:
        msg = (f"[turn guard] {n} tool calls. Stop now: write _parts/<your section>/HANDOFF.md and end your turn with "
               "`HANDOFF: _parts/<your section>/HANDOFF.md`. Do not start anything new.")
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    main()
