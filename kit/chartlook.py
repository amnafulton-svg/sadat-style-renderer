"""Chart design per video, in turn: video 1 gets A (editorial), video 2 B (graph paper), video 3 C (bold), then A
again (producer 2026-11-19). The counter is <dest>/.chart_look_next, so every new video in one folder takes the next
design; new_chat.py and new_video.py call assign() right after copying the template. --chart-look forces one."""
from __future__ import annotations
import json
from pathlib import Path

LOOKS = 'ABC'


def assign(proj: Path, dest: Path, force: str | None = None) -> str:
    state = Path(dest) / '.chart_look_next'
    if force:
        look = force.upper()
    else:
        try:
            look = state.read_text().strip().upper()
        except OSError:
            look = 'A'
        if look not in LOOKS:
            look = 'A'
        state.write_text(LOOKS[(LOOKS.index(look) + 1) % len(LOOKS)] + '\n')
    (Path(proj) / 'src/lib/chartlook.json').write_text(json.dumps({'look': look}) + '\n', encoding='utf8')
    return look
