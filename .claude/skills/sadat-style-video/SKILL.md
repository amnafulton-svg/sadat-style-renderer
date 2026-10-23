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
- **How many sections (producer 2026-10-22, cost):** one section per ~2.5-3 minutes of narration, so a 30-minute
  script gets 10-12, never fewer than 3 or more than 14, split on story turns. Measured on Britain (11 sections):
  most of the cost is each editor re-reading its own growing chat, while its setup is small (~13k tokens), so
  fewer, bigger sections cost MORE; many tiny ones cost more again in setup, joins and repeat fixes.
- For a long script, each section is made in **three phases, each a fresh subagent** (general-purpose, `model:
  "opus"`): **Pick → Build → Check**. Why (2026-10-21 Britain measure): ~54 % of a video's cost was editors re-reading
  their own growing chat on every step, and a third of that chat was sheets they had already decided on. A phase
  ends by writing its result to a file, so the next phase starts small and never carries the earlier pictures.
  Run one phase for all sections at a time: launch every section's Pick in ONE message as foreground Agent calls
  (`run_in_background: false`; they run side by side), then every Build in one message, then every Check. Never
  start a second agent for a section while one is running (2026-10-17: a background round looked "not started" 10 s
  in, a second round doubled every editor). An agent writes no files for its first minutes; it is alive while
  `_work/turns/<agent id>` changed in the last 10 min. Every phase brief gives the section's time range, its plan
  rows and the brief file, and says, word for word: "Never cat, loop or grep whole dumps (search results, JSON,
  logs, transcripts, latam.tsx): pipe them to `python tools/read.py "<question>"`. Search and download only with
  tools/source.py; any HTTP call of your own uses `User-Agent: SadatStyleVideoKit/1.1 (https://github.com/amnafulton-svg/sadat-style-renderer; documentary research)` and
  never an email, name, account id or token. source.py paces Wikimedia and retries by itself: never write your own
  fetch, retry or wait-loop scripts. If it prints `rate-limited`, go on with your next line and come back to it later;
  never sleep or wait on anything for more than 4 minutes (an idle chat's cache expires after 5 and the whole chat is
  paid again). Read each file once: never re-read SKILL.md, EDITING_RULES.md, the brief or a sheet you already opened.
  When your chat passes ~100k tokens (or after ~80 tool calls) a `[turn guard]` message tells you to wrap up:
  finish the step in hand, write your phase file, and end with `HANDOFF: <that file>`." When a phase agent ends with
  `HANDOFF:`, start a fresh agent for the SAME phase that reads that file first and carries on.
  - **Phase 1 · Pick** (all the looking at sources). Brief adds, word for word: "You choose every shot of your
    section; you do not cut clips or write code. First run `python tools/facts.py <section start> <section end>`
    once: the spoken sentences with their times and safe cut points (never grep/awk sentences.md or transcript.txt).
    Do the legwork in batches with `python tools/batch.py "<command>" "<command>" ...` (free, no model): it runs
    several `python tools/source.py` / `sheets.py` / `facts.py` commands side by side in ONE call (searches, ia-files,
    downloads, sheets) and prints each one's short result; media another section logged in `_work/used.tsv` are
    marked [USED sN] and rights-reserved films are dropped. Put a whole chore in one call: all of several lines'
    searches together, then all the downloads and sheets together. Every step you take yourself re-sends your whole
    chat, so never run those commands one at a time, and put independent tool calls in ONE message (several Bash
    calls side by side) instead of one per turn. Screen search sheets and whole-film sheets with
    `python tools/look.py` (defects, which ranges are clean). Then open yourself (Read) the sheet of each film you
    cut from and each photo you use, and pick the in-point against the exact words spoken over it: what is named
    must be on screen when it is said. Never open the same image twice; open sheets, not single full-size stills.
    Download what you pick (source.py ia-get / commons / serper) and log each pick in `_work/used.tsv` before
    choosing it (grep it first: no film range or photo another section logged). Write `_parts/<section>/picks.md`:
    one row per scene in time order: from–to (narration seconds, cuts only on a sentence end, list comma or pause
    ≥ 0.3 s), the exact words spoken over it, the layer (film / board / DocMap / Chart / DocCard / type over
    film), the source file path in `_cache` + in-point + duration + any crop (watermark/timecode strip only), or the
    photo/scan path, what is on screen at the named word (so a builder who never sees it can place it), NameStrip /
    tag / label texts with their spoken second, map/chart figures with their spoken seconds, and the credit
    (archive.org id or Commons page, licence, unclear-rights flag). Then end with `PICKS: _parts/<section>/picks.md`."
  - **Phase 2 · Build** (no pictures). Brief adds, word for word: "Read `_parts/<section>/picks.md` and build exactly
    it: cut each clip with `tools/cut.py` (name `<section>_<what>`), copy photos to public/photos and scans to
    public/docs, write the scenes in `src/timeline/parts/<section>.tsx`, and `_parts/<section>/CREDITS.md` from the
    picks' credits. Don't open images: picks.md is your eyes. If a pick can't be built (file missing, clip too short)
    take the nearest clean range of the same source that picks.md describes and note it. Change the file with small
    Edits, not whole rewrites. Run `npx tsc --noEmit` and `python tools/validate.py` and clear every ERROR in your
    section (validate.py also errors on one picture held over three sentences, nothing on screen after a cut,
    blank film and two clips showing the same setting of one film: cut.py logs each clip's source in `_work/clips.tsv`). Write `_parts/<section>/build.md` (what was built, any change from picks.md and why, WARNs left) and end
    with `BUILT: _parts/<section>/build.md`."
  - **Phase 3 · Check** (the review boards). Brief adds, word for word: "Read `_parts/<section>/picks.md` and
    `build.md`, then run `python tools/board.py --from <section start> --to <section end>` and open every board: fix
    each tile whose picture doesn't show what its words say, or is clipped, colliding, unpadded 4:3 or has a strip on
    the wrong person, with small Edits. When a shot itself is wrong, screen the alternatives with look.py and open
    only the sheet you take the new in-point from (log it in `_work/used.tsv`). Re-board only the fixed range and
    look again. Run tsc + validate.py (zero ERRORs in your section). Keep `_parts/<section>/HANDOFF.md`: what the
    section shows, what you fixed, what is left. End with `HANDOFF: _parts/<section>/HANDOFF.md`."
  A fresh Final subagent checks the whole cut on the review boards (step 6).
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

My own chat is long by now and every step I take re-sends it, so the whole-cut check runs in ONE fresh subagent
(`model: "opus"`, foreground), never in my chat. Its brief, word for word: "You are the Final check of this
Sadat-style video. Read `CLAUDE.md`, this skill's house rules and every `_parts/*/HANDOFF.md`.
1. `npx tsc --noEmit` passes.
2. `python tools/validate.py`: zero ERRORs. Clear the WARNs or note why one stays.
3. **Whole-cut review boards:** `python tools/board.py` (or `--from S --to S` per section) stills every scene
   mid-scene plus the end frame of every DocMap, Chart and DocCard, 12 per board with the words spoken over each
   tile, in `_review/`. Open every board. Per tile: does the picture show what its words say at that moment (the
   thing named, the right era/place/person), nothing clipped, labels readable and not colliding, 4:3 film padded,
   strips on the right person. Also across tiles: the same shot held over several sentences, the same crowd or room
   shown twice. Fix every flagged tile with small Edits (when a shot itself is wrong, screen alternatives with
   look.py, open only the sheet you take the new in-point from, log it in `_work/used.tsv`), then re-board only the
   fixed range and look again. A NameStrip or label you're unsure of gets its own still
   (`node tools/stills.mjs _stills <t>`).
4. Run tsc + validate.py once more (zero ERRORs). Write `_parts/FINAL.md`: what you fixed (scene, why), WARNs left
   and why, and a last line `STATUS: READY` or `STATUS: NOT READY: <what is left>`. End with `FINAL: _parts/FINAL.md`."
I read only `_parts/FINAL.md` (not the boards). NOT READY: fix what it lists (or brief a fresh Final again) before
going on.
STATUS: READY: then I offer the Studio preview (`npm run studio`, opens localhost:3000) and the render.

## 7. Render (only when asked)

```
python <kit>/ship.py .        # from the project folder; <kit> = the cloned sadat-style-renderer
```

ship.py type-checks, reads the composition, zips `src/` + `public/`, makes a release on the render repo and starts
the Actions run (20 chunk jobs, sound per chunk). It prints the run link. When the run is green, the producer
downloads `final-<name>` from the run page. Several videos at once: `ship.py ../a ../b` makes one release and one run.
