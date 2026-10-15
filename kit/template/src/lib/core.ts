// Shared timing, fonts, palette and easing for every layer.
import {Easing, interpolate} from 'remotion';
import {loadFont as loadBebas} from '@remotion/google-fonts/BebasNeue';
import {loadFont as loadPlayfair} from '@remotion/google-fonts/PlayfairDisplay';
import {loadFont as loadCaslon} from '@remotion/google-fonts/LibreCaslonText';
import {loadFont as loadElite} from '@remotion/google-fonts/SpecialElite';
import {loadFont as loadOswald} from '@remotion/google-fonts/Oswald';
import words from './words.json';

export const FPS = 25; // the reference is 25 fps
export const W = 1920;
export const H = 1080;

// no cold open: the narration starts on frame 0 (user: no text intro)
export const NARRATION_OFFSET = 0;

export const FONT = {
  title: loadBebas('normal', {weights: ['400'], subsets: ['latin']}).fontFamily, // condensed caps, grunge-masked in TitleCard
  didone: loadPlayfair('normal', {weights: ['700'], subsets: ['latin']}).fontFamily, // big numbers / years / section titles ("1967", "22 times")
  serif: (loadCaslon('italic', {weights: ['400'], subsets: ['latin']}), loadCaslon('normal', {weights: ['400'], subsets: ['latin']})).fontFamily, // quotes, list words, name strips
  type: loadElite('normal', {weights: ['400'], subsets: ['latin']}).fontFamily, // typewriter label tape, date stamps
  cond: loadOswald('normal', {weights: ['700'], subsets: ['latin']}).fontFamily, // red caps on kraft notes
};

export const C = {
  crimson: '#9e1b1b', // highlight bars behind keywords
  red: '#c0262d', // marker circles, kraft-note caps, ruler line
  cream: '#f2ead8',
  gold: '#c9a45c', // title-card subtitle
  ink: '#111',
  tag: '#0c0c0c',
};

// ---- word cues --------------------------------------------------------------------------------
type Word = {w: string; s: number; e: number};
const WORDS = words as Word[];
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');

/** narration time (s) of the first word starting with `cue` at or after `after` seconds.
 *  Cues use whisper's spelling ("forcassal", "Pico", "Damam", "Dehran"). Throws on a miss so a
 *  wrong cue fails the render instead of drifting silently. */
export const at = (cue: string, after = 0): number => {
  const c = norm(cue);
  const hit = WORDS.find((x) => x.s >= after - 0.01 && norm(x.w).startsWith(c));
  if (!hit) throw new Error(`word cue not found: "${cue}" after ${after}s`);
  return hit.s;
};
export const endOf = (cue: string, after = 0): number => {
  const c = norm(cue);
  const hit = WORDS.find((x) => x.s >= after - 0.01 && norm(x.w).startsWith(c));
  if (!hit) throw new Error(`word cue not found: "${cue}" after ${after}s`);
  return hit.e;
};

/** narration seconds -> composition frame */
export const nf = (narrSec: number) => Math.round((narrSec + NARRATION_OFFSET) * FPS);
export const sf = (sec: number) => Math.round(sec * FPS);

// ---- easing helpers ---------------------------------------------------------------------------
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1); // fast-in, long settle: print fly-ins
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1); // camera moves on the evidence board

/** 0..1 progress of `frame` over [start, start+dur] frames */
export const prog = (frame: number, start: number, dur: number, ease = easeOut) =>
  interpolate(frame, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

/** deterministic pseudo-random in [0,1) */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};
