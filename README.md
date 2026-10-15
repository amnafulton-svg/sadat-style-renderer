# sadat-style-renderer

GitHub Actions renderer for the Sadat-style documentary cuts (`latam-doc` and the ones after it). It is kept
separate from `documentary-renderer`, so neither repo's code, releases or runs touch the other.

Each video is one release zip holding:
- `src/`: the project's Remotion code (layers, vendored house components, timeline);
- `public/`: footage, photos, docs, maps, audio;
- `video.json`: `{composition, frames, fps}`.

The repo itself only holds the dependencies (`package.json` + lock), the fonts and the workflow.

## Ship

```
python ship.py ..\latam-doc
python ship.py ..\video-a ..\video-b      # one release, one run, 20 chunk jobs split between them
```

`ship.py` runs the type check, probes the composition and zips. Then it creates the release, starts the `Render
Sadat-style videos` workflow and prints the run link. Download the MP4 from that run (artifact `final-<project>`).

## How the workflow renders

- **Picture:** muted frame-range chunks render in parallel and are checked for length and stream damage, retried up to 3×.
- **Sound:** Remotion renders the whole soundtrack once, audio-only, so every `<Audio>` in the TSX lands in the mix
  exactly as Studio plays it: narration, SFX, burn sounds and music. There is no hand-kept mix script.
- **Combine:** the chunks are concatenated without re-encoding and muxed with the sound. Durations are checked
  against `frames / fps`.
- **Re-stitch only:** rerun with `chunks_from_run=<run id>` to reuse the chunks and sound from an earlier run.
- **Fonts:** Bahnschrift maps to Barlow Semi Condensed, and Georgia maps to Gelasio. Google fonts load at render time.
- **Subtitles:** none.
