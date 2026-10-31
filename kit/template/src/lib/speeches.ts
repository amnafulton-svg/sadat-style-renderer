// Leaders' key lines: a real filmed speech (its own sound) cut in BETWEEN two parts of the voice-over. The narration
// stops at a part break, a film burn takes us into the speech, a second burn brings us back and the narration goes on
// from where it stopped (the Bin Laden reference: Obama's 13 s line at a part boundary, never over the narrator).
// Entries are written by tools/speech.py into speeches.json. An empty list = the normal cut, nothing changes.
import list from './speeches.json';
import {nf, sf} from './core';

export type Speech = {
  at: number; // narration seconds where the voice-over pauses (a scene's `from`, on a part / paragraph break)
  file: string; // public/speeches/<file>.mp4 (cut + cleaned by tools/speech.py)
  dur: number; // seconds of the speech clip
  line1: string; // who speaks ("Franklin D. Roosevelt")
  line2?: string; // where / when ("Congress, 8 December 1941")
  burnIn?: number; // film burn into the speech (default 4)
  burnOut?: number; // film burn back to the narration (default 5)
  subs?: boolean; // the film has burned-in English subtitles: the name tag goes top left, off them
  focusY?: number; // % of the frame height the slow push-in heads for (default 58: faces in a lectern shot)
};

export const SPEECHES: Speech[] = [...(list as Speech[])].sort((a, b) => a.at - b.at);

/** frames of one speech insert */
export const speechFrames = (s: Speech) => sf(s.dur);

/** frame of the finished video for a narration second (the speeches before it push it later) */
export const vf = (t: number) => nf(t) + SPEECHES.filter((s) => nf(s.at) <= nf(t)).reduce((n, s) => n + speechFrames(s), 0);

export const SPEECH_FRAMES = SPEECHES.reduce((n, s) => n + speechFrames(s), 0);
