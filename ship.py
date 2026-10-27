"""Send one or more Sadat-style video projects to GitHub Actions for rendering.

    python ship.py ..\\latam-doc [..\\other-doc ...] [--composition LatamDoc] [--repo owner/name]

Each video gets its own release and workflow run (all 20 chunk jobs), one after the other.
Each project is a Remotion folder with src/index.ts and public/. Pre-flight: type check, composition
probe (frames/fps). Then zip src/ + public/ + video.json, release, dispatch, print the run link.
Nothing is downloaded: the MP4 is the run's "final-<name>" artifact.
"""
import fcntl
import hashlib
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = 'amnafulton-svg/sadat-style-renderer'
STORED = {'.mp4', '.mov', '.webm', '.mp3', '.m4a', '.aac', '.jpg', '.jpeg', '.png', '.webp', '.zip'}
GH = shutil.which('gh') or r'C:\Program Files\GitHub CLI\gh.exe'
NPX = shutil.which('npx') or 'npx'


def run(cmd, cwd=None, capture=False):
    print('>', ' '.join(str(c) for c in cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture, encoding='utf8', errors='replace')
    if r.returncode:
        if capture:
            print(r.stdout, r.stderr)
        sys.exit(f'failed: {cmd[0]} (exit {r.returncode})')
    return r.stdout if capture else ''


def probe(project, composition):
    out = run([NPX, 'remotion', 'compositions', 'src/index.ts'], cwd=project, capture=True)
    found = {m[0]: (int(m[1]), int(m[2])) for m in re.findall(r'^(\S+)\s+(\d+)\s+\d+x\d+\s+(\d+)', out, re.M)}
    if not found:
        sys.exit(f'{project}: no compositions found\n{out}')
    if composition is None:
        if len(found) > 1:
            sys.exit(f'{project}: several compositions {list(found)}; pass --composition')
        composition = next(iter(found))
    if composition not in found:
        sys.exit(f'{project}: composition {composition} not in {list(found)}')
    fps, frames = found[composition]
    return {'composition': composition, 'fps': fps, 'frames': frames}


# GitHub refuses release files of 2 GiB or more (America Had No Credit Cards: 267 clips, 2.47 GB). A bigger video
# goes up as <name>.zip (video.json, src/ and the first media) + <name>.zip.part2, .part3 ... each a whole zip of
# more public/ files; unpack.sh unzips them all. The discover job only lists *.zip, so a video is still one zip there.
PART_LIMIT = 1_900_000_000


def make_zip(project, meta, dest):
    """Zips the project into dest (and dest.partN when it is too big for one release file); returns the files."""
    files = [p for top in ('src', 'public') for p in sorted((project / top).rglob('*')) if p.is_file()]
    for old in dest.parent.glob(dest.name + '.part*'):
        old.unlink()
    parts, z, size = [], None, 0
    for p in files:
        n = p.stat().st_size
        if z is None or (size + n > PART_LIMIT and size):
            if z:
                z.close()
            parts.append(dest if not parts else dest.with_name(f'{dest.name}.part{len(parts) + 1}'))
            z, size = zipfile.ZipFile(parts[-1], 'w'), 0
            if len(parts) == 1:
                z.writestr('video.json', json.dumps(meta, indent=2))
        if n >= PART_LIMIT:
            sys.exit(f'{p}: {n / 1e6:.0f} MB is too big for one GitHub release file')
        kind = zipfile.ZIP_STORED if p.suffix.lower() in STORED else zipfile.ZIP_DEFLATED
        z.write(p, p.relative_to(project).as_posix(), compress_type=kind)
        size += n
    z.close()
    for f in parts:
        print(f'  {f.name}: {f.stat().st_size / 1e6:.0f} MB')
    return parts


def prepare(project, a, zips):
    """type check, probe and zip one project; returns its release files"""
    if not (project / 'src' / 'index.ts').exists() or not (project / 'public').is_dir():
        sys.exit(f'{project}: needs src/index.ts and public/')
    if not a.no_tsc:
        run([NPX, 'tsc', '--noEmit'], cwd=project)
    meta = probe(project, a.composition)
    print(f'{project.name}: {meta}')
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', project.name)
    return make_zip(project, meta, zips / f'{name}.zip')


def dispatch(files, a, zips):
    """one release + one workflow run (all 20 chunk jobs) for one video; returns the run"""
    # One release + dispatch at a time on this machine (Classic Studio sends several videos at once): the lock keeps
    # the tag unique and lets the run lookup below find this dispatch, not another video's (2026-10-17 tag clash).
    lock = open(zips / '.ship.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX)
    stem = next(f.stem for f in files if f.suffix == '.zip')
    tag = 'r' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + hashlib.md5(stem.encode()).hexdigest()[:6]
    run([GH, 'release', 'create', tag, *map(str, files), '--repo', a.repo, '--title', tag, '--notes', stem])
    for f in files:
        f.unlink()
    run([GH, 'workflow', 'run', 'render.yml', '--repo', a.repo, '--ref', 'main',
         '-f', f'release_tag={tag}', '-f', 'workers_per_video=20'])
    time.sleep(6)
    out = run([GH, 'run', 'list', '--repo', a.repo, '--workflow', 'render.yml', '--limit', '1',
               '--json', 'databaseId,url,status'], capture=True)
    r = json.loads(out)[0]
    time.sleep(2)
    lock.close()
    print(f'\n{stem}: release {tag} · 20 chunk jobs')
    print(f'run: {r["url"]}  ({r["status"]})', flush=True)
    return r


def wait(r, a):
    """until the run is completed (gh hiccups are retried)"""
    while True:
        p = subprocess.run([GH, 'run', 'view', str(r['databaseId']), '--repo', a.repo, '--json', 'status,conclusion'],
                           text=True, capture_output=True)
        try:
            j = json.loads(p.stdout)
            if j['status'] == 'completed':
                print(f'run {r["databaseId"]}: {j["conclusion"]}', flush=True)
                return
        except (ValueError, KeyError):
            pass
        time.sleep(60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('projects', nargs='+')
    ap.add_argument('--composition', help='composition id (only needed when a project has several)')
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--no-tsc', action='store_true', help='skip the type check')
    a = ap.parse_args()
    zips = HERE / 'zips'
    zips.mkdir(exist_ok=True)
    # Every video gets its own release and run with all 20 chunk jobs, one after the other: 5 videos in one run
    # (4 jobs each) were still rendering after 2.5 h (2026-10-27). The next video is zipped while the last one
    # renders and sent when its run is done.
    last = None
    for proj in a.projects:
        files = prepare(Path(proj).resolve(), a, zips)
        if last:
            wait(last, a)
        last = dispatch(files, a, zips)
    print('when a run is green, download the MP4 from its run page (artifact final-<name>)')


if __name__ == '__main__':
    main()
