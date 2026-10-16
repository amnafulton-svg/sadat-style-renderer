# Editing rules: the "Sadat" grammar (house version)

The style comes from *How Sadat Fooled the Entire World in 1973*. The rules below are the reference's grammar
**plus the producer's house rules**, which win wherever they differ (marked **HOUSE**). `tools/validate.py`
enforces the checkable ones.

## 0. The core idea

The video is built like an **investigator's desk**, not a "documentary with B-roll".

- **Archive film** is the *world*: what happened.
- **Paper** is the *evidence*: prints, document scans, maps and notes on a wall, desk or paper board.
- **Type** is the *verdict*: one word, number or name stamped the moment the narrator says it, **over film or a
  print**, never as a screen of its own.

Moving between these three planes means something. Film → board says "now look at the proof". Board → film says
"and this is what it caused".

## 1. Pacing

| Measure | Reference | Rule here |
|---|---|---|
| Median shot | 1.6 s | Film montage 2.5–5 s per shot; faster only in the hook and in spoken lists |
| Shots over 8 s | 12% | Only boards/maps/charts where something keeps arriving or the camera moves |
| Opening | epigraph + title | **HOUSE: no title intro.** The video starts on the first spoken word, on moving film |

- **HOUSE:** the first ~35 s is the hook. Fast cuts are allowed there (each still ≥ 1.2 s).
- **HOUSE:** after the hook, no picture holds less than 2.5 s. One film shot under changing narration for more than ~9 s
  gets split at a phrase end.
- **HOUSE:** pictures change only on a **sentence end, a comma break in a spoken list, or a pause ≥ 0.3 s**, never
  in the middle of a phrase. Take the times from `transcript.txt` (whisper word starts).

## 2. Layer stack (bottom → top)

| # | Layer | Component | Used when |
|---|---|---|---|
| 1 | Background | `ConcreteWall`, `Paper`, `Desk`, `Black` (`layers/Backgrounds.tsx`) | Board and type scenes |
| 2 | Archive film | `F` (= `Film` with auto-pad, `timeline/video.tsx`) | The narration describes something that was filmed |
| 3 | Map | `DocMap` (`layers/Evidence.tsx`) | **HOUSE:** journeys, borders, who held what. NASA terrain, 3D tilt |
| 4 | Document | `DocCard` (`layers/Evidence.tsx`) | **HOUSE:** a real scan (law, treaty, letter, newspaper) with the quoted line marked on its word |
| 5 | Chart | `Chart` (`layers/Evidence.tsx`) | **HOUSE:** real figures said in the script, each landing on its spoken number |
| 6 | Prints | `PhotoPrint` (`layers/Print.tsx`) | A named person, place or object. A print can hold moving film (`film` prop) |
| 7 | Annotations | `NameStrip`, `RedCircle`, `BlackTag`, `DateTag`, `KraftNote` | Pointing at the detail the narration names |
| 8 | Type | `BigSerif`, `Highlight`, `QuoteText`, `ListWords`, `GhostTitle`, `LabelTape` (`layers/Type.tsx`) | The one word to remember |
| 9 | Camera | `Camera` (`layers/Stage.tsx`) | Slow move over a board; prints never move on their own once they land |
| 10 | Transition | `Enter` kinds + `BURNS` (`Main.tsx`) | Between scenes (sec. 5) |
| 11 | Skin | `Grain`, `Dust`, `Vignette` (`overlays/`) | Always on, every frame (makes film and paper one printed object) |

**HOUSE, banned (validate.py errors):** `MapBlinds` (the red-line map on blinds), `TitleCard`, `Epigraph`,
`Flash` (white flash), `Ribbon` (light-leak ribbons).

## 3. Choosing the picture (decision order)

1. **Was the moment filmed?** → `F`. Real archive film from the narration's era always comes first.
2. **Is a person, place or object named?** → `PhotoPrint` (real photo) with a `NameStrip` **on the spoken name**
   (every named person on screen gets one; `sub` = country or role).
3. **Geography (journey, border, spread, territory)?** → `DocMap`. Not for biography lines ("born in X").
4. **A document is quoted or named (a law, treaty, letter, headline)?** → `DocCard` with the real scan, the quoted
   words marked as they are spoken.
5. **Numbers the script gives?** → `Chart` (line or bars) landing on the spoken figures, or `BigSerif` for one number
   **over film or a print** of what the number counts (bank crowds under a bank count, bread lines under jobless %).
