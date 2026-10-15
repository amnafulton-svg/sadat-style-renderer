// Transitions. The reference uses each one for a specific kind of change — never as decoration:
//   cut       — inside one beat (shot to shot of the same moment). Most changes are cuts.
//   dissolve  — time passes / thought continues (board to board, abstract lines). ~1 s.
//   whip      — rapid list of consequences (montage of later events): energy, "and then, and then".
//   torn      — paper tears to reveal a document/newspaper world: we leave footage for evidence.
//   rack      — focus pulls in after a ribbon: a new chapter of the story settles into view.
//   flash     — a white pop on a hard fact (a single word like "Oil." or a date).
//   ribbon    — beige light-leak strands sweeping across: the reference's signature move between acts.
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {easeInOut, easeOut, prog, rand} from '../lib/core';

export type EnterKind = 'cut' | 'dissolve' | 'whip' | 'whipL' | 'torn' | 'rack';
/** frames the incoming scene overlaps the outgoing one */
export const OVERLAP: Record<EnterKind, number> = {cut: 0, dissolve: 22, whip: 6, whipL: 6, torn: 12, rack: 0};

export const Enter: React.FC<{kind: EnterKind; children: React.ReactNode}> = ({kind, children}) => {
  const f = useCurrentFrame();
  if (kind === 'cut') return <AbsoluteFill>{children}</AbsoluteFill>;
  if (kind === 'dissolve') return <AbsoluteFill style={{opacity: prog(f, 0, OVERLAP.dissolve, easeInOut)}}>{children}</AbsoluteFill>;
  if (kind === 'rack') {
    const p = prog(f, 0, 16, easeOut);
    return <AbsoluteFill style={{filter: p < 1 ? `blur(${(1 - p) * 18}px)` : undefined, transform: `scale(${1.04 - 0.04 * p})`}}>{children}</AbsoluteFill>;
  }
  if (kind === 'whip' || kind === 'whipL') {
    const p = prog(f, 0, OVERLAP.whip, easeOut);
    const dir = kind === 'whip' ? 1 : -1;
    return (
      <AbsoluteFill style={{transform: `translateX(${dir * (1 - p) * 1920}px)`, filter: p < 1 ? `blur(${(1 - p) * 40}px)` : undefined}}>{children}</AbsoluteFill>
    );
  }
  // torn: a jagged paper edge sweeps left → right revealing the new scene, with a white paper fibre rim
  const p = prog(f, 0, OVERLAP.torn, easeInOut);
  const edgeX = interpolate(p, [0, 1], [-160, 2080]);
  const pts: string[] = [];
  const n = 28;
  for (let i = 0; i <= n; i++) pts.push(`${edgeX + (rand(i * 3.1) - 0.5) * 90}px ${(i / n) * 100}%`);
  const clip = `polygon(0 0, ${pts.join(',')}, 0 100%)`;
  const rim = `polygon(0 0, ${pts.map((q) => q.replace(/^(-?[\d.]+)px/, (_, x) => `${+x + 18}px`)).join(',')}, 0 100%)`;
  return (
    <AbsoluteFill>
      {p < 1 && <AbsoluteFill style={{clipPath: rim, background: '#efe9dc', boxShadow: '0 0 30px #000'}} />}
      <AbsoluteFill style={{clipPath: p < 1 ? clip : undefined}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

/** white flash peaking at frame 2 (place its Sequence 2 frames before the hit) */
export const Flash: React.FC<{strength?: number}> = ({strength = 0.9}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 2, 12], [0, strength, 0], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#fffaf0', opacity: o, pointerEvents: 'none'}} />;
};

/** beige light-leak ribbon: soft bezier strands sweeping across in ~1 s, screen-blended */
export const Ribbon: React.FC<{dur?: number; seed?: number}> = ({dur = 26, seed = 1}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], {extrapolateRight: 'clamp'});
  const o = interpolate(p, [0, 0.25, 0.7, 1], [0, 1, 1, 0]);
  const x = interpolate(p, [0, 1], [-1400, 1700]);
  const strands = [0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
    const y0 = 200 + rand(seed * 10 + i) * 700;
    const amp = 180 + rand(seed * 20 + i) * 260;
    const w = 120 + rand(seed * 30 + i) * 220;
    return {d: `M -200 ${y0} C 500 ${y0 - amp}, 1000 ${y0 + amp}, 2200 ${y0 - amp * 0.4}`, w, a: 0.14 + rand(seed + i) * 0.22};
  });
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: o, pointerEvents: 'none'}}>
      <svg width={1920} height={1080} style={{transform: `translateX(${x}px) rotate(-8deg)`, filter: 'blur(60px)'}}>
        {strands.map((s, i) => (
          <path key={i} d={s.d} stroke={i % 2 ? '#f3dcb0' : '#e8c48a'} strokeWidth={s.w} strokeOpacity={s.a} fill="none" />
        ))}
      </svg>
      <AbsoluteFill style={{background: `radial-gradient(ellipse 40% 60% at ${50 + x / 40}% 50%, rgba(255,228,180,${0.55 * o}), transparent 70%)`}} />
    </AbsoluteFill>
  );
};
