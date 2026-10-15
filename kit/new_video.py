"""Start a new Sadat-style video from the kit.

    python kit/new_video.py <name> <script.md|.txt> <voice-over.mp3|.wav|.m4a> [--dest DIR] [--no-install] [--no-words]

Creates <dest>/<name>/ (default dest: the folder that holds this repo) from kit/template, puts the voice-over at
public/audio/narration.mp3 and the script at script.md, installs the skill into <name>/.claude/skills, runs
npm install and the word timings. Then open <name>/ in Claude Code and say: "make the video" (skill sadat-style-video).
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
REPO = KIT.parent
ap = argparse.ArgumentParser()
ap.add_argument('name')
ap.add_argument('script')
ap.add_argument('voice')
ap.add_argument('--dest', default=str(REPO.parent))
ap.add_argument('--no-install', action='store_true')
ap.add_argument('--no-words', action='store_true')
a = ap.parse_args()

name = re.sub(r'[^A-Za-z0-9_-]+', '-', a.name).strip('-').lower()
proj = Path(a.dest).resolve() / name
script, voice = Path(a.script).resolve(), Path(a.voice).resolve()
for f in (script, voice):
    if not f.is_file():
        sys.exit(f'not found: {f}')
if proj.exists():
    sys.exit(f'{proj} already exists (pick another name or delete it)')

shutil.copytree(KIT / 'template', proj, ignore=shutil.ignore_patterns('node_modules', '_cache', '_stills', '_sheets'))
shutil.copy2(script, proj / 'script.md')
narr = proj / 'public/audio/narration.mp3'
if voice.suffix.lower() == '.mp3':
    shutil.copy2(voice, narr)
else:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(voice), '-c:a', 'libmp3lame', '-b:a', '192k', str(narr)], check=True)
skill = REPO / '.claude/skills/sadat-style-video'
shutil.copytree(skill, proj / '.claude/skills/sadat-style-video')
(proj / 'CLAUDE.md').write_text(
    f'# {name}\n\nA Sadat-style documentary made from the kit in `{REPO}`.\n'
    'Use the **sadat-style-video** skill for all work here (rules in EDITING_RULES.md).\n'
    f'Render only when the producer asks: `python "{REPO / "ship.py"}" .`\n', encoding='utf8')
(proj / '.gitignore').write_text('node_modules/\n_cache/\n_stills/\n_sheets/\nout/\n', encoding='utf8')
print('created', proj)

npm = shutil.which('npm') or 'npm'
if not a.no_install:
    subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=proj, check=True)
if not a.no_words:
    r = subprocess.run([sys.executable, 'tools/words.py'], cwd=proj)
    if r.returncode:
        print('word timings failed: install faster-whisper (pip install faster-whisper), then run python tools/words.py')
print(f'\nnext: open {proj} in Claude Code and ask for the video (skill: sadat-style-video)')
