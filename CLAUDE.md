# sadat-style-renderer

Two things live here:

1. **The render farm**: `ship.py` + `.github/workflows/render.yml` render any Sadat-style project on GitHub Actions
   (one release + one run per ship, sound per chunk). The producer downloads the MP4 from the run.
2. **The kit**: `kit/template/` (Remotion project + tools), `kit/new_video.py` (starts a video) and the
   **sadat-style-video** skill in `.claude/skills/`. Any Claude Code account can make a video with it:
   clone this repo, run `python kit/new_video.py <name> <script> <voice-over>`, open the new folder and follow the skill.

Never render unless the producer asks. Never edit `kit/template` for one video's needs; edit the video's own folder.
