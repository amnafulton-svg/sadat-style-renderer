// House evidence layers (vendored from archive-remotion-factory/renderer): the documentary map (NASA terrain,
// 3D tilt) and the document card (real scan on graph paper, the quote marked on its word).
// Also the data chart (real figures as a line / bars, each landing on its spoken word).
// All take narration seconds, like every other layer here, and convert to the scene's local timing.
import React from 'react';
import {C, FONT, nf, prog} from '../lib/core';
import {useCue, useScene} from '../lib/scene';
import {ConcreteWall} from './Backgrounds';
import {DocumentaryMap} from '../vendor/DocumentaryMap';
import {DocumentCard} from '../vendor/DocumentCard';
import {DataChart} from '../vendor/DataChart';
import type {ArchiveChart, ArchiveScene, HistoricalMapSpec} from '../vendor/types';

/** map spec with every appearAt / startAt / endAt in narration seconds (the vendored map wants 0-1 fractions) */
export const DocMap: React.FC<{spec: HistoricalMapSpec; id: number}> = ({spec, id}) => {
  const {frame, startFrame, durFrames} = useScene();
  const fr = (s?: number) => (s === undefined ? undefined : Math.max(0, Math.min(1, (nf(s) - startFrame) / durFrames)));
  const local: HistoricalMapSpec = {
    ...spec,
    style: 'documentary',
    places: spec.places?.map((p) => ({...p, appearAt: fr(p.appearAt)})),
    territories: spec.territories?.map((t) => ({...t, appearAt: fr(t.appearAt)})),
    regions: spec.regions?.map((r) => ({...r, appearAt: fr(r.appearAt)})),
    routes: spec.routes?.map((r) => ({...r, startAt: fr(r.startAt), endAt: fr(r.endAt)})),
  };
  const scene = {index: id} as unknown as ArchiveScene;
  return <DocumentaryMap scene={scene} spec={local} frame={frame} durationInFrames={durFrames} holdStart holdEnd />;
};

type Rect = [number, number, number, number];
// HOUSE (Chipyong-ni review 2026-10-25): guessed boxes sat beside or across the printed words. A mark's `lines` come
// from tools/docmark.py (OCR of the scan: one rect per printed line); tools/validate.py errors on a mark that does not
// sit on printed lines. `box` (one rect) is still read, and checked the same way.
type Mark = {lines?: Rect[]; box?: Rect; at: number; until?: number; style?: 'highlight' | 'underline' | 'circle'};

/** a real scan; `at` and each mark's at/until in narration seconds; rects as [x0, y0, x1, y1] fractions of the scan */
export const DocCard: React.FC<{photo: string; aspect: number; at: number; source: string; marks: Mark[]}> = ({photo, aspect, at, source, marks}) => {
  const {frame, startFrame, durFrames} = useScene();
  const rel = (s: number) => (nf(s) - startFrame) / 25;
  return (
    <DocumentCard
      seed={photo}
      frame={frame}
      durationInFrames={durFrames}
      doc={{
        photo: `docs/${photo}`,
        aspect,
        at: rel(at),
        source,
        marks: marks.map((m) => ({
          rects: (m.lines ?? (m.box ? [m.box] : [])).map((b) => [b[0], b[1], b[2] - b[0], b[3] - b[1]] as Rect),
          at: rel(m.at),
          until: m.until === undefined ? undefined : rel(m.until),
          style: m.style ?? 'highlight',
        })),
      }}
    />
  );
};

/** two or three figures to compare: each number fills the frame and counts up onto its spoken word, a bar to scale
 *  under it (producer, Pacific 5:26 2026-11-10: two thin bars in a mostly empty chart; the big numbers were the pick).
 *  Chart switches to this by itself for bars/columns of 2-3 plain rows. */
