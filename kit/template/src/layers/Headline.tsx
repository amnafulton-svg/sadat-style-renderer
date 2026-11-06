// HeadlineCard — a real news article page (producer 2026-11-05, from the Bin Laden reference; restyled 2026-11-06
// "doesn't look professional"): the cleaned page sits in a quiet browser window with the outlet's address, tilted a
// little in depth. It rises in, the camera glides between parts of the page (headline -> the paragraph being read),
// a marker sweeps over the printed words on their cue.
// The picture comes from `node tools/headline.mjs <url> <name> "phrase"`, which prints `w`, `h`, `site` and every box
// ([x, y, w, h] in the page's own pixels). Times are narration seconds.
//   <ConcreteWall dim={0.45}>
//     <HeadlineCard src="headlines/agu.png" w={717} h={1544} site="eos.org" at={1577.0}
//       cam={[{at: 1577.0, box: [40, 70, 637, 67]}, {at: 1578.1, box: [40, 1380, 640, 110]}]}
//       marks={[{at: 1579.7, lines: [[570, 1419, 74, 19], [40, 1445, 172, 19]]}]} />
//   </ConcreteWall>
import React from 'react';
import {Img, interpolate, staticFile} from 'remotion';
import {nf, prog, easeInOut} from '../lib/core';
import {useScene} from '../lib/scene';

type Box = [number, number, number, number];
const BAR = 46; // browser bar height, page pixels

