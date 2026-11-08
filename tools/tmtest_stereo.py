#!/usr/bin/env python3
"""Audio tests for Taj Mahal Stereo (2 in, 2 out) via lv2host. The DSP itself is tested by
tmtest.py on the mono plugin; this checks what the stereo build adds.

The promises:
  - the same signal on both inputs is the mono plugin, exactly (so there's no mono/stereo switch:
    patch one source into both inputs);
  - the dry path keeps left and right apart, also when bypassed;
  - left and right inputs really reach the tank differently (L feeds half A, R feeds half B),
    and both outputs hear both inputs through the tank.

Native:  make && make NAME=nhe-taj-mahal-stereo
         gcc -O2 -Idpf/distrho/src -Idpf/distrho/src/lv2 tools/lv2host.c -o tools/lv2host -ldl
         python3 tools/tmtest_stereo.py
ARM:     TM_SO=<arm stereo .so> TM_SO_MONO=<arm mono .so> \
         TM_HOST="qemu-arm -L /usr/arm-linux-gnueabihf <arm lv2host>" python3 tools/tmtest_stereo.py
Exit code is the number of failed checks.
"""
import numpy as np, subprocess, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, '..', 'bin')
SO = os.environ.get('TM_SO', os.path.join(BIN, 'nhe-taj-mahal-stereo.lv2', 'nhe-taj-mahal-stereo_dsp.so'))
SO_MONO = os.environ.get('TM_SO_MONO', os.path.join(BIN, 'nhe-taj-mahal.lv2', 'nhe-taj-mahal_dsp.so'))
HOST = os.environ.get('TM_HOST', os.path.join(HERE, 'lv2host')).split()
ORDER = ['predelay', 'decay', 'diffusion', 'chorus_speed', 'chorus_depth', 'chorus_feedback',
         'direct', 'reverb_level', 'vintage', 'tails', 'lv2_enabled']
DEF = dict(predelay=81, decay=72, diffusion=9, chorus_speed=61, chorus_depth=31, chorus_feedback=20,
           direct=0, reverb_level=99, vintage=1, tails=1, lv2_enabled=1)
SR = 48000
fails = 0


def run(x, sr=SR, events=(), so=None, **kw):
    """x: (n,) for the mono plugin or (n, 2) for the stereo one. Returns (n, 2)."""
    so = so or SO
    ni = 1 if x.ndim == 1 else 2
    p = dict(DEF); p.update(kw)
    port = {s: ni + 2 + i for i, s in enumerate(ORDER)}
    with tempfile.TemporaryDirectory() as td:
        fi, fo = os.path.join(td, 'i.raw'), os.path.join(td, 'o.raw')
        np.ascontiguousarray(x, dtype=np.float32).tofile(fi)
        args = HOST + [so, fi, fo, str(sr), str(ni), '2'] + [str(p[s]) for s in ORDER]
        args += ['@%d:%d=%g' % (t, port[s], v) for (t, s, v) in events]
        subprocess.run(args, check=True)
        return np.fromfile(fo, dtype=np.float32).reshape(-1, 2)


def check(name, ok, info=''):
    global fails
    print('%s %s  %s' % ('PASS' if ok else 'FAIL', name, info))
    fails += 0 if ok else 1


def db(v):
    return 20 * np.log10(max(float(v), 1e-12))


def rms(w):
    return db(np.sqrt(np.mean(np.asarray(w, dtype=np.float64) ** 2)))


def plucks(sr, secs, notes=(196, 262, 330, 147, 392), every=0.9, seed=1):
    t = np.arange(int(sr * secs)) / sr
    y = np.zeros_like(t)
    for k, f in enumerate(notes * 20):
        t0 = 0.05 + k * every
        if t0 >= secs: break
        m = t >= t0
        tt = t[m] - t0
        y[m] += 0.3 * np.exp(-tt * 3.0) * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
    return y.astype(np.float32)


st = lambda a, b: np.stack([a, b], axis=1)
xa = plucks(SR, 6.0)
xb = plucks(SR, 6.0, notes=(330, 147, 262, 196, 110), every=1.1)
z = np.zeros_like(xa)
LSB24 = 2.0 ** -23

# --- same signal on both inputs = the mono plugin ------------------------------------------
CASES = [dict(), dict(vintage=0), dict(direct=60, reverb_level=50), dict(decay=99, diffusion=3),
         dict(chorus_feedback=99, chorus_depth=99, chorus_speed=99), dict(predelay=0, decay=1)]
