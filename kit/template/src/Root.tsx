import React from 'react';
import {Composition} from 'remotion';
import {Main, TOTAL_FRAMES} from './Main';
import {FPS, H, W} from './lib/core';

export const Root: React.FC = () => (
  <Composition id="Documentary" component={Main} durationInFrames={TOTAL_FRAMES} fps={FPS} width={W} height={H} />
);