export const HeadlineCard: React.FC<{
  src: string; w: number; h: number; at: number;
  /** the outlet's address shown in the browser bar (tools/headline.mjs prints it), e.g. "telegraph.co.uk" */
  site?: string;
  /** where the camera looks: the first box from the start, each next one glides in from its `at` (fill = share of the frame width) */
  cam: {at: number; box: Box; fill?: number}[];
  /** marker on printed words: `lines` straight from tools/headline.mjs, swept one line after the other */
  marks?: {at: number; lines: Box[]}[];
  /** lean the page the other way (alternate between cards in a row) */
  flip?: boolean;
}> = ({src, w, h, at, site, cam, marks = [], flip = false}) => {
  const {frame, startFrame, durFrames} = useScene();
  const L = (s: number) => nf(s) - startFrame;
  // the camera never comes closer than the whole page width in ~80% of the frame: edges stay visible, text stays readable
  const sMax = (1920 * 0.8) / w;
  const view = (k: {box: Box; fill?: number}) => {
    const [x, y, bw, bh] = k.box;
    const s = Math.min((1920 * (k.fill ?? 0.72)) / bw, (1080 * 0.7) / bh, sMax);
    return {s, cx: x + bw / 2, cy: y + bh / 2, box: k.box};
  };
  let v = view(cam[0]);

  for (let i = 1; i < cam.length; i++) {
    const p = prog(frame, L(cam[i].at), 32, easeInOut);
    if (p <= 0) break;
    const n = view(cam[i]);
    v = {...v, s: v.s + (n.s - v.s) * p, cx: v.cx + (n.cx - v.cx) * p, cy: v.cy + (n.cy - v.cy) * p};

  }
  // a framed page never leaves dead space above its top bar: keep the window top inside the frame
  const s = v.s * interpolate(frame, [0, durFrames], [1, 1.035]);
  const enter = prog(frame, L(at), 22, easeInOut);
  const dir = flip ? -1 : 1;
  const rotY = dir * interpolate(frame, [0, durFrames], [-7, -3.5]) * (0.4 + 0.6 * enter) ;
  const rotX = interpolate(enter, [0, 1], [16, 3.5]);
  const lift = (1 - enter) * 220;

  return (
    <div style={{position: 'absolute', inset: 0, perspective: 2600, perspectiveOrigin: '960px 540px', overflow: 'hidden'}}>
      {/* soft floor light behind the page */}
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 55% at 50% 52%, rgba(255,250,240,0.10), rgba(0,0,0,0) 70%)'}} />
      <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h + BAR, transformOrigin: '0 0', opacity: Math.min(1, enter * 1.6),
        transform: `translate(960px, ${540 + lift}px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(${s}) translate(${-v.cx}px, ${-(v.cy + BAR)}px)`,
        borderRadius: 14, overflow: 'hidden', background: '#fff',
        boxShadow: '0 2px 0 rgba(255,255,255,0.35) inset, 0 40px 90px rgba(0,0,0,0.55), 0 12px 30px rgba(0,0,0,0.45)'}}>
        {/* browser bar */}
        <div style={{position: 'absolute', left: 0, top: 0, width: w, height: BAR, background: '#ececee', borderBottom: '1px solid #d6d6da',
          display: 'flex', alignItems: 'center', gap: 8, padding: '0 16px', boxSizing: 'border-box'}}>
          {[0, 1, 2].map((i) => <div key={i} style={{width: 11, height: 11, borderRadius: 6, background: '#c4c4c9'}} />)}
          <div style={{marginLeft: 14, flex: 1, height: 28, borderRadius: 14, background: '#fff', border: '1px solid #dcdce0',
            display: 'flex', alignItems: 'center', gap: 8, padding: '0 14px', boxSizing: 'border-box',
            fontFamily: 'Inter, "Helvetica Neue", Arial, sans-serif', fontSize: 15, color: '#55555c', letterSpacing: 0.1}}>
            <svg width="11" height="13" viewBox="0 0 11 13"><rect x="1" y="5.5" width="9" height="7" rx="1.5" fill="#8a8a92" /><path d="M3 5.5V4a2.5 2.5 0 0 1 5 0v1.5" stroke="#8a8a92" strokeWidth="1.5" fill="none" /></svg>
            <span style={{fontWeight: 600, color: '#2c2c31'}}>{site ?? ''}</span>
          </div>
        </div>
        <div style={{position: 'absolute', left: 0, top: BAR, width: w, height: h}}>
          <Img src={staticFile(src)} style={{position: 'absolute', inset: 0, width: w, height: h}} />
          {marks.flatMap((m, i) => {
            const total = m.lines.reduce((a, b) => a + b[2], 0) || 1;
            let done = 0;
            return m.lines.map(([x, y, bw, bh], j) => {
              const start = L(m.at) + (14 * done) / total;
              done += bw;
              const p = prog(frame, start, Math.max(4, (14 * bw) / total));
              const tilt = ((i * 7 + j * 3) % 5 - 2) * 0.12;
              return <div key={`${i}-${j}`} style={{position: 'absolute', left: x - 4, top: y + bh * 0.12, width: (bw + 8) * p, height: bh * 0.86,
                background: 'linear-gradient(180deg, rgba(255,226,64,0.55), rgba(255,214,10,0.72) 55%, rgba(255,226,64,0.5))',
                mixBlendMode: 'multiply', borderRadius: '3px 7px 4px 8px', transform: `rotate(${tilt}deg)`, transformOrigin: '0 50%'}} />;
            });
          })}
        </div>
      </div>
      {/* screen-glass sheen sliding across as the page settles */}
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'soft-light',
        background: `linear-gradient(115deg, rgba(255,255,255,0) ${interpolate(frame, [0, durFrames], [10, 60])}%, rgba(255,255,255,0.10) ${interpolate(frame, [0, durFrames], [22, 72])}%, rgba(255,255,255,0) ${interpolate(frame, [0, durFrames], [34, 84])}%)`}} />
      {/* depth: the frame edges fall off */}
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(ellipse 75% 70% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45))'}} />
      {/* top-right shade so the white source tag stays readable over a white page */}
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(ellipse 34% 15% at 84% 4%, rgba(0,0,0,0.62), rgba(0,0,0,0) 100%)'}} />
    </div>
  );
};
