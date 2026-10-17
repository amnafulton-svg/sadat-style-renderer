// node tools/stills.mjs <out-dir> t1 t2 ...   (t = narration seconds) -> one jpg per time
// Renders single frames of the cut so they can be checked by eye. Uses the project's first composition.
import {bundle} from '@remotion/bundler';
import {ensureBrowser, getCompositions, renderStill} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const [out, ...ts] = process.argv.slice(2);
if (!out || !ts.length) {
  console.error('usage: node tools/stills.mjs <out-dir> t1 t2 ...');
  process.exit(1);
}
fs.mkdirSync(out, {recursive: true});
await ensureBrowser(); // a fresh project downloads headless Chrome once
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
try {
  const [composition] = await getCompositions(serveUrl);
  for (const t of ts) {
    const frame = Math.max(0, Math.min(composition.durationInFrames - 1, Math.round(+t * composition.fps)));
    const file = path.join(out, `t${(+t).toFixed(2).padStart(7, '0')}.jpg`);
    await renderStill({serveUrl, composition, frame, output: file, imageFormat: 'jpeg', jpegQuality: 85});
    console.log(file);
  }
} finally {
  // each bundle is ~1 GB in /tmp: 288 left behind filled 183 GB in 3 days (2026-10-17)
  fs.rmSync(serveUrl, {recursive: true, force: true});
}
