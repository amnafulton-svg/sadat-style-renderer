"""Procedural textures for the layers (no stock assets needed).

concrete.jpg  dark grunge wall behind print clusters, quote cards and section titles
paper.jpg     cream document paper for label tape lists and date tags
kraft.jpg     brown kraft note paper
newsprint.jpg greyish newspaper stock for the headline sheet
desk.jpg      dark wooden desk under the evidence board
grain_0..7.png  film grain frames (alpha), cycled by the Grain overlay
dust_0..5.png   dust specks / hairs (alpha), flashed by the Dust overlay
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "public/textures")
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 1350
rng = np.random.default_rng(1973)


def fractal(w, h, octaves=6, base=4):
    """sum of upscaled random grids = cheap value noise, 0..1"""
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((max(2, n * h // w), n)).astype(np.float32)
        acc += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        tot += amp
        amp *= 0.55
    return acc / tot


def tint(gray, lo, hi):
    lo, hi = np.array(lo, np.float32), np.array(hi, np.float32)
    return np.clip(lo + gray[..., None] * (hi - lo), 0, 255).astype(np.uint8)


def save(arr, name, q=90):
    Image.fromarray(arr).save(OUT / name, quality=q)
    print("wrote", OUT / name)


# concrete: mottled dark grey, pits, faint stains
g = fractal(W, H, 7, 3)
g = (g - g.min()) / (g.max() - g.min())
pits = rng.random((H, W)) > 0.9985
g[pits] *= 0.35
fine = rng.normal(0, 0.035, (H, W)).astype(np.float32)
c = np.clip(0.18 + 0.32 * g + fine, 0, 1)
stain = fractal(W, H, 3, 2)
c *= 0.8 + 0.3 * stain
save(tint(c, (8, 8, 9), (205, 200, 192)), "concrete.jpg")

# paper: warm cream with fibres
g = fractal(W, H, 6, 6)
fib = rng.normal(0, 0.02, (H, W)).astype(np.float32)
p = np.clip(0.82 + 0.12 * (g - 0.5) + fib, 0, 1)
save(tint(p, (120, 104, 78), (250, 241, 220)), "paper.jpg")

# kraft
g = fractal(W, H, 6, 5)
fib = rng.normal(0, 0.03, (H, W)).astype(np.float32)
k = np.clip(0.6 + 0.2 * (g - 0.5) + fib, 0, 1)
save(tint(k, (70, 45, 20), (215, 170, 115)), "kraft.jpg")

# newsprint
g = fractal(W, H, 6, 6)
fib = rng.normal(0, 0.025, (H, W)).astype(np.float32)
n = np.clip(0.8 + 0.12 * (g - 0.5) + fib, 0, 1)
save(tint(n, (90, 86, 76), (232, 226, 210)), "newsprint.jpg")

# desk: dark wood grain (stretched noise)
g = fractal(W // 12, H, 6, 4)
g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
rings = 0.5 + 0.5 * np.sin(np.linspace(0, 90, H)[:, None] + g * 18)
d = np.clip(0.25 + 0.35 * rings * g + rng.normal(0, 0.02, (H, W)), 0, 1)
save(tint(d, (12, 7, 4), (120, 78, 45)), "desk.jpg")

# grain frames (1920x1080, grey noise in alpha)
for i in range(8):
    nz = rng.normal(0, 1, (540, 960)).astype(np.float32)
    nz = np.asarray(Image.fromarray(np.clip(128 + nz * 60, 0, 255).astype(np.uint8)).resize((1920, 1080), Image.BILINEAR))
    rgba = np.zeros((1080, 1920, 4), np.uint8)
    rgba[..., :3] = nz[..., None]
    rgba[..., 3] = 255
    Image.fromarray(rgba[..., :3]).save(OUT / f"grain_{i}.png")
print("grain done")

# dust: white/black specks and a few hairs on transparent
for i in range(6):
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for _ in range(int(rng.integers(6, 16))):
        x, y = rng.integers(0, 1920), rng.integers(0, 1080)
        r = float(rng.uniform(1, 4.5))
        col = (255, 255, 255, int(rng.integers(120, 230))) if rng.random() < 0.6 else (0, 0, 0, int(rng.integers(120, 220)))
        dr.ellipse([x - r, y - r * rng.uniform(0.5, 1), x + r, y + r], fill=col)
    for _ in range(int(rng.integers(0, 3))):
        x, y = float(rng.integers(100, 1820)), float(rng.integers(100, 980))
        pts = [(x, y)]
        ang = rng.uniform(0, 6.28)
        for _ in range(12):
            ang += rng.normal(0, 0.35)
            x, y = x + 6 * np.cos(ang), y + 6 * np.sin(ang)
            pts.append((x, y))
        dr.line(pts, fill=(235, 235, 235, 170) if rng.random() < 0.5 else (10, 10, 10, 170), width=2)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im.save(OUT / f"dust_{i}.png")
print("dust done")
