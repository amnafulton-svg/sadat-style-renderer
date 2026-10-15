// Reads video.json from every release zip and splits each video into frame-range chunks.
import {execFileSync} from 'node:child_process';
import {readdirSync} from 'node:fs';
import {basename, join} from 'node:path';

const dir = process.argv[2] || 'incoming';
const workers = Math.max(1, Number.parseInt(process.argv[3] || '20', 10) || 20);
const zips = readdirSync(dir).filter((n) => n.toLowerCase().endsWith('.zip')).sort();
if (zips.length === 0) throw new Error(`No zip files in ${dir}`);

const videos = [];
const chunks = [];
for (const zip of zips) {
  const stem = basename(zip, '.zip').replace(/[^a-zA-Z0-9._-]+/g, '_').slice(0, 90) || 'video';
  const meta = JSON.parse(execFileSync('unzip', ['-p', join(dir, zip), 'video.json'], {encoding: 'utf8'}));
  const frames = Number(meta.frames);
  if (!meta.composition || !Number.isFinite(frames) || frames < 1) throw new Error(`${zip}: bad video.json ${JSON.stringify(meta)}`);
  const n = Math.min(workers, frames);
  videos.push({zip_name: zip, stem, composition: meta.composition, chunk_count: n, fps: meta.fps, frames});
  for (let i = 0; i < n; i++) {
    const start = Math.floor((i * frames) / n);
    const end = Math.floor(((i + 1) * frames) / n) - 1;
    chunks.push({zip_name: zip, stem, composition: meta.composition, chunk_id: String(i + 1).padStart(3, '0'), frames: `${start}-${end}`});
  }
}
console.log(`chunks=${JSON.stringify({include: chunks})}`);
console.log(`videos=${JSON.stringify({include: videos})}`);
