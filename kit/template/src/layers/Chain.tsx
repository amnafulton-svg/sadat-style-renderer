// ChainBoard — an evidence board (producer 2026-11-05, from the Bin Laden reference): prints pinned on a big wall,
// joined by red string, the camera flying from print to print as the narration names each link, then pulling back
// to the whole chain. For a line that ties several causes, people or events to one thing ("three pressures met in one
// place", "the money went from A to B to C"). The wall is a world WxH px (default 3840x2160, twice the frame); every
// x/y/w is in world px, every `at` in narration seconds. Films play inside their print from the moment it lands, then
// rest on `poster` (a jpg of the film's last frame under public/, e.g. ffmpeg -sseof -0.25 -i f.mp4 -frames:v 1).
//   <ConcreteWall dim={0.4}><ChainBoard
//     nodes={[{id: 'cc', src: 'camp.jpg', at: 1724.5, x: 1920, y: 1450, w: 980, aspect: 1.36, title: 'Camp Century'},
//             {id: 'army', src: 'redstone.mp4', film: {start: 0, len: 4.6, poster: 'chain/redstone_last.jpg'},
//              at: 1728.6, x: 640, y: 600, w: 960, aspect: 1.62, title: "The Army's budget", sub: 'a nuclear mission'}]}
//     links={[{from: 'army', to: 'cc', at: 1730.8, fs: 'right', ts: 'left'}]}
//     cam={[{at: 1723.9, x: 1920, y: 1480, zoom: 1.0}, {at: 1728.3, x: 640, y: 660, zoom: 1.2},
//           {at: 1744.4, x: 1920, y: 1000, zoom: 0.47, dur: 45}]} /></ConcreteWall>
// zoom 1.2 = one print close; 0.47 = the whole 3840 wall. Check the stills: titles must not sit on a string's pin.
import React from 'react';
import {Img, OffthreadVideo, Sequence, interpolate, staticFile} from 'remotion';
import {FONT, easeInOut, easeOut, prog} from '../lib/core';
import {useCue, useScene} from '../lib/scene';
import {GRADE, Grade} from './Film';

export type ChainNode = {
  id: string; src: string; at: number; x: number; y: number; w: number; aspect: number; rot?: number;
  grade?: Grade; film?: {start: number; len: number; poster: string}; title?: string; sub?: string; titleAt?: number;
};
type Side = 'top' | 'bottom' | 'left' | 'right';
export type ChainLink = {from: string; to: string; at: number; sag?: number; fs?: Side; ts?: Side};
export type ChainCam = {at: number; x: number; y: number; zoom: number; dur?: number};

const RED = '#b3261e';

const Pin: React.FC<{x: number; y: number; p: number}> = ({x, y, p}) => (
  <div style={{position: 'absolute', left: x - 15, top: y - 15, width: 30, height: 30, borderRadius: 15, opacity: p,
    transform: `scale(${0.6 + 0.4 * p})`, background: `radial-gradient(circle at 35% 35%, #ff6b5e, ${RED} 55%, #5e0f0b)`,
    boxShadow: '0 6px 10px rgba(0,0,0,.6)', zIndex: 5}} />
);

