// Photo prints and the annotations the reference puts on them.
// PhotoPrint: a real photo as a physical print (white border, slight tilt, drop shadow) that flies in from
//   off-screen in ~0.3 s and settles, one per narrated beat, accumulating into a cluster. WHY: a group of
//   people / a list of things is shown as evidence being laid on the table, so the count builds with the voice.
// NameStrip: torn white paper strip with a serif name, slapped on when the person is NAMED. On a photo it is the
//   print's own names=[{text, sub, at, fx}]: hung under the photo's bottom edge, people's order left to right (fx).
// RedCircle: hand-drawn marker loop around one face/detail: "this one".
// BlackTag / DateTag: small black label (who / when), the reference's date & name tags.
import React from 'react';
import {Img, OffthreadVideo, interpolate, staticFile} from 'remotion';
import {C, FONT, easeInOut, easeOut, prog, rand} from '../lib/core';
import {HAND_K} from '../lib/core';
import INK_AUTO from '../lib/ink.json';
// tools/fixink.py measures the picture behind each plain line / note and writes the colour that shows there
const inkAuto = (text: string, at: number) => (INK_AUTO as Record<string, {ink?: boolean; arrow?: string; color?: string; soft?: string}>)[`${text}|${at}`];

import {Stage, StageCtx, StageSteps, useCue, useScene} from '../lib/scene';
import {GRADE, Grade} from './Film';
import {Z_LABEL, safeY} from './Type';

type From = 'left' | 'right' | 'top' | 'bottom' | 'fade';

export const PhotoPrint: React.FC<{
  src: string;
  at: number; // narration s when it lands
  x: number; // centre, px
  y: number;
  w: number; // print width incl. border, px
  rot?: number;
  from?: From;
  grade?: Grade;
  border?: number;
  objectPosition?: string;
  aspect?: number; // force picture aspect (w/h), cropping the photo
  drift?: number; // px of slow drift over the scene
  film?: {start: number; rate?: number}; // src is then a clip in public/footage: moving film inside the print (needs aspect)
  children?: React.ReactNode; // annotations in print-local px
  tag?: {line1: string; line2?: string; at?: number; size?: number}; // the print's black caption, stuck on its bottom-left edge
  names?: PrintNameT[]; // name strips hung under the photo; fx = where that person stands (0-1) orders them left to right
  hand?: PrintHandT; // one person's portrait: the name written by hand in pencil on the wall beside the print
}> = ({src, at, x, y, w, rot = 0, from = 'bottom', grade = 'sepia', border = 14, objectPosition = 'center', aspect, drift = 18, film, children, tag, names, hand}) => {
  const cue = useCue();
  const {frame, durFrames} = useScene();
  const start = cue(at) - 8; // lands on the word: the 8-frame flight ends as the word starts
  const p = prog(frame, start, 9, easeOut);
  const off = {left: [-1500, 0], right: [1500, 0], top: [0, -1100], bottom: [0, 1100], fade: [0, 0]}[from];
  const dx = off[0] * (1 - p);
  const dy = off[1] * (1 - p);
  const r = rot + (from === 'fade' ? 0 : (1 - p) * (rand(x + y) > 0.5 ? 9 : -9));
  const opacity = from === 'fade' ? p : frame < start ? 0 : 1;
  const d = interpolate(frame, [0, durFrames], [0, drift]);
  // waits in the middle of the wall, and is pushed to its own place as each later print flies in (stagePlan)
  const sx = stageX(React.useContext(StageCtx)[`${src}|${at}`], frame, cue);
  return (
    <div
      style={{
        position: 'absolute',
        // whole-px left/top + the moving part in transform: Chrome snaps left/top to whole pixels, so a slow
        // drift there stepped 1 px every ~0.7 s and the prints shook (Alaska 2026-10-23); transforms move sub-pixel
        left: x - w / 2,
        top: y,
        width: w,
        transform: `translate(${dx + sx + d * 0.6}px, ${dy - d * 0.3}px) translateY(-50%) rotate(${r}deg) scale(${1 + (1 - p) * 0.06})`,
        opacity,
        background: '#f1ece0',
        padding: border,
        boxShadow: '0 22px 50px rgba(0,0,0,0.65), 0 4px 10px rgba(0,0,0,0.5)',
      }}
    >
      <div style={{position: 'relative', width: '100%', aspectRatio: aspect ? `${aspect}` : undefined, overflow: aspect || film ? 'hidden' : 'visible'}}>
        {film ? (
          <OffthreadVideo
            src={staticFile(`footage/${src}`)}
            startFrom={Math.round(film.start * 25)}
            playbackRate={film.rate ?? 1}
            muted
            style={{display: 'block', width: '100%', height: '100%', objectFit: 'cover', objectPosition, filter: GRADE[grade]}}
          />
        ) : (
          <Img
            src={staticFile(`photos/${src}`)}
            style={{display: 'block', width: '100%', height: aspect ? '100%' : 'auto', objectFit: 'cover', objectPosition, filter: GRADE[grade]}}
          />
        )}
        {children}
      </div>
      {names && (
        // one row hanging off the bottom edge (half on the white border, half below), people's order left to right;
        // right-aligned when the black caption takes the bottom-left corner
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            transform: 'translateY(55%)',
            display: 'flex',
            justifyContent: tag ? 'flex-end' : 'center',
            alignItems: 'flex-start',
            gap: 16,
            padding: tag ? '0 18px 0 0' : 0,
            zIndex: 3,
          }}
        >
          {[...names].sort((a, b) => (a.fx ?? 0.5) - (b.fx ?? 0.5)).map((n, i) => (
            <PrintName key={i} {...n} />
          ))}
        </div>
      )}
      {tag && <PrintTag {...tag} at={tag.at ?? at + 0.2} room={w} />}
      {hand && <PrintHand {...hand} side={hand.side ?? (x < 960 ? 'right' : 'left')} room={((hand.side ?? (x < 960 ? 'right' : 'left')) === 'right' ? 1920 - (x + w / 2) : x - w / 2) - 150} />}
    </div>
  );
};

