// Global finishing layers, always on top of every scene (the reference's "printed film" skin):
// Grain — 8 noise plates cycled every frame, overlay blend. Dust — a random speck/hair plate every few frames.
// Vignette — a light frame-wide darkening that ties graphics and film into one image.
import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {rand} from '../lib/core';

export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.13}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{mixBlendMode: 'overlay', opacity, pointerEvents: 'none'}}>
      <Img src={staticFile(`textures/grain_${f % 8}.png`)} style={{width: '100%', height: '100%'}} />
    </AbsoluteFill>
  );
};

export const Dust: React.FC<{every?: number}> = ({every = 7}) => {
  const f = useCurrentFrame();
  const slot = Math.floor(f / every);
  const on = rand(slot * 1.7) > 0.45 && f % every < 2; // dust only flickers for 2 frames
  if (!on) return null;
  const i = Math.floor(rand(slot * 3.3) * 6);
  const flip = rand(slot * 5.1) > 0.5 ? -1 : 1;
  return (
    <AbsoluteFill style={{opacity: 0.55, pointerEvents: 'none', transform: `scale(${flip}, ${-flip})`}}>
      <Img src={staticFile(`textures/dust_${i}.png`)} style={{width: '100%', height: '100%'}} />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 85% at 50% 50%, transparent 55%, rgba(0,0,0,.45) 100%)', pointerEvents: 'none'}} />
);
