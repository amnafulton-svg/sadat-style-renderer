// Documentary data charts: line / column / bar graphics. Every element is timed to its spoken word: `at` values are
// seconds from the scene start (the Chart layer converts narration seconds), and an element finishes arriving on its
// word, then holds until the scene ends, so data never flashes past or lingers.
//
// Three designs, one per video in turn (producer 2026-11-19: "for a video it uses A, the other B, the 3rd C"):
//   A editorial: dark field, Playfair serif titles and numbers, slim bars, red rule under the title
//   B graph paper: cream paper with a blue grid, typewriter labels, handwritten numbers, ink axes
//   C bold: concrete wall, huge Bebas titles and numbers, thick blocks with the name and number inside
// The video's design is src/lib/chartlook.json ({"look": "A"|"B"|"C"}), written by new_chat.py / new_video.py in turn;
// `chart.look` overrides it for one chart.
import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import type {ArchiveChart, ChartFormat} from './types';
import {ACCENT, ON_ACCENT} from './Palette';
import {FONT as KF, OnPaper} from '../lib/core';
import videoLook from '../lib/chartlook.json';

type LookId = 'A' | 'B' | 'C';
const RED = ACCENT;
const CREAM = '#f4efe4';
const INK = '#1f1b16';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const easeOut = {...clamp, easing: Easing.out(Easing.cubic)};
const easeInOut = {...clamp, easing: Easing.inOut(Easing.cubic)};

// plot box: clear of the title above and the source line at the bottom
const PLOT = {left: 250, right: 1680, top: 330, bottom: 820};
const GROW = 0.9; // seconds an element takes to arrive; it lands on its word

type Skin = {
  id: LookId;
  ink: string; // main text
  soft: string; // secondary text (axis numbers, quiet labels)
  bar: string; // a bar that is not highlighted
  grid: string; // horizontal value lines (none on B: the paper has its own grid)
  axis: string;
  axisW: number;
  yAxis: boolean; // B draws the vertical axis too, like a chart drawn on graph paper
  area: number; // opacity of the fill under the main line (0 = none)
  lineW: number;
  label: CSSProperties; // row / column names
  upper: boolean; // names in capitals
  value: CSSProperties; // the numbers next to bars and columns
  valueK: number; // value width per character, as a share of its font size
  tick: CSSProperties; // axis numbers and years
  small: CSSProperties; // marker texts, series names, segment names
};

