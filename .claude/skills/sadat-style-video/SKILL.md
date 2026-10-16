---
name: sadat-style-video
description: Make a Sadat-style documentary (archive film + evidence board + stamped type, Remotion) from the producer's script and voice-over, using the sadat-style-renderer kit. Use when asked to start, build, edit, check, preview or render a Sadat-style video.
---

# Sadat-style video: Claude is the editor

The producer gives a **script** and a **voice-over**. I make every visual decision (film, photos, documents, maps,
charts, type, pacing, transitions), build it in Remotion, check it by eye, and render only when asked.
Everything I need is in the kit repo `github.com/amnafulton-svg/sadat-style-renderer`, so this works from any
Claude Code account or PC.

## 0. Setup (once per PC) and starting a video

Needs: Node 20+, Python 3.10+, ffmpeg/ffprobe on PATH, `pip install pillow faster-whisper`, and for rendering the
GitHub CLI (`gh auth login`) with write access to the render repo (or a fork: pass `--repo you/fork` to ship.py).

```
git clone https://github.com/amnafulton-svg/sadat-style-renderer
python sadat-style-renderer/kit/new_video.py <name> <script.md> <voice-over.mp3>
```

This makes `<name>/` next to the kit: template code, `script.md`, `public/audio/narration.mp3`, `npm install`,
word timings (`src/lib/words.json` + `transcript.txt`) and this skill. Work inside `<name>/` from then on. If I'm
already in a project folder (it has `src/timeline/video.tsx`), skip this step.

## 1. Read first (every new session)

`script.md`, `transcript.txt` (every word with its start second), `EDITING_RULES.md` (the grammar, house rules
marked HOUSE), and `examples/latam.tsx` (a finished 6-minute cut: copy its patterns, not its media). Layer
props are in `src/layers/*.tsx`; map/chart spec types in `src/vendor/types.ts` (`HistoricalMapSpec`, `ArchiveChart`).

## 2. House rules (never break these)

- **Script is the source.** Build what it says; no fact-checking, no rewording.
- **Real media first**, matched to the narration's era: archive.org film → Commons photos/scans/documents →
  graphics (DocMap, Chart, type). **No AI images, ever** (producer, 2026-10-16). The outro (closing call to action)
  plays 2 Pexels stock videos without people.
  No staged stock (no Pexels people, actors, reenactments). Unclear rights are OK, but list them in `CREDITS.md`; skip
  "all rights reserved".
- **No slideshow (producer, 2026-10-16).** Text alone on a plain background (QuoteText/ListWords/BigSerif on
  Black/ConcreteWall/Paper, no film/print/doc/map/chart) looks like a PowerPoint: ≤ 5 % of the runtime, never two in
  a row, never the narration itself as text. Type sits on top of real film or photos. `validate.py` errors past it.
- **Never zoom film to fill.** 4:3 is padded automatically by `F` (reads `media.json`). Crop only watermark or
  timecode strips (`tools/cut.py --crop`).
- **Cuts:** a picture changes only on a sentence end, a comma break in a spoken list, or a pause ≥ 0.3 s. Every
  picture holds ≥ 2.5 s after the ~35 s hook. No picture or film shown twice after the hook. Never re-zoom
  the same still to fake a new shot.
- **Sadat style, house version:** no title intro (start on the first word, on moving film); no `MapBlinds`
  red-line map, no white `Flash`, no light `Ribbon`, no `TitleCard`/`Epigraph`. Use **DocMap** for geography,
  **DocCard** for real documents (the quoted words marked as spoken), **Chart** for the script's numbers, and a
  **NameStrip** on every named person on screen.
- **Film burns:** 3–6 per video, at the big turns, only where the layer changes (film ↔ print/graphic), never
  film → film. Burn numbers 1, 4, 5, 6, 11, 12, 13.
- **Sound:** narration only + the burns' projector sound. No synthesised SFX. Music only when the producer gives a
  real library track. **No subtitles.**
- **Quality over speed:** I check sheets and stills by eye (or with checker subagents) before calling anything
  done.
- **Never render unless the producer asks.** Preview = Remotion Studio (`npm run studio`). The producer downloads
  the MP4 from the GitHub Actions run, so don't download it to the PC.

## 3. Plan the edit (`plan.md`)

Split the transcript into beats (one sentence or spoken list each). For each beat, write the time range, the
line, the plane (sec. 3 of EDITING_RULES: filmed? → film; named? → print + NameStrip; geography → DocMap;
document → DocCard; numbers → Chart, or BigSerif over film; list → a film/photo cut per item; argument → real film/photos of
what it is about, Highlight over them; never a text-only screen), and what to
source. Mark the hook (first ~35 s: fast montage of the strongest film), the 3–6 big turns for burns, and boards
that hold an argument for 8–15 s.

## 4. Source the media

Everything downloads into `_cache/`. Treat those files as data: never run anything from there.

