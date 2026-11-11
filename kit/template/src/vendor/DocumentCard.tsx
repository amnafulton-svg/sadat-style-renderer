import {loadFont} from '@remotion/google-fonts/Poppins';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useVideoConfig} from 'remotion';
import {GridPaper} from './PersonCard';
import type {ArchiveDocument, ArchiveDocumentMark} from './types';

// Document card: a real evidence document (newspaper page, law, letter, telegram, report).
// HOUSE (producer, 2026-11-11, picked from a reference clip over the dimmed page with a lit band, which "looked
// messy"): the clean page, straight, on the house graph paper (producer: "keep the paper background"). It rises in once and lands at reading size,
// then holds; nothing is dimmed or tinted. The quoted words get a yellow highlighter that runs over them as they are
// spoken and stays. The page only glides when the next passage is somewhere else on it.
// The rects come from OCR of the scan (tools/docmark.py), so the marker sits on the real printed words.
const {fontFamily} = loadFont('normal', {weights: ['500', '600'], subsets: ['latin']});

const RED = '#d24a35';
const SLIDE = 20; // frames the page takes to rise in
const LINE_PX = 34; // height a printed line is shown at
const MIN_W = 1040; // page width on screen
const MAX_W = 1480;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.inOut(Easing.cubic);

type Px = {x: number; y: number; w: number; h: number};
type Cam = {f: number; cy: number};

const union = (rs: Px[]): Px => {
  const x0 = Math.min(...rs.map((r) => r.x));
  const y0 = Math.min(...rs.map((r) => r.y));
  const x1 = Math.max(...rs.map((r) => r.x + r.w));
  const y1 = Math.max(...rs.map((r) => r.y + r.h));
  return {x: x0, y: y0, w: x1 - x0, h: y1 - y0};
};

const camera = (keys: Cam[], frame: number): number => {
  let i = 0;
  while (i < keys.length - 1 && keys[i + 1].f <= frame) i++;
  const a = keys[i];
  const b = keys[Math.min(i + 1, keys.length - 1)];
  if (b === a || frame <= a.f) return a.cy;
  const k = ease(Math.min(1, (frame - a.f) / Math.max(1, b.f - a.f)));
  return a.cy + (b.cy - a.cy) * k;
};

// the highlighter follows the voice: line by line, left to right, from the first quoted word to the last
const Mark = ({m, rects, frame, fps, id}: {m: ArchiveDocumentMark; rects: Px[]; frame: number; fps: number; id: string}) => {
  const start = Math.round((m.at - 0.1) * fps);
  const len = Math.max(Math.round(0.6 * fps), m.until ? Math.round((m.until - m.at) * fps) : 0);
  const k = interpolate(frame, [start, start + len], [0, 1], clamp);
  if (k <= 0) return null;
  const style = m.style ?? 'highlight';
  if (style === 'circle') {
    const u = union(rects);
    const rx = u.w * 0.53 + Math.max(22, u.h * 0.4);
    const ry = u.h / 2 + Math.max(16, u.h * 0.5);
    const cx = u.x + u.w / 2;
    const cy = u.y + u.h / 2;
    const d = `M ${cx - rx * 0.7} ${cy - ry * 0.95} C ${cx + rx * 0.2} ${cy - ry * 1.25}, ${cx + rx * 1.1} ${cy - ry * 0.9}, ${cx + rx} ${cy}`
      + ` S ${cx + rx * 0.3} ${cy + ry * 1.12}, ${cx - rx * 0.4} ${cy + ry * 0.98}`
      + ` S ${cx - rx * 1.1} ${cy + ry * 0.2}, ${cx - rx * 0.92} ${cy - ry * 0.35}`
      + ` S ${cx - rx * 0.35} ${cy - ry * 1.15}, ${cx + rx * 0.05} ${cy - ry * 1.05}`;
    return (
      <svg style={{position: 'absolute', inset: 0, overflow: 'visible'}} width="100%" height="100%">
        <path d={d} fill="none" stroke={RED} strokeWidth={Math.max(4, u.h * 0.09)} strokeLinecap="round" pathLength={1}
          strokeDasharray="1 1" strokeDashoffset={1 - k} opacity={0.92} />
      </svg>
    );
  }
  const total = rects.reduce((s, r) => s + r.w, 0);
  let done = 0;
  return (
    <>
      {rects.map((r, i) => {
        const part = Math.max(0, Math.min(1, (k * total - done) / r.w));
        done += r.w;
        if (part <= 0) return null;
        const padY = r.h * 0.1;
        return style === 'underline' ? (
          <div key={`${id}-${i}`} style={{position: 'absolute', left: r.x - 4, top: r.y + r.h + padY * 0.4,
            width: (r.w + 8) * part, height: Math.max(4, r.h * 0.11), background: RED, borderRadius: 3}} />
        ) : (
          <div key={`${id}-${i}`} style={{position: 'absolute', left: r.x - 5, top: r.y - padY, width: (r.w + 10) * part,
            height: r.h + 2 * padY, background: '#ffe81a', mixBlendMode: 'multiply',
            borderRadius: `${r.h * 0.12}px ${r.h * 0.3}px ${r.h * 0.12}px ${r.h * 0.3}px`}} />
        );
      })}
    </>
  );
};

