"""Three backgrounds made by GPT for one video (producer 2026-11-25: "for every new video gpt makes 3 backgrounds
that match the energy of the video topic", inside the channel's family mood from kit/bgfamilies.json).

    ~/yt/.venv/bin/python kit/bgmake.py <project> [--channel <id>]

new_chat.py starts it in the background right after the project is made, so it runs during npm install, word
timings and the chat's own film search. GPT (codex exec, the subscription) first picks 3 surfaces for the topic:
two dark ones (behind prints, quote and person cards: kit ConcreteWall / Desk) and one light one (behind label tape
lists and date tags: kit Paper). Then the 3 images are made side by side. Each is scaled to 2400x1350, checked for
text (OCR; one retry), and its brightness is evened out to what the old textures had. Only when all of that is done
is src/lib/bgset.json written (the layers read it); if anything fails the video keeps the old kit textures for that
slot. These are BACKGROUNDS ONLY: surfaces, never a picture of the story (no-AI rule stays for story content).
Log: _work/backgrounds/bgmake.log.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageStat

KIT = Path(__file__).resolve().parent
OCR_PY = Path.home() / 'yt/.venv-ocr/bin/python'
GEN = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'generated_images'
TIMEOUT = 900
# colour strength on screen (mean max-min of RGB) above these looked loud (Emperor red silk 115, walnut 70; calm ones
# 6-43; ivory papers 59-83 read yellow, the grey-blue one 25), producer 2026-11-26: fix loud colours + the light paper
DARK_CHROMA, LIGHT_CHROMA = 45.0, 35.0
DARK_TARGET, LIGHT_TARGET = 45.0, 215.0  # mean grey after dim; dark kept low: colour surfaces look brighter than grey concrete

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('--channel', default='')
a = ap.parse_args()
proj = Path(a.project).resolve()
work = proj / '_work' / 'backgrounds'
work.mkdir(parents=True, exist_ok=True)
logf = open(work / 'bgmake.log', 'a', encoding='utf8')


def log(*msg):
    print(time.strftime('%H:%M:%S'), *msg, file=logf, flush=True)


def codex(prompt: str, name: str, write: bool) -> tuple[str, str]:
    exe = shutil.which('codex', path=f"{Path.home() / '.local/bin'}:{os.environ.get('PATH', '')}") or 'codex'
    last = work / f'{name}_last.txt'
    last.unlink(missing_ok=True)
    cmd = [exe, 'exec', '--skip-git-repo-check', '--ephemeral', '-s', 'workspace-write' if write else 'read-only',
           '--color', 'never', '-o', str(last), '-']
    with open(work / f'{name}.log', 'wb') as fh:
        p = subprocess.Popen(cmd, cwd=work, stdin=subprocess.PIPE, stdout=fh, stderr=subprocess.STDOUT,
                             start_new_session=True)
        try:
            p.communicate(prompt.encode('utf8'), timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9)
            p.wait()
            raise RuntimeError(f'{name}: GPT took over {TIMEOUT // 60} min')
    out = (work / f'{name}.log').read_text('utf8', 'replace')
    return (last.read_text('utf8', 'replace') if last.exists() else ''), out


fams = json.loads((KIT / 'bgfamilies.json').read_text('utf8'))
family = fams.get(a.channel) or fams['default']
script = (proj / 'script.md').read_text('utf8', 'replace') if (proj / 'script.md').exists() else ''
topic = proj.name.replace('-', ' ')
recent = []  # what the last videos already had, so the next one picks different materials
for f in sorted(proj.parent.glob('*/src/lib/bgset.json'), key=lambda f: f.stat().st_mtime, reverse=True):
    if f.parents[2] == proj:
        continue
    try:
        b = json.loads(f.read_text('utf8'))
    except Exception:  # noqa: BLE001
        continue
    descs = [x.get('desc', '') for x in (b.get('dark') or []) + [b.get('light') or {}] if x.get('desc')]
    if descs:
        recent.append('; '.join(d[:90] for d in descs))
    if len(recent) >= 8:
        break
RECENT = '\n'.join(f'- {r}' for r in recent) or '- (none yet)'

PLAN = f"""You choose 3 BACKGROUNDS for one history documentary video. Do not make any image now; reply with JSON only.

