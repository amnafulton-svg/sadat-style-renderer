"""Fix cuts that land before the narrator speaks (validate: "cuts N s before the voice").

Whisper glues the breath before a sentence onto its first word, so a scene cut on that word comes up to a second
early (producer, Hitler's generals 2:12 2026-10-26: "this scene came out early about 1s"). This
  1. corrects src/lib/words.json + transcript.txt from the audio (tools/voice.py; words.py does it for new videos),
  2. moves every scene start that comes > 0.4 s before the voice to 0.1 s before it: the scene before holds longer,
     cues of this scene that fell in the pause (at=, appearAt, startAt, endAt, out=) and a film burn there move with
     it. A clip of the scene before that is too short to hold is cut again, longer, from its source film
     (_work/clips.tsv + _cache, via cut.py, with the crop it logged). A move is skipped (and listed) when the scene would
     drop under 2.5 s (1 s in the hook) or the clip can't be re-cut.
Run validate after.

    python tools/fixonset.py [--root .] [--dry-run]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import voice  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--hook', type=float, default=35)
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve()
EARLY, LEAD = 0.4, 0.1
OV = {'cut': 0, 'dissolve': 22, 'whip': 6, 'whipL': 6, 'torn': 12, 'rack': 0}
HEAD = re.compile(r"\{id: '([\w-]+)', from: (-?[\d.]+), to: ([\d.]+|END), enter: '(\w+)'")
CUE = re.compile(r'\b(at|appearAt|startAt|endAt|out)(=\{\s*|:\s*)([\d.]+)')


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


db = voice.levels(ROOT)

# 1. word timings
wp = ROOT / 'src/lib/words.json'
W = json.loads(wp.read_text(encoding='utf8'))
nw = voice.fix_words(W, db)
if nw and not a.dry_run:
    wp.write_text(json.dumps(W, ensure_ascii=False), encoding='utf8')
    lines, cur = [], []
    for w in W:  # one line per sentence, as words.py writes one per whisper segment
        cur.append(w)
        if re.search(r'[.!?]["\')\]]*$', w['w']):
            lines.append(cur)
            cur = []
    lines += [cur] if cur else []
    (ROOT / 'transcript.txt').write_text(''.join(
        f"{ws[0]['s']:8.2f}-{ws[-1]['e']:7.2f}  " + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in ws) + '\n' for ws in lines),
        encoding='utf8')
print(f'{nw} word starts moved to where the voice starts')

# 2. cuts
files = [p for p in (ROOT / 'src/timeline/parts').glob('*.tsx') if re.fullmatch(r'[a-z]+\d+', p.stem)]
files = sorted(files, key=lambda p: int(re.sub(r'\D', '', p.stem))) or [ROOT / 'src/timeline/video.tsx']
src = {p: p.read_text(encoding='utf8') for p in files}
vt = ROOT / 'src/timeline/video.tsx'
video = vt.read_text(encoding='utf8')
M = json.loads((ROOT / 'src/lib/media.json').read_text())
scenes = []  # (file, id, from, to, enter)
for p, s in src.items():
    for m in HEAD.finditer(s):
        scenes.append((p, m.group(1), float(m.group(2)), m.group(3), m.group(4)))


def block(s, sid):
    m = re.search(r"\{id: '" + re.escape(sid) + r"'", s)
    n = re.compile(r"\n\s*\{id: '").search(s, m.end())
    return m.start(), n.start() if n else len(s)


CLIPS = {r.split('\t')[0]: r.split('\t') for r in (ROOT / '_work/clips.tsv').read_text(encoding='utf8').splitlines()
         if r.count('\t') in (3, 4)} if (ROOT / '_work/clips.tsv').exists() else {}
recut_done = []


def aspect(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height', '-of', 'csv=p=0', str(p)], capture_output=True, text=True)
    w, h = r.stdout.strip().split(',')[:2]  # storage shape: cut.py scales -2:1080 and ignores the pixel aspect
    return int(w) / int(h)


def shot_changes(src, t0, t1):
    """source-film times of shot changes between t0 and t1: a hard cut (scene score > 0.2) or a soft one spread over
    a few frames (3 frames summing > 0.22: the salute -> crane cut in LC-40432 scored .10 .15 .06)"""
    r = subprocess.run(['ffmpeg', '-v', 'info', '-ss', f'{t0:.2f}', '-t', f'{t1 - t0:.2f}', '-i', str(src), '-an', '-vf',
                        r'scale=320:-2,select=gte(scene\,0),metadata=print:key=lavfi.scene_score', '-f', 'null', '-'],
                       capture_output=True, text=True)
    ts = [float(x) for x in re.findall(r'pts_time:([\d.]+)', r.stderr)]
    sc = [float(x) for x in re.findall(r'scene_score=([\d.]+)', r.stderr)]
    out = []
    for i in range(1, min(len(ts), len(sc))):  # frame 0 scores against nothing
        # (each of the 3 frames moves: pulled-down film alternates .12 / .00 inside one shot, postwar4 57 s)
        if sc[i] > 0.2 or (min(sc[i:i + 3]) > 0.04 and sum(sc[i:i + 3]) > 0.22):
            if not out or t0 + ts[i] - out[-1] > 0.3:
                out.append(t0 + ts[i])
    return out


def recut(clip, dur):
    """cut the clip again from its source film, dur s long (cut.py logged where it came from); returns the playback
    rate that makes it hold (1, or slower to stay inside its shot), or why it can't"""
    if clip not in CLIPS:
        return f'{clip} is too short to hold (no source in _work/clips.tsv)'
    film, start, crop = CLIPS[clip][1], CLIPS[clip][2], (CLIPS[clip] + [''])[4]
    srcs = sorted((ROOT / '_cache').rglob(film)) if (ROOT / '_cache').exists() else []
    if not srcs:
        return f'{clip} is too short to hold ({film} not in _cache)'
    if not crop and abs(aspect(srcs[0]) - M[clip]['w'] / M[clip]['h']) > 0.01:  # cropped before cut.py logged crops
        return f'{clip} is too short to hold (it was cropped from {film}: re-cut it by hand)'
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(srcs[0])],
                       capture_output=True, text=True)
    if float(start) + dur > float(r.stdout) - 0.05:  # the film ends first: start a little earlier
        start = f'{max(0.0, float(r.stdout) - 0.05 - dur):.2f}'
    # never run into the film's next shot (Berlin smoke -> a soup line): hold the shot slowed down instead
    # (cuts inside the old clip were the editor's; only its end and the extension are checked)
    slow, st = 1.0, float(start)
    sc = shot_changes(srcs[0], max(st + 1.0, st + M[clip]['d'] - 0.6), st + dur)
    if sc:
        end = sc[0] - 0.08
        if not shot_changes(srcs[0], st + 0.1, end):  # one shot: start earlier in it, as late as fits
            back = shot_changes(srcs[0], max(0.0, st - 2.0), st + 0.1)
            st = max(back[-1] + 0.08 if back else max(0.0, st - 2.0), end - dur)
            start = f'{st:.2f}'
        slow = min(1.0, (end - st) / (dur - 0.2))
        if slow < 0.8:
            return f'{clip} is too short to hold (its shot ends {end - st:.2f} s in, too short even at 0.8x)'
        dur = end - st
    recut_done.append(f'{clip}: re-cut {dur:.2f} s from {film} @ {start}' + (f', played at {slow:.2f}x to stay in '
                                                                               f'its shot' if slow < 1 else ''))
    if not a.dry_run:
        subprocess.run([sys.executable, str(ROOT / 'tools/cut.py'), str(srcs[0]), start, f'{dur:.2f}', clip[:-4]]
                       + (['--crop', crop] if crop else []), cwd=ROOT, check=True, capture_output=True)
        M[clip]['d'] = round(dur, 2)
    return slow


