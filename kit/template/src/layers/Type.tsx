// Type layers. In the reference, text never narrates — it STAMPS the one word the viewer must keep:
// a year, a count, a name, a verdict. Each element lands on its spoken word, never before.
// BigSerif   — the one figure the argument rests on ("1967", "22 times"), on a cream index slip. Used sparingly.
// Highlight  — serif phrase with a crimson bar growing behind it, over footage: ONLY a real quote from a person or
//              document, in quote marks (producer 2026-11-05; validate.py errors otherwise).
// QuoteText  — word-by-word blur-in serif, timed to the voice reading it.
// GhostTitle — huge faint section word behind an expert/quote card: the theme of the passage.
// LabelTape  — typewriter text on dark embossed tape: an institution / file label.
// ListWords  — serif list words appearing one per spoken word ("geography. tribe. history.").
// KraftNote  — kraft-paper note with red condensed caps: the investigator's scribbled conclusion.
import React from 'react';
import {interpolate, staticFile} from 'remotion';
import INK_AUTO from '../lib/ink.json';
// tools/fixink.py measures the picture behind each plain line / note and writes the colour that shows there
const inkAuto = (text: string, at: number) => (INK_AUTO as Record<string, {ink?: boolean; arrow?: string}>)[`${text}|${at}`];
import {C, FONT, OnDark, OnPaper, easeOut, prog, rand} from '../lib/core';
import {useCue, useScene} from '../lib/scene';

type Pos = {x: number; y: number; anchor?: 'center' | 'left' | 'right'};
const place = ({x, y, anchor = 'center'}: Pos): React.CSSProperties => ({
  position: 'absolute',
  left: x,
  top: y,
  transform: anchor === 'center' ? 'translate(-50%,-50%)' : anchor === 'left' ? 'translate(0,-50%)' : 'translate(-100%,-50%)',
});

// keeps a label's centre far enough from the top/bottom edge that the whole box (height h) stays 40 px inside the frame
export const safeY = (y: number, h: number) => Math.max(40 + h / 2, Math.min(y, 1040 - h / 2));

// HOUSE (Chipyong-ni review 2026-10-25): labels, bars and type always sit above the prints and film of their scene
// (a print that slid in later covered "ENTIRE REGIMENTS DESTROYED"), and light type that is not on paper must still
// read on a white sky ("the manpower, the momentum" vanished at 0:18): it gets a solid tag behind it, never a blur.
export const Z_LABEL = 40;
export const isLight = (c: string) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(c.trim());
  if (!m) return true;
  const n = parseInt(m[1], 16);
  return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255 > 0.55;
};
// HOUSE (producer, Japan oil 2026-11-15): no dark blur, outline or box behind the big number, in any video. It is a
// plain typewriter line whose colour follows the picture (tools/fixink.py); running type over film sits on a solid tag.
/** solid dark tag behind light running type over film (inside a block with isolation: isolate) */
const Panel: React.FC<{size: number; opacity: number}> = ({size, opacity}) => (
  <div style={{position: 'absolute', inset: `${-size * 0.32}px ${-size * 0.55}px`, zIndex: -1, opacity, pointerEvents: 'none', background: C.tag}} />
);

/** the one number the argument rests on: a plain typewriter line with what it counts under it, fading in and out.
 *  Warm white on a dark picture, dark ink on a bright one - tools/fixink.py measures the picture and decides
 *  (`ink` forces dark by hand). `color` and `bar` are kept for old timelines and are not needed. */