const SKINS: Record<LookId, Skin> = {
  A: {
    id: 'A', ink: CREAM, soft: 'rgba(244,239,228,0.6)', bar: 'rgba(244,239,228,0.3)', grid: 'rgba(244,239,228,0.13)',
    axis: 'rgba(244,239,228,0.5)', axisW: 2, yAxis: false, area: 0.28, lineW: 7, upper: true,
    label: {fontFamily: KF.cond, fontWeight: 700, fontSize: 32, letterSpacing: 3},
    value: {fontFamily: KF.didone, fontWeight: 700, fontSize: 60, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'},
    valueK: 0.62,
    tick: {fontFamily: KF.cond, fontWeight: 700, fontSize: 28, letterSpacing: 2},
    small: {fontFamily: KF.cond, fontWeight: 700, fontSize: 26, letterSpacing: 4},
  },
  B: {
    id: 'B', ink: INK, soft: 'rgba(31,27,22,0.75)', bar: 'rgba(31,27,22,0.82)', grid: 'rgba(0,0,0,0)',
    axis: INK, axisW: 3, yAxis: true, area: 0, lineW: 9, upper: false,
    label: {fontFamily: KF.type, fontSize: 34},
    value: {fontFamily: KF.hand, fontWeight: 700, fontSize: 56},
    valueK: 0.56,
    tick: {fontFamily: KF.type, fontSize: 30},
    small: {fontFamily: KF.hand, fontWeight: 700, fontSize: 36},
  },
  C: {
    id: 'C', ink: CREAM, soft: 'rgba(244,239,228,0.7)', bar: 'rgba(244,239,228,0.14)', grid: 'rgba(0,0,0,0)',
    axis: 'rgba(244,239,228,0.35)', axisW: 2, yAxis: false, area: 0.22, lineW: 10, upper: true,
    label: {fontFamily: KF.cond, fontWeight: 700, fontSize: 30, letterSpacing: 4},
    value: {fontFamily: KF.title, fontSize: 76},
    valueK: 0.45,
    tick: {fontFamily: KF.title, fontSize: 48},
    small: {fontFamily: KF.cond, fontWeight: 700, fontSize: 26, letterSpacing: 4},
  },
};

const pickLook = (chart: ArchiveChart): LookId => {
  const l = String(chart.look ?? (videoLook as {look?: string}).look ?? 'A').toUpperCase();
  return l === 'B' || l === 'C' ? l : 'A';
};
const SkinCtx = React.createContext<Skin>(SKINS.A);
const useSkin = () => React.useContext(SkinCtx);
const cap = (s: Skin, text: string) => (s.upper ? text.toUpperCase() : text);

export const fmt = (n: number, f: ChartFormat = {}, decimals = f.decimals ?? 0) => {
  const fixed = Math.abs(n) >= 1000 && decimals === 0
    ? Math.round(n).toLocaleString('en-US')
    : n.toFixed(decimals);
  return `${f.prefix ?? ''}${fixed}${f.suffix ?? ''}`;
};

// 0 → 1 as an element arrives so that it lands at `at`
const arrive = (t: number, at: number, dur = GROW) => interpolate(t, [at - dur, at], [0, 1], easeOut);
// a name never clips: a longer name than its column shrinks to fit (Alaska 2026-10-23)
const fitSize = (text: string, width: number, size: number, perChar: number) =>
  Math.max(18, Math.min(size, width / Math.max(1, text.length * perChar)));

// ---------------------------------------------------------------- backdrops
const Grain = ({o}: {o: number}) => (
  <AbsoluteFill style={{backgroundImage: `url(${staticFile('textures/grain_3.png')})`, mixBlendMode: 'overlay', opacity: o}} />
);
const Vignette = ({s}: {s: number}) => (
  <AbsoluteFill style={{background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 45%, rgba(0,0,0,${s}) 100%)`}} />
);
const PAPER_GRID = 'linear-gradient(rgba(70,110,150,.16) 1px, transparent 1px), linear-gradient(90deg, rgba(70,110,150,.16) 1px, transparent 1px), linear-gradient(rgba(70,110,150,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(70,110,150,.07) 1px, transparent 1px)';

export const ChartBackdrop = ({look = 'A'}: {look?: LookId; frame?: number}) => {
  if (look === 'B') return (
    <AbsoluteFill style={{backgroundColor: '#ece6d8'}}>
      <Img src={staticFile('textures/paper.jpg')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85}} />
      <AbsoluteFill style={{backgroundImage: PAPER_GRID, backgroundSize: '120px 120px, 120px 120px, 24px 24px, 24px 24px'}} />
      <Vignette s={0.35} />
    </AbsoluteFill>
  );
  if (look === 'C') return (
    <AbsoluteFill style={{backgroundColor: '#111'}}>
      <Img src={staticFile('textures/concrete.jpg')} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(.45) saturate(.4)'}} />
      <Grain o={0.4} />
      <Vignette s={0.7} />
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 90% 80% at 40% 35%, #2a2622 0%, #141210 60%, #090807 100%)'}}>
      <Grain o={0.5} />
      <Vignette s={0.55} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- title block
const Header = ({chart, t}: {chart: ArchiveChart; t: number}) => {
  const s = useSkin();
  const a = chart.appear ?? 0;
  const o = interpolate(t, [a, a + 0.7], [0, 1], easeOut);
  const source = chart.source ? (
    <div style={{position: 'absolute', right: 150, bottom: 62, maxWidth: 900, textAlign: 'right', opacity: o * (s.id === 'B' ? 0.65 : 0.55),
      ...(s.id === 'B' ? {fontFamily: KF.type, fontSize: 22, color: INK} : {fontFamily: KF.cond, fontWeight: 700, fontSize: 22, letterSpacing: 4, color: CREAM})}}>
      {s.id === 'B' ? `Source: ${chart.source}` : `SOURCE: ${chart.source.toUpperCase()}`}
    </div>
  ) : null;
  if (s.id === 'C') {
    const title = chart.title.toUpperCase();
    const size = Math.min(118, 1560 / Math.max(1, title.length * 0.42));
    return (
      <>
        <div style={{position: 'absolute', left: 150, top: 80, right: 150, display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', columnGap: 28, rowGap: 8, opacity: o, transform: `translateX(${(1 - o) * -40}px)`}}>
          <div style={{fontFamily: KF.title, fontSize: size, lineHeight: 0.9, color: CREAM}}>{title}</div>
          {chart.kicker ? (
            <div style={{fontFamily: KF.cond, fontWeight: 700, fontSize: 24, letterSpacing: 5, color: ON_ACCENT, background: RED, padding: '6px 14px', marginBottom: size * 0.12, whiteSpace: 'nowrap'}}>{chart.kicker.toUpperCase()}</div>
          ) : null}
        </div>
        {source}
      </>
    );
  }
  const size = Math.min(76, 1560 / Math.max(1, chart.title.length * 0.5));
  return (
    <>
      <div style={{position: 'absolute', left: 150, top: 88, opacity: o, transform: `translateY(${(1 - o) * 20}px)`}}>
        <div style={s.id === 'B'
          ? {fontFamily: KF.type, fontSize: 28, letterSpacing: 3, color: RED}
          : {fontFamily: KF.cond, fontWeight: 700, fontSize: 26, letterSpacing: 7, color: RED}}>
          {(chart.kicker ?? 'BY THE NUMBERS').toUpperCase()}
        </div>
        <div style={{fontFamily: KF.didone, fontWeight: 900, fontSize: size, lineHeight: 1.05, color: s.ink, marginTop: 6, maxWidth: 1600}}>{chart.title}</div>
        {s.id === 'A' ? <div style={{width: 120 * o, height: 5, background: RED, marginTop: 20}} /> : null}
      </div>
      {source}
    </>
  );
};

// ---------------------------------------------------------------- line chart
const LineChart = ({chart, t}: {chart: ArchiveChart; t: number}) => {
  const s = useSkin();
  const series = chart.series ?? [];
  const allX = series.flatMap((v) => v.points.map((p) => p[0]));
  const allY = series.flatMap((v) => v.points.map((p) => p[1]));
  const [x0, x1] = chart.x ?? [Math.min(...allX), Math.max(...allX)];
  const [y0, y1] = chart.y ?? [0, Math.max(...allY) * 1.12];
  const right = s.id === 'C' ? PLOT.right - 120 : PLOT.right; // C's big end number needs room at the right
  const W = right - PLOT.left;
  const H = PLOT.bottom - PLOT.top;
  const sx = (x: number) => PLOT.left + ((x - x0) / (x1 - x0)) * W;
  const sy = (y: number) => PLOT.bottom - ((y - y0) / (y1 - y0)) * H;
  const a = chart.appear ?? 0;

  // the line's leading edge reaches each reveal x exactly when its word is spoken
  const reveal = chart.reveal?.length ? chart.reveal : [{x: x1, at: a + 3}];
  const firstAt = reveal[0].at;
  const startAt = Math.max(a + 0.5, firstAt - Math.min(2.4, Math.max(0.8, firstAt - a - 0.5)));
  const times = [startAt, ...reveal.map((r) => r.at)];
  const xs = [x0, ...reveal.map((r) => r.x)];
  for (let i = 1; i < times.length; i++) times[i] = Math.max(times[i], times[i - 1] + 0.05);
  let head = xs[0];
  for (let i = 0; i < times.length - 1; i++) {
    if (t >= times[i]) head = interpolate(t, [times[i], times[i + 1]], [xs[i], xs[i + 1]], easeInOut);
  }
  if (t >= times[times.length - 1]) head = xs[xs.length - 1];
  const moving = t > startAt && t < times[times.length - 1] + 0.6;

  const yAt = (pts: [number, number][], x: number) => {
    if (x <= pts[0][0]) return pts[0][1];
    for (let i = 1; i < pts.length; i++) {
      if (x <= pts[i][0]) {
        const [ax, ay] = pts[i - 1];
        const [bx, by] = pts[i];
        return ay + ((x - ax) / (bx - ax)) * (by - ay);
      }
    }
    return pts[pts.length - 1][1];
  };
  const drawn = (pts: [number, number][]) => {
    const kept = pts.filter((p) => p[0] < head).map((p) => [sx(p[0]), sy(p[1])]);
    kept.push([sx(head), sy(yAt(pts, head))]);
    return kept;
  };

  const axisIn = interpolate(t, [a + 0.2, a + 1.0], [0, 1], easeOut);
  const yTicks = chart.yTicks ?? [0.25, 0.5, 0.75, 1].map((g) => y0 + (y1 - y0) * g);
  const xTicks = chart.xTicks ?? [x0, x1];
  const axisFmt = {...chart.format, decimals: chart.format?.axisDecimals ?? 0};
  const tickFill = {...s.tick, fill: s.soft} as CSSProperties;
  const yTickStyle = s.id === 'C' ? {...tickFill, fontFamily: KF.cond, fontWeight: 700, fontSize: 26, letterSpacing: 2} : tickFill;
  const mainColor = (c?: string) => (c === 'cream' ? (s.id === 'B' ? INK : CREAM) : RED);

  return (
    <AbsoluteFill>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="chartArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={RED} stopOpacity={s.area} />
            <stop offset="100%" stopColor={RED} stopOpacity={0} />
          </linearGradient>
        </defs>
        {yTicks.map((v) => (
          <g key={v} opacity={axisIn}>
            <line x1={PLOT.left} x2={PLOT.left + W * axisIn} y1={sy(v)} y2={sy(v)} stroke={s.grid} strokeWidth={1} />
            <text x={PLOT.left - 22} y={sy(v) + 10} textAnchor="end" style={yTickStyle}>{fmt(v, axisFmt)}</text>
          </g>
        ))}
        {s.id === 'C' ? xTicks.map((x) => (
          <line key={`g${x}`} opacity={axisIn} x1={sx(x)} x2={sx(x)} y1={PLOT.top} y2={PLOT.bottom} stroke="rgba(244,239,228,.16)" strokeDasharray="4 10" strokeWidth={2} />
        )) : null}
        <line x1={PLOT.left} x2={PLOT.left + W * axisIn} y1={PLOT.bottom} y2={PLOT.bottom} stroke={s.axis} strokeWidth={s.axisW} />
        {s.yAxis ? <line x1={PLOT.left} x2={PLOT.left} y1={PLOT.bottom} y2={PLOT.bottom - (H + 20) * axisIn} stroke={s.axis} strokeWidth={s.axisW} /> : null}
        {xTicks.map((x) => (
          <text key={x} x={sx(x)} y={PLOT.bottom + (s.id === 'C' ? 56 : 46)} textAnchor="middle" opacity={axisIn} style={tickFill}>{x}</text>
        ))}
        {(chart.markers ?? []).map((m) => {
          const on = interpolate(t, [(m.at ?? 0) - 0.5, m.at ?? 0], [0, 1], easeOut) * (m.at === undefined ? (head >= m.x ? 1 : 0) : 1);
          return (
            <g key={m.label} opacity={on}>
              <line x1={sx(m.x)} x2={sx(m.x)} y1={PLOT.bottom} y2={PLOT.bottom - (H + 10) * on} stroke={s.ink} strokeOpacity={0.55} strokeWidth={2} strokeDasharray="8 8" />
              <text x={sx(m.x) + 14} y={PLOT.top + 20} style={{...s.small, fill: s.ink} as CSSProperties}>{cap(s, m.label)}</text>
            </g>
          );
        })}
        {series.map((v, si) => {
          const pts = drawn(v.points);
          const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
          const color = mainColor(v.color);
          const primary = si === 0;
          // the line name sits right of its end, but a line ending near the plot's right edge has no room: then it
          // goes right-aligned under the end dot, below the line over its whole width (1926 video 2026-11-01)
          const end = pts[pts.length - 1];
          const name = v.label ? cap(s, v.label) : '';
          const nameW = name.length * (s.id === 'B' ? 18 : 20);
          const inside = sx(v.points[v.points.length - 1][0]) + 18 + nameW > 1880;
          let nameY = end[1] + (primary ? 44 : 30);
          if (inside) {
            for (let x = end[0] - nameW; x < end[0]; x += 20) {
              const k = pts.findIndex((p) => p[0] >= x);
              if (k > 0) nameY = Math.max(nameY, pts[k - 1][1] + ((x - pts[k - 1][0]) / (pts[k][0] - pts[k - 1][0] || 1)) * (pts[k][1] - pts[k - 1][1]) + 40);
            }
            nameY = Math.min(nameY, PLOT.bottom - 12);
          }
          const r = s.id === 'C' ? 15 : s.id === 'A' ? 12 : 9;
          return (
            <g key={si}>
              {primary && s.area > 0 ? <path d={`${d} L${end[0]},${PLOT.bottom} L${pts[0][0]},${PLOT.bottom} Z`} fill="url(#chartArea)" /> : null}
              <path d={d} stroke={color} strokeWidth={primary ? s.lineW : s.lineW * 0.6} fill="none" strokeLinejoin="round" strokeLinecap="round" opacity={primary ? (s.id === 'B' ? 0.9 : 1) : 0.8} />
              {t > startAt ? <circle cx={pts[0][0]} cy={pts[0][1]} r={primary ? r * 0.8 : r * 0.55} fill={s.id === 'B' ? INK : CREAM} /> : null}
              {t > startAt ? (
                <circle cx={end[0]} cy={end[1]} r={primary ? r : r * 0.65} fill={color} stroke={s.id === 'B' ? 'none' : CREAM} strokeWidth={s.id === 'B' ? 0 : primary ? 4 : 2} />
              ) : null}
              {name && t > startAt ? (
                <text x={inside ? end[0] : end[0] + 18} y={nameY} textAnchor={inside ? 'end' : 'start'} style={{...s.small, fill: color} as CSSProperties}>{name}</text>
              ) : null}
            </g>
          );
        })}
      </svg>
      {/* running value at the line head while it draws */}
      {series[0] && moving && chart.runningTag !== false && !(chart.callouts ?? []).some((c) => t >= c.at - 0.2 && Math.abs(c.x - head) < (x1 - x0) * 0.04) ? (
        <RunningTag
          x={sx(head)}
          y={sy(yAt(series[0].points, head))}
          text={fmt(yAt(series[0].points, head), chart.format)}
          opacity={interpolate(t, [startAt, startAt + 0.3], [0, 1], clamp)}
        />
      ) : null}
      {(chart.callouts ?? []).map((c, i, all) => {
        const v = series[c.series ?? 0];
        const y = c.y ?? yAt(v.points, c.x);
        const on = arrive(t, c.at, 0.5);
        return <Callout key={i} x={sx(c.x)} y={sy(y)} text={c.text ?? fmt(y, chart.format)} opacity={on} below={c.below} last={i > 0 && i === all.length - 1} />;
      })}
    </AbsoluteFill>
  );
};

// the small number that rides the line head while it draws
const RunningTag = ({x, y, text, opacity}: {x: number; y: number; text: string; opacity: number}) => {
  const s = useSkin();
  const style: CSSProperties = s.id === 'B'
    ? {fontFamily: KF.hand, fontWeight: 700, fontSize: 40, color: INK}
    : s.id === 'C'
      ? {fontFamily: KF.title, fontSize: 56, color: CREAM, textShadow: '0 4px 18px rgba(0,0,0,.8)'}
      : {fontFamily: KF.cond, fontWeight: 700, fontSize: 32, letterSpacing: 2, color: CREAM, textShadow: '0 4px 18px rgba(0,0,0,.8)'};
  return (
    <div style={{position: 'absolute', left: Math.min(x, PLOT.right + 40), top: y - (s.id === 'C' ? 84 : 66), transform: 'translateX(-50%)', opacity, whiteSpace: 'nowrap', lineHeight: 1, fontVariantNumeric: 'tabular-nums', ...style}}>
      {text}
    </div>
  );
};

// a callout on the line: A = serif number on a short leader, B = handwritten note with a pen arrow, C = huge Bebas number
const Callout = ({x, y, text, opacity, below, last}: {x: number; y: number; text: string; opacity: number; below?: boolean; last?: boolean}) => {
  const s = useSkin();
  const lift = (1 - opacity) * 12;
  if (s.id === 'B') {
    // the note sits up and to the right of its point (to the left near the right edge), a curved arrow down to it
    const flip = x > 1380;
    const dir = below ? 1 : -1;
    const nx = flip ? x - 70 : x + 70;
    const ny = y + dir * 110;
    const tipX = x + (flip ? -8 : 8);
    const tipY = y + dir * 22;
    return (
      <>
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity}}>
          <path d={`M${nx},${ny - dir * 6} Q${flip ? x - 20 : x + 20},${ny - dir * 10} ${tipX},${tipY}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <path d={`M${tipX - 10},${tipY + dir * 18} L${tipX},${tipY} L${tipX + (flip ? -20 : 20)},${tipY + dir * 12}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div style={{position: 'absolute', left: nx + (flip ? -12 : 12), top: ny - 40 + lift, transform: flip ? 'translateX(-100%)' : undefined, opacity, fontFamily: KF.hand, fontWeight: 700, fontSize: 58, lineHeight: 1, color: last ? RED : INK, whiteSpace: 'nowrap'}}>{text}</div>
      </>
    );
  }
  const big = s.id === 'C';
  const size = big ? (last ? 130 : 104) : 72;
  const top = below ? y + 36 : y - size - 34;
  // near the plot's edges the number grows inward, so it never runs off the frame or over the y ticks
  const anchor = x < PLOT.left + 260 ? 'left' : x > PLOT.right - 300 ? 'right' : 'centre';
  return (
    <>
      {!big ? (
        <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity}}>
          <line x1={x} x2={x} y1={below ? y + 18 : y - 18} y2={below ? y + 34 : y - 34} stroke={last ? RED : CREAM} strokeWidth={2} />
        </svg>
      ) : null}
      <div style={{position: 'absolute', left: anchor === 'left' ? x + 8 : anchor === 'right' ? x + 24 : x, top: top + lift,
        transform: anchor === 'left' ? undefined : anchor === 'right' ? 'translateX(-100%)' : 'translateX(-50%)', opacity, whiteSpace: 'nowrap', lineHeight: 1, color: last ? RED : CREAM,
        textShadow: '0 6px 26px rgba(0,0,0,.75)',
        ...(big ? {fontFamily: KF.title, fontSize: size} : {fontFamily: KF.didone, fontWeight: 700, fontSize: size, fontVariantNumeric: 'lining-nums', fontFeatureSettings: '"lnum" 1'})}}>
        {text}
      </div>
    </>
  );
};

// ---------------------------------------------------------------- columns (vertical bars, each on its word)
const ColumnChart = ({chart, t}: {chart: ArchiveChart; t: number}) => {
  const s = useSkin();
  const rows = chart.rows ?? [];
  const max = chart.max ?? Math.max(...rows.flatMap((r) => [r.amount, ...(r.steps ?? []).map((st) => st.amount)])) * 1.08;
  const top = PLOT.top + 40;
  const base = PLOT.bottom - 50;
  const W = PLOT.right - PLOT.left;
  const H = base - top;
  const slot = W / rows.length;
  const barW = Math.min(s.id === 'C' ? 220 : 170, slot * (s.id === 'C' ? 0.7 : 0.56));
  const a = chart.appear ?? 0;
  const axisIn = interpolate(t, [a + 0.2, a + 1.0], [0, 1], easeOut);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: PLOT.left, top: base, width: W * axisIn, height: s.axisW, backgroundColor: s.axis}} />
      {rows.map((r, i) => {
        const {amount, text, grow} = rowValue(r, t, chart.format);
        const h = (amount / max) * H * grow;
        const cx = PLOT.left + slot * (i + 0.5);
        const hl = r.highlight ?? i === rows.length - 1;
        const vSize = fitSize(text, slot - 16, Number(s.value.fontSize), s.valueK);
        const label = cap(s, r.label);
        return (
          <div key={i}>
            <div style={{position: 'absolute', left: cx - barW / 2, top: base - h, width: barW, height: h, background: hl ? RED : s.bar, boxSizing: 'border-box',
              borderTop: s.id === 'C' && h > 8 ? `8px solid ${hl ? CREAM : 'rgba(244,239,228,.5)'}` : undefined}} />
            <div style={{...s.value, position: 'absolute', transform: 'translateX(-50%)', left: cx, top: base - h - vSize * 1.2 - 6, opacity: grow, whiteSpace: 'nowrap', lineHeight: 1.2,
              fontSize: vSize, color: hl ? RED : s.ink}}>{text}</div>
            <div style={{...s.label, position: 'absolute', transform: 'translateX(-50%)', left: cx, top: base + 16, textAlign: 'center', whiteSpace: 'nowrap', color: s.ink,
              opacity: interpolate(grow, [0, 0.3], [0, 1], clamp), fontSize: fitSize(label, slot - 12, Math.min(30, Number(s.label.fontSize)), 0.7)}}>
              {label}
              {r.sub ? <div style={{fontSize: 21, letterSpacing: 1, color: s.soft, marginTop: 4}}>{r.sub}</div> : null}
            </div>
          </div>
        );
      })}
      <Badge chart={chart} t={t} left={PLOT.left} top={PLOT.top - 30} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- bars (horizontal, each row on its word)
const BarChart = ({chart, t}: {chart: ArchiveChart; t: number}) => {
  const s = useSkin();
  const rows = chart.rows ?? [];
  const max = chart.max ?? Math.max(...rows.flatMap((r) => [r.amount, ...(r.steps ?? []).map((st) => st.amount), r.segments ? r.segments.reduce((sum, g) => sum + g.amount, 0) : 0])) * 1.04;
  const rowH = Math.min(118, (PLOT.bottom - PLOT.top + 60) / rows.length);
  if (s.id === 'C' && !rows.some((r) => r.segments?.length)) return <BlockBars chart={chart} t={t} max={max} rowH={rowH} />;
  const labelSize = Number(s.label.fontSize);
  const perChar = s.id === 'B' ? 0.6 : 0.62 + Number(s.label.letterSpacing ?? 0) / labelSize;
  // the name column widens for long names instead of clipping them (Zulu 2026-10-23), up to 700 px
  const LABEL = chart.labelWidth ?? Math.min(700, Math.max(360, ...rows.map((r) => (r.label ?? '').length * labelSize * perChar + 40)));
  // the value rides the bar end: reserve room for the longest value text so it ends by x 1810
  const vSize = Number(s.value.fontSize);
  const longest = Math.max(fmt(max, chart.format).length, ...rows.flatMap((r) => [r.text, ...(r.steps ?? []).map((st) => st.text)]).map((v) => (v ?? '').length));
  const TRACK = Math.max(300, Math.min(1000, 1600 - LABEL - 160, 1640 - LABEL - 26 - longest * vSize * s.valueK));
  const barH = Math.min(s.id === 'B' ? 46 : 44, rowH * 0.5);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 150, top: PLOT.top - 20, width: 1640}}>
        {rows.map((r, i) => {
          const hl = r.highlight ?? i === rows.length - 1;
          const {amount, text, grow} = rowValue(r, t, chart.format);
          const labelIn = arrive(t, r.at - 0.4, 0.5); // the name is in place before the bar finishes growing
          const label = cap(s, r.label ?? '');
          const barW = r.segments ? r.segments.reduce((w, g) => w + (g.amount / max) * TRACK * arrive(t, g.at), 0) : Math.max(grow > 0 ? 6 : 0, (amount / max) * TRACK * grow);
          return (
            <div key={i} style={{position: 'relative', display: 'flex', alignItems: 'center', height: rowH}}>
              <div style={{width: LABEL, flexShrink: 0, overflow: 'hidden'}}>
                <div style={{...s.label, whiteSpace: 'nowrap', fontSize: fitSize(label, LABEL - 30, labelSize, perChar), color: hl || s.id === 'B' ? s.ink : s.soft, transform: `translateY(${(1 - labelIn) * 105}%)`}}>{label}</div>
              </div>
              {s.id === 'A' ? <div style={{position: 'absolute', left: LABEL, right: 0, top: rowH / 2 + barH / 2 + 8, height: 1, background: 'rgba(244,239,228,.12)', opacity: labelIn}} /> : null}
              <div style={{position: 'relative', width: TRACK, height: barH, flexShrink: 0}}>
                {chart.track ? <div style={{position: 'absolute', inset: 0, backgroundColor: s.id === 'B' ? 'rgba(31,27,22,0.08)' : 'rgba(244,239,228,0.08)', opacity: labelIn}} /> : null}
                {r.segments ? (
                  <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, display: 'flex'}}>
                    {r.segments.map((g, k) => {
                      const gg = arrive(t, g.at);
                      const fill = s.id === 'B' ? (k % 2 ? 'rgba(31,27,22,0.55)' : 'rgba(31,27,22,0.82)') : (k % 2 ? 'rgba(244,239,228,0.25)' : 'rgba(244,239,228,0.42)');
                      return (
                        <div key={k} style={{position: 'relative', width: (g.amount / max) * TRACK * gg, height: '100%', backgroundColor: fill, borderRight: `2px solid ${s.id === 'B' ? '#ece6d8' : '#0e0d0b'}`}}>
                          <div style={{...s.small, position: 'absolute', left: 6, top: -34, whiteSpace: 'nowrap', color: s.ink, opacity: interpolate(gg, [0.6, 1], [0, 1], clamp), fontSize: s.id === 'B' ? 28 : 22}}>{cap(s, g.label)}</div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: barW, background: hl ? RED : s.bar, boxShadow: s.id === 'B' ? '0 3px 0 rgba(0,0,0,.08)' : 'none'}} />
                )}
              </div>
              <div style={{...s.value, position: 'absolute', left: LABEL + barW + 22, whiteSpace: 'nowrap', lineHeight: 1.2, color: hl ? RED : s.ink, opacity: grow}}>{text}</div>
            </div>
          );
        })}
      </div>
      <Badge chart={chart} t={t} left={150 + LABEL} top={PLOT.top - 20 + rows.length * rowH + 4} />
    </AbsoluteFill>
  );
};

// C: thick blocks with the name inside at the left and the number inside at the right; a short bar still holds both
const BlockBars = ({chart, t, max, rowH}: {chart: ArchiveChart; t: number; max: number; rowH: number}) => {
  const rows = chart.rows ?? [];
  const TRACK = 1620;
  const h = Math.min(84, rowH - 16);
  const nameSize = Math.min(30, h * 0.36);
  const numSize = Math.min(76, h * 0.9);
  const top = PLOT.top - 50;
  return (
    <AbsoluteFill>
      {rows.map((r, i) => {
        const hl = r.highlight ?? i === rows.length - 1;
        const {amount, text, grow} = rowValue(r, t, chart.format);
        const name = (r.label ?? '').toUpperCase();
        const need = name.length * nameSize * 0.8 + text.length * numSize * 0.45 + 110;
        const w = Math.min(TRACK, Math.max(need, (amount / max) * TRACK)) * grow;
        return (
          <div key={i} style={{position: 'absolute', left: 150, top: top + i * rowH, width: w, height: h, background: hl ? RED : 'rgba(244,239,228,.14)', overflow: 'hidden',
            opacity: Math.min(1, grow * 3), display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 26px', boxSizing: 'border-box',
            borderLeft: `8px solid ${hl ? CREAM : 'rgba(244,239,228,.5)'}`}}>
            <div style={{fontFamily: KF.cond, fontWeight: 700, fontSize: nameSize, letterSpacing: 4, color: CREAM, whiteSpace: 'nowrap'}}>{name}</div>
            <div style={{opacity: interpolate(grow, [0.7, 1], [0, 1], clamp), fontFamily: KF.title, fontSize: numSize, color: CREAM, marginLeft: 26, whiteSpace: 'nowrap', paddingTop: numSize * 0.08}}>{text}</div>
          </div>
        );
      })}
      <Badge chart={chart} t={t} left={150} top={top + rows.length * rowH + 4} />
    </AbsoluteFill>
  );
};

const Badge = ({chart, t, left, top}: {chart: ArchiveChart; t: number; left: number; top: number}) => {
  const s = useSkin();
  if (!chart.badge) return null;
  const on = arrive(t, chart.badge.at, 0.5);
  const font: CSSProperties = s.id === 'B' ? {fontFamily: KF.type, fontSize: 32} : s.id === 'C' ? {fontFamily: KF.title, fontSize: 52, padding: '8px 16px 2px'} : {fontFamily: KF.cond, fontWeight: 700, fontSize: 32, letterSpacing: 3};
  return (
    <div style={{position: 'absolute', left, top, opacity: on, transform: `translateY(${(1 - on) * 14}px)`, color: ON_ACCENT, backgroundColor: RED, padding: '6px 14px 5px', whiteSpace: 'nowrap', ...font}}>
      {chart.badge.text}
    </div>
  );
};

// a row's current amount: grows in on its word, then steps to each later value on that value's word
const rowValue = (r: NonNullable<ArchiveChart['rows']>[number], t: number, format?: ChartFormat) => {
  const grow = arrive(t, r.at);
  let amount = r.segments ? r.segments.reduce((sum, g) => sum + g.amount, 0) : r.amount;
  let shown = amount * grow;
  let text = r.text ?? fmt(shown, format);
  let prev = amount;
  for (const st of r.steps ?? []) {
    const p = arrive(t, st.at, 1.1);
    if (p <= 0) break;
    amount = prev + (st.amount - prev) * p;
    shown = amount;
    text = p >= 1 && st.text ? st.text : fmt(amount, format);
    prev = st.amount;
  }
  if (r.steps?.length) return {amount: shown / Math.max(grow, 1e-6), text, grow};
  // count up only when the row text is the number itself ("71%"); a worded text ("OVER $1 TRILLION") never shows a counting number
  if (r.text && grow < 1 && r.text.includes(fmt(amount, format))) text = fmt(shown, format);
  return {amount, text, grow};
};

export const DataChart = ({chart, frame, durationInFrames, backdrop = true}: {
  chart: ArchiveChart;
  frame: number;
  durationInFrames: number;
  // false when the scene frame under the chart already shows the same backdrop
  backdrop?: boolean;
}) => {
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const end = Math.min(durationInFrames / fps, chart.until ?? Infinity);
  if (t > end + 0.1) return null;
  const out = interpolate(t, [end - 0.45, end], [1, 0], clamp);
  const a = chart.appear ?? 0;
  const fieldIn = interpolate(t, [a - 0.1, a + 0.4], [0, 1], clamp);
  const skin = SKINS[pickLook(chart)];
  const body = chart.type === 'line' ? <LineChart chart={chart} t={t} /> : chart.type === 'columns' ? <ColumnChart chart={chart} t={t} /> : <BarChart chart={chart} t={t} />;
  const leave = chart.until !== undefined ? out : 1;
  // the backdrop is there from the scene's first frame; only the chart fades in on `appear` (Tax withholding 2026-10-24)
  return (
    <SkinCtx.Provider value={skin}>
      <OnPaper.Provider value={skin.id === 'B'}>
        <AbsoluteFill style={{pointerEvents: 'none', opacity: leave}}>
          {backdrop ? <ChartBackdrop look={skin.id} /> : null}
          <AbsoluteFill style={{opacity: fieldIn}}>
            <Header chart={chart} t={t} />
            {body}
          </AbsoluteFill>
        </AbsoluteFill>
      </OnPaper.Provider>
    </SkinCtx.Provider>
  );
};
