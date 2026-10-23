// Backgrounds the reference builds its graphic set pieces on.
// - ConcreteWall: dark grunge wall behind print clusters, quote cards and expert cards (people / testimony).
// - Desk: dark wood under the evidence board (investigation / thesis lines).
// - Paper: cream stock behind label-tape lists and date tags.
// Each one drifts and carries a soft moving spotlight so a 10–30 s hold never looks frozen.
import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile} from 'remotion';
import {useScene} from '../lib/scene';
import {OnPaper} from '../lib/core';

const Textured: React.FC<{tex: string; dim?: number; spot?: boolean; edge?: number; children?: React.ReactNode}> = ({tex, dim = 0, spot = true, edge = 0.7, children}) => {
  const {frame, durFrames} = useScene();
  const drift = interpolate(frame, [0, durFrames], [0, -40]);
  const sx = interpolate(frame, [0, durFrames], [35, 62]);
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img
        src={staticFile(`textures/${tex}`)}
        style={{position: 'absolute', width: 2400, height: 1350, left: -240, top: -135, transform: `translateX(${drift}px)`, filter: `brightness(${1 - dim})`}}
      />
      {spot && (
        <AbsoluteFill
          style={{background: `radial-gradient(ellipse 55% 65% at ${sx}% 45%, rgba(255,240,210,0.10) 0%, transparent 60%), radial-gradient(ellipse 80% 80% at 50% 50%, transparent 40%, rgba(0,0,0,${edge}) 100%)`}}
        />
      )}
      {children}
    </AbsoluteFill>
  );
};

export const ConcreteWall: React.FC<{children?: React.ReactNode; dim?: number}> = ({children, dim = 0.25}) => (
  <Textured tex="concrete.jpg" dim={dim}>
    {children}
  </Textured>
);
export const Desk: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <Textured tex="desk.jpg" dim={0.1}>
    {children}
  </Textured>
);
export const Paper: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <Textured tex="paper.jpg" dim={-0.08} edge={0.32}>
    <OnPaper.Provider value={true}>{children}</OnPaper.Provider>
  </Textured>
);
export const Black: React.FC<{children?: React.ReactNode}> = ({children}) => <AbsoluteFill style={{background: '#050505'}}>{children}</AbsoluteFill>;