export const BigSerif: React.FC<Pos & {text: string; at: number; size?: number; color?: string; sub?: string; bar?: boolean; out?: number; ink?: boolean}> = ({
  text,
  at,
  size = 260,
  color: colorIn,
  sub,
  out,
  ink: inkIn,
  ...pos
}) => {
  const paper = React.useContext(OnPaper);
  const cue = useCue();
  const {frame} = useScene();
  const dark = React.useContext(OnDark);
  // typewriter line, plain on the picture: no outline, no box, no pool behind it. Its colour follows the picture -
  // warm white on a dark one, `ink` (near-black) on a bright one (sky, sea, snow, paper). Light type over film
  // also dims the frame a little while it is up; ink never dims.
  const s0 = cue(at) - 3;
  const q = prog(frame, s0, 9);
  const fade = out !== undefined ? 1 - prog(frame, cue(out), 10) : 1;
  const dk = paper || (inkAuto(text, at)?.ink ?? !!inkIn);
  const col = dk ? (colorIn && !isLight(colorIn) ? colorIn : '#15120e') : '#f7efdc';
  const big = Math.min(size * 0.8, 160);
  
  return (
    <>
      {!dk && !dark && <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, background: '#000', opacity: 0.4 * q * fade, zIndex: 1, pointerEvents: 'none'}} />}
      <div style={{...place(pos), opacity: q * fade, textAlign: 'center', zIndex: Z_LABEL, filter: `blur(${(1 - q) * 5}px)`}}>
        <div style={{fontFamily: FONT.type, fontSize: big, lineHeight: 1.1, letterSpacing: big * 0.03, color: col, whiteSpace: 'nowrap'}}>{text}</div>
        {sub && (
          <div style={{fontFamily: FONT.type, fontSize: Math.min(Math.max(big * 0.4, 36), Math.max(30, 680 / (sub.length * 0.62))), lineHeight: 1.2, letterSpacing: 2, color: dk ? '#221e18' : '#e6e3d8', marginTop: big * 0.12, opacity: prog(frame, s0 + 8, 10), whiteSpace: 'nowrap'}}>{sub}</div>
        )}
      </div>
    </>
  );
};

/** crimson bar sweeps in behind the phrase (left→right), the phrase sits on it in cream serif */
export const Highlight: React.FC<Pos & {text: string; at: number; size?: number; out?: number; italic?: boolean}> = ({text, at, size = 64, out, italic, ...pos}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 3;
  const bar = prog(frame, s, 9);
  const txt = prog(frame, s + 1, 5);
  const o = out !== undefined ? 1 - prog(frame, cue(out), 6) : 1;
  return (
    <div style={{...place({...pos, y: safeY(pos.y, size * 1.2 + 12)}), opacity: o, zIndex: Z_LABEL}}>
      <div
        style={{
          position: 'absolute',
          inset: '-6px -26px',
          background: C.crimson,
          transformOrigin: 'left center',
          transform: `scaleX(${bar}) skewX(-4deg)`,
          boxShadow: '0 10px 30px rgba(0,0,0,.45)',
        }}
      />
      <div style={{position: 'relative', fontFamily: FONT.serif, fontStyle: italic ? 'italic' : 'normal', fontSize: size, color: '#fbf6ea', whiteSpace: 'nowrap', opacity: txt, lineHeight: 1.2}}>
        {text}
      </div>
    </div>
  );
};

/** words of `text` appear one by one, each at its cue (narration s); blur 10→0 */
export const QuoteText: React.FC<Pos & {words: {w: string; at: number}[]; size?: number; width?: number; color?: string; mark?: string[]}> = ({
  words,
  size = 62,
  width = 900,
  color: colorIn,
  mark = [],
  ...pos
}) => {
  const paper = React.useContext(OnPaper);
  const color = colorIn ?? (paper ? C.ink : C.cream);
  const cue = useCue();
  const {frame} = useScene();
  const light = !paper && isLight(color);
  return (
    <div style={{...place(pos), width, fontFamily: FONT.serif, fontSize: size, lineHeight: 1.32, color, zIndex: Z_LABEL, isolation: 'isolate'}}>
      {light && words.length > 0 && <Panel size={size} opacity={prog(frame, cue(words[0].at) - 2, 7)} />}
      {words.map((x, i) => {
        const p = prog(frame, cue(x.at) - 2, 7);
        const m = mark.includes(x.w);
        return (
          <span key={i} style={{display: 'inline-block', marginRight: size * 0.26, opacity: p, filter: `blur(${(1 - p) * 10}px)`, position: 'relative'}}>
            {m && <span style={{position: 'absolute', inset: '4px -8px 0', background: C.crimson, transform: `scaleX(${p})`, transformOrigin: 'left', zIndex: -1}} />}
            <span style={{position: 'relative', color: m && paper && !colorIn ? C.cream : undefined}}>{x.w}</span>
          </span>
        );
      })}
    </div>
  );
};

export const GhostTitle: React.FC<Pos & {text: string; size?: number}> = ({text, size = 300, ...pos}) => {
  const {frame, durFrames} = useScene();
  const p = prog(frame, 0, 20);
  const dx = interpolate(frame, [0, durFrames], [30, -30]);
  return (
    <div
      style={{
        ...place(pos),
        marginLeft: dx,
        fontFamily: FONT.title,
        fontSize: size,
        color: 'rgba(255,255,255,0.11)',
        letterSpacing: 8,
        whiteSpace: 'nowrap',
        opacity: p,
      }}
    >
      {text}
    </div>
  );
};

