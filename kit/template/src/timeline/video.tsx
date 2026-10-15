// THE EDIT for this video. Every scene: {id, from, to, enter, why, el} in narration seconds
// (whisper word starts from src/lib/words.json). Scenes tile the narration with no gaps:
// each `from` equals the previous `to`, and the last `to` is END. See examples/latam.tsx for a full
// 6-minute cut and EDITING_RULES.md + the sadat-style-video skill for the rules.
import React from 'react';
import {Film, FilmProps} from '../layers/Film';
import {Black, ConcreteWall, Paper} from '../layers/Backgrounds';
import {BlackTag, DateTag, NameStrip, PhotoPrint} from '../layers/Print';
import {BigSerif, GhostTitle, Highlight, LabelTape, ListWords, QuoteText} from '../layers/Type';
import {Chart, DocCard, DocMap} from '../layers/Evidence';
import {EnterKind} from '../transitions';
import media from '../lib/media.json';

export type Scene = {id: string; from: number; to: number; enter: EnterKind; why: string; el: React.ReactNode};

// word-by-word helpers for QuoteText / ListWords: q('a b c', [t0, t1, t2]), l('one|two', [t0, t1])
export const q = (s: string, t0: number[]) => s.split(' ').map((w, i) => ({w, at: t0[i]}));
export const l = (s: string, t0: number[]) => s.split('|').map((w, i) => ({w, at: t0[i]}));

// house rule: 4:3 film is never zoomed to fill — anything narrower than 1.7:1 is padded automatically
const M = media as Record<string, {w: number; h: number; d: number}>;
export const F: React.FC<FilmProps> = (p) => <Film fit={M[p.src] && M[p.src].w / M[p.src].h < 1.7 ? 'pad' : 'fill'} {...p} />;

// unused imports are fine while the edit is being written; delete what the cut never uses
void [Black, ConcreteWall, Paper, BlackTag, DateTag, NameStrip, PhotoPrint, BigSerif, GhostTitle, Highlight, LabelTape, ListWords, QuoteText, Chart, DocCard, DocMap];

export const END = 5; // last narration word end + ~2 s, then the 2.2 s fade

export const SCENES: Scene[] = [
  {id: 'start', from: 0, to: END, enter: 'cut', why: 'placeholder until the edit is written',
    el: <Black />},
];

// film burns (projector sound included) only where the picture changes layer (film <-> print/graphic), 3-6 per video
export const BURNS: {at: number; n: number}[] = [];

// real SFX files in public/sfx only (no synthesised effects)
export const SFX: {at: number; file: string; vol: number}[] = [];