moved, skipped = 0, []
for k in range(1, len(scenes)):
    p, sid, fr, to, en = scenes[k]
    pp, psid, pfr, pto, pen = scenes[k - 1]
    o = voice.onset(db, fr)
    if o is None or o - fr <= EARLY:
        continue
    end = float(to) if to != 'END' else 1e9
    hold = 2.5 if fr >= a.hook else 1.0
    new = round(min(o - LEAD, end - hold), 2)  # part of the way when the scene would get too short
    if o - new > 0.5:
        skipped.append(f'{sid} at {fmt(fr)}: voice at {fmt(o)} but the scene would hold only {end - o + LEAD:.2f} s')
        continue
    b0, b1 = block(src[pp], psid)
    pb = src[pp][b0:b1]
    need = new - pfr + OV.get(pen, 0) / 25
    short = [(fm.group(1), float(fm.group(2)) + need * float(fm.group(3) or 1) + 0.2)
             for fm in re.finditer(r'<F src="([^"]+)" start=\{([\d.]+)\}(?:[^>]*?rate=\{([\d.]+)\})?', pb)
             if fm.group(1) in M and (M[fm.group(1)]['d'] - float(fm.group(2))) / float(fm.group(3) or 1) < need]
    res = [(c, recut(c, d)) for c, d in short]
    why = [x for _, x in res if isinstance(x, str)]
    if why:
        skipped.append(f'{sid} at {fmt(fr)}: voice at {fmt(o)} but {psid}\'s clip {why[0]}')
        continue
    for c, slow in res:  # a clip slowed to stay in its shot: rate= on its F (times an existing rate)
        if slow < 1:
            def _rate(m, slow=slow):
                old = float(m.group(2)) if m.group(2) else 1.0
                return m.group(1) + f' rate={{{fmt(round(old * slow, 2))}}}'
            pb = re.sub(r'(<F src="' + re.escape(c) + r'" start=\{[\d.]+\})(?: rate=\{([\d.]+)\})?', _rate, pb)
    # the scene before ends later
    hm = HEAD.search(pb)
    pb = pb[:hm.start(3)] + fmt(new) + pb[hm.end(3):]
    src[pp] = src[pp][:b0] + pb + src[pp][b1:]
    # this scene starts later; its cues in the pause move with it
    b0, b1 = block(src[p], sid)
    b = src[p][b0:b1]
    hm = HEAD.search(b)
    head = b[:hm.end()].replace(f'from: {hm.group(2)}', f'from: {fmt(new)}', 1)
    body = CUE.sub(lambda m: m.group(1) + m.group(2) + (fmt(new) if fr - 0.01 <= float(m.group(3)) < new else m.group(3)),
                   b[hm.end():])
    src[p] = src[p][:b0] + head + body + src[p][b1:]
    video = re.sub(r'(at:\s*)' + re.escape(fmt(fr)) + r'(\s*,\s*n:)', lambda m: m.group(1) + fmt(new) + m.group(2), video)
    scenes[k] = (p, sid, new, to, en)
    moved += 1
    print(f'{p.name} {sid}: starts {fmt(fr)} -> {fmt(new)} (voice at {fmt(o)}, {o - fr:.2f} s after the old cut)')

if not a.dry_run:
    for p, s in src.items():
        p.write_text(s, encoding='utf8')
    vt.write_text(video, encoding='utf8')
print(f'{moved} cuts moved to the voice, {len(skipped)} left for the editor' + (' (dry run)' if a.dry_run else ''))
for x in skipped:
    print('  ' + x)
for x in recut_done:
    print('  ' + x + ' (look at its last second: the longer cut may run into the next shot)')
