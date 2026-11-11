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
| 4b | News page | `HeadlineCard` (`layers/Headline.tsx`) | A real news article (headline, the line being read) in a browser window with the outlet address, marker on its words |
| 4c | Chain board | `ChainBoard` (`layers/Chain.tsx`) | Prints (films play inside) pinned on a wall, red string joining causes/people to one thing, camera flying link to link |
| 5 | Chart | `Chart` (`layers/Evidence.tsx`) | **HOUSE:** real figures said in the script, each landing on its spoken number |
| 6 | Prints | `PhotoPrint` (`layers/Print.tsx`) | A named person, place or object. A print can hold moving film (`film` prop) |
| 6b | Full-screen photo | `FullPhoto` (`layers/Film.tsx`) | **HOUSE:** a shot with one photo that holds up full screen: fills the frame, slow zoom in |
| 7 | Annotations | `PhotoPrint hand=`, `HandNote`, `PhotoPrint names=`, `NameStrip`, `RedCircle`, `BlackTag`, `DateTag`, `KraftNote` | Pointing at the detail the narration names |
| 8 | Type | `BigSerif`, `Highlight`, `QuoteText`, `ListWords`, `GhostTitle`, `LabelTape` (`layers/Type.tsx`) | The one word to remember. **HOUSE:** `Highlight` (the red bar) only for a real quote from a person or document, in quote marks |
| 9 | Camera | `Camera` (`layers/Stage.tsx`) | Slow drift over a board (scale 0.95-1.12, at most 3 % per second); prints never move on their own once they land |
| 10 | Transition | `Enter` kinds + `BURNS` (`Main.tsx`) | Between scenes (sec. 5) |
| 11 | Skin | `Grain`, `Dust`, `Vignette` (`overlays/`) | Always on, every frame (makes film and paper one printed object) |

**HOUSE, banned (validate.py errors):** `MapBlinds` (the red-line map on blinds), `TitleCard`, `Epigraph`,
`Flash` (white flash), `Ribbon` (light-leak ribbons).

## 3. Choosing the picture (decision order)

1. **Was the moment filmed?** → `F`. Real archive film from the narration's era always comes first.
2. **Is a person, place or object named?** → `PhotoPrint` (real photo) with the person's name strip **on the spoken
   name** (every named person on screen gets one; `sub` = country or role), hung under that person's photo:
   `names={[{text: 'Col. Eli Lilly', sub: 'grandfather · founder', at: 359.62, fx: 0.79}]}`.
   **One portrait of one person alone on the wall** → the print goes big on one side (w 620-700, x near 540 or
   1380) and the name is written by hand beside it, on the spoken name; `role` = rank and post (two short lines),
   `note` = the one date or fact the script says about them, written in orange on its own spoken word:
   `<PhotoPrint src="s1_nagano.jpg" at={49.3} x={540} y={540} w={700} ... hand={{name: 'Osami Nagano', role:
   'Fleet Admiral\nChief, Naval General Staff', note: 'until February 1944', at: 50.18, noteAt: 53.0}} />`.
3. **Geography (journey, border, spread, territory)?** → `DocMap`. Not for biography lines ("born in X").
4. **A document is quoted or named (a law, treaty, letter, headline)?** → `DocCard` with the real scan, the quoted
   words marked as they are spoken. **HOUSE:** the mark's `lines` come from `tools/docmark.py <scan> "the words"`
   (OCR), never a box guessed by eye; validate errors on a mark that is not on printed lines.
   The card shows the clean page straight on the graph paper, rising in once and holding still, nothing dimmed, a
   yellow highlighter running over the quoted words as they are spoken (producer, 2026-11-11: the dimmed page with a
   lit band looked messy). Mark only the words the narrator quotes, with `until` at the end of the quote.
