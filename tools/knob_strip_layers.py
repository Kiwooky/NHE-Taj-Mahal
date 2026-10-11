"""Retina knob filmstrip from a static body + a moving layer (both on the same square canvas).
Premultiplied-alpha rotation at 4x supersampling, box-filtered back down: no dark fringes, no palette.
usage: build_strip2x.py static.png moving.png out.png pivot_x pivot_y crop_x0 crop_size frames sweep"""
import sys, numpy as np
from PIL import Image
st, mv, out = sys.argv[1:4]
px, py = float(sys.argv[4]), float(sys.argv[5])          # pivot, edge coordinates (pixel centres at .5)
x0, size, N, SW = int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), float(sys.argv[9])
UP = 4
def premul(im):
    a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255
    a[..., :3] *= a[..., 3:4]; return a
S = premul(Image.open(st)); M = premul(Image.open(mv))
H, W = M.shape[:2]
# 4x upsample each premultiplied channel once (Lanczos), rotate per frame at 4x (bicubic), box-reduce
Mup = [Image.fromarray(M[..., c], 'F').resize((W*UP, H*UP), Image.LANCZOS) for c in range(4)]
frames = []
for i in range(N):
    ang = -SW/2 + SW*i/(N-1)                       # degrees clockwise from 12 o'clock
    rot = np.stack([np.asarray(ch.rotate(-ang, resample=Image.BICUBIC, center=(px*UP, py*UP))) for ch in Mup], -1)
    rot = rot.reshape(H, UP, W, UP, 4).mean(axis=(1, 3))
    rot = np.clip(rot, 0, None); rot[..., :3] = np.minimum(rot[..., :3], rot[..., 3:4]); rot[..., 3] = np.clip(rot[..., 3], 0, 1)
    comp = rot + S * (1 - rot[..., 3:4])           # moving layer over the static body (premultiplied "over")
    comp = comp[x0:x0+size, x0:x0+size]
    al = comp[..., 3:4]
    rgb = np.where(al > 1e-6, comp[..., :3] / np.maximum(al, 1e-6), 0)
    frames.append(np.dstack([np.clip(rgb, 0, 1), al]))
strip = np.concatenate(frames, axis=1)
Image.fromarray((strip * 255 + 0.5).astype(np.uint8), 'RGBA').save(out, optimize=True)
print('wrote', out, strip.shape[1], 'x', strip.shape[0], f'({N} frames of {size}px)')
