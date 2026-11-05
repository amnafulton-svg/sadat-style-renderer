// HeadlineCard — a real news article page on the wall (producer 2026-11-05, from the Bin Laden reference): it rises
// in, the camera glides between parts of the page (headline -> the paragraph being read) and a highlighter sweeps
// over the printed words on their cue. The picture comes from `node tools/headline.mjs <url> <name> "phrase"`, which
// prints `w`, `h` and every box ([x, y, w, h] in the page's own pixels). Times are narration seconds.
//   <ConcreteWall dim={0.45}>
//     <HeadlineCard src="headlines/agu.png" w={717} h={1544} at={1577.0}
//       cam={[{at: 1577.0, box: [40, 70, 637, 67]}, {at: 1578.1, box: [40, 1380, 640, 110]}]}
//       marks={[{at: 1579.7, lines: [[570, 1419, 74, 19], [40, 1445, 172, 19]]}]} />
//   </ConcreteWall>
import React from 'react';
import {Img, interpolate, staticFile} from 'remotion';
import {nf, prog, easeInOut} from '../lib/core';
import {useScene} from '../lib/scene';

type Box = [number, number, number, number];
export const HeadlineCard: React.FC<{
  src: string; w: number; h: number; at: number;
  /** where the camera looks: the first box from the start, each next one glides in from its `at` (fill = share of the frame width) */
  cam: {at: number; box: Box; fill?: number}[];
  /** highlighter on printed words: `lines` straight from tools/headline.mjs, swept one line after the other */
  marks?: {at: number; lines: Box[]}[];
}> = ({src, w, h, at, cam, marks = []}) => {
  const {frame, startFrame, durFrames} = useScene();
  const L = (s: number) => nf(s) - startFrame;
  const view = (k: {box: Box; fill?: number}) => {
    const [x, y, bw, bh] = k.box;
    const s = Math.min((1920 * (k.fill ?? 0.8)) / bw, (1080 * 0.86) / bh);
    return {s, cx: x + bw / 2, cy: y + bh / 2};
  };
  let v = view(cam[0]);
  for (let i = 1; i < cam.length; i++) {
    const p = prog(frame, L(cam[i].at), 30, easeInOut);
    if (p <= 0) break;
    const n = view(cam[i]);
    v = {s: v.s + (n.s - v.s) * p, cx: v.cx + (n.cx - v.cx) * p, cy: v.cy + (n.cy - v.cy) * p};
  }
  const s = v.s * interpolate(frame, [0, durFrames], [1, 1.04]);
  const enter = prog(frame, L(at), 14);
  const tx = 960 - s * v.cx;
  const ty = 540 - s * v.cy + (1 - enter) * 160;
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, transformOrigin: '0 0',
      transform: `translate(${tx}px, ${ty}px) scale(${s})`, opacity: enter,
      background: '#fff', borderRadius: 4, boxShadow: '0 30px 80px rgba(0,0,0,0.65)'}}>
      <Img src={staticFile(src)} style={{position: 'absolute', inset: 0, width: w, height: h}} />
      {marks.flatMap((m, i) => {
        const total = m.lines.reduce((a, b) => a + b[2], 0) || 1;
        let done = 0;
        return m.lines.map(([x, y, bw, bh], j) => {
          const start = L(m.at) + (12 * done) / total;
          done += bw;
          const p = prog(frame, start, Math.max(3, (12 * bw) / total));
          return <div key={`${i}-${j}`} style={{position: 'absolute', left: x - 3, top: y - 1, width: (bw + 6) * p, height: bh + 2,
            background: 'rgba(255, 212, 0, 0.55)', mixBlendMode: 'multiply', borderRadius: 2}} />;
        });
      })}
    </div>
  );
};
