#!/usr/bin/env python3
"""Audio tests for Taj Mahal via lv2host.

Native:  make && gcc -O2 -Idpf/distrho/src -Idpf/distrho/src/lv2 tools/lv2host.c -o tools/lv2host -ldl
         python3 tools/tmtest.py
ARM:     TM_SO=<arm .so> TM_HOST="qemu-arm -L /usr/arm-linux-gnueabihf <arm lv2host>" python3 tools/tmtest.py
Exit code is the number of failed checks.
"""
import numpy as np, subprocess, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SO = os.environ.get('TM_SO', os.path.join(HERE, '..', 'bin', 'nhe-taj-mahal.lv2', 'nhe-taj-mahal_dsp.so'))
HOST = os.environ.get('TM_HOST', os.path.join(HERE, 'lv2host')).split()
ORDER = ['predelay', 'decay', 'diffusion', 'chorus_speed', 'chorus_depth', 'chorus_feedback',
         'direct', 'reverb_level', 'vintage', 'tails', 'lv2_enabled']
DEF = dict(predelay=81, decay=72, diffusion=9, chorus_speed=61, chorus_depth=31, chorus_feedback=20,
           direct=0, reverb_level=99, vintage=1, tails=1, lv2_enabled=1)
PORT = {s: 3 + i for i, s in enumerate(ORDER)}


def run(x, sr=48000, events=(), **kw):
    p = dict(DEF); p.update(kw)
    with tempfile.TemporaryDirectory() as td:
        fi, fo = os.path.join(td, 'i.raw'), os.path.join(td, 'o.raw')
        x.astype(np.float32).tofile(fi)
        args = HOST + [SO, fi, fo, str(sr), '1', '2'] + [str(p[s]) for s in ORDER]
        args += ['@%d:%d=%g' % (t, PORT[s], v) for (t, s, v) in events]
        subprocess.run(args, check=True)
        y = np.fromfile(fo, dtype=np.float32).reshape(-1, 2)
    return y[:, 0], y[:, 1]


def db(v):
    return 20 * np.log10(max(float(v), 1e-12))


def rms(w, a, b, sr):
    return db(np.sqrt(np.mean(w[int(a * sr):int(b * sr)] ** 2)))


def rt60(l, r, sr):
    e = l ** 2 + r ** 2
    edc = np.cumsum(e[::-1])[::-1]
    edc = 10 * np.log10(edc / edc[0] + 1e-30)
    i5, i35 = np.argmax(edc < -5), np.argmax(edc < -35)
    return (i35 - i5) / sr * 2          # T30, extrapolated to 60 dB


def onset_ms(l, r, sr):
    e = np.abs(l) + np.abs(r)
    return np.argmax(e > e.max() * 0.01) / sr * 1000


fails = []


def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + ('  ' + info if info else ''))
    if not ok:
        fails.append(name)


def finite(*a):
    return all(np.all(np.isfinite(v)) for v in a)


