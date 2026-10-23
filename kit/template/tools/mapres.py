"""Blurry close-zoom maps, for validate.py: how many source pixels each screen pixel of a DocMap gets.

DocumentaryMap.tsx draws maps/doc/world.jpg (8192 px for 360 deg = 1920 map units: 4.27 px per unit) and every
spec.basemaps image (px / (bbox degrees * 1920/360)) on a plane scaled by `zoom` screen px per map unit, tilted
(rotateX tilt, rotateZ spin, perspective 1500), so a screen pixel gets src_px_per_unit / (zoom * perspective) source
pixels. Below the limit the picture is blocky mush. The limit is RES on smooth terrain (sea, plains, green Ireland:
soft but fine at 0.12, zoom 30; mottled at 0.09, Zululand zoom 43) and rises with the detail of the world.jpg pixels
under the view (snow and fjords show blocks sooner: Alaska was blocky at 0.18, zoom 24): limit = max(RES, detail / 180),
detail = mean grey step between neighbouring world.jpg pixels (Ireland 6, Zululand 10-15, Chugach 35-60).
The camera is followed like cameraAt(): from (fromCenter, fromZoom = zoom * 0.75 if unset) to (center, zoom * 1.035),
and each step is checked on a grid of screen points against the top basemap under that point.

    python tools/mapres.py [--root DIR]        # standalone, prints every map's worst figure; validate.py calls check()
"""
import math
import re
import struct
from pathlib import Path

RES = 0.12        # source px per screen px on smooth terrain (world.jpg at zoom ~35); more detailed terrain needs more
DETAIL = 180      # limit = max(RES, detail / DETAIL)
MAX_BAD = 0.10    # share of the map on screen that may fall below RES (an edge strip past a basemap counts)
PLANE_W, PLANE_H, PERSP, UPD = 2700, 1800, 1500, 1920 / 360
WORLD = ('maps/doc/world.jpg', (-180.0, -90.0, 180.0, 90.0))


def img_size(path):
    """(w, h) of a jpg/png without PIL; None if unreadable"""
    try:
        with open(path, 'rb') as f:
            d = f.read(2)
            if d == b'\x89P':
                f.seek(16)
                return struct.unpack('>II', f.read(8))
            while d and d != b'':
                m = f.read(2)
                if len(m) < 2 or m[0] != 0xFF:
                    return None
                if m[1] in (0xC0, 0xC1, 0xC2):
                    f.read(3)
                    h, w = struct.unpack('>HH', f.read(4))
                    return w, h
                f.seek(struct.unpack('>H', f.read(2))[0] - 2, 1)
    except OSError:
        return None


_world = {}


def detail(root, bb):
    """mean grey step between neighbouring world.jpg pixels inside bbox (0 without PIL: the limit is then RES)"""
    if 'g' not in _world:
        try:
            from PIL import Image
            import numpy as np
            Image.MAX_IMAGE_PIXELS = None
            _world['g'] = np.asarray(Image.open(root / 'public' / WORLD[0]).convert('L'), dtype=np.int16)
        except Exception:
            _world['g'] = None
    g = _world['g']
    if g is None:
        return 0.0
    h, w = g.shape
    x0, x1 = int((bb[0] + 180) / 360 * w), int((bb[2] + 180) / 360 * w) + 2
    y0, y1 = int((90 - bb[3]) / 180 * h), int((90 - bb[1]) / 180 * h) + 2
    c = g[max(0, y0):y1, max(0, x0):x1]
    if c.shape[0] < 2 or c.shape[1] < 2:
        return 0.0
    return float(abs(c[:, 1:] - c[:, :-1]).mean() + abs(c[1:] - c[:-1]).mean())


def block(s, i, op='{', cl='}'):
    """text of the balanced op..cl block starting at s[i] == op"""
    n = 0
    for j in range(i, len(s)):
        n += (s[j] == op) - (s[j] == cl)
        if n == 0:
            return s[i:j + 1]
    return s[i:]


