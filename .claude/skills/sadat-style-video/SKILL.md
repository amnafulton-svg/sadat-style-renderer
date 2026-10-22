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
marked HOUSE), and `examples/latam.tsx` (a finished 6-minute cut: copy its patterns, not its media; section editors don't read it
whole, they ask `tools/read.py` how it does a thing). Layer
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
- **Quality over speed:** every sheet and still gets checked before anything is called done. Picture-to-words
  judgement (which shot, which in-point, does the cut match the line) is done with my own eyes; `tools/look.py`
  only screens for defects (below).
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

- **Who looks at what (hybrid, producer 2026-10-20).** From 10-17 to 10-20 editors never opened images and judged
  everything from look.py's words; the cuts stopped matching the narration ("not synced like before"), because a
  screen model calls a clean shot of the wrong thing "clean". So:
  - **My own eyes (Read the image), for every picture that goes on screen:** the film sheet I take an in-point
    from (read it once, pick all the in-points I need from that film, note them in HANDOFF.md, don't re-open it),
    a photo/scan before it goes on a board, the opening shot, and the review boards of my cut
    (`tools/board.py`, step 6). Judge each against the exact words spoken over it: the thing named must be on
    screen when it is said (paratroopers = men under parachutes, not just planes; "Panzer divisions" = tanks, not a
    quiet street).
  - **`tools/look.py` (Sonnet helper), for screening only:** search-result sheets (Commons/Serper/archive.org
    candidates: which tiles are real, period, clean, big enough), whole-film sheets to find the clean usable
    ranges before I open the one I pick from, `sheets.py` defect sheets, and re-checking a fixed defect.
    `python tools/look.py "<what to judge>" <images…> --note "<the narration lines / what each is for>"` prints one
    line per image or tile range. It finds watermarks, logos, timecode, title cards, black/blurry/frozen frames,
    AI look, modern people, tiny photos, clipped text. Its "fits the line" is a hint, never the decision.
  - **Cost:** an image I open stays in my context and is paid for on every later turn, so open sheets and boards,
    not single full-size stills; never open the same image twice; let look.py throw out the junk first; and the
    turn guard below keeps each editor short.
- **Dumps = `tools/read.py` (Haiku reader, same cost rule).** Never `cat`, loop over or grep whole dumps into the
  session: search results, JSON (media.json, words/transcripts), logs, loops over many files, latam.tsx. Pipe them
  instead: `python tools/read.py "<question>" <files…>` or `<command> | python tools/read.py "<question>"`. It
  answers with only the lines asked for (short text passes through as is). 2026-10-17 bunker measure: `cat`/`for`/
  `awk`/`grep` output was still ~37% of what editors re-read. Your own section code, plan and HANDOFF.md you read
  directly, but only the lines you need (`sed -n`), right before you edit them.
- **No personal data in any request (privacy rule, 2026-10-18).** Search and download only through
  `tools/source.py` and `tools/cut.py`. If you must make your own HTTP call (curl, requests, urllib), send the kit's
  fixed header `User-Agent: SadatStyleVideoKit/1.1 (https://github.com/amnafulton-svg/sadat-style-renderer; documentary research)` and nothing else about anyone: never
  an email address, name, account id, token or file path in a header, URL, query or upload (a section editor once
  put the producer's email in a Wikimedia User-Agent). The same goes for files the video ships with.
- Screen film sheets with look.py, then open the sheet of each film you actually cut from and pick the in-point
  yourself against the line. Avoid title cards, watermarks, timecode, black or blurry stretches, and the wrong era.
  Each clip must be at least as long as its scene (+0.9 s for dissolves).
- **Photo order (producer, 2026-10-16):** archive.org and Commons first (try 2-3 Commons queries). Only when they
  find nothing usable for the line, run `source.py serper` (Google Images, paid credits: one or two queries per
  gap, not for every line). Check its sheet hard: real period photos/documents only; no watermarks, stock-site
  logos, AI art, modern reenactments or wrong era. Web images have unclear rights: list them in `CREDITS.md`.
- Photos go to `public/photos/`, document scans to `public/docs/` (crop scanner edges and colour bars off).
  Copy from `_cache` with a short descriptive name.
- **How many sections (producer 2026-10-21, cost):** one section per ~5 minutes of narration, so a 30-minute
  script gets 6, and never more than 8, split on story turns. Each extra editor re-reads the same rules and setup
  from scratch (past 30-min videos ran 10-16 editors). A big section loses nothing: when its editor gets long, the
  turn guard hands it to a fresh editor that carries on from HANDOFF.md. Never split a section further to go faster.
- For a long script, give each section to a subagent in parallel (general-purpose). Launch all of them in ONE
  message as foreground Agent calls (`run_in_background: false`): they still run side by side and the turn waits
  for their results. Never start a second editor for a section while one is running (2026-10-17: a background
  round looked "not started" 10 s in, a second round doubled every editor). A new editor writes no files for its
  first minutes; it is alive while `_work/turns/<agent id>` changed in the last 10 min. Give each one its lines, the
  plan rows and these rules, and have it return chosen clip in-points and photo files. Every brief says, word for
  word: "Screen search sheets and whole-film sheets with `python tools/look.py` (defects, which ranges are clean).
  Then open yourself (Read) the sheet of each film you cut from and each photo you use, and pick the in-point
  against the exact words spoken over it: what is named must be on screen when it is said. Never open the same
  image twice; open sheets and boards, not single full-size stills. When your section is built, run
  `python tools/board.py --from <section start> --to <section end>` and open every board: fix each tile whose
  picture doesn't show what its words say, then re-board the fixed part. Never cat, loop or grep
  whole dumps (search results, JSON, logs, transcripts, latam.tsx): pipe them to `python tools/read.py "<question>"`.
  Read your own section code and plan directly, only the lines you need. Search and download only with
  tools/source.py; any HTTP call of your own uses `User-Agent: SadatStyleVideoKit/1.1 (https://github.com/amnafulton-svg/sadat-style-renderer; documentary research)`
  and never an email, name, account id or token. source.py paces Wikimedia and retries by itself: never write
  your own fetch, retry or wait-loop scripts; if it prints `rate-limited`, go on with your next line and come back to
  it later, and never sleep or wait on anything for more than 4 minutes (an idle chat's cache expires after 5 and the
  whole chat is paid again). Keep _parts/<section>/HANDOFF.md up to date as you go (done, picks with in-points,
  left, problems). After ~80 tool calls a `[turn guard]` message from the producer's project hook tells you to
  wrap up: then finish the step in hand, update HANDOFF.md and end with `HANDOFF: _parts/<section>/HANDOFF.md`."
  When an editor ends with `HANDOFF:`, start a fresh section editor with the same brief plus "read that HANDOFF.md
  first and carry on from it" (a fresh one re-reads far less than one long session). I check what they pick on
  the review boards (step 6).
- Write `CREDITS.md`: every source (archive.org id / Commons page), its licence, and the unclear-rights ones.
- `python tools/sheets.py _sheets` makes review sheets of everything in public/. Screen all of them with look.py for
  defects.

## 5. Write the edit: `src/timeline/video.tsx`

- Scenes `{id, from, to, enter, why, el}` in narration seconds, tiled with no gaps (each `from` = previous `to`),
  last `to: END`. `END` = last word end + ~2 s. Start each scene on the first word of its beat (or in the pause before it).
- `why` = the line it covers + why this picture. It keeps the edit honest.
- Film: `<F src="x.mp4" start={s} grade="bw|sepia|warm|blue" />` (optional `focusY`, `rate`).
- Boards: `<ConcreteWall>` or `<Paper>` holding `PhotoPrint`s that land on their words (`at`), with `NameStrip`,
  `RedCircle`, `DateTag`, `BlackTag` inside or beside them, and optionally a `Camera keys=[…]` drift (scale 0.95-1.12, at most 3 % per second: never a zoom into a detail;
  the Great Plains pushes to 1.25-2.1x read as a "weird zoom", producer 2026-10-21).
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
3. **Whole-cut review boards, with my own eyes:** `python tools/board.py` (or `--from S --to S` per section) stills
   every scene mid-scene plus the end frame of every DocMap, Chart and DocCard, 12 per board with the words spoken
   over each tile, in `_review/`. For a long cut, give each section's boards to a fresh subagent (`model: "opus"`,
   foreground, all in one message) that opens every board and returns one line per tile that is wrong; a short
   cut I open myself. Per tile: does the picture show what its words say at that moment (the thing named, the
   right era/place/person), nothing clipped, labels readable and not colliding, 4:3 film padded, strips on the
   right person. Fix every flagged tile, then re-board only the fixed time range. A NameStrip or label I'm unsure
   of gets its own still (`node tools/stills.mjs _stills <t>`).
4. Then offer the Studio preview (`npm run studio`, opens localhost:3000) and the render.

## 7. Render (only when asked)

```
python <kit>/ship.py .        # from the project folder; <kit> = the cloned sadat-style-renderer
```

ship.py type-checks, reads the composition, zips `src/` + `public/`, makes a release on the render repo and starts
the Actions run (20 chunk jobs, sound per chunk). It prints the run link. When the run is green, the producer
downloads `final-<name>` from the run page. Several videos at once: `ship.py ../a ../b` makes one release and one run.
