"""PostToolUse hook: keeps section editors (subagents) short so they don't re-read a huge context on every turn.

Counts tool calls per subagent (agent_id) in _work/turns/. At SOFT calls it tells the editor to wrap up and write
its hand-off; from HARD on it repeats that every 5 calls. The main chat then starts a fresh editor that reads the
hand-off (SKILL.md, section editors). 2026-10-17 measure: one coal section editor ran 264 turns = 74M cache reads.
The main chat (no agent_id) is not counted.
2026-10-22 phases test: Pick editors reached 160-200k in ~65 calls, so the call count alone came too late. The guard
also reads the agent's real chat size (last usage in its transcript) and hands off at CTX_SOFT tokens: a fresh agent
starts at ~15k and reads the phase file, which is far cheaper than re-sending 200k on every step.
"""
import json
import os
import sys
from pathlib import Path

SOFT = int(os.environ.get("TURN_GUARD_SOFT", 80))
HARD = int(os.environ.get("TURN_GUARD_HARD", 100))
CTX_SOFT = int(os.environ.get("TURN_GUARD_CTX_SOFT", 100_000))
CTX_HARD = int(os.environ.get("TURN_GUARD_CTX_HARD", 125_000))


def chat_size(d, agent):
    """Tokens in the agent's chat at its last step (input + cache read + cache write), 0 if unknown."""
    tp = d.get("agent_transcript_path") or ""
    if not tp:
        main = d.get("transcript_path") or ""
        tp = main[:-6] + f"/subagents/agent-{agent}.jsonl" if main.endswith(".jsonl") else ""
    try:
        with open(tp, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            lines = f.read().decode("utf8", "replace").splitlines()
    except OSError:
        return 0
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            u = json.loads(line)["message"]["usage"]
        except (ValueError, KeyError, TypeError):
            continue
        return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return 0


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
    size = chat_size(d, agent)
    mark = folder / (agent + ".ctx")
    if size >= CTX_SOFT and not mark.exists():
        mark.write_text(str(n))
        msg = (f"[turn guard] Your chat is {size // 1000}k tokens and every step re-sends all of it. Finish only the "
               "step in hand, then write your hand-off to your phase file (_parts/<your section>/picks.md, build.md or "
               "HANDOFF.md): what is done and where (files, clip in-points, picks), what is left in order, open "
               "problems. Then end with your result plus the line `HANDOFF: <that file>`. A fresh agent for the same "
               "phase will carry on from it.")
    elif size >= CTX_HARD and n % 3 == 0:
        msg = (f"[turn guard] Chat {size // 1000}k tokens. Stop now: write your phase file and end your turn with "
               "`HANDOFF: <that file>`. Do not start anything new.")
    elif n == SOFT:
        msg = (f"[turn guard] You have made {n} tool calls. Your context is getting expensive to re-read. Finish only "
               "the step in hand, then write your hand-off to your phase file (_parts/<your section>/picks.md, build.md or HANDOFF.md): what is done and where "
               "(files, clip in-points, picks), what is left in order, open problems. Then end with your result plus "
               "the line `HANDOFF: <that file>`. A fresh agent for the same phase will carry on from it.")
    elif n >= HARD and (n - HARD) % 5 == 0:
        msg = (f"[turn guard] {n} tool calls. Stop now: write your phase file and end your turn with "
               "`HANDOFF: <that file>`. Do not start anything new.")
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    main()