/** px a print stands off its own place right now: centred with the prints already on the wall, home once all are in */
const stageX = (st: StageSteps | undefined, frame: number, cue: (s: number) => number) =>
  (st ?? []).reduce((v, s, i, a) => v + ((a[i + 1]?.dx ?? 0) - s.dx) * prog(frame, cue(s.until) - 9, 12, easeInOut), st?.[0]?.dx ?? 0);

/** a label, ring or note that belongs to a waiting print travels with it */
const StageShift: React.FC<{st: StageSteps; children: React.ReactNode}> = ({st, children}) => {
  const cue = useCue();
  const {frame} = useScene();
  return <div style={{position: 'absolute', inset: 0, zIndex: Z_LABEL, pointerEvents: 'none', transform: `translateX(${stageX(st, frame, cue)}px)`}}>{children}</div>;
};

/** HOUSE (producer, Japan oil 22:13, 2026-11-15): prints that arrive one after another do not leave half the wall
 *  empty while the first one waits - "the image should be in the middle and after the second image is shown it
 *  should be pushed to the left". Reads the scene's element tree: the prints on the wall so far sit centred as a
 *  group, and slide to the places the editor gave them as the next one flies in; what is placed on or under a
 *  waiting print (a label, a ring) travels with it. Left alone when the next print arrives within 3 s (a short wait keeps the editor's layout: producer, Asashimo/Kasumi), when a
 *  print carries a handwritten name beside it, or when something else already stands on the wall the print would
 *  wait on. */