for kw in CASES:
    ym = run(xa, so=SO_MONO, **kw)
    ys = run(st(xa, xa), **kw)
    d = np.abs(ym - ys).max()
    check('same signal on both inputs = the mono plugin: %s' % (kw or 'defaults'), d < LSB24, 'max diff %.2g' % d)
ev = [(SR, 'decay', 30), (2 * SR, 'chorus_depth', 90), (3 * SR, 'lv2_enabled', 0), (4 * SR, 'lv2_enabled', 1),
      (int(4.5 * SR), 'tails', 0), (5 * SR, 'lv2_enabled', 0)]
d = np.abs(run(xa, so=SO_MONO, events=ev) - run(st(xa, xa), events=ev)).max()
check('...also through live changes, bypass and tails', d < LSB24, 'max diff %.2g' % d)

# --- dry path keeps the sides apart -----------------------------------------------------------
y = run(st(xa, xb), direct=99, reverb_level=0)
check('dry only: out L = in L and out R = in R, exactly',
      np.array_equal(y[:, 0], xa) and np.array_equal(y[:, 1], xb))
y = run(st(xa, xb), events=[(SR, 'lv2_enabled', 0)], tails=0)
n = 2 * SR
# (the 10 ms bypass fade settles about 1e-5 short of unity, -100 dB: the mono plugin does the same)
d = max(np.abs(y[n:, 0] - xa[n:]).max(), np.abs(y[n:, 1] - xb[n:]).max())
check('bypassed, tails off: in L -> out L, in R -> out R (within -90 dB)', d < 10 ** (-90 / 20), 'max diff %.2g' % d)
y = run(st(xa, z), events=[(SR, 'lv2_enabled', 0)], tails=1, direct=0)
yt = run(st(xa, z), tails=1, direct=0)
check('bypassed, tails on: dry L stays on the left (right side is reverb tail only)',
      rms(y[3 * SR:, 1]) < rms(yt[3 * SR:, 1]) - 12, 'R tail %.1f dB vs playing %.1f dB'
      % (rms(y[3 * SR:, 1]), rms(yt[3 * SR:, 1])))

# --- the inputs reach the tank differently, both outputs hear both ---------------------------
yl = run(st(xa, z))
yr = run(st(z, xa))
for name, y in (('left-only input', yl), ('right-only input', yr)):
    check('%s: reverb on both outputs' % name, abs(rms(y[:, 0]) - rms(y[:, 1])) < 6,
          'L %.1f dB, R %.1f dB' % (rms(y[:, 0]), rms(y[:, 1])))
corr = np.corrcoef(yl[:, 0], yr[:, 0])[0, 1]
check('left-only and right-only inputs give different reverbs', abs(corr) < 0.5, 'correlation %.2f' % corr)
lin = run(st(xa, xb), vintage=0); sep = run(st(xa, z), vintage=0) + run(st(z, xb), vintage=0)
d = np.abs(lin - sep).max()
check('Vintage off: both inputs together = the sum of each alone (nothing cross-talks)', d < 1e-4,
      'max diff %.2g' % d)

# --- rates, extremes, silence -------------------------------------------------------------------
for sr in (44100, 96000):
    a = plucks(sr, 3.0); b = plucks(sr, 3.0, notes=(330, 110), every=1.3)
    y = run(st(a, b), sr=sr)
    check('%d Hz: finite and level sane' % sr, np.isfinite(y).all() and np.abs(y).max() < 4,
          'peak %.1f dBFS' % db(np.abs(y).max()))
noise = (np.random.default_rng(3).standard_normal((SR * 4, 2)) * 0.5).astype(np.float32)
y = run(noise, decay=99, chorus_feedback=99, chorus_depth=99, diffusion=9, reverb_level=99, direct=99)
check('extremes, loud uncorrelated noise: finite', np.isfinite(y).all(), 'peak %.1f dBFS' % db(np.abs(y).max()))
y = run(np.zeros((SR * 2, 2), np.float32))
check('silence stays silent', np.abs(y).max() < 1e-6, 'peak %.2g' % np.abs(y).max())

print('\nall passed' if fails == 0 else '\n%d FAILED' % fails)
sys.exit(fails)
