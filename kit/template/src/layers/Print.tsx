// Photo prints and the annotations the reference puts on them.
// PhotoPrint: a real photo as a physical print (white border, slight tilt, drop shadow) that flies in from
//   off-screen in ~0.3 s and settles, one per narrated beat, accumulating into a cluster. WHY: a group of
//   people / a list of things is shown as evidence being laid on the table, so the count builds with the voice.
// NameStrip: torn white paper strip with a serif name, slapped on when the person is NAMED.
// RedCircle: hand-drawn marker loop around one face/detail: "this one".
// BlackTag / DateTag: small black label (who / when), the reference's date & name tags.
import React from 'react';
import {Img, OffthreadVideo, interpolate, staticFile} from 'remotion';
import {C, FONT, easeOut, prog, rand} from '../lib/core';
import {useCue, useScene} from '../lib/scene';
import {GRADE, Grade} from './Film';
import {Z_LABEL, safeY} from './Type';

type From = 'left' | 'right' | 'top' | 'bottom' | 'fade';

export const PhotoPrint: React.FC<{
  src: string;
  at: number; // narration s when it lands
  x: number; // centre, px
  y: number;
  w: number; // print width incl. border, px
  rot?: number;
  from?: From;
  grade?: Grade;
  border?: number;
  objectPosition?: string;
  aspect?: number; // force picture aspect (w/h), cropping the photo
  drift?: number; // px of slow drift over the scene
  film?: {start: number; rate?: number}; // src is then a clip in public/footage: moving film inside the print (needs aspect)
  children?: React.ReactNode; // annotations in print-local px
}> = ({src, at, x, y, w, rot = 0, from = 'bottom', grade = 'sepia', border = 14, objectPosition = 'center', aspect, drift = 18, film, children}) => {
  const cue = useCue();
  const {frame, durFrames} = useScene();
  const start = cue(at) - 8; // lands on the word: the 8-frame flight ends as the word starts
  const p = prog(frame, start, 9, easeOut);
  const off = {left: [-1500, 0], right: [1500, 0], top: [0, -1100], bottom: [0, 1100], fade: [0, 0]}[from];
  const dx = off[0] * (1 - p);
  const dy = off[1] * (1 - p);
  const r = rot + (from === 'fade' ? 0 : (1 - p) * (rand(x + y) > 0.5 ? 9 : -9));
  const opacity = from === 'fade' ? p : frame < start ? 0 : 1;
  const d = interpolate(frame, [0, durFrames], [0, drift]);
  return (
    <div
      style={{
        position: 'absolute',
        // whole-px left/top + the moving part in transform: Chrome snaps left/top to whole pixels, so a slow
        // drift there stepped 1 px every ~0.7 s and the prints shook (Alaska 2026-10-23); transforms move sub-pixel
        left: x - w / 2,
        top: y,
        width: w,
        transform: `translate(${dx + d * 0.6}px, ${dy - d * 0.3}px) translateY(-50%) rotate(${r}deg) scale(${1 + (1 - p) * 0.06})`,
        opacity,
        background: '#f1ece0',
        padding: border,
        boxShadow: '0 22px 50px rgba(0,0,0,0.65), 0 4px 10px rgba(0,0,0,0.5)',
      }}
    >
      <div style={{position: 'relative', width: '100%', aspectRatio: aspect ? `${aspect}` : undefined, overflow: aspect || film ? 'hidden' : 'visible'}}>
        {film ? (
          <OffthreadVideo
            src={staticFile(`footage/${src}`)}
            startFrom={Math.round(film.start * 25)}
            playbackRate={film.rate ?? 1}
            muted
            style={{display: 'block', width: '100%', height: '100%', objectFit: 'cover', objectPosition, filter: GRADE[grade]}}
          />
        ) : (
          <Img
            src={staticFile(`photos/${src}`)}
            style={{display: 'block', width: '100%', height: aspect ? '100%' : 'auto', objectFit: 'cover', objectPosition, filter: GRADE[grade]}}
          />
        )}
        {children}
      </div>
    </div>
  );
};

