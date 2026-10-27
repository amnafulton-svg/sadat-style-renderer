"""Start a new Sadat-style video made by ONE Claude Code chat (the england-plain way), not the section workflow.

    python kit/new_chat.py <name> <script.md|.txt> <voice-over.mp3|.wav|.m4a> [--dest DIR] [--no-install] [--no-words] [--launch]

Creates <dest>/<name>/ (default dest: ~/sadat-chat) from kit/template with only the plain tools (no look.py, read.py,
batch.py, turn_guard.py: those start helper sessions, which is what ate the weekly limit) and no
skill. CLAUDE.md is the whole brief: the tools, the beat plan and film search (zniti test 2026-10-26: the section
workflow's per-sentence plan and archive.org searches found far better film), the lessons from the england-plain test
(2026-10-24) and when it is done. A `.onechat` file makes source.py and validate.py hold the chat to the plan and to
the section workflow's fresh Final check on the review boards (zniti2-2, 2026-10-26: without it a fitness-class shot
went out under "a political analyst sits under the lights").
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
HELPERS = ('look.py', 'read.py', 'batch.py', 'turn_guard.py')
PY = Path.home() / 'yt/.venv/bin/python'  # system python3 has no PIL
ap = argparse.ArgumentParser()
ap.add_argument('name')
ap.add_argument('script')
ap.add_argument('voice')
ap.add_argument('--dest', default=str(Path.home() / 'sadat-chat'))
ap.add_argument('--no-install', action='store_true')
ap.add_argument('--no-words', action='store_true')
ap.add_argument('--editing', choices=('solo', 'sections'), default='solo',
                help='solo: this chat edits the whole video, helpers only fetch media (Chipyong-ni, ~$45); '
                     'sections: the chat may hand sections to subagent editors (cannabis video, ~$95)')
ap.add_argument('--media', type=int, default=3, choices=range(0, 7), metavar='0-6',
                help='most subagents fetching media at once (0 = the chat finds its media itself)')
ap.add_argument('--launch', action='store_true', help='start the chat in tmux (Opus 5.5, auto permissions)')
a = ap.parse_args()

if a.media == 0:
    MEDIA = 'Do not use subagents to fetch media: find, download and check it yourself.'
else:
    MEDIA = (f'At most {a.media} subagent{"s" if a.media != 1 else ""} fetching media at once (Wikimedia blocked the '
             'machine when 8 ran together). **The film search always goes to these helpers, also on a short video:** '
             'once plan.md is written, give each helper a block of film rows (their times, lines and source ideas). '
             'It runs the searches for every row (archive.org first, then Commons video), sheets the candidates and '
             'returns per row: the film (its own title and what the whole film is about), the clean in-point, the '
             'sheet path and everything in the frame (who is in it and what they are doing, not only the part that '
             'fits), or "no film:" with the queries it ran. It does not cut clips or edit; you choose from what it '
             'brings back, and you open the sheet of each film you cut from yourself before you cut.')
if a.editing == 'solo':
    SPLIT = ('**You edit the whole video yourself, in this chat.** Write every section, look at the stills and make '
             'every fix here. Never hand editing, sections, stills checks or fixes to subagents: each one has to load '
             'the whole project again, and that doubled the cost of the cannabis video. Subagents may only find, '
             'download and sheet media for you, plus the ONE fresh Final check at the end (Done, below). ' + MEDIA)
else:
    SPLIT = ('You may hand sections to subagent editors (one per section), then check and join their work yourself. '
             + MEDIA)

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
- `tools/board.py [--from S --to S]`: review boards, one still per scene, 12 per image with the words spoken over
  each (for the Final check, Done below).
- `tools/mapres.py`, `tools/make_textures.py`: map sharpness, paper/wall textures.
- `tools/docmark.py <doc> "phrase"`: OCR the scan and print the exact `lines:` rects for a mark on those words
  (`--rows a-b` for whole lines, no phrase to list every line).

## 1. Plan before you search (plan.md)
The section workflow found better film than one chat because it planned every sentence first (zniti test,
2026-10-26). So before any search (source.py refuses to search until plan.md exists):
- `{PY} tools/facts.py 0 99999` prints every sentence with its start-end time.
- Write `plan.md`: one table row per sentence (or spoken list), in order:
  `| # | Time | Line | Plane | Source ideas |` with Time in seconds (`12.40-18.90`) and the line's words.
- Plane = what the screen is for that line: **film** (it was filmed: events, places, crowds, machines, war, any
  moment after ~1900), **named** (a person: print + names), **geography** (DocMap), **document** (DocCard of the real
  paper), **numbers** (chart, or a figure over film), **list** (one cut per item), **argument** (real film/photos with a
  highlight). Never a text-only screen.
- Source ideas = the exact thing seen on this line and 2-3 searches for it (the event, the place, the year, the
  newsreel name), not the video's topic.
- Mark the hook (first ~35 s) and the 3-6 big turns for burns.

## 2. Find film for every film line
- Match the footage to the year the line is about: for a modern story, look for footage from that time first.
- For each film row: at least 3 searches made for that line, **archive.org first** (`source.py ia-search`), then
  `commons --video`, and only then photos.
- **You pick with your own eyes.** Open (Read) the sheet of each film you cut from and each photo you use, and pick
  the in-point against the exact words spoken over it: what is named must be on screen when it is said, and nothing
  in the frame may fight the line. Judge the whole frame and the film's own subject, not only the part you want: a
  fitness class taped in a studio is not "a political analyst under the lights" (zniti2-2, 2026-10-26), a cooking,
  sport, school or training film never stands in for news, politics or war.
- **The right picture beats film.** Loose stand-in film loses to a strong real photo of the exact thing (the old
  workflow put the real 2004 Bush–Kerry debate photo on "the previous night's presidential debate", a colour macro of
  a crocodile's slit pupil on "the pupil of a reptile"). Then write `better photo: query 1; query 2; query 3` (the
  film searches you ran, at least one on archive.org) in that row's Source ideas.
- If nothing usable exists, write `no film: query 1; query 2; query 3` the same way and use the best real
  photos/documents there.
- Never the same film three times in a row under different lines (one eye film for "the man's left eye", "the pupil
  elongates" and "a human pupil again"): each line gets its own picture.
- validate.py ERRORs: no plan.md, a sentence with no row, a film row that shows film for under half its time without
  that "no film:"/"better photo:" record, and fewer than one archive.org search per 20 s of narration. Searches are
  logged in `_work/searches.tsv` by source.py.

## Lessons from the last chat-made video (england-plain, 2026-10-24): do not repeat these
1. **The exact place.** A line about Raglan shows Raglan, not another castle; Denbigh, Caerphilly, Rhuddlan each
   get their own picture or none. Check every place picture against its file title on a sheet.
2. **The right era.** No Victorian or modern buildings, cars, cranes, glass offices or modern photos of a building
   under lines about an earlier century (a 1970s archive building under "county committees" in the 1640s,
   Goldsmiths' Hall with parked cars). Use period paintings, engravings, maps and documents instead.
3. **The right person.** A name tag or person card goes only on a picture of that person (or their arms/house,
   tagged as such). A group portrait of three women is not "Edward Somerset"; a manor is not "Joan Thirsk".
4. **Never an empty screen.** A scene opens on its picture: the first print/doc lands within 1 s of the cut.
5. Keep the split below (How the work is split).
6. Keep what worked: a strong moving opening, real documents with the spoken line highlighted, steady motion.
7. **A date or number lands on its word.** A DateTag/figure appears when the narrator says it, and the scene that
   carries it starts at the sentence that says it (not a beat later).
8. **Marks sit on the printed words.** Every DocCard highlight/underline comes from `tools/docmark.py <doc> "the
   spoken words"` (OCR), never a box guessed by eye; circles only ring an area (a town, a signature).
9. **Labels are always on top and readable.** Name tags and labels are never covered by a print that lands later;
   light type over film or photos keeps its dark backing; keep type off bright sky.

## How the work is split (the producer's choice)
{SPLIT}

## Done =
- `{PY} tools/validate.py` shows **0 ERRORs** (fix every one; WARNs fixed or explained in NOTES.md),
- `npx tsc --noEmit` is clean,
- **the Final check has passed** (the section workflow's step that made its cuts match the words). When the cut is
  finished, start ONE fresh subagent (general-purpose, `model: "opus"`, foreground) with this brief, word for word:
  "You are the Final check of this Sadat-style video. Read `CLAUDE.md`, `EDITING_RULES.md`, `plan.md` and NOTES.md.
  1. `npx tsc --noEmit` passes. 2. `{PY} tools/validate.py`: zero ERRORs except the one saying the Final check is
  missing (that one clears when you write `_parts/FINAL.md`). 3. Whole-cut review boards: `{PY} tools/board.py`
  stills every scene mid-scene plus the end frame of every DocMap, Chart and DocCard, 12 per board with the words
  spoken over each tile, in `_review/`. Open every board. Per tile: does the picture show what its words say at that
  moment (the thing named, the right era/place/person, and nothing in the frame that fights the line: people doing
  something else, a different kind of programme), nothing clipped, labels readable and not colliding, 4:3 film
  padded, strips on the right person. Also across tiles: the same shot held over several sentences, the same crowd,
  room or film shown twice. Fix every flagged tile with small Edits (a wrong shot: search again with
  `tools/source.py`, open only the sheet you take the new in-point from, or use the best real photo), then re-board
  only the fixed range and look again. 4. Run tsc + validate.py once more. Write `_parts/FINAL.md`: what you fixed
  (scene, why), WARNs left and why, and a last line `STATUS: READY` or `STATUS: NOT READY: <what is left>`. End
  with `FINAL: _parts/FINAL.md`."
  Read only `_parts/FINAL.md` (not the boards). NOT READY: fix what it lists, then brief a fresh Final again.
  validate.py ERRORs until `_parts/FINAL.md` says `STATUS: READY` and is newer than every file in `src/timeline/`
  (so any change after the check needs the check again; keep later changes for the producer's notes).
Do not render the full video unless the producer asks; then: `{PY} "{REPO / "ship.py"}" .`
''', encoding='utf8')
(proj / '.onechat').write_text('one-chat project: plan.md + film search rules (tools/plancheck.py)\n', encoding='utf8')
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