export const stagePlan = (el: React.ReactNode): {stage: Stage; el: React.ReactNode} => {
  type P = {src: string; at: number; x: number; y: number; w: number; hand?: unknown};
  type O = {node: React.ReactElement; x: number; y: number; at: number};
  const none = {stage: {}, el};
  const prints: P[] = [];
  const others: O[] = [];
  const walk = (n: React.ReactNode) =>
    React.Children.forEach(n, (c) => {
      if (!React.isValidElement(c)) return;
      const p = c.props as Record<string, unknown>;
      if (c.type === PhotoPrint) return void prints.push(p as unknown as P);
      const x = p.x ?? p.cx;
      const y = p.y ?? p.cy;
      if (typeof x === 'number' && typeof y === 'number') others.push({node: c, x, y, at: typeof p.at === 'number' ? p.at : 0});
      if (typeof p.children !== 'function') walk(p.children as React.ReactNode);
    });
  walk(el);
  if (prints.length < 2 || prints.some((p) => p.hand || ![p.x, p.y, p.w, p.at].every((v) => typeof v === 'number'))) return none;
  const groups: P[][] = [];
  for (const p of [...prints].sort((a, b) => a.at - b.at)) {
    const g = groups[groups.length - 1];
    if (g && p.at - g[0].at < 3) g.push(p);
    else groups.push([p]);
  }
  if (groups.length < 2) return none;
  const last = groups[groups.length - 1][0].at;
  const stage: Stage = {};
  const ride = new Map<React.ReactElement, string>(); // a label / ring -> the print it stands on
  for (let k = 0; k < groups.length - 1; k++) {
    const on = groups.slice(0, k + 1).flat();
    const dx = Math.round(960 - (Math.min(...on.map((p) => p.x - p.w / 2)) + Math.max(...on.map((p) => p.x + p.w / 2))) / 2);
    if (Math.abs(dx) < 40) return none;
    for (const o of others) {
      if (o.at >= last - 0.3 || Math.abs(o.x - 960) < 40) continue; // arrives with the finished layout / a line centred on the screen
      const near = (p: P) => Math.abs(o.y - p.y) < p.w * 0.62 + 100;
      const own = on.find((p) => near(p) && Math.abs(o.x - p.x) < p.w / 2 + 60);
      if (own) ride.set(o.node, `${own.src}|${own.at}`);
      else if (on.some((p) => near(p) && Math.abs(o.x - (p.x + dx)) < p.w / 2 + 320)) return none; // stands where the print would wait, counting how wide a typed line with its sub-line is
    }
    for (const p of on) (stage[`${p.src}|${p.at}`] ??= []).push({until: groups[k + 1][0].at, dx});
  }
  if (!ride.size) return {stage, el};
  const rebuild = (n: React.ReactNode): React.ReactNode =>
    React.Children.map(n, (c) => {
      if (!React.isValidElement(c) || c.type === PhotoPrint) return c;
      const key = ride.get(c);
      if (key) return <StageShift st={stage[key]}>{c}</StageShift>;
      const ch = (c.props as {children?: React.ReactNode}).children;
      return ch && typeof ch !== 'function' ? React.cloneElement(c, {}, rebuild(ch)) : c;
    });
  return {stage, el: rebuild(el)};
};

type PrintNameT = {text: string; sub?: string; at: number; fx?: number; fy?: number; rot?: number; size?: number}; // fx: where the person stands (0-1), only orders the row

/** a name strip hanging under the photo it names, in the row of the print's names (producer, cannabis 6:00
 *  2026-10-25: free strips floated beside the photo, "where does it belongs?"; then strips on the faces: "the white
 *  tag should be under the image not on the face") */
const PrintName: React.FC<PrintNameT> = ({text, sub, at, rot = -2, size = 34}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 6);
  return (
    <div
      style={{
        transform: `rotate(${rot}deg) scale(${1.3 - 0.3 * p})`,
        opacity: p,
        background: '#f6f3ec',
        padding: '12px 26px 10px',
        clipPath: torn(text),
        boxShadow: '0 6px 14px rgba(0,0,0,.5)',
        zIndex: 3,
        textAlign: 'center',
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{fontFamily: FONT.serif, fontSize: size, color: '#151515', lineHeight: 1.05}}>{text}</div>
      {sub && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: size * 0.5, color: '#444', marginTop: 3}}>{sub}</div>}
    </div>
  );
};

type PrintHandT = {name: string; role?: string; note?: string; at: number; noteAt?: number; side?: 'left' | 'right'; size?: number; color?: string};

/** one person's portrait: the name written by hand in white pencil on the wall beside the print, an arrow drawn
 *  to the photo, role in small typewriter, an optional dated note in orange pencil written on its own spoken word.
 *  It sits on the free side of the print (the print goes big on one side of the wall, w 620-700) and sizes itself
 *  to the room left (producer, Pacific 0:46 2026-11-10: designed serif type beside the print "looks templated";
 *  the handwritten note was the pick, the date in orange) */