def bezier(x, x1=0.45, y1=0, x2=0.2, y2=1):
    """CSS cubic-bezier as Remotion's Easing.bezier"""
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        if 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 < x:
            lo = t
        else:
            hi = t
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3


proj = lambda lon, lat: ((lon + 180) * UPD, (90 - lat) * UPD)
nums = lambda t: [float(x) for x in re.findall(r'-?[\d.]+', t)]


def maps(src):
    """[(scene index, spec text)] for every DocMap"""
    return [(m.start(), block(src, src.index('{', m.end()))) for m in re.finditer(r'<DocMap\b[^>]*?spec=\{', src)]


def basemaps(spec, src, root):
    """[(path, bbox, px per map unit)] bottom to top, world.jpg first"""
    out = []
    m = re.search(r'basemaps:\s*\[', spec)
    items = []
    if m:
        body = block(spec, m.end() - 1, '[', ']')[1:-1]
        for it in re.finditer(r"\{[^{}]*?src:\s*'([^']+)'[^{}]*?bbox:\s*\[([^\]]+)\]|\b([A-Z_][A-Z0-9_]*)\b", body):
            if it.group(3):
                c = re.search(rf"const {it.group(3)}\s*=\s*\{{[^{{}}]*?src:\s*'([^']+)'[^{{}}]*?bbox:\s*\[([^\]]+)\]", src)
                if c:
                    items.append((c.group(1), tuple(nums(c.group(2))[:4])))
            else:
                items.append((it.group(1), tuple(nums(it.group(2))[:4])))
    for p, bb in [WORLD] + items:
        wh = img_size(root / 'public' / p)
        if not wh or len(bb) < 4:
            continue
        w, s, e, n = bb
        out.append((p, bb, min(wh[0] / ((e - w) * UPD), wh[1] / ((n - s) * UPD))))
    return out


def camera(spec):
    """cameraAt() inputs: (from xy, from zoom, to xy, to zoom), tilt from/to; None if the zoom is automatic"""
    m = re.search(r'camera:\s*\{([^}]*)\}', spec)
    c = m.group(1) if m else ''
    get = lambda k: re.search(rf'\b{k}:\s*(\[[^\]]*\]|-?[\d.]+)', c)
    z, ctr, fz, fc = get('zoom'), get('center'), get('fromZoom'), get('fromCenter')
    if not z:  # autoCamera(): fit places and route points
        pts = [proj(*nums(x)[:2]) for x in re.findall(r'(?:coordinates|points):\s*(\[\s*-?[\d.]+\s*,\s*-?[\d.]+\s*\])', spec)]
        pts += [proj(*nums(x)[:2]) for x in re.findall(r'\[\s*(-?[\d.]+\s*,\s*-?[\d.]+)\s*\]', ' '.join(re.findall(r'points:\s*\[(.*?)\]\s*[,}]', spec, re.S)))]
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        sx, sy = max(40, max(xs) - min(xs)), max(24, max(ys) - min(ys))
        tz, to = min(1920 / (sx * 1.5), 1080 / (sy * 1.8)), ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    else:
        tz = float(z.group(1))
        to = proj(*nums(ctr.group(1))[:2]) if ctr else None
        if to is None:
            return None
    tz = max(0.6, tz)
    frm = proj(*nums(fc.group(1))[:2]) if fc else to
    fz = max(0.6, float(fz.group(1)) if fz else tz * 0.75)
    t = re.search(r'tilt:\s*\{\s*from:\s*(-?[\d.]+),\s*to:\s*(-?[\d.]+)', spec)
    return frm, fz, to, tz, (float(t.group(1)), float(t.group(2))) if t else (36.0, 22.0)