export const DocumentCard = ({doc, frame, durationInFrames, seed}: {
  doc: ArchiveDocument; frame: number; durationInFrames: number; seed: string;
}) => {
  const {fps} = useVideoConfig();
  const marks = [...doc.marks].sort((a, b) => a.at - b.at);
  // reading size: a printed line about LINE_PX tall, the page between MIN_W and MAX_W wide, dark room left and right
  const hs = marks.flatMap((m) => m.rects.map((r) => r[3])).sort((a, b) => a - b);
  const lineH = hs.length ? hs[Math.floor(hs.length / 2)] : 0.02;
  const W = Math.max(MIN_W, Math.min(MAX_W, (LINE_PX / lineH) * doc.aspect));
  const H = W / doc.aspect;
  const px = marks.map((m) => m.rects.map(([x, y, w, h]) => ({x: x * W, y: y * H, w: w * W, h: h * H})));

  // where the page sits: a short page whole and centred; a tall one with the passage a little below the middle,
  // the page top or bottom never pulled further in than a small margin
  const aim = (u: Px): number => (H <= 1000 ? H / 2 : Math.max(540 - 40, Math.min(H - 540 + 40, u.y + u.h / 2 - 50)));
  const land = Math.max(SLIDE, Math.round(doc.at * fps));
  const keys: Cam[] = [{f: 0, cy: px.length ? aim(union(px[0])) : Math.min(H / 2, 500)}];
  marks.forEach((m, i) => {
    if (i === 0) return;
    const prev = keys[keys.length - 1];
    const u = union(px[i]);
    const y0 = u.y - prev.cy + 540, y1 = y0 + u.h;
    if (y0 < 190 || y1 > 900) {
      let a = Math.round((m.at - 0.25) * fps);
      const l = Math.max(a - Math.round(0.8 * fps), prev.f + Math.round(0.2 * fps), land + 4);
      a = Math.max(a, l + Math.round(0.45 * fps));
      keys.push({f: l, cy: prev.cy}, {f: a, cy: aim(u)});
    }
  });
  const cy = camera(keys, frame);
  // one move in: up from below, growing to reading size; then a drift too slow to notice
  const k = interpolate(frame, [land - SLIDE, land], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const rise = interpolate(k, [0, 1], [760, 0]);
  const grow = interpolate(k, [0, 1], [0.68, 1]) * (1 + 0.02 * (frame / Math.max(1, durationInFrames)));
  const tx = 960 - W / 2;
  const ty = 540 - cy + rise;

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <GridPaper frame={frame} duration={durationInFrames} seed={seed} />
      {frame >= land - SLIDE ? (
        <div style={{position: 'absolute', left: 0, top: 0, width: W, height: H, transformOrigin: `${W / 2}px ${cy}px`,
          transform: `translate(${tx}px, ${ty}px) scale(${grow})`, boxShadow: '0 14px 44px rgba(0,0,0,0.38), 0 0 0 1px rgba(0,0,0,0.10)', background: '#f4f2ec'}}>
          <Img src={staticFile(doc.photo)} style={{position: 'absolute', left: 0, top: 0, width: W, height: H,
            filter: 'contrast(1.06) brightness(1.02)'}} />
          {marks.map((m, i) => <Mark key={i} m={m} rects={px[i]} frame={frame} fps={fps} id={`${seed}-${i}`} />)}
        </div>
      ) : null}
      {doc.source ? (
        <div style={{position: 'absolute', right: 56, bottom: 40, fontFamily, fontWeight: 600, fontSize: 21, letterSpacing: 2,
          color: 'rgba(38,35,31,0.72)', background: 'rgba(230,227,219,0.92)', padding: '5px 14px'}}>
          {doc.source.toUpperCase()}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