export const ChainBoard: React.FC<{
  nodes: ChainNode[]; links: ChainLink[]; cam: ChainCam[];
  W?: number; H?: number;
}> = ({nodes, links, cam, W = 3840, H = 2160}) => {
  const cue = useCue();
  const {frame, durFrames} = useScene();
  // camera: glide from key to key
  let v = {x: cam[0].x, y: cam[0].y, z: cam[0].zoom};
  for (let i = 1; i < cam.length; i++) {
    const p = prog(frame, cue(cam[i].at), cam[i].dur ?? 30, easeInOut);
    if (p <= 0) break;
    v = {x: v.x + (cam[i].x - v.x) * p, y: v.y + (cam[i].y - v.y) * p, z: v.z + (cam[i].zoom - v.z) * p};
  }
  const z = v.z * interpolate(frame, [0, durFrames], [1, 1.03]);
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  // where a string is pinned: the middle of one edge of the print, just inside its white border
  const end = (n: ChainNode, s: Side) => { const h = n.w / n.aspect;
    return {top: {x: n.x, y: n.y - h / 2 - 2}, bottom: {x: n.x, y: n.y + h / 2 + 2}, left: {x: n.x - n.w / 2 - 2, y: n.y}, right: {x: n.x + n.w / 2 + 2, y: n.y}}[s]; };
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: W, height: H, transformOrigin: '0 0',
      transform: `translate(${960 - z * v.x}px, ${540 - z * v.y}px) scale(${z})`}}>
      {nodes.map((n) => {
        const land = cue(n.at) - 8;
        const p = prog(frame, land, 10, easeOut);
        if (frame < land) return null;
        const h = n.w / n.aspect;
        const filter = GRADE[n.grade ?? 'none'];
        const tp = prog(frame, cue(n.titleAt ?? n.at + 0.4), 8);
        return (
          <div key={n.id} style={{position: 'absolute', left: n.x - n.w / 2, top: n.y - h / 2, width: n.w, height: h,
            transform: `translateY(${(1 - p) * 120}px) rotate(${(n.rot ?? 0) + (1 - p) * 6}deg) scale(${1 + (1 - p) * 0.08})`,
            opacity: Math.min(1, p * 1.6), background: '#f1ece0', padding: 16, boxSizing: 'content-box', marginLeft: -16, marginTop: -16,
            boxShadow: '0 30px 60px rgba(0,0,0,.7), 0 6px 14px rgba(0,0,0,.5)'}}>
            <div style={{position: 'relative', width: n.w, height: h, overflow: 'hidden', background: '#111'}}>
              {n.film ? (
                <>
                  <Img src={staticFile(n.film.poster)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter}} />
                  <Sequence from={land} durationInFrames={Math.floor(n.film.len * 25) - 2} layout="none">
                    <OffthreadVideo src={staticFile(`footage/${n.src}`)} startFrom={Math.round(n.film.start * 25)} muted
                      style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter}} />
                  </Sequence>
                </>
              ) : (
                <Img src={staticFile(`photos/${n.src}`)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter}} />
              )}
            </div>
            {n.title && (
              <div style={{position: 'absolute', left: -6, bottom: -34, transform: `rotate(-1.5deg) scale(${1.25 - 0.25 * tp})`, opacity: tp,
                transformOrigin: 'left center', background: '#141414', padding: '12px 24px 10px', boxShadow: '0 8px 18px rgba(0,0,0,.6)', zIndex: 4}}>
                <div style={{fontFamily: FONT.cond, fontSize: 46, color: '#f2ead8', letterSpacing: 1, whiteSpace: 'nowrap', textTransform: 'uppercase'}}>{n.title}</div>
                {n.sub && <div style={{fontFamily: FONT.serif, fontStyle: 'italic', fontSize: 32, color: '#cfc6b4', whiteSpace: 'nowrap', marginTop: 2}}>{n.sub}</div>}
              </div>
            )}
          </div>
        );
      })}
      <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', zIndex: 4}}>
        {links.map((l, i) => {
          const a = end(byId[l.from], l.fs ?? 'bottom'), b = end(byId[l.to], l.ts ?? 'top');
          const p = prog(frame, cue(l.at), 22, easeInOut);
          if (p <= 0) return null;
          const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 + (l.sag ?? 120);
          const d = `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
          return (
            <g key={i}>
              <path d={d} pathLength={1} strokeDasharray={`${p} 1`} fill="none" stroke="rgba(0,0,0,.55)" strokeWidth={9} transform="translate(5 9)" />
              <path d={d} pathLength={1} strokeDasharray={`${p} 1`} fill="none" stroke={RED} strokeWidth={7} strokeLinecap="round" />
            </g>
          );
        })}
      </svg>
      {links.flatMap((l, i) => {
        const a = end(byId[l.from], l.fs ?? 'bottom'), b = end(byId[l.to], l.ts ?? 'top'), s = cue(l.at);
        return [<Pin key={'a' + i} x={a.x} y={a.y} p={prog(frame, s - 2, 5)} />, <Pin key={'b' + i} x={b.x} y={b.y} p={prog(frame, s + 18, 5)} />];
      })}
    </div>
  );
};
