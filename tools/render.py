#!/usr/bin/env python3
"""Render the pedal face's screenshot and thumbnail from the built bundle.

Run `make` first, then:  python3 tools/render.py
Writes bundle/nhe-taj-mahal.lv2/modgui/screenshot-tajmahal.png and
thumbnail-tajmahal.png (rebuild afterwards to copy them into bin/).
The face is shown at the factory "Taj Mahal" preset, all buttons on.
Needs playwright (Chromium) and pillow.
"""
import re, os, asyncio
from playwright.async_api import async_playwright
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, 'bin', 'nhe-taj-mahal.lv2', 'modgui')
OUT = os.path.join(ROOT, 'bundle', 'nhe-taj-mahal.lv2', 'modgui')

html = open(R + '/icon-tajmahal.html').read()
css = open(R + '/stylesheet-tajmahal.css').read()
html = re.sub(r'\{\{#effect.*?\{\{/effect[^}]*\}\}', '', html, flags=re.S)
html = html.replace('{{{cns}}}', '').replace('{{{ns}}}', '')
css = css.replace('{{{cns}}}', '').replace('{{{ns}}}', '').replace('/resources/', 'file://' + R + '/')

FRAMES, KW = 65, 62          # knob strip: 65 frames of 62 px


def knob(v, lo, hi):
    return '-%dpx 0' % (round((v - lo) / (hi - lo) * (FRAMES - 1)) * KW)


preset = {'predelay': (81, 0, 140), 'decay': (72, 1, 99), 'diffusion': (9, 0, 9),
          'chorus_speed': (61, 0, 99), 'chorus_depth': (31, 0, 99), 'chorus_feedback': (20, 0, 99),
          'direct': (0, 0, 99), 'reverb_level': (99, 0, 99)}
extra = ''.join('.tajmahal .tm-%s{background-position:%s}' % (k, knob(*v)) for k, v in preset.items())
extra += '.tajmahal .tm-button{background-position:-95px 0}'      # LEDs lit
page = '<html><head><style>body{margin:0;background:transparent}%s%s</style></head><body>%s</body></html>' % (css, extra, html)
tmp = os.path.join(ROOT, 'build', 'face.html')
os.makedirs(os.path.dirname(tmp), exist_ok=True)
open(tmp, 'w').write(page)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 600, 'height': 350})
        await pg.goto('file://' + tmp)
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(ROOT, 'build', 'screenshot_full.png'), omit_background=True)
        await b.close()

asyncio.run(main())
im = Image.open(os.path.join(ROOT, 'build', 'screenshot_full.png')).convert('RGB')
im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(
    OUT + '/screenshot-tajmahal.png', optimize=True)
t = im.copy(); t.thumbnail((256, 64), Image.LANCZOS); t.save(OUT + '/thumbnail-tajmahal.png', optimize=True)
print('screenshot and thumbnail written to', OUT)
