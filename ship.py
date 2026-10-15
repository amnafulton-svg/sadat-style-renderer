"""Send one or more Sadat-style video projects to GitHub Actions for rendering.

    python ship.py ..\\latam-doc [..\\other-doc ...] [--composition LatamDoc] [--repo owner/name]

All videos in one call go into ONE release and ONE workflow run (20 chunk jobs split between them).
Each project is a Remotion folder with src/index.ts and public/. Pre-flight: type check, composition
probe (frames/fps). Then zip src/ + public/ + video.json, release, dispatch, print the run link.
Nothing is downloaded: the MP4 is the run's "final-<name>" artifact.
"""
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


def make_zip(project, meta, dest):
    with zipfile.ZipFile(dest, 'w') as z:
        z.writestr('video.json', json.dumps(meta, indent=2))
        for top in ('src', 'public'):
            for p in sorted((project / top).rglob('*')):
                if p.is_file():
                    kind = zipfile.ZIP_STORED if p.suffix.lower() in STORED else zipfile.ZIP_DEFLATED
                    z.write(p, p.relative_to(project).as_posix(), compress_type=kind)
    print(f'  {dest.name}: {dest.stat().st_size / 1e6:.0f} MB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('projects', nargs='+')
    ap.add_argument('--composition', help='composition id (only needed when a project has several)')
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--no-tsc', action='store_true', help='skip the type check')
    a = ap.parse_args()

    zips = HERE / 'zips'
    zips.mkdir(exist_ok=True)
    tag = 'r' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    files = []
    for proj in a.projects:
        project = Path(proj).resolve()
        if not (project / 'src' / 'index.ts').exists() or not (project / 'public').is_dir():
            sys.exit(f'{project}: needs src/index.ts and public/')
        if not a.no_tsc:
            run([NPX, 'tsc', '--noEmit'], cwd=project)
        meta = probe(project, a.composition)
        print(f'{project.name}: {meta}')
        name = re.sub(r'[^A-Za-z0-9._-]+', '_', project.name)
        dest = zips / f'{name}.zip'
        make_zip(project, meta, dest)
        files.append(dest)

    workers = max(1, 20 // len(files))
    run([GH, 'release', 'create', tag, *map(str, files), '--repo', a.repo, '--title', tag,
         '--notes', ', '.join(f.stem for f in files)])
    for f in files:
        f.unlink()
    run([GH, 'workflow', 'run', 'render.yml', '--repo', a.repo, '--ref', 'main',
         '-f', f'release_tag={tag}', '-f', f'workers_per_video={workers}'])
    time.sleep(6)
    out = run([GH, 'run', 'list', '--repo', a.repo, '--workflow', 'render.yml', '--limit', '1',
               '--json', 'databaseId,url,status'], capture=True)
    r = json.loads(out)[0]
    print(f'\nrelease {tag} · {workers} chunk jobs per video')
    print(f'run: {r["url"]}  ({r["status"]})')
    print('when it is green, download the MP4 from the run page (artifact final-<name>)')


if __name__ == '__main__':
    main()