6. **A list** ("geography, tribe, history") → a fast film or photo cut per item (the item's word as a `LabelTape`
   on it). `ListWords` / `KraftNote` only on top of a picture.
7. **A quote or the argument itself** → film or real photos of what the line is about (its era, its people, its
   places, its objects), with `Highlight` over the film for the key words. Abstract lines ("money vanished", "trust
   broke") still get real pictures: empty tills, closed banks, crowds, faces, the objects named.

**HOUSE: no slideshow (producer, 2026-10-16).** Text alone on `Black`, `ConcreteWall` or `Paper` (QuoteText /
ListWords / BigSerif with no film, print, document, map or chart) makes the video look like a PowerPoint. Never put
the narration itself on screen as text. Text-only screens may total at most **5 % of the runtime** and never two in a
row; `validate.py` errors past that and lists them. When film is thin, climb the ladder: other searches → the same
event from another angle → real photos/scans → documents → map/chart → only then type. Never an AI image.

**HOUSE media rules:**
- Real media only: archive.org film, then Wikimedia Commons photos/scans/documents, then graphics (map, chart,
  type). **No AI images, ever (producer, 2026-10-16)** — not even as a last resort.
- The outro (the closing "subscribe ... see you in the next one" call to action) plays **2 Pexels stock videos**
  without people (calm shots that fit the topic: sky, sea, the place, old buildings), one after the other.
- Era-matched: no 1950s film under a 1990s line.
- No staged stock (no Pexels people, actors, reenactments). Stock only for a real named place, without people.
- Rights: public domain / CC / US government / Prelinger first. Unclear rights are OK; list them in `CREDITS.md`.
  Skip anything marked "all rights reserved".
- **Never zoom film to fill the frame.** 4:3 film is padded automatically (`F` reads `media.json`). Crop only
  watermark/timecode strips (`tools/cut.py --crop`).
- No picture twice after the hook (validate.py errors), and never re-zoom one still to fake a new shot.
- The script is the source: build what it says, no fact-checking or rewriting.

## 4. Timing

- **Everything lands on its word.** Every `at` is a narration second from `transcript.txt`. Prints fly in for 8
  frames and land as the word starts; type pops just before its word.
- **Prints land, then the camera moves** (`Camera` keys), or the board simply holds while the argument builds.
- **One board per argument.** It leaves when the argument ends, not when a timer runs out.

## 5. Transitions

| Kind | Frames | Meaning |
|---|---|---|
| `cut` | 0 | Same beat, next shot (most changes) |
| `dissolve` | 22 | Time passes / thought continues (board → board) |
| `whip` / `whipL` | 6 | "And then… and then…" consequence lists |
| `torn` | 12 | Leave the world for the evidence (film → paper) |
| `rack` | 0 | Settle into focus on a new board |
| **film burn** (`BURNS`) | ~1 s | **HOUSE:** the big turns of the story, 3–6 per video, **only on a layer change** (film ↔ print/graphic), never film → film. Numbers 1, 4, 5, 6, 11, 12, 13. The burn carries its own projector sound and hides a hard cut |

A transition used for decoration means nothing, so most changes are hard cuts.

## 6. Look

- **Film grade:** `bw` for ominous or older material, `sepia`/`warm` for neutral history, `blue` for cold/modern.
- **Type:** Playfair for numbers, Libre Caslon for phrases, quotes and name strips, Bebas for ghost titles,
  Special Elite for tape labels. Crimson highlight bars, red marker circles.
- **Prints:** white border, small tilt (±1–4°), drop shadow, never stretched.
- **HOUSE:** no subtitles.

## 7. Sound

- The narration is the clock (`public/audio/narration.mp3`, starts at frame 0).
- **HOUSE: no synthesised SFX.** Real files in `public/sfx` only, listed in `SFX`. The film burns bring their own
  projector sound.
- Music: none until the producer picks a real library track (YouTube Audio Library / Epidemic Sound). It then goes in
  `Main.tsx` as `audio/music_bed.*` with a ducked volume under the voice.

## 8. Adding a scene (checklist)

1. Find the phrase in `transcript.txt`; note the start of its first word and of the next phrase.
2. Pick the plane by sec. 3.
3. Add `{id, from, to, enter, why, el}` to `src/timeline/video.tsx`. Write the **why**: the line it covers and why
   this picture.
4. Cue every print, strip and type at its spoken word.
5. `python tools/validate.py`, then `node tools/stills.mjs _stills <t1> <t2> …` and look at the frames.
