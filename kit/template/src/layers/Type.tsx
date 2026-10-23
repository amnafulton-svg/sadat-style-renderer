// Type layers. In the reference, text never narrates — it STAMPS the one word the viewer must keep:
// a year, a count, a name, a verdict. Each element lands on its spoken word, never before.
// BigSerif   — huge didone figure ("1967", "22 times"): numbers that carry the argument. Blur-in pop.
// Highlight  — serif phrase with a crimson bar growing behind it, over footage: the claim being made.
// QuoteText  — word-by-word blur-in serif, timed to the voice reading it.
// GhostTitle — huge faint section word behind an expert/quote card: the theme of the passage.
// LabelTape  — typewriter text on dark embossed tape: an institution / file label.
// ListWords  — serif list words appearing one per spoken word ("geography. tribe. history.").
// KraftNote  — kraft-paper note with red condensed caps: the investigator's scribbled conclusion.
import React from 'react';
import {interpolate, staticFile} from 'remotion';
import {C, FONT, OnPaper, easeOut, prog, rand} from '../lib/core';
import {useCue, useScene} from '../lib/scene';

type Pos = {x: number; y: number; anchor?: 'center' | 'left' | 'right'};
const place = ({x, y, anchor = 'center'}: Pos): React.CSSProperties => ({
  position: 'absolute',
  left: x,
  top: y,
  transform: anchor === 'center' ? 'translate(-50%,-50%)' : anchor === 'left' ? 'translate(0,-50%)' : 'translate(-100%,-50%)',
});

export const BigSerif: React.FC<Pos & {text: string; at: number; size?: number; color?: string; sub?: string; bar?: boolean; out?: number}> = ({
  text,
  at,
  size = 260,
  color: colorIn,
  sub,
  bar = false,
  out,
  ...pos
}) => {
  const color = colorIn ?? (React.useContext(OnPaper) && !bar ? C.ink : C.cream);
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 2;
  const p = prog(frame, s, 10);
  const o = out !== undefined ? 1 - prog(frame, cue(out), 8) : 1;
  return (
    <div style={{...place(pos), opacity: p * o, textAlign: 'center'}}>
      {bar && (
        <div
          style={{
            position: 'absolute',
            inset: `${size * 0.02}px ${-size * 0.16}px ${sub ? -size * 0.05 : size * 0.02}px`,
            transform: `scaleX(${interpolate(p, [0, 1], [0.3, 1])})`,
            background: 'rgba(5,5,5,0.86)',
          }}
        />
      )}
      <div
        style={{
          position: 'relative',
          fontFamily: FONT.didone,
          fontWeight: 700,
          fontSize: size,
          lineHeight: 1,
          color,
          letterSpacing: -2,
          filter: `blur(${(1 - p) * 14}px)`,
          transform: `scale(${1.12 - 0.12 * p})`,
          textShadow: '0 10px 40px rgba(0,0,0,.7)',
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </div>
      {sub && (
        <div style={{position: 'relative', fontFamily: FONT.serif, fontStyle: 'italic', fontSize: Math.max(size * 0.17, 48), color: '#efe7d6', textShadow: '0 2px 12px rgba(0,0,0,.9)', marginTop: size * 0.06, opacity: prog(frame, s + 8, 10)}}>
          {sub}
        </div>
      )}
    </div>
  );
};

/** crimson bar sweeps in behind the phrase (left→right), the phrase sits on it in cream serif */
export const Highlight: React.FC<Pos & {text: string; at: number; size?: number; out?: number; italic?: boolean}> = ({text, at, size = 64, out, italic, ...pos}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 3;
  const bar = prog(frame, s, 9);
  const txt = prog(frame, s + 3, 8);
  const o = out !== undefined ? 1 - prog(frame, cue(out), 6) : 1;
  return (
    <div style={{...place(pos), opacity: o}}>
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
  return (
    <div style={{...place(pos), width, fontFamily: FONT.serif, fontSize: size, lineHeight: 1.32, color}}>
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

/** Dymo-style embossed tape, typed on one character every frame */
export const LabelTape: React.FC<Pos & {text: string; at: number; size?: number; rot?: number}> = ({text, at, size = 40, rot = -1.5, ...pos}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 3;
  const n = Math.max(0, Math.min(text.length, Math.floor(frame - s)));
  const w = text.length * (size * 0.6 + 4) + 52; // a long tape never runs off the frame
  const a = pos.anchor ?? 'center';
  const lo = 48 + (a === 'center' ? w / 2 : a === 'right' ? w : 0);
  const hi = 1872 - (a === 'center' ? w / 2 : a === 'left' ? w : 0);
  const x = Math.max(lo, Math.min(pos.x, hi));
  return (
    <div style={{...place({...pos, x}), opacity: frame >= s ? 1 : 0}}>
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
  return (
    <div style={{...(inline ? {marginTop: 14} : place(pos)), textAlign: pos.anchor === 'left' ? 'left' : 'center'}}>
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
