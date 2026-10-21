// Set pieces that hold a whole scene.
// Camera     — keyframed move over a large board (evidence-board drift / pull back). The reference moves the
//              camera, never the photos, once they have landed: the viewer reads the board like an investigator.
// MapBlinds  — period map under venetian-blind light that slides across it, with a red ruler line drawn on cue.
//              WHY: the reference shows maps as documents in a dark office, not as GIS graphics — power drawn by hand.
// Epigraph   — cold-open quote on black, line by line, then the attribution (the thesis before the story).
// TitleCard  — grunge-eroded condensed title + gold subtitle (the reference's 0:23 title).
import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile} from 'remotion';
import {C, FONT, easeInOut, prog} from '../lib/core';
import {useCue, useScene} from '../lib/scene';

export type Key = {at: number; x: number; y: number; s: number}; // narration s; board-px centre + scale
/** keys are narration seconds; the camera eases between them (board is 1920x1080 at s=1 centred at 960,540) */
// HOUSE (producer 2026-10-21, Great Plains "weird zoom"): the camera drifts, it never punches in. Scale stays within
// 0.95-1.12 and changes at most 3 % per second; the view never leaves the board. Applied here so a bold key never
// reaches the render; tools/validate.py errors on such keys so the editor sees them.
const S_MAX = 1.12, S_MIN = 0.95, RATE = 0.03;
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const calm = (keys: Key[]): Key[] => {
  const out: Key[] = [];
  keys.forEach((k, i) => {
    let s = clamp(k.s, S_MIN, S_MAX);
    if (i > 0) {
      const lim = RATE * Math.max(k.at - keys[i - 1].at, 0.04);
      s = clamp(s, out[i - 1].s - lim, out[i - 1].s + lim);
    }
    const hx = 960 / s, hy = 540 / s; // half the visible board at this scale
    out.push({at: k.at, s, x: s > 1 ? clamp(k.x, hx, 1920 - hx) : 960, y: s > 1 ? clamp(k.y, hy, 1080 - hy) : 540});
  });
  return out;
};
export const Camera: React.FC<{keys: Key[]; children: React.ReactNode}> = ({keys, children}) => {
  const cue = useCue();
  const {frame} = useScene();
  keys = calm(keys);
  const fr = keys.map((k) => cue(k.at));
  let x = keys[0].x;
  let y = keys[0].y;
  let s = keys[0].s;
  for (let i = 1; i < keys.length; i++) {
    if (frame >= fr[i - 1]) {
      const p = interpolate(frame, [fr[i - 1], Math.max(fr[i], fr[i - 1] + 1)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut});
      x = keys[i - 1].x + (keys[i].x - keys[i - 1].x) * p;
      y = keys[i - 1].y + (keys[i].y - keys[i - 1].y) * p;
      s = keys[i - 1].s + (keys[i].s - keys[i - 1].s) * p;
    }
  }
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${960 - x * s}px, ${540 - y * s}px) scale(${s})`, transformOrigin: '0 0'}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const MapBlinds: React.FC<{
  src: string;
  line?: {at: number; from: [number, number]; to: [number, number]}; // screen px
  fromScale?: number;
  toScale?: number;
  focus?: [number, number]; // % of image
  children?: React.ReactNode;
}> = ({src, line, fromScale = 1.05, toScale = 1.22, focus = [50, 50], children}) => {
  const cue = useCue();
  const {frame, durFrames} = useScene();
  const sc = interpolate(frame, [0, durFrames], [fromScale, toScale]);
  const shift = interpolate(frame, [0, durFrames], [-220, 140]);
  const lp = line ? prog(frame, cue(line.at), 18, easeInOut) : 0;
  return (
    <AbsoluteFill style={{background: '#0b0907', overflow: 'hidden'}}>
      <Img
        src={staticFile(`photos/${src}`)}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${focus[0]}% ${focus[1]}%`,
          transform: `scale(${sc})`,
          transformOrigin: `${focus[0]}% ${focus[1]}%`,
          filter: 'grayscale(.5) sepia(.55) contrast(1.15) brightness(.9)',
        }}
      />
      {/* blind slats: a skewed repeating shadow that slides slowly across the map */}
      <AbsoluteFill
        style={{
          left: -400,
          right: -400,
          transform: `translateX(${shift}px) skewX(-18deg)`,
          background: 'repeating-linear-gradient(90deg, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 70px, rgba(0,0,0,.62) 110px, rgba(0,0,0,.62) 150px, rgba(0,0,0,0) 190px)',
          filter: 'blur(14px)',
        }}
      />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 70% at 45% 45%, rgba(255,214,150,.10), transparent 55%), radial-gradient(ellipse 80% 80% at 50% 50%, transparent 40%, rgba(0,0,0,.8) 100%)'}} />
      {line && (
        <svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
          <line
            x1={line.from[0]}
            y1={line.from[1]}
            x2={line.from[0] + (line.to[0] - line.from[0]) * lp}
            y2={line.from[1] + (line.to[1] - line.from[1]) * lp}
            stroke={C.red}
            strokeWidth={7}
            strokeLinecap="round"
            opacity={0.95}
          />
        </svg>
      )}
      {children}
    </AbsoluteFill>
  );
};