const PrintHand: React.FC<PrintHandT & {room: number}> = ({name, role, note, at, noteAt, side = 'right', size, color = '#e8915a', room}) => {
  const cue = useCue();
  const {frame} = useScene();
  const sz = size ?? Math.max(84, Math.min(158, room / (name.length * 0.4)));
  const p = prog(frame, cue(at), 16);
  const pa = prog(frame, cue(at) + 12, 10);
  const pr = prog(frame, cue(at) + 14, 10);
  const pn = note ? prog(frame, cue(noteAt ?? at), 12) : 0;
  const chalk = '#f4f1e8';
  const right = side === 'right';
  const wipe = (q: number) => `inset(-20% ${100 - q * 104}% -20% 0)`; // written on left to right
  const sh = 'none'; // crisp thin edge, no blur (producer 2026-11-15: no shadow behind text)
  const inset = sz * 0.7;
  return (
    <div
      style={{
        position: 'absolute',
        top: '32%', // low enough that the name's rising end stays under a date tag in the top corner
        ...(right ? {left: 'calc(100% + 96px)'} : {right: 'calc(100% + 96px)'}),
        width: room,
        transform: 'rotate(-3deg)',
        transformOrigin: right ? 'left center' : 'right center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: right ? 'flex-start' : 'flex-end',
        zIndex: Z_LABEL,
      }}
    >
      <div style={{position: 'relative'}}>
        <div style={{fontFamily: FONT.hand, fontWeight: 700, fontSize: (sz) * HAND_K, lineHeight: 0.9, color: chalk, whiteSpace: 'nowrap', clipPath: wipe(p), textShadow: sh}}>{name}</div>
        <svg width={150} height={130} viewBox="0 0 260 130" style={{position: 'absolute', top: sz * 0.78, ...(right ? {left: -70} : {right: -70, transform: 'scaleX(-1)'}), overflow: 'visible'}}>
          <path d="M250 20 C 180 120, 90 130, 10 80" fill="none" stroke={chalk} strokeWidth={9} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - pa} />
          <path d="M44 62 L8 80 L40 108" fill="none" stroke={chalk} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" opacity={pa > 0.95 ? 1 : 0} />
        </svg>
      </div>
      {role && (
        <div style={{fontFamily: FONT.type, fontSize: Math.max(30, sz * 0.25), lineHeight: 1.35, color: chalk, opacity: 0.9 * pr, margin: `${sz * 0.25}px ${right ? 0 : inset}px 0 ${right ? inset : 0}px`, maxWidth: room - inset, whiteSpace: 'pre-line', textAlign: right ? 'left' : 'right', textShadow: sh}}>
          {role}
        </div>
      )}
      {note && (
        <div style={{fontFamily: FONT.hand, fontWeight: 700, fontSize: (sz * 0.5) * HAND_K, color, margin: `${sz * 0.14}px ${right ? 0 : inset}px 0 ${right ? inset : 0}px`, whiteSpace: 'nowrap', clipPath: wipe(pn), textShadow: sh}}>{note}</div>
      )}
    </div>
  );
};

/** torn top and bottom edges of a paper strip (seeded by its text) */
const torn = (text: string) => {
  const top = Array.from({length: 18}, (_, i) => `${(i / 17) * 100}% ${i % 2 ? 0 : 7 + rand(i + text.length) * 8}%`).join(',');
  const bot = Array.from({length: 18}, (_, i) => `${100 - (i / 17) * 100}% ${i % 2 ? 100 : 93 - rand(i * 3 + text.length) * 8}%`).join(',');
  return `polygon(${top},${bot})`;
};

/** the caption of one print, stuck across its bottom-left edge (60 % on the print, 40 % below), so it always sits
 *  under the photo it names and moves with it (producer, cannabis 2026-10-25: "why the text in the black box is
 *  not under the image?": free BlackTags were placed by hand and landed across the frame from their print) */
// rough serif widths per character (em): capitals are wide, so an all-caps caption needs ~0.72 em a letter
const serifEm = (t: string) => [...t].reduce((n, c) => n + (c === ' ' ? 0.3 : /[A-Z0-9]/.test(c) ? 0.72 : /[a-z]/.test(c) ? 0.52 : 0.45), 0);

/** the print's black caption. It never runs past its own print (JP Morgan 2026-11-23: captions wider than the print
 *  slid under the next one): the type shrinks to fit the print's width, and below 22 px it wraps onto two lines. */
