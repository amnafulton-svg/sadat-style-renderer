"""Where the narrator's voice really starts, read from the audio.

Whisper glues the breath before a sentence onto its first word (Hitler's generals 2026-10-26: "The" 132.44-133.12
while the voice starts at 133.05), so a cut on that word's start lands up to a second before the narrator speaks
(producer: "this scene came out early about 1s"). words.py corrects the words with this; fixonset.py and validate
use it on the cuts.
"""
import subprocess
from pathlib import Path

import numpy as np

FR = 0.02  # 20 ms frames


def levels(root):
    """loudness of public/audio/narration.mp3 in dB per 20 ms frame (cached in _cache/voice_db.npy)"""
    root = Path(root)
    mp3 = root / 'public/audio/narration.mp3'
    st = mp3.stat()
    sig = np.array([st.st_size, int(st.st_mtime)], dtype=np.float64)
    cache = root / '_cache/voice_db.npy'
    if cache.exists():
        c = np.load(cache)
        if c[0] == sig[0] and c[1] == sig[1]:
            return c[2:]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp3), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    h = int(16000 * FR)
    n = len(a) // h
    db = 20 * np.log10(np.sqrt((a[:n * h].reshape(n, h) ** 2).mean(1)) + 1)
    cache.parent.mkdir(exist_ok=True)
    np.save(cache, np.concatenate([sig, db]))
    return db


def onset(db, t, look=1.5):
    """the time the voice is up (3 frames within 10 dB of the speech level around t) at or after t; None if silent"""
    i = max(0, int(round(t / FR)))
    ref = np.percentile(db[max(0, i - 150):i + 150], 85)
    seg = db[i:i + int(look / FR)] > ref - 10
    for k in range(len(seg) - 2):
        if seg[k] and seg[k + 1] and seg[k + 2]:
            return round(t + k * FR, 2)
    return None


def fix_words(words, db):
    """move word starts that swallowed a pause to where the voice starts; returns how many moved"""
    n = 0
    for i, w in enumerate(words):
        glued = i == 0 or w['s'] - words[i - 1]['e'] < 0.12
        if not glued or w['e'] - w['s'] < 0.35:
            continue
        o = onset(db, w['s'], look=w['e'] - w['s'])
        if o is not None and o - w['s'] > 0.25:
            w['s'] = round(min(o - 0.03, w['e'] - 0.05), 3)
            n += 1
    return n