def main():
    rs = np.random.RandomState(3)

    # 1. preset: pre-delay, decay, stability, at every sample rate -------------
    rts = []
    for sr in (44100, 48000, 96000):
        x = np.zeros(sr * 16); x[0] = 1.0
        l, r = run(x, sr)
        t = rt60(l, r, sr); rts.append(t)
        check('preset finite @%d' % sr, finite(l, r))
        check('pre-delay 81 ms @%d' % sr, abs(onset_ms(l, r, sr) - 82) < 2, '%.1f ms' % onset_ms(l, r, sr))
        check('RT60 at Decay 72 @%d' % sr, 4.5 < t < 7.0, '%.2f s' % t)
        check('tail dies out @%d' % sr, np.abs(np.r_[l, r][-sr // 2:]).max() < 1e-6 or
              np.abs(l[-sr // 2:]).max() < 1e-6)
        check('stereo decorrelated @%d' % sr, abs(np.corrcoef(l, r)[0, 1]) < 0.2,
              'corr %+.2f' % np.corrcoef(l, r)[0, 1])
    check('RT60 consistent across rates', max(rts) - min(rts) < 0.6, ' / '.join('%.2f' % t for t in rts))

    # 2. Decay knob is monotonic ------------------------------------------------
    sr = 48000; x = np.zeros(sr * 24); x[0] = 1.0
    ts = [rt60(*run(x, sr, decay=d, vintage=0), sr) for d in (1, 30, 50, 72, 99)]
    check('Decay monotonic', all(a < b for a, b in zip(ts, ts[1:])), ' < '.join('%.2f' % t for t in ts))
    check('Decay range 0.3-25 s', 0.3 < ts[0] < 1.0 and 10 < ts[-1] < 25)

    # 3. level: about unity at full wet -----------------------------------------
    n = np.zeros(sr * 6); n[:sr * 2] = rs.randn(sr * 2) * 0.25
    l, r = run(n, sr)
    lev = rms(l, 0, 2.5, sr)
    check('wet level ~ unity', -16 < lev < -9, 'in -12.0 dBFS -> out %.1f dBFS' % lev)

    # 4. Direct passes dry at unity with Reverb Level 0 -------------------------
    l, r = run(n, sr, direct=99, reverb_level=0)
    check('Direct 99 = dry at unity', np.allclose(l[:sr * 2], n[:sr * 2], atol=1e-5) and
          np.allclose(r[:sr * 2], n[:sr * 2], atol=1e-5))

    # 5. first run: controls start exactly where set, no glide or fade-in ------
    x = np.zeros(sr * 3); x[0] = 1.0
    l, r = run(x, sr, predelay=20)
    check('first run snaps pre-delay (20 ms)', abs(onset_ms(l, r, sr) - 21) < 2, '%.1f ms' % onset_ms(l, r, sr))
    l, r = run(n[:sr], sr, lv2_enabled=0)
    check('starts bypassed: dry at unity from sample 0', np.allclose(l[:4096], n[:4096], atol=1e-5))

    # 6. bypass with Tails on: tail keeps ringing, dry at unity, no click ------
    t = np.arange(sr * 10) / sr
    x = np.zeros(sr * 10); x[:2 * sr] = rs.randn(2 * sr) * 0.25
    x[2 * sr:] += 0.1 * np.sin(2 * np.pi * 220 * t[2 * sr:])          # player keeps playing
    S = 2 * sr
    l, r = run(x, sr, events=[(S, 'lv2_enabled', 0)])
    resid = l - x * (t >= 2.05)
    check('Tails on: tail rings after bypass', rms(resid, 2.5, 4.0, sr) > -40, '%.1f dBFS' % rms(resid, 2.5, 4.0, sr))
    check('Tails on: dry at unity while bypassed', np.allclose(l[3 * sr:3 * sr + 2000] - resid[3 * sr:3 * sr + 2000],
                                                             x[3 * sr:3 * sr + 2000], atol=1e-6))
    # the input itself steps from noise to a sine at S, so allow its own jumps
    jump = np.abs(np.diff(l[S - 100:S + 2000])).max()
    sig = max(np.abs(np.diff(l[S - 3000:S - 100])).max(), np.abs(np.diff(x[S - 100:S + 2000])).max())
    check('Tails on: no click at bypass', jump <= sig * 1.05, 'jump %.3f vs signal %.3f' % (jump, sig))

    # 7. bypass with Tails off: reverb gone, restarts clean --------------------
    l, r = run(x, sr, tails=0, events=[(S, 'lv2_enabled', 0)])
    resid = l - x * (t >= 2.05)
    check('Tails off: reverb cut', rms(resid, 2.5, 4.0, sr) < -100, '%.1f dBFS' % rms(resid, 2.5, 4.0, sr))
    x3 = np.zeros(sr * 6); x3[:sr] = rs.randn(sr) * 0.25
    l, r = run(x3, sr, tails=0, lv2_enabled=0, events=[(3 * sr, 'lv2_enabled', 1)])
    check('Tails off: nothing fed while bypassed', rms(l, 3.05, 5, sr) < -100, '%.1f dBFS' % rms(l, 3.05, 5, sr))

    # 8. knob moves don't blow up; pre-delay sweep stays finite ----------------
    ev = [(int(k * sr / 4), 'predelay', v) for k, v in enumerate([0, 140, 10, 120, 81] * 4)]
    l, r = run(n, sr, events=ev)
    check('pre-delay sweep finite', finite(l, r) and np.abs(l).max() < 4)

    # 9. torture: everything at maximum, loud input, all rates -----------------
    for sr in (44100, 48000, 96000):
        tx = np.zeros(sr * 30); tx[:sr * 5] = rs.randn(sr * 5) * 0.9
        for v in (1, 0):
            l, r = run(tx, sr, predelay=140, decay=99, diffusion=0, chorus_speed=99, chorus_depth=99,
                       chorus_feedback=99, direct=99, reverb_level=99, vintage=v)
            check('torture vintage=%d @%d finite' % (v, sr), finite(l, r) and np.abs(l).max() < 30,
                  'peak %.1f' % np.abs(l).max())

    # 10. silence in, silence out ------------------------------------------------
    sr = 48000
    l, r = run(np.zeros(sr * 3), sr)
    check('silence stays silent', np.abs(np.r_[l, r]).max() < 1e-6)

    print('\n%d failed' % len(fails) if fails else '\nall passed')
    return len(fails)


if __name__ == '__main__':
    sys.exit(main())
