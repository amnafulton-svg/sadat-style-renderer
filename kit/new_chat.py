"""Start a new Sadat-style video made by ONE Claude Code chat (the england-plain way), not the section workflow.

    python kit/new_chat.py <name> <script.md|.txt> <voice-over.mp3|.wav|.m4a> [--dest DIR] [--no-install] [--no-words] [--launch]

Creates <dest>/<name>/ (default dest: ~/sadat-chat) from kit/template with only the plain tools (no look.py, read.py,
batch.py, board.py, facts.py, turn_guard.py: those start helper sessions, which is what ate the weekly limit) and no
skill. CLAUDE.md is the whole brief: the tools, the lessons from the england-plain test (2026-10-24) and when it is done.
--launch opens the chat in tmux session <name> on Opus 5.5; without it the last line prints the command.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
REPO = KIT.parent
HELPERS = ('look.py', 'read.py', 'batch.py', 'board.py', 'facts.py', 'turn_guard.py')
PY = Path.home() / 'yt/.venv/bin/python'  # system python3 has no PIL
ap = argparse.ArgumentParser()
ap.add_argument('name')
ap.add_argument('script')
ap.add_argument('voice')
ap.add_argument('--dest', default=str(Path.home() / 'sadat-chat'))
ap.add_argument('--no-install', action='store_true')
ap.add_argument('--no-words', action='store_true')
ap.add_argument('--launch', action='store_true', help='start the chat in tmux (Opus 5.5, auto permissions)')
a = ap.parse_args()

name = re.sub(r'[^A-Za-z0-9_-]+', '-', a.name).strip('-').lower()
proj = Path(a.dest).resolve() / name
script, voice = Path(a.script).resolve(), Path(a.voice).resolve()
for f in (script, voice):
    if not f.is_file():
        sys.exit(f'not found: {f}')
if proj.exists():
    sys.exit(f'{proj} already exists (pick another name or delete it)')

shutil.copytree(KIT / 'template', proj, ignore=shutil.ignore_patterns(
    'node_modules', '_cache', '_stills', '_sheets', '_review', '__pycache__', *HELPERS))
shutil.copy2(script, proj / 'script.md')
narr = proj / 'public/audio/narration.mp3'
if voice.suffix.lower() == '.mp3':
    shutil.copy2(voice, narr)
else:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(voice), '-c:a', 'libmp3lame', '-b:a', '192k', str(narr)], check=True)

(proj / 'CLAUDE.md').write_text(f'''# {name}

A Sadat-style documentary built in Remotion from this folder, by you, in this one chat.

- Script: `script.md`. Voice-over: `public/audio/narration.mp3` (the timeline is the voice-over). Word timings:
  `src/lib/words.json` + `transcript.txt` (made by tools/words.py).
- The look is fixed by the components in `src/` (layers, overlays, transitions, vendor charts and maps) and the rules
  in `EDITING_RULES.md`: read both first. `examples/` shows how a timeline is written. The cut goes in
  `src/timeline/` (video.tsx, sections in `src/timeline/parts/s1.tsx, s2.tsx ...`).
- Composition `Documentary`, 1920x1080, 25 fps.
- Do not use any skill and do not read or run anything from ~/sadat-style-renderer, ~/sadat or ~/classic-studio.

## Tools (run Python as `{PY}`; each script's top lines say how to use it)
- `tools/source.py`: archive.org search/files/download, Wikimedia Commons images and video, Google Images (Serper),
  contact sheets of films. Commons is searched first; when it finds under 2 images, or Wikimedia rate-limits this
  machine, it switches to Serper by itself. Do not write your own downloaders or hammer upload.wikimedia.org.
- `tools/cut.py`: cut a clip from a source film. `tools/media.py`: list what is in public/ (sizes, lengths).
- `tools/words.py`: word timings. `tools/sheets.py <dir>`: review sheets of every clip, photo and doc in public/.
- `node tools/stills.mjs <dir> t1 t2 ...`: render single frames of the cut to look at.
- `tools/validate.py`: the rule check. `tools/repeats.py` (called by validate): same shot/photo twice, blank film.
- `tools/mapres.py`, `tools/make_textures.py`: map sharpness, paper/wall textures.
- `tools/docmark.py <doc> "phrase"`: OCR the scan and print the exact `lines:` rects for a mark on those words
  (`--rows a-b` for whole lines, no phrase to list every line).

## Lessons from the last chat-made video (england-plain, 2026-10-24): do not repeat these
1. **The exact place.** A line about Raglan shows Raglan, not another castle; Denbigh, Caerphilly, Rhuddlan each
   get their own picture or none. Check every place picture against its file title on a sheet.
2. **The right era.** No Victorian or modern buildings, cars, cranes, glass offices or modern photos of a building
   under lines about an earlier century (a 1970s archive building under "county committees" in the 1640s,
   Goldsmiths' Hall with parked cars). Use period paintings, engravings, maps and documents instead.
3. **The right person.** A name tag or person card goes only on a picture of that person (or their arms/house,
   tagged as such). A group portrait of three women is not "Edward Somerset"; a manor is not "Joan Thirsk".
4. **Never an empty screen.** A scene opens on its picture: the first print/doc lands within 1 s of the cut.
5. **At most 3 subagents fetching media at once.** Wikimedia blocked the machine when 8 ran together.
6. Keep what worked: a strong moving opening, real documents with the spoken line highlighted, steady motion.
7. **A date or number lands on its word.** A DateTag/figure appears when the narrator says it, and the scene that
   carries it starts at the sentence that says it (not a beat later).
8. **Marks sit on the printed words.** Every DocCard highlight/underline comes from `tools/docmark.py <doc> "the
   spoken words"` (OCR), never a box guessed by eye; circles only ring an area (a town, a signature).
9. **Labels are always on top and readable.** Name tags and labels are never covered by a print that lands later;
   light type over film or photos keeps its dark backing; keep type off bright sky.

## Done =
- `{PY} tools/validate.py` shows **0 ERRORs** (fix every one; WARNs fixed or explained in NOTES.md),
- `npx tsc --noEmit` is clean,
- you have looked at stills of the whole cut (one per scene) against the narration and fixed what was wrong.
Do not render the full video unless the producer asks; then: `{PY} "{REPO / "ship.py"}" .`
''', encoding='utf8')
(proj / '.gitignore').write_text('node_modules/\n_cache/\n_stills/\n_sheets/\nout/\n', encoding='utf8')
print('created', proj)

npm = shutil.which('npm') or 'npm'
if not a.no_install:
    subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=proj, check=True)
if not a.no_words:
    r = subprocess.run([str(PY), 'tools/words.py'], cwd=proj)
    if r.returncode:
        print('word timings failed: run tools/words.py by hand')
cmd = f'cd {proj} && claude --model claude-opus-5-5 --permission-mode auto'
if a.launch:
    subprocess.run(['tmux', 'new-session', '-d', '-s', name, cmd], check=True)
    print(f'chat running: tmux attach -t {name}   (then say: make the video)')
else:
    print(f'\nnext: {cmd}\nthen say: make the video')