const BigNumbers: React.FC<{chart: ArchiveChart}> = ({chart}) => {
  const cue = useCue();
  const {frame} = useScene();
  const rows = chart.rows ?? [];
  const n = rows.length;
  const max = Math.max(...rows.map((r) => Math.abs(r.amount)), 1e-9);
  const cream = '#f2ead8';
  const flagged = rows.some((r) => r.highlight);
  const tone = (i: number) => (flagged ? (rows[i].highlight ? '#d2362f' : cream) : [cream, '#d2362f', '#b9b1a0'][i]);
  const f = chart.format ?? {};
  const show = (v: number) =>
    `${f.prefix ?? ''}${v.toLocaleString('en-US', {minimumFractionDigits: f.decimals ?? 0, maximumFractionDigits: f.decimals ?? 0})}${f.suffix ?? ''}`;
  const pitch = 830 / n;
  const base = n === 2 ? 300 : 190;
  return (
    <ConcreteWall dim={0.55}>
      <div style={{position: 'absolute', left: 120, top: 64, zIndex: 40}}>
        {chart.kicker && <div style={{fontFamily: FONT.cond, fontSize: 30, letterSpacing: 6, color: C.red}}>{chart.kicker.toUpperCase()}</div>}
        <div style={{fontFamily: FONT.cond, fontSize: 58, letterSpacing: 3, color: cream, marginTop: 4}}>{chart.title.toUpperCase()}</div>
      </div>
      {chart.source && (
        <div style={{position: 'absolute', right: 120, top: 76, maxWidth: 520, textAlign: 'right', fontFamily: FONT.cond, fontSize: 24, letterSpacing: 3, color: cream, opacity: 0.55, zIndex: 40}}>
          SOURCE: {chart.source}
        </div>
      )}
      {rows.map((r, i) => {
        const p = prog(frame, cue(r.at) - 8, 14);
        const end = r.text ?? show(r.amount);
        const txt = p >= 1 ? end : show(r.amount * p);
        const size = Math.min(base, 1050 / (Math.max(end.length, 3) * 0.5));
        return (
          <div key={i} style={{position: 'absolute', left: 120, right: 120, top: 215 + i * pitch, opacity: prog(frame, cue(r.at) - 8, 4), zIndex: 40}}>
            <div style={{display: 'flex', alignItems: 'baseline', gap: 44}}>
              <div style={{fontFamily: FONT.didone, fontWeight: 700, fontSize: size, lineHeight: 1, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1', color: tone(i), letterSpacing: -size / 50, whiteSpace: 'nowrap', textShadow: '0 8px 40px rgba(0,0,0,.8)'}}>{txt}</div>
              <div style={{fontFamily: FONT.cond, fontSize: n === 2 ? 62 : 48, lineHeight: 1.1, letterSpacing: 5, color: cream}}>
                {r.label.toUpperCase()}
                {r.sub && <div style={{fontSize: n === 2 ? 34 : 28, letterSpacing: 3, opacity: 0.65, marginTop: 6}}>{r.sub}</div>}
              </div>
            </div>
            <div style={{height: n === 2 ? 34 : 24, marginTop: n === 2 ? 22 : 14, width: `${Math.max(0.6, (Math.abs(r.amount) / max) * 100 * p)}%`, background: tone(i), boxShadow: '0 6px 20px rgba(0,0,0,.6)'}} />
          </div>
        );
      })}
    </ConcreteWall>
  );
};

/** the house data chart (DataChart.tsx); appear / until / reveal / markers / callouts / row times in narration seconds */
const PlainChart: React.FC<{chart: ArchiveChart}> = ({chart}) => {
  const {frame, startFrame, durFrames} = useScene();
  const rel = (s: number) => (nf(s) - startFrame) / 25;
  const opt = (s?: number) => (s === undefined ? undefined : rel(s));
  const local: ArchiveChart = {
    ...chart,
    appear: opt(chart.appear),
    until: opt(chart.until),
    reveal: chart.reveal?.map((r) => ({...r, at: rel(r.at)})),
    markers: chart.markers?.map((m) => ({...m, at: opt(m.at)})),
    callouts: chart.callouts?.map((c) => ({...c, at: rel(c.at)})),
    rows: chart.rows?.map((r) => ({...r, at: rel(r.at), steps: r.steps?.map((st) => ({...st, at: rel(st.at)}))})),
    badge: chart.badge && {...chart.badge, at: rel(chart.badge.at)},
  };
  return <DataChart chart={local} frame={frame} durationInFrames={durFrames} />;
};

export const Chart: React.FC<{chart: ArchiveChart}> = ({chart}) => {
  const rows = chart.rows ?? [];
  const big = chart.type !== 'line' && (rows.length === 2 || rows.length === 3) && !rows.some((r) => r.steps?.length || r.segments?.length) && !chart.badge;
  return big ? <BigNumbers chart={chart} /> : <PlainChart chart={chart} />;
};
