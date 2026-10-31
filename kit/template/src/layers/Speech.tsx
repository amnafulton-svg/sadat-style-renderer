// One leader's speech insert: the whole film frame over a blurred copy of itself (never zoomed to fill), a slow push-in
// of 12 % over the clip, a black name/date tag, the film skin, and the clip's own (cleaned) sound.
import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {GRADE} from './Film';
import {BlackTag} from './Print';
import {SceneProvider} from '../lib/scene';
import {Speech, speechFrames} from '../lib/speeches';
import {Dust, Grain, Vignette} from '../overlays';

const Picture: React.FC<{s: Speech}> = ({s}) => {
  const f = useCurrentFrame();
  const q = speechFrames(s);
  const zoom = interpolate(f, [0, q], [1, 1.12], {extrapolateRight: 'clamp'});
  const src = staticFile(`speeches/${s.file}`);
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <OffthreadVideo src={src} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: `${GRADE.bw} blur(28px) brightness(0.45)`, transform: 'scale(1.15)'}} />
      <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: `50% ${s.focusY ?? 58}%`}}>
        <OffthreadVideo src={src} muted style={{width: '100%', height: '100%', objectFit: 'contain', filter: GRADE.bw}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const SpeechInsert: React.FC<{s: Speech}> = ({s}) => {
  const q = speechFrames(s);
  return (
    <AbsoluteFill>
      <SceneProvider startFrame={0} durFrames={q}>
        <Picture s={s} />
        <BlackTag at={0.8} x={80} y={850} line1={s.line1} line2={s.line2} />
      </SceneProvider>
      <Vignette />
      <Grain />
      <Dust />
      <Audio src={staticFile(`speeches/${s.file}`)} />
    </AbsoluteFill>
  );
};
