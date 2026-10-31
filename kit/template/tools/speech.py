"""Leaders' key lines: a real filmed speech, with its own sound, cut in between two parts of the voice-over.

    python tools/speech.py words <file-or-url> [--from S] [--to S]
          # what is said, with word times (whisper), sentence ends marked |: pick a full sentence of 10-20 s
    python tools/speech.py cut <file-or-url> <start> <end> <name> --at T --line1 "Franklin D. Roosevelt"
          [--line2 "Congress, 8 December 1941"] [--crop W:H:X:Y] [--focus 58]
          # -> public/speeches/<name>.mp4 (sound cleaned and levelled to the narrator) + its entry in src/lib/speeches.json
    python tools/speech.py list
    python tools/speech.py rm <name>

Find the film with tools/source.py (ia-search "roosevelt infamy speech", commons "..." <key> --video). URLs are
downloaded to _cache/speeches/ once. --at is the narration second where the voice-over stops: the `from` of the
scene the narration goes on with, after a sentence end (a paragraph break plays best). Main.tsx plays the speech there
between two film burns and the narration then carries on; validate.py checks the placement. --crop removes a
burned-in timecode or logo (PeriscopeFilm 854x480: 642:395:106:0); check it on a sheet first.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / 'src/lib/speeches.json'
OUT = ROOT / 'public/speeches'
CACHE = ROOT / '_cache/speeches'
UA = 'SadatStyleVideoKit/1.1 (https://github.com/amnafulton-svg/sadat-style-renderer; documentary research)'


def local(src):
    """a URL is fetched once into _cache/speeches/ (data only: never run anything from there)"""
    if not re.match(r'https?://', src):
        p = Path(src)
        if not p.is_file():
            raise SystemExit(f'not found: {src}')
        return p
    name = re.sub(r'[^A-Za-z0-9_.-]+', '_', urllib.parse.unquote(Path(urllib.parse.urlparse(src).path).name))[-80:]
    dest = CACHE / name
    if dest.is_file() and dest.stat().st_size > 1 << 20:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = urllib.parse.quote(src, safe=':/?&=%')  # archive.org file names with spaces
    for attempt in range(4):  # archive.org answers a 170-byte 500 page now and then
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=600) as r, open(dest.with_suffix('.part'), 'wb') as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if dest.with_suffix('.part').stat().st_size > 1 << 20:
                dest.with_suffix('.part').replace(dest)
                return dest
        except OSError as ex:
            print(f'download attempt {attempt + 1}: {ex}', file=sys.stderr)
        time.sleep(10 * (attempt + 1))
    raise SystemExit(f'could not download {src}')


def load():
    return json.loads(LIST.read_text(encoding='utf8')) if LIST.exists() else []


def save(items):
    LIST.write_text(json.dumps(sorted(items, key=lambda x: x['at']), indent=1, ensure_ascii=False) + '\n', encoding='utf8')


def words(a):
    if os.environ.get('WHISPER_DEPS'):
        sys.path.insert(0, os.environ['WHISPER_DEPS'])
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('faster-whisper missing: pip install faster-whisper  (or set WHISPER_DEPS to a folder that has it)')
    src = local(a.src)
    wav = CACHE / f'{src.stem}_{a.lo:g}_{a.hi:g}.wav'
    wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(a.lo), '-i', str(src)]
    if a.hi:
        cmd += ['-t', str(a.hi - a.lo)]
    subprocess.run(cmd + ['-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
    m = WhisperModel('small', device='cpu', compute_type='int8')
    segs, _ = m.transcribe(str(wav), word_timestamps=True, beam_size=5, vad_filter=False)
    for s in segs:
        line = ' '.join(f"{w.word.strip()}@{w.start + a.lo:.2f}" + (' |' if re.search(r'[.!?]$', w.word.strip()) else '')
                        for w in (s.words or []))
        print(f'{s.start + a.lo:7.2f}-{s.end + a.lo:7.2f}  {line}')
    wav.unlink(missing_ok=True)


def cut(a):
    src = local(a.src)
    if a.end - a.start < 3:
        raise SystemExit('end must be after start (seconds in the source film)')
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f'{a.name}.mp4'
    dur = a.end - a.start
    vf = (f'crop={a.crop},' if a.crop else '') + \
        'scale=trunc(iw*sar/2)*2:ih,setsar=1,scale=-2:1080:flags=lanczos,fps=25,format=yuv420p'
    # old film sound: rumble off, hiss down, levelled to the narrator, no click at either end
    af = (f'highpass=f=90,afftdn=nf=-30,loudnorm=I=-17:TP=-2:LRA=11,'
          f'afade=t=in:d=0.15,afade=t=out:st={max(0, dur - 0.3):.2f}:d=0.3')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.start), '-i', str(src), '-t', f'{dur:.3f}',
                    '-vf', vf, '-af', af, '-ar', '44100', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(dest)], check=True)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(dest)],
                           capture_output=True, text=True, check=True)
    real = round(float(probe.stdout.strip()), 2)
    items = [x for x in load() if x['file'] != dest.name and abs(x['at'] - a.at) > 0.05]
    e = {'at': a.at, 'file': dest.name, 'dur': real, 'line1': a.line1}
    if a.line2:
        e['line2'] = a.line2
    if a.focus is not None:
        e['focusY'] = a.focus
    save(items + [e])
    print(f'{dest.relative_to(ROOT)}  {real} s  at narration {a.at}  ({len(items) + 1} speeches)')
    print(f'check it: node tools/stills.mjs _review/speech sp{sorted(items + [e], key=lambda x: x["at"]).index(e) + 1}+1')


def show(_):
    for k, x in enumerate(sorted(load(), key=lambda x: x['at']), 1):
        print(f"{k}. at {x['at']:8.2f}  {x['dur']:5.2f} s  {x['file']:<28} {x['line1']} / {x.get('line2', '')}")


def rm(a):
    items = load()
    keep = [x for x in items if Path(x['file']).stem != a.name]
    if len(keep) == len(items):
        raise SystemExit(f'no speech named {a.name}')
    save(keep)
    (OUT / f'{a.name}.mp4').unlink(missing_ok=True)
    print(f'removed {a.name}')


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest='cmd', required=True)
p = sp.add_parser('words'); p.add_argument('src'); p.add_argument('--from', dest='lo', type=float, default=0)
p.add_argument('--to', dest='hi', type=float, default=0); p.set_defaults(fn=words)
p = sp.add_parser('cut'); p.add_argument('src'); p.add_argument('start', type=float); p.add_argument('end', type=float)
p.add_argument('name'); p.add_argument('--at', type=float, required=True); p.add_argument('--line1', required=True)
p.add_argument('--line2'); p.add_argument('--crop'); p.add_argument('--focus', type=float); p.set_defaults(fn=cut)
p = sp.add_parser('list'); p.set_defaults(fn=show)
p = sp.add_parser('rm'); p.add_argument('name'); p.set_defaults(fn=rm)
a = ap.parse_args()
if a.cmd == 'cut' and not re.fullmatch(r'[a-z0-9_]+', a.name):
    raise SystemExit('name: lowercase letters, digits and _ only (e.g. fdr_infamy)')
a.fn(a)
