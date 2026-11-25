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

from PIL import Image, ImageStat

KIT = Path(__file__).resolve().parent
OCR_PY = Path.home() / 'yt/.venv-ocr/bin/python'
GEN = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'generated_images'
TIMEOUT = 900
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

PLAN = f"""You choose 3 BACKGROUND surfaces for one history documentary video. Do not make any image now; reply with JSON only.

Video (folder name): {topic}
Opening of its script:
{script[:1500]}

The channel's family mood (every background must fit it): {family}

Photo prints, labels and charts sit on top of these backgrounds, so each is a plain flat SURFACE or material that
fills the frame (a wall, cloth, paper, wood, metal, stone, leather...), chosen to match the energy, era and place of
this topic. Never an object, scene, person, flag, map with names, symbol or text from the story.
Make them specific to THIS video, not generic for the channel: the material of its own era, place and world (for a
1930s gold story e.g. vault-door steel, a bullion-room brass plate, an assay-office paper; for a Roman story plaster
and stone of that time), so the next video on this channel gets clearly different ones.
- "dark1" and "dark2": two different dark-toned surfaces (white labels must read on them).
- "light": one light-toned surface (dark text must read on it), like a paper or pale stock of the period.
The three must look clearly different from each other.
Reply with ONLY: {{"dark1": "<surface, colour, light>", "dark2": "<...>", "light": "<...>"}}"""

IMG = """Use the imagegen skill (the built-in image_gen tool, not the CLI). Make exactly ONE image, 16:9 landscape,
photorealistic, very high detail.
It is an empty BACKGROUND for a history documentary: photo prints and name tags will be placed on top of it in the
middle, so the centre must stay calm, even and uncluttered, with no objects, no text, no letters, no numbers, no logos,
no people, no frames, no symbols. Detail and interest only in the texture and in soft lighting falling off toward the
edges (gentle vignette). Shot straight on, flat surface filling the whole frame, no perspective, no horizon.
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
    tone = ('light, pale, bright' if slot == 'light' else
            'medium-dark and low-key, but the texture and colour clearly visible everywhere (not black, not crushed)')
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
        shutil.move(tmp, dst)
        log(slot, 'OK', f'mean {mean:.0f} dim {dim:.2f}', desc[:100])
        return {'file': dst.name, 'dim': round(dim, 3), 'desc': desc}
    return None


log('start', proj.name, 'channel', a.channel or '-', 'family:', family)
plan = None
for attempt in (1, 2):
    try:
        msg, _ = codex(PLAN, f'plan_{attempt}', write=False)
        m = re.search(r'\{.*\}', msg, re.S)
        plan = json.loads(m.group(0)) if m else None
        if plan and all(isinstance(plan.get(k), str) and plan[k].strip() for k in ('dark1', 'dark2', 'light')):
            break
        plan = None
    except Exception as e:  # noqa: BLE001
        log('plan try', attempt, 'failed:', e)
if not plan:
    log('no plan: the video keeps the kit textures')
    sys.exit(1)
log('plan', json.dumps(plan))
with ThreadPoolExecutor(3) as ex:
    res = dict(zip(('dark1', 'dark2', 'light'), ex.map(lambda k: make(k, plan[k]), ('dark1', 'dark2', 'light'))))
dark = [res[k] for k in ('dark1', 'dark2') if res[k]]
bgset = {'channel': a.channel, 'family': family, 'dark': dark, 'light': res['light']}
tmp = proj / 'src/lib/bgset.json.tmp'
tmp.write_text(json.dumps(bgset, indent=1) + '\n', encoding='utf8')
os.replace(tmp, proj / 'src/lib/bgset.json')
log('done:', len(dark), 'dark +', 'light' if res['light'] else 'no light', '-> src/lib/bgset.json')
