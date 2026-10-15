"""Find and fetch real media. Downloads go to _cache/ (data only: never run anything from there).

    python tools/source.py ia-search "panama canal construction" [--rows 15]
    python tools/source.py ia-files <identifier>                  # video files + rights of one archive.org item
    python tools/source.py ia-get <identifier> "<file>" <topic>   # -> _cache/<topic>/<name>.<ext>
    python tools/source.py commons "<query>" <key> [--rows 8] [--video]
          # -> _cache/commons/<key>_<n>.*, <key>.json (title/license/date/page), <key>_sheet.jpg
    python tools/source.py sheet <video-file-or-url> out.jpg [--start S] [--every 1] [--count 40]
          # contact sheet with the time on every tile, to pick clean in-points
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / '_cache'
UA = {'User-Agent': 'sadat-style-video-kit/1.0 (documentary research)'}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return json.loads(r.read().decode('utf8'))


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    tmp = dest.with_name(dest.name + '.part')
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(tmp, 'wb') as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)
    return dest


def ia_search(q, rows):
    fields = ('identifier', 'title', 'year', 'licenseurl', 'rights')
    url = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode(
        [('q', f'({q}) AND mediatype:movies'), ('rows', rows), ('output', 'json')] + [('fl[]', f) for f in fields])
    for d in get(url)['response']['docs']:
        rights = str(d.get('rights', ''))
        lic = d.get('licenseurl') or rights or 'unclear'
        flag = '  ** ALL RIGHTS RESERVED: skip' if re.search(r'all rights reserved', rights, re.I) else ''
        print(f"{d['identifier']:<55} {str(d.get('year', '')):<6} {str(d.get('title', ''))[:70]}  [{str(lic)[:50]}]{flag}")


def ia_files(ident):
    m = get(f'https://archive.org/metadata/{urllib.parse.quote(ident)}')
    md = m.get('metadata', {})
    print('title :', md.get('title'))
    print('year  :', md.get('year') or md.get('date'))
    print('rights:', md.get('licenseurl') or md.get('rights') or 'unclear')
    for f in m.get('files', []):
        if re.search(r'\.(mp4|ogv|mpeg|mpg|avi|mov|mkv|webm)$', f['name'], re.I):
            size = int(f.get('size', 0) or 0) / 1e6
            print(f"  {f['name']:<70} {size:8.1f} MB  {f.get('format', '')}  {f.get('length', '')}")


def ia_get(ident, name, topic):
    stem = re.sub(r'[^A-Za-z0-9_-]+', '_', Path(name).stem)[:40]
    dest = CACHE / topic / f'{stem}{Path(name).suffix.lower()}'
    download(f'https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(name)}', dest)
    print(dest)


def commons(q, key, rows, video):
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrlimit': rows,
        'gsrsearch': q + (' filetype:video' if video else ' filetype:bitmap'),
        'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': 2400})
    pages = sorted(get(url).get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 0))
    out, files = [], []
    for i, p in enumerate(pages):
        ii = p['imageinfo'][0]
        meta = ii.get('extmetadata', {})
        src = ii['url'] if video else ii.get('thumburl', ii['url'])
        ext = Path(urllib.parse.urlparse(src).path).suffix.lower() or '.jpg'
        dest = CACHE / 'commons' / f'{key}_{i}{ext}'
        try:
            download(src, dest)
        except Exception as e:
            print('  fail', p['title'], e)
            continue
        strip = lambda k: re.sub('<[^>]+>', '', meta.get(k, {}).get('value', '')).strip()
        rec = {'file': dest.relative_to(ROOT).as_posix(), 'title': p['title'], 'page': ii.get('descriptionurl'),
               'size': f"{ii.get('width')}x{ii.get('height')}", 'license': strip('LicenseShortName'),
               'date': re.sub(r'date QS:.*', '', strip('DateTimeOriginal'))[:40]}
        out.append(rec)
        files.append(dest)
        print(f"  {dest.name:<22} {rec['size']:<11} {rec['license']:<18} {rec['date']:<14} {p['title'][5:80]}")
    (CACHE / 'commons').mkdir(parents=True, exist_ok=True)
    json.dump(out, open(CACHE / 'commons' / f'{key}.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False)
    if files and not video:
        sheet_images(files, CACHE / 'commons' / f'{key}_sheet.jpg')
        print('sheet:', CACHE / 'commons' / f'{key}_sheet.jpg')


def font(n):
    from PIL import ImageFont
    for f in ('arial.ttf', 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/Library/Fonts/Arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet_images(files, out, cols=4, tw=420, th=320):
    from PIL import Image, ImageDraw
    rows = (len(files) + cols - 1) // cols
    im = Image.new('RGB', (cols * (tw + 8), rows * (th + 28)), 'white')
    d = ImageDraw.Draw(im)
    f = font(16)
    for i, p in enumerate(files):
        x, y = (i % cols) * (tw + 8), (i // cols) * (th + 28)
        try:
            t = Image.open(p).convert('RGB')
            w, h = t.size
            t.thumbnail((tw, th))
            im.paste(t, (x, y + 24))
            d.text((x + 2, y + 3), f'{Path(p).name}  {w}x{h}', fill='black', font=f)
        except Exception as e:
            d.text((x + 2, y + 3), f'{Path(p).name} ERROR {e}', fill='red', font=f)
    im.save(out, quality=82)


def sheet_video(src, out, start, every, count):
    from PIL import Image, ImageDraw
    out = Path(out)
    tmp = out.with_suffix('.tiles')
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = []
    for k in range(count):
        t = start + k * every
        o = tmp / f'{k:03d}.jpg'
        r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(src), '-frames:v', '1', '-vf', 'scale=320:-2', str(o)])
        if r.returncode or not o.exists():
            break
        tiles.append((t, o))
    if not tiles:
        sys.exit('no frames (bad file, or start past the end)')
    cols = 8
    th = Image.open(tiles[0][1]).height
    im = Image.new('RGB', (cols * 324, ((len(tiles) + cols - 1) // cols) * (th + 22)), 'white')
    d = ImageDraw.Draw(im)
    f = font(15)
    for i, (t, o) in enumerate(tiles):
        x, y = (i % cols) * 324, (i // cols) * (th + 22)
        im.paste(Image.open(o), (x, y + 20))
        d.text((x + 2, y + 2), f'{t:.1f}s', fill='black', font=f)
    im.save(out, quality=80)
    for _, o in tiles:
        o.unlink()
    tmp.rmdir()
    print(out, f'{len(tiles)} tiles from {start}s every {every}s')


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest='cmd', required=True)
p = sp.add_parser('ia-search'); p.add_argument('q'); p.add_argument('--rows', type=int, default=15)
p = sp.add_parser('ia-files'); p.add_argument('id')
p = sp.add_parser('ia-get'); p.add_argument('id'); p.add_argument('file'); p.add_argument('topic')
p = sp.add_parser('commons'); p.add_argument('q'); p.add_argument('key')
p.add_argument('--rows', type=int, default=8); p.add_argument('--video', action='store_true')
p = sp.add_parser('sheet'); p.add_argument('src'); p.add_argument('out')
p.add_argument('--start', type=float, default=0); p.add_argument('--every', type=float, default=1)
p.add_argument('--count', type=int, default=40)
a = ap.parse_args()
if a.cmd == 'ia-search':
    ia_search(a.q, a.rows)
elif a.cmd == 'ia-files':
    ia_files(a.id)
elif a.cmd == 'ia-get':
    ia_get(a.id, a.file, a.topic)
elif a.cmd == 'commons':
    commons(a.q, a.key, a.rows, a.video)
else:
    sheet_video(a.src, a.out, a.start, a.every, a.count)
