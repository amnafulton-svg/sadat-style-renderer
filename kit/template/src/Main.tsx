// The composition: scenes in <Sequence>s (each wrapped in its SceneProvider + entrance transition),
// then the film-burn transitions (with their own sound), then the global film skin, then audio.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {nf, sf} from './lib/core';
import {SceneProvider} from './lib/scene';
import {Enter, OVERLAP} from './transitions';
import {FilmBurnOverlay, filmBurnTiming} from './vendor/FilmBurn';
import {Dust, Grain, Vignette} from './overlays';
import {BURNS, END, SCENES, SFX} from './timeline/video';

export const TOTAL_FRAMES = nf(END);

export const Main: React.FC = () => {
  const fadeOut = nf(END) - sf(2.2);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SCENES.map((s) => {
        const start = nf(s.from) - OVERLAP[s.enter];
        const dur = nf(s.to) - start;
        return (
          <Sequence key={s.id} name={s.id} from={start} durationInFrames={dur}>
            <SceneProvider startFrame={start} durFrames={dur}>
              <Enter kind={s.enter}>{s.el}</Enter>
            </SceneProvider>
          </Sequence>
        );
      })}
      {BURNS.map((b, i) => {
        const {pre, frames} = filmBurnTiming(b.n, 25);
        return (
          <Sequence key={`burn${i}`} from={nf(b.at) - pre} durationInFrames={frames} name={`burn ${b.n} @ ${b.at}`}>
            <FilmBurnOverlay n={b.n} />
          </Sequence>
        );
      })}
      <Sequence from={fadeOut} name="fade out">
        <FadeToBlack dur={sf(2.2)} />
      </Sequence>
      <Vignette />
      <Grain />
      <Dust />

      {/* audio: narration from frame 0; no music bed yet */}
      <Sequence from={nf(0)} name="narration">
        <Audio src={staticFile('audio/narration.mp3')} />
      </Sequence>
      {/* music: none yet — the producer picks a real library track; it goes here as audio/music_bed.* with a ducked envelope */}
      {SFX.map((x, i) => (
        <Sequence key={`sfx${i}`} from={Math.max(0, nf(x.at))} durationInFrames={sf(3)} name={`sfx ${x.file}`}>
          <Audio src={staticFile(`sfx/${x.file}`)} volume={x.vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const FadeToBlack: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{background: '#000', opacity: interpolate(f, [0, dur], [0, 1], {extrapolateRight: 'clamp'})}} />;
};