/** torn white paper strip with a serif name; slapped on (scale 1.3 -> 1) on the named word */
export const NameStrip: React.FC<{text: string; at: number; x: number; y: number; rot?: number; size?: number; sub?: string}> = ({
  text,
  at,
  x,
  y,
  rot = -3,
  size = 44,
  sub,
}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 6);
  const jag = Array.from({length: 18}, (_, i) => `${(i / 17) * 100}% ${i % 2 ? 0 : 7 + rand(i + text.length) * 8}%`).join(',');
  const jagB = Array.from({length: 18}, (_, i) => `${100 - (i / 17) * 100}% ${i % 2 ? 100 : 93 - rand(i * 3 + text.length) * 8}%`).join(',');
  return (
    <div
      style={{
        position: 'absolute',
        left: Math.max(260, Math.min(x, 1660)),
        top: safeY(y, size * 1.25 + 30 + (sub ? size : 0)),
        transform: `translate(-50%,-50%) rotate(${rot}deg) scale(${1.3 - 0.3 * p})`,
        opacity: p,
        background: '#f6f3ec',
        padding: '16px 34px 14px',
        clipPath: `polygon(${jag},${jagB})`,
        boxShadow: '0 6px 14px rgba(0,0,0,.5)',
        zIndex: Z_LABEL,
        textAlign: 'center',
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{fontFamily: FONT.serif, fontSize: size, color: '#151515', lineHeight: 1.05}}>{text}</div>
      {sub && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: size * 0.5, color: '#444', marginTop: 4}}>{sub}</div>}
    </div>
  );
};

/** hand-drawn marker ellipse that draws itself in ~0.5 s (coordinates in the parent's px) */
export const RedCircle: React.FC<{at: number; cx: number; cy: number; rx: number; ry: number; stroke?: number}> = ({at, cx, cy, rx, ry, stroke = 7}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 12);
  // slightly overshooting, wobbly loop like a real marker stroke
  const pts = Array.from({length: 61}, (_, i) => {
    const a = (i / 60) * Math.PI * 2.15 - Math.PI / 2;
    const wob = 1 + 0.05 * Math.sin(i * 0.9) + 0.03 * (i / 60);
    return `${cx + Math.cos(a) * rx * wob},${cy + Math.sin(a) * ry * wob}`;
  });
  const len = Math.PI * (rx + ry) * 1.1;
  return (
    <svg style={{position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible', pointerEvents: 'none'}}>
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={C.red}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - p)}
        opacity={0.92}
      />
    </svg>
  );
};

/** small black label: white serif line + optional italic second line (name/role, place/year) */
export const BlackTag: React.FC<{at: number; x: number; y: number; line1: string; line2?: string; size?: number; align?: 'left' | 'right'}> = ({
  at,
  x,
  y,
  line1,
  line2,
  size = 46,
  align = 'left',
}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at) - 3, 8);
  const w = Math.max(line1.length * size * 0.7, (line2?.length ?? 0) * size * 0.58 * 0.5) + 44; // a long tag never runs off the frame
  return (
    <div
      style={{
        position: 'absolute',
        [align]: align === 'left' ? Math.min(x, 1920 - 48 - w) : 1920 - Math.max(x, 48 + w),
        top: y,
        background: C.tag,
        padding: '12px 22px 12px',
        opacity: p,
        transform: `translateX(${(1 - p) * (align === 'left' ? -30 : 30)}px)`,
        boxShadow: '0 8px 20px rgba(0,0,0,.5)',
        zIndex: Z_LABEL,
      }}
    >
      <div style={{fontFamily: FONT.serif, color: '#f4f0e6', fontSize: size, lineHeight: 1.1, whiteSpace: 'nowrap'}}>{line1}</div>
      {line2 && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', color: '#bdb6a6', fontSize: size * 0.58, marginTop: 4, whiteSpace: 'nowrap'}}>{line2}</div>}
    </div>
  );
};

/** black date tag with white serif date ("24 October 1972" in the reference); typed on letter by letter */
export const DateTag: React.FC<{at: number; text: string; x: number; y: number; size?: number}> = ({at, text, x, y, size = 46}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 4;
  const n = Math.max(0, Math.min(text.length, Math.floor((frame - s) / 1.2)));
  const left = Math.min(x, 1920 - 48 - (text.length * size * 0.62 + 56)); // a long date never runs off the right edge
  return (
    <div style={{position: 'absolute', left, top: Math.max(40, Math.min(y, 1040 - size * 1.25 - 28)), background: C.tag, padding: '14px 28px', opacity: frame >= s ? 1 : 0, boxShadow: '0 8px 20px rgba(0,0,0,.5)', zIndex: Z_LABEL}}>
      <span style={{fontFamily: FONT.serif, fontSize: size, color: '#f4f0e6', whiteSpace: 'pre'}}>{text.slice(0, n)}</span>
      <span style={{fontFamily: FONT.serif, fontSize: size, color: 'transparent', whiteSpace: 'pre'}}>{text.slice(n)}</span>
    </div>
  );
};