export const Epigraph: React.FC<{lines: string[]; by: string}> = ({lines, by}) => {
  const {frame, durFrames} = useScene();
  const out = 1 - prog(frame, durFrames - 14, 14);
  return (
    <AbsoluteFill style={{background: '#030303', alignItems: 'center', justifyContent: 'center', opacity: out}}>
      <div style={{textAlign: 'center'}}>
        {lines.map((l, i) => {
          const p = prog(frame, 8 + i * 22, 18);
          return (
            <div key={i} style={{fontFamily: FONT.serif, fontSize: 70, color: C.cream, letterSpacing: 3, lineHeight: 1.3, opacity: p, filter: `blur(${(1 - p) * 8}px)`}}>
              {l}
            </div>
          );
        })}
        <div style={{width: interpolate(prog(frame, 60, 20), [0, 1], [0, 120]), height: 2, background: C.gold, margin: '34px auto 22px'}} />
        <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: 36, color: '#a99f8c', letterSpacing: 4, opacity: prog(frame, 66, 18)}}>{by}</div>
      </div>
    </AbsoluteFill>
  );
};

export const TitleCard: React.FC<{title: string; sub: string}> = ({title, sub}) => {
  const {frame, durFrames} = useScene();
  const p = prog(frame, 0, 16);
  const seed = Math.floor(frame / 3) % 4; // grunge "boils" a little like printed film
  const out = 1 - prog(frame, durFrames - 8, 8);
  return (
    <AbsoluteFill style={{background: '#050505', opacity: out}}>
      <Img src={staticFile('textures/concrete.jpg')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.22}} />
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <filter id="grunge" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.035 0.06" numOctaves={4} seed={seed} result="n" />
            <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3.2 2.15" result="m" />
            <feComposite in="SourceGraphic" in2="m" operator="in" />
          </filter>
        </defs>
        {title.split('\n').map((line, i, all) => (
          <text
            key={i}
            x={960}
            y={(all.length > 1 ? 440 : 560) + i * 200}
            textAnchor="middle"
            fontFamily={FONT.title}
            fontSize={all.length > 1 ? 210 : 230}
            letterSpacing={6}
            fill="#ece5d6"
            filter="url(#grunge)"
            style={{opacity: p}}
            transform={`translate(960 540) scale(${1.06 - 0.06 * p}) translate(-960 -540)`}
          >
            {line}
          </text>
        ))}
      </svg>
      <div
        style={{
          position: 'absolute',
          top: title.includes('\n') ? 720 : 640,
          width: '100%',
          textAlign: 'center',
          fontFamily: FONT.serif,
          fontSize: 40,
          letterSpacing: 14,
          color: C.gold,
          opacity: prog(frame, 14, 16),
        }}
      >
        {sub}
      </div>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 75% at 50% 50%, transparent 40%, rgba(0,0,0,.85) 100%)'}} />
    </AbsoluteFill>
  );
};
