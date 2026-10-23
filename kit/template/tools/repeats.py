"""Perceptual repeat check for validate.py: the same film shot or photo shown twice under different file names.

Section editors cut two clips from one archive film at overlapping seconds (s8_tunnel_drive.mp4 / s9_tunnel_night.mp4),
or save one photo twice. validate.py's name check cannot see that; this compares what is on screen.

Each film is sampled every 0.5 s over the part its scene shows (start=, rate=, scene length; one ffmpeg decode per
file), each photo once.
Frame -> grey, black borders trimmed, centre 80 %, 64-bit DCT hash (pHash). Two scenes repeat when a frame of one is
within MAX_D bits of a frame of the other on at least MIN_HITS frame pairs, or one pair within SURE_D (one hit for
two photos). Tuned on three projects: repeats measured 0-10 bits, the closest unrelated shots 12+.
Hashes are cached in _cache/repeat_hashes.json (file size + mtime keyed), so a re-run takes seconds.

    python tools/repeats.py [--root DIR] [--hook 35] [--debug] [--sheet repeats.jpg]   # validate.py calls check()
"""
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

MAX_D = 10        # pHash bits apart for "same picture" (same shot, other cut ~0-8; different shots of one film 14+)
MIN_HITS = 2      # frame pairs that must match between two films (one stray look-alike frame is not a repeat) ...
SURE_D = 6        # ... unless that one pair is this close (a fast pan sampled out of step matches on one frame only)
STEP = 0.5        # seconds between sampled frames of a film (pans and walking crowds need it this dense)
W, H = 192, 108   # frames are hashed from this size
MIN_STD = 10      # frames flatter than this (black, white flash, fog) say nothing about the shot
_N = 32
_C = np.cos(np.pi * (2 * np.arange(_N)[None, :] + 1) * np.arange(_N)[:, None] / (2 * _N))  # DCT-II basis


