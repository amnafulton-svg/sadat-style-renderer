// Source numbers, top right, over every scene ("[17] Source in Description", the producer's reference video):
// the brackets come first, then the number, then the words type on while their spacing closes up; on the way out
// the brackets and number go first and the words fade off left to right. Times come from tools/sources.py -> sources.json.
import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {loadFont as loadPoppins} from '@remotion/google-fonts/Poppins';
import {nf} from '../lib/core';
import sources from '../lib/sources.json';

const POPPINS = loadPoppins('normal', {weights: ['600'], subsets: ['latin']}).fontFamily;
const WORDS = 'Source in Description';
const OUT = 12; // frames of the way out
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Tag: React.FC<{n: number[]; dur: number}> = ({n, dur}) => {
  const f = useCurrentFrame();
  const out = f - (dur - OUT);
  const label = n.length > 1 ? WORDS.replace('Source', 'Sources') : WORDS;
  const num = n.join(', ');
  const numOn = f >= 3 && out < 0;
  const bracketsOn = out < 0; // on the way out the brackets (and number) go first, then the words
  const spacing = interpolate(f, [4, 18], [0.32, 0.01], clamp);
  const wide = (num.length + label.length + 3) * 19.5; // ~Poppins 600 at 34 px; a long "[11, 12, 13]" slides left
  return (
    <div style={{position: 'absolute', left: Math.min(1222, 1860 - wide), top: 62, display: 'flex', alignItems: 'baseline', gap: 12,
      fontFamily: POPPINS, fontWeight: 600, fontSize: 34, color: '#fff', whiteSpace: 'pre',
      textShadow: '0 2px 6px rgba(0,0,0,.75), 0 0 2px rgba(0,0,0,.6)', opacity: out >= OUT ? 0 : 1}}>
      <span style={{opacity: bracketsOn ? 1 : 0}}>[<span style={{opacity: numOn ? 1 : 0}}>{num}</span>]</span>
      <span style={{letterSpacing: `${spacing}em`}}>
        {label.split('').map((ch, i) => {
          const inA = interpolate(f, [5 + i * 0.6, 8 + i * 0.6], [0, 1], clamp);
          const outA = interpolate(out, [1 + i * 0.35, 3 + i * 0.35], [1, 0], clamp);
          return <span key={i} style={{opacity: Math.min(inA, outA)}}>{ch}</span>;
        })}
      </span>
    </div>
  );
};

export const SourceTags: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    {(sources as {n: number[]; from: number; to: number}[]).map((s, i) => {
      const dur = Math.max(OUT + 20, nf(s.to) - nf(s.from));
      return (
        <Sequence key={i} from={nf(s.from)} durationInFrames={dur} name={`source [${s.n.join(', ')}]`}>
          <Tag n={s.n} dur={dur} />
        </Sequence>
      );
    })}
  </AbsoluteFill>
);
