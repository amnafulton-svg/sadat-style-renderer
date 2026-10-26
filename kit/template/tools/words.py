"""Word timings of the narration -> src/lib/words.json (+ transcript.txt with times, for reading).

    python tools/words.py [public/audio/narration.mp3] [--model small]

Needs faster-whisper (pip install faster-whisper). If it lives in a separate folder, set WHISPER_DEPS to it.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if os.environ.get('WHISPER_DEPS'):
    sys.path.insert(0, os.environ['WHISPER_DEPS'])
try:
    from faster_whisper import WhisperModel
except ImportError:
    sys.exit('faster-whisper missing: pip install faster-whisper  (or set WHISPER_DEPS to a folder that has it)')

ap = argparse.ArgumentParser()
ap.add_argument('audio', nargs='?', default=str(ROOT / 'public/audio/narration.mp3'))
ap.add_argument('--model', default='small')
a = ap.parse_args()

m = WhisperModel(a.model, device='cpu', compute_type='int8')
segs, _ = m.transcribe(a.audio, word_timestamps=True, beam_size=5, vad_filter=False)
words, lines, segs_w = [], [], []
for s in segs:
    ws = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for w in (s.words or [])]
    words += ws
    if ws:
        segs_w.append(ws)
        lines.append(f"{ws[0]['s']:8.2f}-{ws[-1]['e']:7.2f}  " + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in ws))
sys.path.insert(0, str(ROOT / 'tools'))
try:  # whisper glues the breath before a sentence onto its first word: start it where the voice starts
    import voice
    print(f'{voice.fix_words(words, voice.levels(ROOT))} word starts moved to where the voice starts')
    lines = [f"{ws[0]['s']:8.2f}-{ws[-1]['e']:7.2f}  " + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in ws) for ws in segs_w]
except Exception as ex:  # noqa: BLE001
    print(f'voice-start correction skipped ({ex})')
json.dump(words, open(ROOT / 'src/lib/words.json', 'w', encoding='utf-8'), ensure_ascii=False)
(ROOT / 'transcript.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'{len(words)} words, last ends {words[-1]["e"] if words else 0}s -> src/lib/words.json, transcript.txt')