const PrintTag: React.FC<{at: number; line1: string; line2?: string; size?: number; room: number}> = ({at, line1, line2, size = 38, room}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at) - 3, 8);
  const space = room - 28 - 44 - 10; // left offset, padding, a little air before the print's right edge
  const fit = Math.min(size, space / Math.max(serifEm(line1), (line2 ? serifEm(line2) * 0.58 : 0), 1));
  const wrap = fit < 22;
  size = wrap ? 22 : Math.floor(fit);
  return (
    <div
      style={{
        position: 'absolute',
        left: 28,
        bottom: 0,
        transform: `translate(${(1 - p) * -30}px, 40%)`,
        opacity: p,
        background: C.tag,
        padding: '12px 22px 12px',
        boxShadow: '0 8px 20px rgba(0,0,0,.5)',
        zIndex: 2,
      }}
    >
      <div style={{fontFamily: FONT.serif, color: '#f4f0e6', fontSize: size, lineHeight: 1.1, whiteSpace: wrap ? 'normal' : 'nowrap', maxWidth: wrap ? space : undefined}}>{line1}</div>
      {line2 && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', color: '#bdb6a6', fontSize: size * 0.58, marginTop: 4, whiteSpace: 'nowrap'}}>{line2}</div>}
    </div>
  );
};

/** torn white paper strip with a serif name; slapped on (scale 1.3 -> 1) on the named word */
export const NameStrip: React.FC<{text: string; at: number; x: number; y: number; rot?: number; size?: number; sub?: string}> = ({
  text,
  at,
  x,
  y,
  rot = -3,
  size = 44,
  sub,
}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 6);
  return (
    <div
      style={{
        position: 'absolute',
        left: Math.max(260, Math.min(x, 1660)),
        top: safeY(y, size * 1.25 + 30 + (sub ? size : 0)),
        transform: `translate(-50%,-50%) rotate(${rot}deg) scale(${1.3 - 0.3 * p})`,
        opacity: p,
        background: '#f6f3ec',
        padding: '16px 34px 14px',
        clipPath: torn(text),
        boxShadow: '0 6px 14px rgba(0,0,0,.5)',
        zIndex: Z_LABEL,
        textAlign: 'center',
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{fontFamily: FONT.serif, fontSize: size, color: '#151515', lineHeight: 1.05}}>{text}</div>
      {sub && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: size * 0.5, color: '#444', marginTop: 4}}>{sub}</div>}
    </div>
  );
};

/** hand-drawn marker ellipse that draws itself in ~0.5 s (coordinates in the parent's px) */
export const RedCircle: React.FC<{at: number; cx: number; cy: number; rx: number; ry: number; stroke?: number}> = ({at, cx, cy, rx, ry, stroke = 7}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 12);
  // one clean pen stroke: a smooth loop that opens out a little and runs just past its start. No wobble along the
  // line (producer, Japan oil 4:30, 2026-11-15: "doesnt look clean it always looks like it has little cercles")
  const N = 120;
  const pts = Array.from({length: N + 1}, (_, i) => {
    const t = i / N;
    const a = t * Math.PI * 2.14 - Math.PI * 0.62;
    const r = 0.965 + 0.07 * t + 0.022 * Math.sin(a + 0.8);
    return `${(cx + Math.cos(a) * rx * r).toFixed(1)},${(cy + Math.sin(a) * ry * r).toFixed(1)}`;
  });
  const len = 1;
  return (
    <svg style={{position: 'absolute', inset: 0, width: '100%', height: '100%', overflow: 'visible', pointerEvents: 'none'}}>
      <polyline pathLength={1}
        points={pts.join(' ')}
        fill="none"
        stroke={C.red}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - p)}
        opacity={0.92}
      />
    </svg>
  );
};

/** handwritten note on a full-screen photo or film: the words are written on at the spoken moment, an arrow is drawn
 *  from them to the thing, an orange ring can close around it, and a second line (place, date) follows in the same pen
 *  (producer, Pacific 5:07 2026-11-10: "USS Quincy" written on the photo with the ship ringed, picked over the black
 *  tag in the corner). White paint pen on dark pictures; `ink` writes in dark ink for a bright sky or wall. Both carry
 *  a crisp thin edge in the opposite tone, so the note reads on a mid-grey photo too; nothing is blurred behind it
 *  and the second line is no longer orange (producer, Japan oil 0:33 2026-11-15: the orange date on a grey sky was
 *  unreadable and the arrow ran through it). An arrow that would start inside the words starts under them.
 *  x/y = where the words start, from/to = arrow start and tip, ring = [cx, cy, rx, ry], all in frame pixels. */