4b. **The press reported it (a news story, a study's coverage, "the papers wrote")?** → `HeadlineCard`: the real
   article page from `node tools/headline.mjs <url> <name> "the words"` (its boxes, never guessed), the camera on the
   headline, then on the line being read, highlighted as it is spoken. **HOUSE (producer, 2026-11-05):** no count:
   use it whenever it is the right picture for that moment, never as filler between films.
4c. **The script ties several causes, people or steps to one thing ("three pressures met", "from A to B to C")?** →
   `ChainBoard`: each link's real film or photo pinned on the wall as it is named, a red string to what it leads to,
   the camera on each link, then back to the whole chain. **HOUSE (producer, 2026-11-05):** no count: use it when the
   narration really is a chain, never as filler.
5. **Numbers the script gives?** → `Chart` (line or bars) landing on the spoken figures, or `BigSerif` for one number
   **over film or a print** of what the number counts (bank crowds under a bank count, bread lines under jobless %).
   Two or three figures to compare (`type: 'bars'`, 2-3 rows) play as big numbers that fill the frame, each
   counting up onto its spoken word with a bar to scale under it: `Chart` does this by itself, write the rows
   as usual (`highlight: true` on a row makes that one red).
6. **A list** ("geography, tribe, history") → a fast film or photo cut per item (the item's word as a `LabelTape`
   on it). `ListWords` / `KraftNote` only on top of a picture.
7. **A quote or the argument itself** → film or real photos of what the line is about (its era, its people, its
   places, its objects). **HOUSE (producer, 2026-11-05):** the red bar (`Highlight`) is only for a real quote from a
   person or a document, its words in quote marks (`text="“No misgivings”"`); never the narrator's own key words
   ("NEVER TOLD", "THE QUESTION"): they made the video look templated. validate.py errors on any other red bar. Abstract lines ("money vanished", "trust
   broke") still get real pictures: empty tills, closed banks, crowds, faces, the objects named.

**HOUSE: no slideshow (producer, 2026-10-16).** Text alone on `Black`, `ConcreteWall` or `Paper` (QuoteText /
ListWords / BigSerif with no film, print, document, map or chart) makes the video look like a PowerPoint. Never put
the narration itself on screen as text. Text-only screens may total at most **5 % of the runtime** and never two in a
row; `validate.py` errors past that and lists them. When film is thin, climb the ladder: other searches → the same
event from another angle → real photos/scans (Commons first, then `source.py serper` Google Images when Commons has nothing) → documents →
map/chart → only then type. Never an AI image.

**HOUSE media rules:**
- Real media only: archive.org film, then Wikimedia Commons photos/scans/documents, then graphics (map, chart,
  type). **No AI images, ever (producer, 2026-10-16)** — not even as a last resort.
- The outro (the closing "subscribe ... see you in the next one" call to action, and any pointer to another video)
  is **footage only, no text on screen** (producer, 2026-11-04): **2 Pexels stock videos** without people (calm shots
  that fit the topic: sky, sea, the place, old buildings), one after the other. No SUBSCRIBE/LIKE/COMMENT type, no
  next-video title, no tags, tapes, dates, names or prints there. Give those scenes ids starting `outro`.
- Era-matched: no 1950s film under a 1990s line.
- **HOUSE:** before ~1895 no film exists, so the earliest street film is an accepted stand-in for 19th-century life, but
  never with automobiles, modern signs or 20th-century machines under a line about an earlier year (pick other seconds
  or a period print). Later footage is fine where the words are about later times.
- **HOUSE: every coin, note, stamp, token or seal on screen gets an object tag naming it** ("3¢ STAMP, 1861"); a
  slogan tape alone is not enough.
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
- **HOUSE: the camera drifts, it never zooms in (producer, 2026-10-21).** Keys stay within scale 0.95-1.12 and change
  at most 3 % per second (1.0 -> 1.08 takes 3 s or more). A detail the words name gets its own print or crop, not a
  push into the board. `Camera` clamps bolder keys and `validate.py` errors on them.
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

- **HOUSE: film plays as it was shot.** Colour film stays colour, black-and-white stays black-and-white; `F` adds no
  tint and no blurred, darkened edges, so leave `grade` off film (it is ignored there). `grade` (`bw`, `sepia`,
  `warm`, `blue`) is for prints and photos only (producer, Pacific 2026-11-10: colour Midway film had been turned
  grey with soft edges; the clean version was the pick).
- **Type:** Playfair for numbers, Libre Caslon for phrases, quotes and name strips, Bebas for ghost titles,
  Special Elite for tape labels. Crimson highlight bars, red marker circles.
- **Prints:** white border, small tilt (±1–4°), drop shadow, never stretched.
- **HOUSE:** no subtitles.
- **HOUSE: text must read against what is under it.** `BigSerif`/`ListWords` default to cream: on `Paper`, light
  desks, pale sky or white print borders give them dark ink (`color`) or a dark plate. Tags, tapes and bars sit beside
  prints, not on their edges or captions, and stay inside the frame at the end of every camera move.
  Light type over film gets a dark backing by itself; still keep it off the brightest part of the frame (sky).
  Labels always draw above prints, so a print landing later never hides a bar.
- **HOUSE: `DateTag` sits in a top corner (producer, 2026-11-05)**, top left by itself, never mid-frame over a face
  or the thing to see; if a face or the subject is in the top left, give it `corner="right"`. (x/y are ignored.)
- **HOUSE: a date or number lands on its word.** A `DateTag`, `BigSerif`, `Highlight` or tape carrying a date or
  figure appears by the time it is said (validate errors when it lands > 0.6 s late). If the sentence that says the
  date starts during the scene before, the new scene starts at that sentence, not on the next comma.
- **HOUSE: text stays long enough to read (hook included).** Every tag, tape, word or quote is fully on screen
  for at least 1 s (0.25 s per word when longer: a 6-word BlackTag needs 1.5 s) before its scene cuts. A tag that
  lands near a cut goes on the next scene, or the cut moves to a later sentence end; never put a tag on a scene
  too short for it (Italy 2026-10-25: a 1.24 s hook shot cut away while "11 days earlier" was still typing). `python
  tools/fixread.py` cues short ones earlier (up to 1.2 s), lets an `out=` run later, or holds the scene to the next
  pause; what it lists after that is yours (shorten the text, or drop it).
- **HOUSE: a cut lands on the voice, not on the breath before it.** whisper glues the pause before a sentence onto
  its first word, so a cut on that word can come up to a second before the narrator speaks (Hitler's generals 2:12
  2026-10-26: "this scene came out early about 1s"). tools/words.py now starts those words where the voice starts
  (tools/voice.py reads the audio); validate errors on a cut > 0.5 s before the voice, and `python tools/fixonset.py`
  moves such cuts to 0.1 s before it (the scene before holds longer, this scene's cues in the pause move along).
- **HOUSE: a name hangs under the photo it names.** On a photo every name strip is the print's own `names=[{text,
  sub, at, fx}]` (optional `rot`, default -2; `size`, default 34): the names hang in one row off the photo's bottom
  edge, half on the white border, in the people's order left to right by fx (where that person stands, 0-1; fx
  only orders the row). A print with a black caption (`tag=`) puts the row on the right, beside it. Never place a
  free `NameStrip` beside a print, and never on a face (cannabis 6:00 2026-10-25: "the name tag on the right side
  feels messy and where does it belongs?", then "the white tag should be under the image not on the face"). Keep
  every LabelTape, Highlight, BlackTag and DateTag off the print's bottom edge: the names hang there. The name goes
  under that person's own print, never under the building or crowd beside it. validate errors on a free
  NameStrip in a shot with a print, names running off the frame, into the black caption, into a label, far wider
  than the photo, or under the wrong print; `python tools/fixnames.py` moves the free ones (to the print named
  after the person, else the nearest). Free NameStrips stay for film and maps only.
- **HOUSE: one portrait alone = a big print and a handwritten name.** A shot whose only picture is one person's
  portrait does not leave a small print in the middle of an empty wall with a strip under it: the print fills one
  side of the wall and `hand={{name, role, note, at, noteAt}}` writes the name in white pencil on the free side
  (it places and sizes itself; arrow to the photo, role in small typewriter, the note in orange pencil), instead
  of `names=`. Only what the script says goes in `role` and `note`. Two or more people, group photos, boards of
  several prints and wide photos keep `names=` / FullPhoto as before (producer, Pacific 0:46 2026-11-10: "i like
  the new portrait"; designed serif type beside it "looks templated", the handwriting was the pick).
- **HOUSE: a print's caption sits under the print.** The black who/what/where tag of a print is the print's own
  `tag={{line1: 'A prescription', line2: 'Fairhaven Pharmacy, 9 Sept. 1899'}}` (optional `at`, default just after
  the print lands; `size`, default 38). PhotoPrint sticks it across its bottom-left edge, so it always sits under
  the photo and moves with it; never place a free `BlackTag` by hand next to a print (cannabis 2026-10-25: the
  tag landed across the frame from its print). In a shot with one print validate errors on a free BlackTag, and
  on a caption that would run off the frame (raise the print or make it smaller). `python tools/fixtags.py`
  moves every free tag onto its print in one go. Free BlackTags stay for
  FullPhoto, film and boards of several prints, placed under the picture they name.
- **HOUSE: on a full-screen photo, write the note on the picture.** When a `FullPhoto` shows the one thing the
  line names, `HandNote` writes its name by hand on a quiet part of the picture at the spoken word, draws an arrow
  to it or an orange ring around it, and adds the place and date in orange:
  `<HandNote x={150} y={250} text="USS Quincy" sub="Savo Island, 9 Aug. 1942" at={307.5} subAt={308.7} size={150}
  ring={[910, 640, 330, 95]} />`, or with an arrow `from={[560, 310]} to={[720, 440]}`. White pencil by default,
  `ink` for a bright sky. Look at a still: the words sit on a calm area, the arrow tip or ring is on the thing.
  One or two short notes a shot; the black tag stays for busy pictures with no calm area (producer, Pacific
  2026-11-10: the handwritten note was picked over the black tag in the corner).
- **HOUSE: one good photo plays full screen.** When a shot's only picture is one photo that is wide (aspect
  >= 1.3) and big enough (enlarged at most 1.6x to fill 1920x1080), it is a `FullPhoto` (fills the frame, slow
  zoom in towards `focusX`/`focusY`), not a `PhotoPrint` on a wall: one print on a wall shot after shot feels
  templated. Tags and type go on top as usual. Prints stay for several photos on a board, tall or small photos,
  and prints with marks drawn on them. If a fitting photo is small, look for a bigger copy first (Commons
  originals). validate errors both ways; `python tools/fixfull.py` converts the flagged prints (caption and names
  become a free BlackTag/NameStrips clear of the other labels): look at a still of each, a caption must not cover a
  face.
  Full screen shows a scan's own edges (black bars, paper margins, scanner strips) that a print hid:
  `python tools/trimfull.py` (`--dry` lists first) crops straight flat borders into <name>_trim.jpg and repoints the
  FullPhoto; it leaves skies and plain walls alone. A wide paper mat around an engraving it can miss: crop by hand.
  A photo whose head is near the top edge gets `focusY={15}` so the crop keeps the head.
- Light type that is not on paper gets a dark scrim behind it (Type.tsx). On a white or busy picture that is still
  not enough: give BigSerif `bar` (dark box), or move the type to a plain part of the frame. Never type across a
  picture's own title or a face.

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
5. `python tools/validate.py`, then `python tools/board.py --from <t1> --to <t2>` and look at the boards yourself:
   each picture must show what its words say.
