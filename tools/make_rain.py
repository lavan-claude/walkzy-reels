#!/usr/bin/env python3
"""Erzeugt Regen-Atmo (Rauschen plus einzelne Tropfen). Aufruf: make_rain.py out.wav dauer_sek"""
import sys, wave, numpy as np
sr = 44100; D = float(sys.argv[2]); n = int(sr * D); rng = np.random.default_rng(3)
def onepole(x, fc):
    a = np.exp(-2 * np.pi * fc / sr); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def stereo():
    w = rng.standard_normal(n)
    hiss = w - onepole(w, 900)            # helles Rauschen
    body = onepole(rng.standard_normal(n), 400) * 2.5  # dumpfes Prasseln
    drops = np.zeros(n)
    for p in rng.integers(0, n - 2000, int(D * 140)):
        k = np.arange(1200); drops[p:p + 1200] += np.sin(2 * np.pi * rng.uniform(1800, 4200) * k / sr) * np.exp(-k / rng.uniform(60, 160)) * rng.uniform(0.05, 0.25)
    return hiss * 0.5 + body * 0.35 + drops
L, R = stereo(), stereo()
t = np.arange(n) / sr; fade = np.minimum(1, np.minimum(t / 0.6, (D - t) / 1.2))
st = np.stack([L * fade, R * fade], 1); st = st / np.max(np.abs(st)) * 0.8
with wave.open(sys.argv[1], "w") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((st * 32767).astype(np.int16).tobytes())