def phash(im):
    """64-bit DCT hash of a picture (PIL image or grey array) after trimming black borders and keeping the centre
    80 %; None if the frame is flat (black, white flash, fog)"""
    if isinstance(im, Image.Image):
        im = im.convert('L').resize((W, H) if im.width >= im.height else (H, W))
    g = np.asarray(im, dtype=np.float32)
    rows, cols = np.where(g.mean(1) > 18)[0], np.where(g.mean(0) > 18)[0]  # letterbox / pillarbox / gate
    if len(rows) < 12 or len(cols) < 12:
        return None
    g = g[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    h, w = g.shape
    g = g[int(h * .1):int(h * .9), int(w * .1):int(w * .9)]
    if g.std() < MIN_STD:
        return None
    a = np.asarray(Image.fromarray(g).resize((_N, _N), Image.BILINEAR), dtype=np.float64)
    d = (_C @ a @ _C.T)[:8, :8].flatten()[1:]
    bits = d > np.median(d)
    return int(''.join('1' if b else '0' for b in bits), 2)


def film_hashes(path, t0, n):
    """hashes of n frames from t0, STEP apart, in one decode (one seek per film, not per frame)"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.2f}', '-i', str(path), '-t', f'{n * STEP:.2f}', '-an',
                        '-vf', f'fps={1 / STEP:g},scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], capture_output=True)
    fr = np.frombuffer(r.stdout, np.uint8)
    return [phash(f.reshape(H, W)) for f in fr[:len(fr) // (W * H) * W * H].reshape(-1, W * H)][:n]


def film_frame(path, t):
    """one frame as a picture (for the sheet)"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', str(path), '-frames:v', '1',
                        '-vf', 'scale=480:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
    return Image.open(BytesIO(r.stdout)) if r.stdout else None


def shown(root, scenes):
    """[(scene id, from, to, kind, file, [seconds in the file])] for every film and photo on screen"""
    out = []
    for sid, fr, to, en, b in scenes:
        for fm in re.finditer(r'<F\s+src="([^"]+)"([^>]*)>', b):
            st = re.search(r'start=\{([\d.]+)\}', fm.group(2))
            rate = re.search(r'rate=\{([\d.]+)\}', fm.group(2))
            st, rate = float(st.group(1)) if st else 0.0, float(rate.group(1)) if rate else 1.0
            out.append((sid, fr, to, 'film', root / 'public/footage' / fm.group(1), st, st + (to - fr) * rate))
        for pm in re.finditer(r'<PhotoPrint\s+src="([^"]+)"([^>]*)>', b):
            src, rest = pm.groups()
            fl = re.search(r'film=\{\{\s*start:\s*([\d.]+)(?:,\s*rate:\s*([\d.]+))?', rest)
            at = re.search(r'\bat=\{([\d.]+)\}', rest)
            t0 = max(fr, float(at.group(1))) if at else fr
            if fl:
                st, rate = float(fl.group(1)), float(fl.group(2) or 1)
                out.append((sid, t0, to, 'film', root / 'public/footage' / src, st, st + (to - t0) * rate))
            else:
                out.append((sid, t0, to, 'photo', root / 'public/photos' / src, 0, 0))
    return out


def sample_times(st, en, dur):
    """the fixed STEP grid (STEP/2, 1.5 STEP, ...) inside the shown seconds, so scenes share cached frames"""
    en = min(en, dur - 0.05) if dur else en
    k0, k1 = int(np.ceil(st / STEP - 0.5)), int(np.floor(en / STEP - 0.5))
    return [round((k + 0.5) * STEP, 2) for k in range(k0, k1 + 1)] or [round((k0 + 0.5) * STEP, 2)]


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def save_sheet(root, found, path):
    """one row per repeat: the two matching pictures side by side, scene ids and distance under them"""
    from PIL import ImageDraw
    pic = lambda n, t: (Image.open(root / 'public/photos' / n) if t is None else film_frame(root / 'public/footage' / n, t))
    sh = Image.new('RGB', (2 * 480 + 30, len(found) * 315), 'white')
    dr = ImageDraw.Draw(sh)
    for i, (n1, ta, n2, tb, label) in enumerate(found):
        for j, (n, t) in enumerate(((n1, ta), (n2, tb))):
            im = pic(n, t)
            if im:
                im = im.convert('RGB')
                im.thumbnail((480, 270))
                sh.paste(im, (10 + j * 490, i * 315 + 5))
            dr.text((10 + j * 490, i * 315 + 278), f'{n} {"" if t is None else f"{t:.1f} s"}', fill='black')
        dr.text((10, i * 315 + 295), label, fill='red')
    sh.save(path, quality=85)


def check(root, scenes, hook=35, cache=None, media=None, debug=False, sheet=None):
    """WARN lines for scenes that show the same picture under another file name; sheet=path saves the pairs side by side"""
    root = Path(root)
    cache = Path(cache) if cache else root / '_cache/repeat_hashes.json'
    try:
        C = json.loads(cache.read_text())
    except (OSError, ValueError):
        C = {}
    items = [x for x in shown(root, scenes) if x[4].exists()]
    jobs = {}
    for sid, fr, to, kind, path, st, en in items:
        stt = path.stat()
        tag = f'{path.name}|{stt.st_size}|{int(stt.st_mtime)}'
        if kind == 'photo':
            jobs[(tag, None)] = (path, None)
        else:
            d = (media or {}).get(path.name, {}).get('d') or C.get(tag + '|d') or duration(path)
            C[tag + '|d'] = d
            for t in sample_times(st, en, d):
                jobs[(tag, t)] = (path, t)

    key = lambda k: f'{k[0]}|{k[1]}'
    todo = {}
    for k in jobs:
        if key(k) not in C:
            todo.setdefault(k[0], []).append(k[1])

    def run(tag):
        """hash the missing frames of one file: a photo, or one decode over the film's missing seconds"""
        ts = todo[tag]
        path = jobs[(tag, ts[0])][0]
        try:
            if ts == [None]:
                return [((tag, None), phash(Image.open(path)))]
            ts = sorted(ts)
            hs = film_hashes(path, ts[0], round((ts[-1] - ts[0]) / STEP) + 1)
            grid = {round(ts[0] + i * STEP, 2): h for i, h in enumerate(hs)}
            return [((tag, t), grid.get(t)) for t in ts]
        except Exception:  # unreadable file: other checks report missing media
            return [((tag, t), None) for t in ts]
    with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        for res in ex.map(run, list(todo)):
            for k, h in res:
                C[key(k)] = h
    if todo:
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(C))
        except OSError:
            pass

    # one entry per (scene, file): its hashes with the second each comes from
    shots = []
    for sid, fr, to, kind, path, st, en in items:
        stt = path.stat()
        tag = f'{path.name}|{stt.st_size}|{int(stt.st_mtime)}'
        hs = [(t, C[key((tag, t))]) for (tg, t) in jobs if tg == tag and C.get(key((tg, t))) is not None
              and (t is None or st - 0.01 <= t <= en + 0.2)]
        if hs:
            shots.append((sid, fr, to, kind, path.name, hs))

    out, pairs, found = [], [], []
    for i, (s1, f1, t1, k1, n1, h1) in enumerate(shots):
        for s2, f2, t2, k2, n2, h2 in shots[i + 1:]:
            if n1 == n2 or (f1 < hook and f2 < hook) or k1 != k2:
                continue  # same file: validate.py's name check; both in the hook: allowed; film vs photo: not compared
            ds = [(bin(a ^ b).count('1'), ta, tb) for ta, a in h1 for tb, b in h2]
            hits = [d for d in ds if d[0] <= MAX_D]
            best = min(ds)
            if debug:
                pairs.append((best[0], len(hits), s1, n1, s2, n2))
            if hits and (k1 == 'photo' or best[0] <= SURE_D or len(hits) >= min(MIN_HITS, len(h1), len(h2))):
                d, ta, tb = min(hits)
                found.append((n1, ta, n2, tb, f'{s1} ~ {s2}  d={d}'))
                where = '' if k1 == 'photo' else f' ({n1} {ta:.1f} s ~ {n2} {tb:.1f} s, {len(hits)} matching frames)'
                out.append(f'{s2} at {f2:.1f} s shows the same {"photo" if k1 == "photo" else "film shot"} as {s1} at '
                           f'{f1:.1f} s: {n2} looks like {n1}{where}; cut to a different shot')
    if sheet and found:
        save_sheet(root, found, sheet)
    if debug:
        for p in sorted(pairs)[:25]:
            print('DEBUG d=%d hits=%d  %s %s  ~  %s %s' % p)
    return out


