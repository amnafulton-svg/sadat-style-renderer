// node tools/stills.mjs <out-dir> t1 t2 ...   (t = narration seconds) -> one jpg per time
//   a time like sp2+4.5 = 4.5 s into the 2nd leader's speech (src/lib/speeches.json); narration seconds skip the speeches
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
const spFile = path.resolve('src/lib/speeches.json');
const speeches = (fs.existsSync(spFile) ? JSON.parse(fs.readFileSync(spFile, 'utf8')) : []).sort((a, b) => a.at - b.at);
// same as vf() in src/lib/speeches.ts: a narration second -> the frame of the finished video
const videoFrame = (t, fps) => {
  const f = (sec) => Math.round(sec * fps);
  const m = /^sp(\d+)\+([\d.]+)$/.exec(t);
  if (m) {
    const k = +m[1] - 1;
    if (!speeches[k]) throw new Error(`no speech ${m[1]} in src/lib/speeches.json`);
    // the speech starts where the narration stopped, after the speeches before it
    return f(speeches[k].at) + speeches.slice(0, k).reduce((a, s) => a + f(s.dur), 0) + f(+m[2]);
  }
  const n = f(+t);
  return n + speeches.filter((s) => f(s.at) <= n).reduce((a, s) => a + f(s.dur), 0);
};
await ensureBrowser(); // a fresh project downloads headless Chrome once
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
try {
  const [composition] = await getCompositions(serveUrl);
  for (const t of ts) {
    const frame = Math.max(0, Math.min(composition.durationInFrames - 1, videoFrame(t, composition.fps)));
    const name = /^sp/.test(t) ? t.replace('+', '_') : `t${(+t).toFixed(2).padStart(7, '0')}`;
    const file = path.join(out, `${name}.jpg`);
    await renderStill({serveUrl, composition, frame, output: file, imageFormat: 'jpeg', jpegQuality: 85});
    console.log(file);
  }
} finally {
  // each bundle is ~1 GB in /tmp: 288 left behind filled 183 GB in 3 days (2026-10-17)
  fs.rmSync(serveUrl, {recursive: true, force: true});
}