def worst(spec, src, root, nx=32, ny=18):
    """[(progress, zoom, share of the screen below the limit, lowest source px per screen px, view bbox, limit)]
    per camera step"""
    cam = camera(spec)
    if not cam:
        return []
    frm, fz, to, tz, (t0, t1) = cam
    bms = basemaps(spec, src, root)
    out = []
    for p in (0, 0.25, 0.5, 0.75, 1):
        e = bezier(min(1, p / 0.8))
        zoom = math.exp(math.log(fz) + (math.log(tz) - math.log(fz)) * e) * (1 + 0.035 * p)
        cx, cy = frm[0] + (to[0] - frm[0]) * e, frm[1] + (to[1] - frm[1]) * e
        a, b = math.radians(t0 + (t1 - t0) * e), math.radians(-4 + 4 * e)
        pts = []
        for i in range(nx):
            for j in range(ny):
                X, Y = (i + 0.5) / nx * 1920 - 960, (j + 0.5) / ny * 1080 - 540
                den = PERSP * math.cos(a) + Y * math.sin(a)
                if den <= 0:
                    continue
                y1 = Y * PERSP / den
                s = PERSP / (PERSP - y1 * math.sin(a))
                x1 = X / s
                rx, ry = x1 * math.cos(b) + y1 * math.sin(b), -x1 * math.sin(b) + y1 * math.cos(b)
                if abs(rx) > PLANE_W / 2 or abs(ry) > PLANE_H / 2:
                    continue  # sky past the plane edge
                lon, lat = (cx + rx / zoom) / UPD - 180, 90 - (cy + ry / zoom) / UPD
                ppu = next((r for _, (w, so, ea, n), r in reversed(bms) if w <= lon <= ea and so <= lat <= n), bms[0][2] if bms else 4.27)
                pts.append((lon, lat, ppu / (zoom * s)))
        tot = len(pts)
        if not tot:
            continue
        lons, lats = [q[0] for q in pts], [q[1] for q in pts]
        bb = (min(lons), min(lats), max(lons), max(lats))
        lim = max(RES, detail(root, bb) / DETAIL) if min(q[2] for q in pts) < max(RES, 0.6) else RES
        bad = sum(q[2] < lim for q in pts)
        low = min(q[2] for q in pts)
        out.append((p, zoom, bad / tot, low, bb, lim))
    return out


def check(root, scenes, src):
    """WARN lines for DocMaps whose picture is blocky at some camera step"""
    root = Path(root)
    out = []
    for sid, fr, to, en, b in scenes:
        for _, spec in maps(b):
            steps = worst(spec, src, root)
            badst = [st for st in steps if st[2] > MAX_BAD]
            if not badst:
                continue
            p, zoom, share, low, bb, lim = max(badst, key=lambda st: st[2] - st[3])
            when = 'at the start' if p == 0 else 'at the end' if p == 1 else f'{int(p * 100)} % in'
            out.append(f'{sid}: map at zoom {zoom:.0f} {when} is blocky: {share:.0%} of the screen gets {low:.2f} source px '
                       f'per screen px (min {lim:.2f} for this terrain); add a sharp basemap (Sentinel-2) covering bbox '
                       f'[{bb[0]:.2f}, {bb[1]:.2f}, {bb[2]:.2f}, {bb[3]:.2f}] or pull the camera back')
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args()
    R = Path(a.root)
    s = (R / 'src/timeline/video.tsx').read_text(encoding='utf8')
    s += ''.join(p.read_text(encoding='utf8') for p in sorted((R / 'src/timeline/parts').glob('s*.tsx'),
                                                                key=lambda p: int(p.stem[1:])))
    for b in re.split(r"(?=\{id: ')", s)[1:]:
        m = re.match(r"\{id: '([\w-]+)'", b)
        for _, spec in maps(b):
            st = worst(spec, s, R)
            if st:
                w = max(st, key=lambda x: x[2] - x[3])
                print(f'{m.group(1) if m else "?":24} zoom {st[0][1]:7.1f} -> {st[-1][1]:7.1f}  worst: '
                      f'{w[2]:4.0%} below {w[5]:.2f}, lowest {w[3]:.3f} px/px at zoom {w[1]:.0f}')
    for w in check(R, [(re.match(r"\{id: '([\w-]+)'", b).group(1), 0, 0, '', b) for b in re.split(r"(?=\{id: ')", s)[1:]
                       if re.match(r"\{id: '([\w-]+)'", b)], s):
        print('WARN ', w)
