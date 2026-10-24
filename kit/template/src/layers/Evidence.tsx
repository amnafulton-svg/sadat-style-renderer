// House evidence layers (vendored from archive-remotion-factory/renderer): the documentary map (NASA terrain,
// 3D tilt) and the document card (real scan on graph paper, the quote marked on its word).
// Also the data chart (real figures as a line / bars, each landing on its spoken word).
// All take narration seconds, like every other layer here, and convert to the scene's local timing.
import React from 'react';
import {nf} from '../lib/core';
import {useScene} from '../lib/scene';
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

/** the house data chart (DataChart.tsx); appear / until / reveal / markers / callouts / row times in narration seconds */
export const Chart: React.FC<{chart: ArchiveChart}> = ({chart}) => {
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
