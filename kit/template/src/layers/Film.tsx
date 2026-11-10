// FilmLayer — archival footage, the workhorse for CONCRETE statements (who did what, where).
// HOUSE (producer, Pacific 2026-11-10): film plays as it was shot, in its own colour, sharp to the edges (FILM_LOOK).
// `fit: "pad"` shows a whole 4:3 picture over a blurred copy of itself.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile} from 'remotion';
import {useScene} from '../lib/scene';

export type Grade = 'bw' | 'sepia' | 'warm' | 'blue' | 'none';

export const GRADE: Record<Grade, string> = {
  bw: 'grayscale(1) contrast(1.18) brightness(0.95)',
  sepia: 'grayscale(0.85) sepia(0.35) contrast(1.12) brightness(0.95)',
  warm: 'saturate(0.55) sepia(0.25) contrast(1.08)',
  blue: 'saturate(0.6) contrast(1.15) brightness(1.05)',
  none: 'none',
};

/** film plays as it was shot: its own colour (colour film stays colour, black-and-white stays black-and-white),
 *  a touch of contrast, no tint and no blurred, darkened edges (producer, Pacific 2026-11-10: colour Midway film
 *  had been turned grey and sepia with soft edges; the clean version was the pick). `grade` is still accepted on
 *  film so old timelines compile, but it no longer tints it. */
export const FILM_LOOK = 'contrast(1.06) saturate(0.85)';

export type FilmProps = {
  src: string; // file in public/footage
  start: number; // source in-point (s)
  fit?: 'fill' | 'pad';
  focusY?: number; // 0..100 vertical crop position for fill (lower = crop more of the bottom, hides burned-in text)
  focusX?: number;
  zoom?: number; // extra scale on fill (e.g. to push past a pillarbox)
  grade?: Grade; // ignored on film (see FILM_LOOK); prints and photos still use it
  rate?: number;
  drift?: boolean; // very slow push, never a punch-in
};

export const Film: React.FC<FilmProps> = ({src, start, fit = 'fill', focusY = 50, focusX = 50, zoom = 1, rate = 1, drift = true}) => {
  const {frame, durFrames} = useScene();
  const push = drift ? interpolate(frame, [0, durFrames], [1, 1.035]) : 1;
  const video = (style: React.CSSProperties) => (
    <OffthreadVideo
      src={staticFile(`footage/${src}`)}
      startFrom={Math.round(start * 25)}
      playbackRate={rate}
      muted
      style={style}
    />
  );
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      {fit === 'pad' ? (
        <>
          {video({width: '100%', height: '100%', objectFit: 'cover', filter: `${FILM_LOOK} blur(28px) brightness(0.45)`, transform: 'scale(1.15)'})}
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `scale(${push})`}}>
            {video({height: '100%', width: '100%', objectFit: 'contain', filter: FILM_LOOK})}
          </AbsoluteFill>
        </>
      ) : (
        video({
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${focusX}% ${focusY}%`,
          filter: FILM_LOOK,
          transform: `scale(${push * zoom})`,
          transformOrigin: `${focusX}% ${focusY}%`,
        })
      )}
    </AbsoluteFill>
  );
};

/** one real photo filling the frame with a slow zoom in: for a shot whose only picture is a photo big and wide enough
 *  to hold up full screen (producer, Italy 2026-10-25: one print on the wall shot after shot "feels templated").
 *  The zoom runs the whole shot, 2.5 % per second, at most 10 %, towards focusX/focusY. */
export const FullPhoto: React.FC<{src: string; grade?: Grade; focusX?: number; focusY?: number; zoom?: number}> = ({
  src,
  grade = 'sepia',
  focusX = 50,
  focusY = 50,
  zoom,
}) => {
  const {frame, durFrames} = useScene();
  const end = zoom ?? 1 + Math.min(0.1, (0.025 * durFrames) / 25);
  const z = interpolate(frame, [0, durFrames], [1, end], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img
        src={staticFile(`photos/${src}`)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${focusX}% ${focusY}%`,
          filter: GRADE[grade],
          transform: `scale(${z})`,
          transformOrigin: `${focusX}% ${focusY}%`,
        }}
      />
      <EdgeSoftness />
    </AbsoluteFill>
  );
};

/** blur + darken towards the frame edges (the reference's soft, vignetted film frame) */
export const EdgeSoftness: React.FC<{strength?: number}> = ({strength = 1}) => (
  <>
    <AbsoluteFill
      style={{
        backdropFilter: `blur(${5 * strength}px)`,
        WebkitMaskImage: 'radial-gradient(ellipse 72% 70% at 50% 50%, transparent 58%, black 100%)',
        maskImage: 'radial-gradient(ellipse 72% 70% at 50% 50%, transparent 58%, black 100%)',
      }}
    />
    <AbsoluteFill style={{background: `radial-gradient(ellipse 75% 75% at 50% 50%, transparent 45%, rgba(0,0,0,${0.75 * strength}) 100%)`}} />
  </>
);
