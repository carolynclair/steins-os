#!/usr/bin/env python3
"""Original quiet design earcons. Writes WAV assets; never plays audio or configures the OS.

Code: MIT. Generated original audio: CC-BY-4.0, Steins;OS contributors.
No samples, recordings, copyrighted melodies, voices or external dependencies.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import wave

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audio'
RATE = 48000
OUT.mkdir(parents=True, exist_ok=True)


def envelope(t, duration, attack=.015, release=.035):
    if t < 0 or t >= duration:
        return 0.0
    a = .5 - .5 * math.cos(math.pi * min(1.0, t / attack))
    r = .5 - .5 * math.cos(math.pi * min(1.0, (duration - t) / release))
    return a * r


def cue(duration, kind):
    rng = random.Random({'activation': 5100, 'meter': 198306, 'stabilise': 1048596}[kind])
    values = []
    smooth = 0.0
    for i in range(round(duration * RATE)):
        t = i / RATE
        if kind == 'activation':
            value = math.sin(2 * math.pi * (420*t + 180*t*t)) + .17*math.sin(2*math.pi*840*t)
        elif kind == 'meter':
            smooth = .94 * smooth + .06 * rng.uniform(-1, 1)
            value = .8*math.sin(2*math.pi*310*t) + .2*math.sin(2*math.pi*625*t) + .15*smooth
        else:
            value = .7*math.sin(2*math.pi*554.365*t) + .3*math.sin(2*math.pi*369.994*t)
        values.append(value * envelope(t, duration) * math.exp(-2.8*t/duration))
    peak = max(abs(v) for v in values) or 1
    return [v * .035 / peak for v in values]


def write(name, values, purpose):
    # Quiet digital headroom, not a calibrated acoustic-level guarantee.
    peak = max(abs(v) for v in values) or 1e-12
    assert peak <= 10 ** (-26/20) + 1e-9
    data = b''.join(struct.pack('<h', round(max(-1,min(1,v))*32767)) for v in values)
    path = OUT / name
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(RATE); wav.writeframes(data)
    rms = math.sqrt(sum(v*v for v in values) / len(values)) or 1e-12
    return {'file':name, 'purpose':purpose, 'sample_rate_hz':RATE, 'channels':1, 'bits':16,
            'frames':len(values), 'duration_ms':round(1000*len(values)/RATE),
            'peak_dbfs':round(20*math.log10(peak),2), 'rms_dbfs':round(20*math.log10(rms),2),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


activation = cue(.09, 'activation')
meter = cue(.16, 'meter')
stabilise = cue(.18, 'stabilise')
preview = [0.0] * round(.8*RATE)
for offset, source in [(0, activation), (.09, meter), (.62, stabilise)]:
    for i, value in enumerate(source):
        at = round(offset*RATE) + i
        if at < len(preview): preview[at] += value
manifest = {
    'status':'design_previews_not_system_configuration',
    'provenance':'Original deterministic synthesis using Python standard library; no input recordings or external samples.',
    'license':'CC-BY-4.0', 'attribution':'Steins;OS contributors',
    'playback':'Not played by the generator. User-controlled preview only; production audio defaults off.',
    'files':[
        write('activation.wav',activation,'One warm activation touch'),
        write('meter.wav',meter,'One resonant movement texture for all tubes'),
        write('stabilise.wav',stabilise,'One successful-stabilisation cue'),
        write('shift-preview.wav',preview,'800ms assembled design exploration')
    ]
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