export const HandNote: React.FC<{
  x: number; y: number; text: string; sub?: string; at: number; subAt?: number; size?: number; rot?: number;
  from?: [number, number]; to?: [number, number]; bend?: number; ring?: [number, number, number, number]; ink?: boolean; color?: string;
}> = ({x, y, text, sub, at, subAt, size = 120, rot = -3, from, to, bend = 50, ring, ink, color = '#e8915a'}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at), 14);
  const pa = prog(frame, cue(at) + 10, 9);
  const pr = prog(frame, cue(at) + 16, 12);
  const ps = sub ? prog(frame, cue(subAt ?? at), 12) : 0;
  const auto = inkAuto(text, at); // the measured choice wins over the `ink` the editor wrote
  const pen = auto?.color ?? ((auto?.ink ?? ink) ? '#14110d' : '#f7efdc');
  const arrowCol = auto?.arrow ?? pen; // the arrow leaves the pen's colour only where that would not show
  const rim = 'transparent'; // no outline on the handwriting (producer 2026-11-15): the pen colour follows the picture
  const soft = auto?.soft; // a grey, busy picture: warm white stays, with a soft dark shadow or a feathered dark patch behind the words
  const sh = 'none';
  const w = 7;
  // the words' box (frame px, before the small tilt): an arrow must not start inside it
  const bw = Math.max(text.length * size * 0.4, (sub ?? '').length * size * 0.62 * 0.4 + 12);
  const bh = size * 0.9 + (sub ? size * 0.62 * 1.25 + 6 : 0);
  if (from && to && from[0] > x - 20 && from[0] < x + bw + 20 && from[1] > y - 20 && from[1] < y + bh + 20) {
    const dxx = to[0] - (x + bw / 2);
    const dyy = to[1] - (y + bh / 2);
    from = Math.abs(dyy) * bw >= Math.abs(dxx) * bh
      ? [Math.max(x + 30, Math.min(from[0], x + bw - 30)), dyy > 0 ? y + bh + 34 : y - 34]
      : [dxx > 0 ? x + bw + 40 : x - 40, Math.max(y + 20, Math.min(from[1], y + bh - 20))];
  }
  let arrow: React.ReactNode = null;
  if (from && to) {
    const dx = to[0] - from[0];
    const dy = to[1] - from[1];
    const len = Math.hypot(dx, dy) || 1;
    const cx = (from[0] + to[0]) / 2 - (dy / len) * bend;
    const cy = (from[1] + to[1]) / 2 + (dx / len) * bend;
    const a = Math.atan2(to[1] - cy, to[0] - cx);
    const h = 30;
    arrow = (
      <>
        {[[rim, w + 6], [arrowCol, w]].map(([c, sw], i) => (
          <React.Fragment key={i}>
            <path d={`M${from[0]} ${from[1]} Q ${cx} ${cy} ${to[0]} ${to[1]}`} fill="none" stroke={c as string} strokeWidth={sw as number} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - pa} />
            <path
              d={`M${to[0] - h * Math.cos(a - 0.5)} ${to[1] - h * Math.sin(a - 0.5)} L${to[0]} ${to[1]} L${to[0] - h * Math.cos(a + 0.5)} ${to[1] - h * Math.sin(a + 0.5)}`}
              fill="none" stroke={c as string} strokeWidth={sw as number} strokeLinecap="round" strokeLinejoin="round" opacity={pa > 0.95 ? 1 : 0}
            />
          </React.Fragment>
        ))}
      </>
    );
  }
  return (
    <>
      <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, zIndex: Z_LABEL, overflow: 'visible'}}>
        {arrow}
        {ring ? (
          <ellipse cx={ring[0]} cy={ring[1]} rx={ring[2]} ry={ring[3]} fill="none" stroke={color} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - pr} transform={`rotate(-4 ${ring[0]} ${ring[1]})`} />
        ) : null}
      </svg>
      {soft === 'grad' ? (
        <div style={{position: 'absolute', left: x - 170, top: y - 110, width: bw + 340, height: bh + 220, zIndex: Z_LABEL, opacity: p, transform: `rotate(${rot}deg)`, background: 'radial-gradient(ellipse closest-side, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.4) 45%, rgba(0,0,0,0) 100%)', pointerEvents: 'none'}} />
      ) : null}
      <div style={{position: 'absolute', left: x, top: y, zIndex: Z_LABEL, transform: `rotate(${rot}deg)`, transformOrigin: '0 50%'}}>
        <div style={{fontFamily: FONT.hand, fontWeight: 700, fontSize: (size) * HAND_K, lineHeight: 0.9, color: pen, whiteSpace: 'nowrap', clipPath: `inset(-60% ${100 - p * 104}% -60% -10%)`, textShadow: sh}}>{text}</div>
        {sub ? (
          <div style={{fontFamily: FONT.hand, fontWeight: 700, fontSize: (size * 0.62) * HAND_K, color: pen, marginTop: 6, marginLeft: 12, whiteSpace: 'nowrap', clipPath: `inset(-60% ${100 - ps * 104}% -60% -10%)`, textShadow: sh}}>{sub}</div>
        ) : null}
      </div>
    </>
  );
};

