#!/usr/bin/env python3
"""
Build a MOD modgui knob filmstrip from two layers:
  body.png   - the knob WITHOUT its marker (square, transparent outside)
  marker.png - the marker alone, same canvas size, drawn at 12 o'clock

The knurl rotates with the knob while the lighting stays fixed: the body is
resampled to polar coordinates, split by angular frequency (harmonics
|k| <= K = broad lighting, kept static; the rest = knurl detail, rotated),
then recombined per frame. The marker is rotated on top.

Usage:
  python3 knob_filmstrip.py body.png marker.png out.png [frames=65] [sweep=270]

Output: one horizontal strip, frames side by side, frame 0 = minimum (7
o'clock for a 270 deg sweep), last = maximum. In the modgui CSS the knob
element's width must equal one frame's width (MOD: frames = strip width /
element width). Quantise afterwards to shrink it (PIL quantize(256) took a
65 x 62px strip from 402 KB to 47 KB with ~3.7/255 mean error).

Requires: numpy, scipy, pillow.
"""
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

body_p, mark_p, out_p = sys.argv[1:4]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 65
SW = float(sys.argv[5]) if len(sys.argv) > 5 else 270.0

body = Image.open(body_p).convert('RGBA')
mark = Image.open(mark_p).convert('RGBA')
S = body.width
UP = 4; SU = S * UP; C = SU / 2                     # work at 4x for clean edges
B = np.asarray(body.resize((SU, SU), Image.LANCZOS)).astype(float) / 255
P = B.copy(); P[..., :3] *= P[..., 3:4]            # premultiplied alpha

NR = int(C) + 2; NA = 2048; K = 3                   # K: harmonics treated as lighting
r = np.arange(NR) + 0.0; th = np.arange(NA) / NA * 2 * np.pi
RR, TT = np.meshgrid(r, th, indexing='ij')
X = C - 0.5 + RR * np.sin(TT); Y = C - 0.5 - RR * np.cos(TT)   # clockwise from 12 o'clock
polar = np.stack([map_coordinates(P[..., c], [Y, X], order=3, mode='nearest') for c in range(4)], -1)
F = np.fft.fft(polar, axis=1); k = np.fft.fftfreq(NA, 1 / NA)
static = np.abs(k) <= K

yy, xx = np.mgrid[0:SU, 0:SU] + 0.5; dx = xx - C; dy = yy - C
rq = np.hypot(dx, dy); tq = np.mod(np.arctan2(dx, -dy), 2 * np.pi) / (2 * np.pi) * NA
alpha_static = P[..., 3]
mark_up = mark.resize((SU, SU), Image.LANCZOS)

frames = []
for i in range(N):
    a = np.deg2rad(-SW / 2 + SW * i / (N - 1))
    ph = np.where(static, 1.0, np.exp(-1j * k * a))
    pol = np.real(np.fft.ifft(F * ph[None, :, None], axis=1))
    polw = np.concatenate([pol, pol[:, :3]], 1)
    out = np.stack([map_coordinates(polw[..., c], [rq, tq], order=1, mode='nearest') for c in range(4)], -1)
    out[..., 3] = alpha_static
    fr = np.clip(out, 0, 1); al = fr[..., 3:4]
    rgb = np.where(al > 1e-4, fr[..., :3] / np.maximum(al, 1e-4), 0)
    img = Image.fromarray((np.dstack([rgb, al]) * 255).round().astype(np.uint8), 'RGBA')
    img.alpha_composite(mark_up.rotate(-np.rad2deg(a), resample=Image.BICUBIC, center=(C, C)))
    frames.append(img.resize((S, S), Image.LANCZOS))

strip = Image.new('RGBA', (S * N, S), (0, 0, 0, 0))
for i, f in enumerate(frames):
    strip.paste(f, (i * S, 0))
strip.save(out_p)
print('wrote', out_p, strip.size, f'{N} frames of {S}x{S}')
