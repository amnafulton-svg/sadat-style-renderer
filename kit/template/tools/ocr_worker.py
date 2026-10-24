"""OCR of one document scan, run inside ~/yt/.venv-ocr (RapidOCR + its own OpenCV/numpy, kept apart from the live
venv). Called by documents.py; not imported by the pipeline.

    .venv-ocr/bin/python ocr_worker.py <image> <out.json>

out.json = {"w", "h", "lines": [{"text", "score", "box": [x0, y0, x1, y1], "words": [{"text", "box"}]}]} in image pixels.
"""
import json
import sys

from PIL import Image
from rapidocr import RapidOCR


def rect(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def main(src, dst):
    with Image.open(src) as im:
        w, h = im.size
    # big newspaper pages: let the detector see more pixels than its default, small type is the point
    engine = RapidOCR(params={"Det.limit_side_len": 2400, "Det.limit_type": "max"})
    r = engine(src, return_word_box=True)
    lines = []
    words_all = r.word_results or [()] * len(r.txts or [])
    for box, text, score, words in zip(r.boxes if r.boxes is not None else [], r.txts or [], r.scores or [], words_all):
        lines.append({
            "text": text, "score": round(float(score), 3), "box": rect(box),
            "words": [{"text": wt, "box": rect(wb)} for wt, _ws, wb in (words or []) if str(wt).strip()],
        })
    with open(dst, "w", encoding="utf-8") as f:
        json.dump({"w": w, "h": h, "lines": lines}, f, ensure_ascii=False)
    print(len(lines), "lines")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