/** Dymo-style embossed tape, typed on one character every frame (long tapes faster: done in 0.6 s) */
export const LabelTape: React.FC<Pos & {text: string; at: number; size?: number; rot?: number}> = ({text, at, size = 40, rot = -1.5, ...pos}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 3;
  const n = Math.max(0, Math.min(text.length, Math.floor((frame - s) / Math.min(1, 15 / Math.max(1, text.length)))));  // typed in <= 0.6 s
  const w = text.length * (size * 0.6 + 4) + 52; // a long tape never runs off the frame
  const a = pos.anchor ?? 'center';
  const lo = 48 + (a === 'center' ? w / 2 : a === 'right' ? w : 0);
  const hi = 1872 - (a === 'center' ? w / 2 : a === 'left' ? w : 0);
  const x = Math.max(lo, Math.min(pos.x, hi));
  return (
    <div style={{...place({...pos, x, y: safeY(pos.y, size * 1.2 + 20)}), opacity: frame >= s ? 1 : 0, zIndex: Z_LABEL}}>
      <div
        style={{
          transform: `rotate(${rot}deg)`,
          background: 'linear-gradient(#1d1d1f,#0d0d0e)',
          padding: '10px 26px',
          borderRadius: 4,
          boxShadow: '0 6px 16px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.08)',
          fontFamily: FONT.type,
          fontSize: size,
          letterSpacing: 4,
          color: '#ece6da',
          textShadow: '0 1px 0 rgba(0,0,0,.9), 0 -1px 0 rgba(255,255,255,.15)',
          whiteSpace: 'pre',
        }}
      >
        {text.slice(0, n)}
        <span style={{color: 'transparent'}}>{text.slice(n)}</span>
      </div>
    </div>
  );
};

/** stacked serif words, each popping in on its cue; previous words dim slightly so the newest leads */
export const ListWords: React.FC<Pos & {items: {w: string; at: number}[]; size?: number; color?: string; gap?: number; dim?: boolean; inline?: boolean}> = ({
  items,
  size = 76,
  color = '#141414',
  gap = 1.15,
  dim = true,
  inline = false,
  ...pos
}) => {
  const cue = useCue();
  const {frame} = useScene();
  const lastOn = items.filter((x) => frame >= cue(x.at) - 2).length - 1;
  const light = !inline && !React.useContext(OnPaper) && isLight(color);
  return (
    <div style={{...(inline ? {marginTop: 14} : place(pos)), textAlign: pos.anchor === 'left' ? 'left' : 'center', ...(inline ? {} : {zIndex: Z_LABEL, isolation: 'isolate'})}}>
      {light && items.length > 0 && <Panel size={size} opacity={prog(frame, cue(items[0].at) - 2, 7)} />}
      {items.map((x, i) => {
        const p = prog(frame, cue(x.at) - 2, 7);
        return (
          <div
            key={i}
            style={{
              fontFamily: FONT.serif,
              fontSize: size,
              lineHeight: gap,
              color,
              opacity: p * (dim && i < lastOn ? 0.45 : 1),
              transform: `translateY(${(1 - p) * 18}px)`,
              filter: `blur(${(1 - p) * 8}px)`,
              whiteSpace: 'nowrap',
            }}
          >
            {x.w}
          </div>
        );
      })}
    </div>
  );
};

/** torn kraft note with red Oswald caps; slides down onto the board */
export const KraftNote: React.FC<Pos & {title: string; at: number; w?: number; rot?: number; children?: React.ReactNode}> = ({title, at, w = 560, rot = 2, children, ...pos}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at) - 6, 9, easeOut);
  const edge = Array.from({length: 24}, (_, i) => `${100 - (i / 23) * 100}% ${100 - (i % 2 ? 0 : 2 + rand(i * 7) * 3)}%`).join(',');
  return (
    <div style={{...place(pos), opacity: p, marginTop: (1 - p) * -60}}>
      <div
        style={{
          width: w,
          transform: `rotate(${rot}deg)`,
          backgroundImage: `url(${staticFile('textures/kraft.jpg')})`,
          backgroundColor: '#b48a5a',
          backgroundSize: 'cover',
          padding: '34px 40px 46px',
          clipPath: `polygon(0 0,100% 0,${edge})`,
          boxShadow: '0 16px 30px rgba(0,0,0,.55)',
        }}
      >
        <div style={{fontFamily: FONT.cond, fontWeight: 700, fontSize: 54, color: C.red, letterSpacing: 2, lineHeight: 1}}>{title}</div>
        {children}
      </div>
    </div>
  );
};