if __name__ == '__main__':
    import argparse
    import time
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument('--hook', type=float, default=35)
    ap.add_argument('--cache', default=None)
    ap.add_argument('--debug', action='store_true', help='print the 25 closest pairs')
    ap.add_argument('--sheet', help='save the repeats side by side to this jpg, to look at them')
    a = ap.parse_args()
    R = Path(a.root)
    s = (R / 'src/timeline/video.tsx').read_text(encoding='utf8')
    s += ''.join(p.read_text(encoding='utf8') for p in sorted((R / 'src/timeline/parts').glob('s*.tsx'),
                                                                key=lambda p: int(p.stem[1:])))
    sc = []
    for b in re.split(r"(?=\{id: ')", s)[1:]:
        m = re.match(r"\{id: '([\w-]+)', from: (-?[\d.]+), to: ([\d.]+|END)", b)
        if m:
            sc.append((m.group(1), float(m.group(2)), 1e9 if m.group(3) == 'END' else float(m.group(3)), '', b))
    try:
        M = json.loads((R / 'src/lib/media.json').read_text())
    except (OSError, ValueError):
        M = {}
    t0 = time.time()
    for w in check(R, sc, a.hook, a.cache, M, a.debug, a.sheet):
        print('WARN ', w)
    print(f'{time.time() - t0:.1f} s')