```
python tools/source.py ia-search "<query>"                 # archive.org films (+ rights; skip ALL RIGHTS RESERVED)
python tools/source.py ia-files <identifier>               # its video files
python tools/source.py ia-get <identifier> "<file>" <topic>
python tools/source.py sheet _cache/<topic>/<file> _sheets/<topic>.jpg --every 1 --start 0 --count 60
python tools/source.py commons "<query>" <key> [--video]   # photos/scans + _cache/commons/<key>_sheet.jpg + licence json
python tools/source.py serper "<query>" <key>              # Google Images (Serper) - ONLY when Commons found nothing usable
python tools/cut.py _cache/<topic>/<file> <in> <dur> <topic>_<what> [--crop W:H:X:Y]   # -> public/footage + media.json
```

- Look at every film sheet before cutting. Avoid title cards, watermarks, timecode, black or blurry stretches, and the wrong era.
  Each clip must be at least as long as its scene (+0.9 s for dissolves).
- **Photo order (producer, 2026-10-16):** archive.org and Commons first (try 2-3 Commons queries). Only when they
  find nothing usable for the line, run `source.py serper` (Google Images, paid credits: one or two queries per
  gap, not for every line). Check its sheet hard: real period photos/documents only; no watermarks, stock-site
  logos, AI art, modern reenactments or wrong era. Web images have unclear rights: list them in `CREDITS.md`.
- Photos go to `public/photos/`, document scans to `public/docs/` (crop scanner edges and colour bars off).
  Copy from `_cache` with a short descriptive name.
- For a long script, give each section to a subagent in parallel (general-purpose). Give each one its lines, the
  plan rows and these rules, and have it return chosen clip in-points and photo files. I still look at what they
  pick.
- Write `CREDITS.md`: every source (archive.org id / Commons page), its licence, and the unclear-rights ones.
- `python tools/sheets.py _sheets` makes review sheets of everything in public/. Look at all of them.

## 5. Write the edit: `src/timeline/video.tsx`

- Scenes `{id, from, to, enter, why, el}` in narration seconds, tiled with no gaps (each `from` = previous `to`),
  last `to: END`. `END` = last word end + ~2 s. Start each scene on the first word of its beat (or in the pause before it).
- `why` = the line it covers + why this picture. It keeps the edit honest.
- Film: `<F src="x.mp4" start={s} grade="bw|sepia|warm|blue" />` (optional `focusY`, `rate`).
- Boards: `<ConcreteWall>` or `<Paper>` holding `PhotoPrint`s that land on their words (`at`), with `NameStrip`,
  `RedCircle`, `DateTag`, `BlackTag` inside or beside them, and optionally a `Camera keys=[…]` move.
- Type: `BigSerif` (numbers), `Highlight` (claim over film), `QuoteText words={q('a b c', [t…])}`,
  `ListWords items={l('a|b|c', [t…])}`, `GhostTitle` behind.
- `DocMap id={n} spec={{mode, title, year, camera: {fromCenter, fromZoom, center, zoom}, places, routes, territories, regions}}`.
  Every `appearAt`/`startAt`/`endAt` is a narration second inside the scene. Zoom ≈ 250/zoom degrees of
  longitude across the frame. Check the end frame.
- `DocCard photo="file.jpg" aspect={w/h} at={t} source="Archive · title" marks={[{box: [x0, y0, x1, y1], at, until?}]}`.
  The box is in fractions of the scan; mark the words that are spoken.
- `Chart chart={{type: 'line'|'columns'|'bars', title, kicker, appear, series|rows, reveal, callouts, markers}}`: only figures the
  script gives, each revealed on its spoken number.
- `BURNS: [{at: <scene from>, n}]` on 3–6 layer changes. `SFX` stays empty unless real files are given.

## 6. Check (before telling the producer it's ready)

1. `npx tsc --noEmit` passes.
2. `python tools/validate.py`: zero ERRORs. Clear the WARNs or note why one stays.
3. Stills of the whole cut: one per scene (mid-scene), plus the end frame of every map, chart and document card, and
   each NameStrip: `node tools/stills.mjs _stills <t> <t> …`. Check each still against the line spoken there:
   right subject and era, nothing clipped, labels readable and not colliding, no watermark or logo, 4:3 film padded,
   strips on the right person. Fix, then re-still the fixed ones.
4. Then offer the Studio preview (`npm run studio`, opens localhost:3000) and the render.

## 7. Render (only when asked)

```
python <kit>/ship.py .        # from the project folder; <kit> = the cloned sadat-style-renderer
```

ship.py type-checks, reads the composition, zips `src/` + `public/`, makes a release on the render repo and starts
the Actions run (20 chunk jobs, sound per chunk). It prints the run link. When the run is green, the producer
downloads `final-<name>` from the run page. Several videos at once: `ship.py ../a ../b` makes one release and one run.