/** small black label: white serif line + optional italic second line (name/role, place/year) */
export const BlackTag: React.FC<{at: number; x: number; y: number; line1: string; line2?: string; size?: number; align?: 'left' | 'right'}> = ({
  at,
  x,
  y,
  line1,
  line2,
  size = 46,
  align = 'left',
}) => {
  const cue = useCue();
  const {frame} = useScene();
  const p = prog(frame, cue(at) - 3, 8);
  const w = Math.max(line1.length * size * 0.7, (line2?.length ?? 0) * size * 0.58 * 0.5) + 44; // a long tag never runs off the frame
  return (
    <div
      style={{
        position: 'absolute',
        [align]: align === 'left' ? Math.min(x, 1920 - 48 - w) : 1920 - Math.max(x, 48 + w),
        top: y,
        background: C.tag,
        padding: '12px 22px 12px',
        opacity: p,
        transform: `translateX(${(1 - p) * (align === 'left' ? -30 : 30)}px)`,
        boxShadow: '0 8px 20px rgba(0,0,0,.5)',
        zIndex: Z_LABEL,
      }}
    >
      <div style={{fontFamily: FONT.serif, color: '#f4f0e6', fontSize: size, lineHeight: 1.1, whiteSpace: 'nowrap'}}>{line1}</div>
      {line2 && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', color: '#bdb6a6', fontSize: size * 0.58, marginTop: 4, whiteSpace: 'nowrap'}}>{line2}</div>}
    </div>
  );
};

/** black date tag with white serif date ("24 October 1972" in the reference); typed on letter by letter (done in 0.6 s at most).
 *  HOUSE (producer 2026-11-05): always in a top corner, never mid-frame over faces: top left by default, corner="right"
 *  puts it top right under the source tag. x/y are ignored (kept so older cuts still compile). */
export const DateTag: React.FC<{at: number; text: string; x?: number; y?: number; size?: number; corner?: 'left' | 'right'}> = ({at, text, corner = 'left', size = 46}) => {
  const cue = useCue();
  const {frame} = useScene();
  const s = cue(at) - 4;
  const n = Math.max(0, Math.min(text.length, Math.floor((frame - s) / Math.min(1.2, 15 / Math.max(1, text.length)))))  // typed in <= 0.6 s;
  const w = text.length * size * 0.62 + 56;
  const left = corner === 'right' ? 1920 - 64 - w : 64;
  const top = corner === 'right' ? 150 : 56; // right: below "[N] Source in Description"
  return (
    <div style={{position: 'absolute', left, top, background: C.tag, padding: '14px 28px', opacity: frame >= s ? 1 : 0, boxShadow: '0 8px 20px rgba(0,0,0,.5)', zIndex: Z_LABEL}}>
      <span style={{fontFamily: FONT.serif, fontSize: size, color: '#f4f0e6', whiteSpace: 'pre'}}>{text.slice(0, n)}</span>
      <span style={{fontFamily: FONT.serif, fontSize: size, color: 'transparent', whiteSpace: 'pre'}}>{text.slice(n)}</span>
    </div>
  );
};