Video (folder name): {topic}
Opening of its script:
{script[:1500]}

The channel's family mood: {family}
Take only its COLOURS and light mood from that line, not its materials.

Style (producer 2026-11-26): minimal, professional motion-graphics backgrounds, like the clean graphic beds of a
high-end broadcast documentary: smooth soft gradient, soft light falloff toward the edges, very fine grain. Nothing
photographic, no objects, no symbols, no text. Photo prints, labels and charts sit on top in the middle, so the
centre stays calm. Each dark one has its own fixed texture (producer's choice):
- "dark1": BLUEPRINT GRID texture: thin fine grid lines (major and minor squares) over the dark gradient.
- "dark2": MATTE PAPER texture: a dark matte paper with fine, even, soft paper grain (no fibres, stains or folds).
- "dark3": HALFTONE texture: a fine halftone dot pattern, dots growing toward one edge or corner and fading out.
- "light": one light background (dark text must read on it): smooth gradient, fine grain, at most a very faint dot
  grid; pale grey, blue-grey, grey-green or stone. Never pink, rose, lilac, yellow or cream.
For each, choose only the colours, so they suit the energy, era and place of THIS topic inside the family mood.
The three darks: three clearly different hues (white labels must read on them), not near-black; at most ONE of them
purple, plum or aubergine. All four: muted, desaturated (the photos must stay the most colourful thing).
The last videos already used these, so pick clearly different colours:
{RECENT}
Reply with ONLY: {{"dark1": "<colours + gradient; blueprint grid>", "dark2": "<colours; matte paper>", "dark3": "<colours; halftone>", "light": "<...>"}}"""

IMG = """Use the imagegen skill (the built-in image_gen tool, not the CLI). Make exactly ONE image, 16:9 landscape.
It is an empty, minimal, professional MOTION-GRAPHICS BACKGROUND for a high-end history documentary (a clean digital
graphic bed, like broadcast design, NOT a photo of a material). Photo prints and name tags will be placed on top in the
middle, so the centre must stay clean, smooth and uncluttered. Smooth soft gradient and gentle light falloff toward
the edges, a very fine even grain, the texture fine, even and quiet (clearly there, never busy). No objects, no
text, no letters, no numbers, no logos, no people, no frames, no symbols, no 3D shapes, no lens flares, no bokeh.
Flat, straight on.
Overall tone: {tone}.
Background: {desc}
This runs unattended: never ask anything. When done, reply with the image file path."""


def find_image(msg: str, out: str, since: float) -> Path | None:
    for txt in (msg, out):
        for hit in re.findall(r"(/[^\s)\]\"'`]*generated_images/[^\s)\]\"'`]+\.(?:png|jpg|jpeg|webp))", txt):
            if Path(hit).is_file():
                return Path(hit)
    return None  # never guess from the shared folder: other videos may be making theirs at the same time


def has_text(path: Path) -> str:
    if not OCR_PY.exists():
        return ''
    out = work / (path.stem + '_ocr.json')
    r = subprocess.run([str(OCR_PY), str(KIT / 'template/tools/ocr_worker.py'), str(path), str(out)],
                       capture_output=True, timeout=300)
    if r.returncode or not out.exists():
        return ''
    words = [ln['text'] for ln in json.loads(out.read_text('utf8')).get('lines', [])
             if ln.get('score', 0) >= 0.8 and len(re.sub(r'\W', '', ln['text'])) >= 3]
    return ' | '.join(words)


def make(slot: str, desc: str) -> dict | None:
    tone = ('light, pale, bright, muted colour (not yellow, not cream)' if slot == 'light' else
            'dark and low-key, muted desaturated colour, smooth (not pure black, not crushed)')
    for attempt in (1, 2):
        since = time.time()
        try:
            msg, out = codex(IMG.format(tone=tone, desc=desc), f'{slot}_{attempt}', write=True)
        except Exception as e:  # noqa: BLE001
            log(slot, 'try', attempt, 'failed:', e)
            continue
        src = find_image(msg, out, since)
        if not src:
            log(slot, 'try', attempt, 'no image in the reply')
            continue
        dst = proj / 'public/textures' / f'bg_{slot}.jpg'
        tmp = work / f'bg_{slot}.jpg'
        im = Image.open(src).convert('RGB').resize((2400, 1350), Image.LANCZOS)
        im.save(tmp, quality=92)
        txt = has_text(tmp)
        if txt:
            log(slot, 'try', attempt, 'has text:', txt[:120])
            continue
        mean = ImageStat.Stat(im.convert('L')).mean[0]
        if slot == 'light':
            if mean < 150:
                log(slot, 'try', attempt, f'too dark for a light background (mean {mean:.0f})')
                continue
            dim = max(-0.25, min(0.2, 1 - LIGHT_TARGET / mean))
        else:
            if not 18 <= mean <= 170:
                log(slot, 'try', attempt, f'wrong brightness for a dark background (mean {mean:.0f})')
                continue
            dim = max(-0.45, min(0.6, 1 - DARK_TARGET / mean))  # never brighten more than 1.45x (noise, loud colour)
        # bake the brightness into the file and tame loud colour, so the file is what the video shows (dim 0)
        arr = np.clip(np.asarray(im, dtype=np.float32) * (1 - dim), 0, 255)
        chroma = float((arr.max(2) - arr.min(2)).mean())
        cap = LIGHT_CHROMA if slot == 'light' else DARK_CHROMA
        out_im = Image.fromarray(arr.astype(np.uint8))
        if chroma > cap:
            out_im = ImageEnhance.Color(out_im).enhance(cap / chroma)
        out_im.save(dst, quality=92)
        tmp.unlink(missing_ok=True)
        log(slot, 'OK', f'mean {mean:.0f} brightness x{1 - dim:.2f} colour {chroma:.0f}' +
            (f' -> {cap:.0f}' if chroma > cap else ''), desc[:100])
        return {'file': dst.name, 'dim': 0, 'desc': desc}
    return None


log('start', proj.name, 'channel', a.channel or '-', 'family:', family)
plan = None
for attempt in (1, 2):
    try:
        msg, _ = codex(PLAN, f'plan_{attempt}', write=False)
        m = re.search(r'\{.*\}', msg, re.S)
        plan = json.loads(m.group(0)) if m else None
        if plan and all(isinstance(plan.get(k), str) and plan[k].strip() for k in ('dark1', 'dark2', 'dark3', 'light')):
            break
        plan = None
    except Exception as e:  # noqa: BLE001
        log('plan try', attempt, 'failed:', e)
if not plan:
    log('no plan: the video keeps the kit textures')
    sys.exit(1)
log('plan', json.dumps(plan))
SLOTS = ('dark1', 'dark2', 'dark3', 'light')
with ThreadPoolExecutor(4) as ex:
    res = dict(zip(SLOTS, ex.map(lambda k: make(k, plan[k]), SLOTS)))
dark = [res[k] for k in SLOTS[:3] if res[k]]
bgset = {'channel': a.channel, 'family': family, 'dark': dark, 'light': res['light']}
tmp = proj / 'src/lib/bgset.json.tmp'
tmp.write_text(json.dumps(bgset, indent=1) + '\n', encoding='utf8')
os.replace(tmp, proj / 'src/lib/bgset.json')
log('done:', len(dark), 'dark +', 'light' if res['light'] else 'no light', '-> src/lib/bgset.json')
