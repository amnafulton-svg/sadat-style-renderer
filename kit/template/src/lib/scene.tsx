// Scene context: every layer is placed in narration seconds (word cues), and converts to the scene's
// local frame here, so a layer can be moved between scenes without re-timing it.
import React, {createContext, useContext} from 'react';
import {useCurrentFrame} from 'remotion';
import {nf} from './core';

const SceneCtx = createContext<{startFrame: number; durFrames: number}>({startFrame: 0, durFrames: 1});

export const SceneProvider: React.FC<{startFrame: number; durFrames: number; children: React.ReactNode}> = ({
  startFrame,
  durFrames,
  children,
}) => <SceneCtx.Provider value={{startFrame, durFrames}}>{children}</SceneCtx.Provider>;

/** local frame of a narration-time cue inside the current scene */
export const useCue = () => {
  const {startFrame} = useContext(SceneCtx);
  return (narrSec: number) => nf(narrSec) - startFrame;
};

export const useScene = () => {
  const frame = useCurrentFrame();
  const ctx = useContext(SceneCtx);
  return {frame, ...ctx, t: frame / ctx.durFrames};
};
