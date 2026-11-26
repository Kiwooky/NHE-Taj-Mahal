"""Taj Mahal user manual (PDF), shared by Taj Mahal and Taj Mahal Stereo.

    python3 tools/make_manual.py bundle/nhe-taj-mahal.lv2/modgui/manual.pdf

Reads the versions from both DistrhoPluginInfo.h files and the presets from presets.ttl, and uses the
two rendered face screenshots. Built-in PDF fonts only, so it stays small. Needs reportlab and Pillow.
The stereo bundle gets the same file: `make NAME=nhe-taj-mahal-stereo` copies the mono modgui/ folder
first, and both modgui.ttl files point at modgui/manual.pdf. Rebuild when controls, presets or the
faces change."""
import io, os, re, sys
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image as RLImage, KeepTogether, NextPageTemplate, PageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'bundle', 'nhe-taj-mahal.lv2', 'modgui', 'manual.pdf')


def version(folder):
    t = open(os.path.join(ROOT, 'plugins', folder, 'DistrhoPluginInfo.h')).read()
    return '.'.join(re.search(r'#define TAJ_VERSION\s+(\d+),\s*(\d+),\s*(\d+)', t).groups())


V_MONO, V_STEREO = version('taj-mahal'), version('nhe-taj-mahal-stereo')
FACE = os.path.join(ROOT, 'bundle', 'nhe-taj-mahal.lv2', 'modgui', 'screenshot-tajmahal.png')
FACE_ST = os.path.join(ROOT, 'bundle', 'nhe-taj-mahal-stereo.lv2', 'modgui', 'screenshot-tajmahal.png')

# presets, in presets.ttl order
PRESETS = []
for blk in open(os.path.join(ROOT, 'bundle', 'nhe-taj-mahal.lv2', 'presets.ttl')).read().split('pset:Preset')[1:]:
    lab = re.search(r'rdfs:label "([^"]+)"', blk).group(1)
    vals = {k: float(v) for k, v in re.findall(r'lv2:symbol "(\w+)" ;\s*pset:value ([-\d.]+)', blk)}
    PRESETS.append((lab, vals))

CHARACTER = {
    'Taj Mahal (1988 factory)': 'The original: a long, swimming, fully diffused hall that blooms 81 ms behind the note.',
    'The size of the universe': 'Everything at maximum. An endless wash that never quite lets go.',
    'Big empty room': 'Short and bare, with a slow, deep, heavily fed-back chorus. A seasick room.',
    'Negative reflections': 'Shortest decay, longest pre-delay, deepest chorus: a single wobbling slap.',
    'Houses of Worship': 'A slow, deep chorus into a long hall that arrives late. Stone and candles.',
    'No place too big': 'The factory hall again, saved as the one to blend under your playing: turn Dry Level up.',
    'Spacy strummer': 'A shorter, half-diffused space that keeps strummed chords clear.',
}

# ---------------------------------------------------------------- look
INK = colors.HexColor('#1b1c20'); ACC = colors.HexColor('#0088ff'); MUTE = colors.HexColor('#5d606b')
RULE = colors.HexColor('#d9dbe0'); TINT = colors.HexColor('#eef5ff'); PANEL = colors.HexColor('#202124')

body = ParagraphStyle('b', fontName='Helvetica', fontSize=9.6, leading=13.8, textColor=INK, spaceAfter=5)
small = ParagraphStyle('s', parent=body, fontSize=8.2, leading=11.2, textColor=MUTE)
h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=ACC, spaceBefore=10,
                    spaceAfter=5, keepWithNext=1)
h3 = ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=10.4, leading=14, textColor=INK, spaceBefore=6,
                    spaceAfter=3, keepWithNext=1)
bullet = ParagraphStyle('bl', parent=body, leftIndent=11, bulletIndent=1, spaceAfter=3)
cell = ParagraphStyle('c', parent=body, fontSize=8.8, leading=11.8, spaceAfter=0)
cellb = ParagraphStyle('cb', parent=cell, fontName='Helvetica-Bold')
cellc = ParagraphStyle('cc', parent=cell, alignment=1)
cellbc = ParagraphStyle('cbc', parent=cellb, alignment=1)

M = 18 * mm
W = A4[0] - 2 * M
BAND = 64 * mm          # dark title band on page 1


def jpeg(path, width_px):
    """Face screenshot as a small JPEG (the PNGs are ~150 KB each)."""
    im = Image.open(path).convert('RGB')
    im = im.resize((width_px, round(width_px * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=80, optimize=True); b.seek(0)
    return b, im.width, im.height


def first_page(c, doc):
    c.saveState()
    c.setFillColor(PANEL); c.rect(0, A4[1] - BAND, A4[0], BAND, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - BAND, A4[0], 1.4 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.setFont('Helvetica-Bold', 34)
    c.drawString(M, A4[1] - 26 * mm, 'TAJ MAHAL')
    c.setFillColor(colors.white); c.setFont('Helvetica', 11)
    c.drawString(M, A4[1] - 34 * mm, 'NEW HORIZON ELECTRONICS')
    c.setFillColor(colors.HexColor('#c9ccd4')); c.setFont('Helvetica', 12.5)
    c.drawString(M, A4[1] - 46 * mm, 'One preset from 1988. A whole cathedral of chorused air.')
    c.setFont('Helvetica', 8.6); c.setFillColor(colors.HexColor('#8d919c'))
    c.drawString(M, A4[1] - 55 * mm, 'User manual  ·  Taj Mahal %s  ·  Taj Mahal Stereo %s  ·  MOD Duo, Duo X and Dwarf'
                 % (V_MONO, V_STEREO))
    footer(c, doc)
    c.restoreState()


def footer(c, doc):
    c.saveState()
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 13 * mm, A4[0] - M, 13 * mm)
    c.setFont('Helvetica', 7.6); c.setFillColor(MUTE)
    c.drawString(M, 9 * mm, 'Taj Mahal by New Horizon Electronics  ·  github.com/Kiwooky/NHE-Taj-Mahal')
    c.drawRightString(A4[0] - M, 9 * mm, str(doc.page))
    c.restoreState()


def later_page(c, doc):
    footer(c, doc)


S = []
P = lambda t, st=body: S.append(Paragraph(t, st))


def B(items):
    for t in items:
        S.append(Paragraph(t, bullet, bulletText='•'))


def T(rows, widths, head=True, center_cols=()):
    data = []
    for i, r in enumerate(rows):
        line = []
        for j, cv in enumerate(r):
            if head and i == 0:
                st = cellbc if j in center_cols else cellb
            else:
                st = cellb if j == 0 else (cellc if j in center_cols else cell)
            line.append(Paragraph(cv, st))
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), 0.4, RULE),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    if head:
        st += [('BACKGROUND', (0, 0), (-1, 0), TINT)]
    t.setStyle(TableStyle(st))
    return t


def face(path, w_mm):
    b, pw, ph = jpeg(path, 900)
    w = w_mm * mm
    return RLImage(b, width=w, height=w * ph / pw)


# ---------------------------------------------------------------- page 1
S.append(Spacer(1, BAND - M + 4 * mm))
S.append(face(FACE, 150)); S.append(Spacer(1, 8))
P('Taj Mahal is a huge, washy hall reverb with a slow stereo chorus in front of it. It recreates the famous '
  '"Taj Mahal" factory preset of a classic 1988 rack multi-effect: every note is detuned and spread before it '
  'reaches the room, so the tail shimmers and swims instead of simply fading. The knobs use the original\'s '
  '0&ndash;99 scales, so the factory numbers drop straight in, and they are where the plugin starts.')

P('Quick start', h2)
for i, t in enumerate([
        'Add <b>Taj Mahal</b> to your pedalboard: your instrument into <b>In</b>, <b>Out L</b> and <b>Out R</b> to '
        'your outputs. For a stereo source, use <b>Taj Mahal Stereo</b> (page 3).',
        'It starts 100% wet, like the original sitting in an effects loop. Inline after your other effects, turn '
        '<b>Dry Level</b> up to about 99 and set the reverb with <b>Reverb Level</b>.',
        'Assign <b>On/Off</b> to a footswitch: open the plugin\'s settings (the gear icon), click the assignment '
        'button next to On/Off and pick a footswitch.',
        'With <b>Tails</b> on, switching it off lets the hall ring out naturally. Switch Tails off to cut it dead.',
        'Try the presets: click the plugin\'s preset list. They change the sound, never your dry/wet balance.'], 1):
    S.append(Paragraph(t, bullet, bulletText='%d.' % i))

# ---------------------------------------------------------------- controls
S.append(PageBreak())
P('The controls', h2)
P('The knobs are grouped like the face: the reverb on the left, the chorus on the right, the mix bottom right. '
  'Everything can be changed while you play; Pre-delay glides rather than jumps, like tape speeding up or slowing down.')
cw = [28 * mm, 20 * mm, 17 * mm, W - 65 * mm]
P('Reverb', h3)
S.append(T([
    ['Knob', 'Range', 'Start', 'What it does'],
    ['Pre-delay', '0&ndash;140 ms', '81', 'The gap before the room answers. Longer keeps the note clear and lets the '
     'hall bloom behind it; 0 puts the reverb right on top of the note.'],
    ['Decay', '1&ndash;99', '72', 'How long the hall rings, from about 0.3 s at 1 to about 16 s at 99. 72 is '
     'about 5.5 s. The scale is exponential: each 10 steps adds roughly half again.'],
    ['Diffusion', '0&ndash;9', '9', 'How much the first reflections are smeared. 9 is a smooth wash; 0 lets '
     'separate echoes through, for a grainier, more metallic room.'],
], cw, center_cols=(1, 2)))
P('Chorus', h3)
S.append(T([
    ['Knob', 'Range', 'Start', 'What it does'],
    ['Speed', '0&ndash;99', '61', 'Chorus rate, 0.1 Hz to 10 Hz on an exponential scale. 61 is about 1.7 Hz.'],
    ['Depth', '0&ndash;99', '31', 'How far the pitch wobbles, up to &plusmn;4 ms of delay swing. 0 switches the '
     'movement off, leaving a plain hall.'],
    ['Feedback', '0&ndash;99 %', '20', 'Feeds the chorus back into itself: more metallic, more flanger-like. '
     'Capped below runaway.'],
], cw, center_cols=(1, 2)))
P('Mix', h3)
S.append(T([
    ['Knob', 'Range', 'Start', 'What it does'],
    ['Dry Level', '0&ndash;99', '0', 'Your dry signal. 0 is 100% wet (the 1988 preset); 99 is full level, for '
     'using Taj Mahal inline.'],
    ['Reverb Level', '0&ndash;99', '99', 'The reverb. 99 sits at about the same loudness as the dry signal.'],
], cw, center_cols=(1, 2)))
P('Switches', h3)
S.append(T([
    ['Switch', 'Start', 'What it does'],
    ['On/Off', 'On', 'The effect on or off. Off passes your dry signal at full level, whatever Dry Level is set to.'],
    ['Vintage', 'On', 'The original\'s grit: the reverb is stored at 16-bit precision and the wet signal saturates '
     'gently (about 1% distortion at full level), like its converters. Off is clean and modern.'],
    ['Tails', 'On', 'What happens when you switch the effect off. On: the input stops but the hall rings out '
     'naturally. Off: the reverb is cut and cleared, so it starts fresh next time.'],
], [28 * mm, 17 * mm, W - 45 * mm], center_cols=(1,)))

P('On/Off and Tails in detail', h3)
S.append(T([
    ['State', 'Into the reverb', 'Reverb you hear', 'Dry signal'],
    ['On', 'yes', 'Reverb Level', 'Dry Level'],
    ['Off, Tails on', 'no', 'Reverb Level, ringing out', 'full'],
    ['Off, Tails off', 'no', 'none (cleared)', 'full'],
], [34 * mm, 30 * mm, 46 * mm, W - 110 * mm]))
P('Every change fades over about 10 ms, so the footswitch never pops. Because the plugin handles On/Off itself '
  '(so it can ring out), it keeps using its share of the processor while switched off.', small)

# ---------------------------------------------------------------- presets + stereo
S.append(PageBreak())
P('Factory presets', h2)
P('Seven presets: the 1988 original plus six new spaces. They set every reverb and chorus control and both '
  'switches, but never <b>Dry Level</b>, <b>Reverb Level</b> or <b>On/Off</b>: loading one keeps your dry/wet '
  'balance and never switches the effect on or off.')
rows = [['Preset', 'Pre-delay', 'Decay', 'Diff.', 'Speed', 'Depth', 'Fdbk', 'Sound']]
for lab, v in PRESETS:
    g = lambda k: '%d' % round(v.get(k, 0))
    rows.append([lab, g('predelay'), g('decay'), g('diffusion'), g('chorus_speed'), g('chorus_depth'),
                 g('chorus_feedback'), CHARACTER.get(lab, '')])
n = 13 * mm
S.append(T(rows, [31 * mm, 17 * mm, n, n, n, n, n, W - 48 * mm - 5 * n], center_cols=(1, 2, 3, 4, 5, 6)))
P('All seven have Vintage and Tails on.', small)

P('Taj Mahal Stereo', h2)
S.append(KeepTogether([face(FACE_ST, 110), Spacer(1, 6)]))
P('For stereo sources, such as a keyboard, a stereo chorus or delay, or a whole stereo mix, there is a second '
  'plugin: <b>Taj Mahal Stereo</b>. Stereo in, stereo out, the same controls and the same presets, with a STEREO '
  'badge on the face.')
B(['The left input runs through its own chorus into one half of the reverb, the right input into the other. The '
   'two sides of your source stay distinct in the tail, while each still spreads across both outputs.',
   'The dry signal stays on its own side, also when the effect is off.',
   'There is no mono/stereo switch: patch one source into both inputs and it sounds exactly like Taj Mahal.'])
P('Which one?', h3)
P('A guitar or a voice, straight in: <b>Taj Mahal</b>. Anything already in stereo: <b>Taj Mahal Stereo</b>. '
  'Both cost about the same on the processor.')

# ---------------------------------------------------------------- tips + about
P('Tips', h2)
B(['<b>Ambient swells:</b> put a volume pedal or swell before Taj Mahal, Decay 85 or more, Dry Level 0. Play, '
   'fade in, let it hang.',
   '<b>Hands on the knobs:</b> assign Decay or Reverb Level to an expression pedal or a MIDI knob in the plugin '
   'settings. Decay changes reach the existing tail, so you can stretch or shrink it as it rings.',
   '<b>Freeze-ish:</b> Decay 99, then switch off with Tails on. The input stops and the hall carries on for '
   'many seconds.',
   '<b>Clean and modern:</b> Vintage off removes the 16-bit grain and saturation, for a cleaner tail under '
   'pianos and pads.',
   '<b>In a loop or not:</b> after a delay, a looper or a mixer send, keep it 100% wet (Dry Level 0). Inline, '
   'set Dry Level 99 and Reverb Level to taste.'])

P('Specifications', h3)
S.append(T([
    ['Inputs / outputs', 'Taj Mahal: 1 in, 2 out. Taj Mahal Stereo: 2 in, 2 out.'],
    ['Sample rates', 'Any rate from 44.1 kHz up, with the same decay times at every rate.'],
    ['Latency', 'None (pre-delay is part of the sound, not latency).'],
    ['Platforms', 'MOD Duo, Duo X and Dwarf.'],
], [34 * mm, W - 34 * mm], head=False))

P('About', h3)
P('Taj Mahal is an independent recreation, by ear and by design, of a factory preset from a 1988 rack reverb. '
  'It is not affiliated with or endorsed by that unit\'s maker. Code: MIT licence. Artwork &copy; New Horizon '
  'Electronics. Built with DPF (DISTRHO Plugin Framework, ISC licence). Source, issues and changes: '
  'github.com/Kiwooky/NHE-Taj-Mahal.', small)

# ---------------------------------------------------------------- build
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=18 * mm,
                      title='Taj Mahal user manual', author='New Horizon Electronics',
                      subject='Taj Mahal and Taj Mahal Stereo for MOD')
frame = Frame(M, 18 * mm, W, A4[1] - M - 18 * mm, id='f', leftPadding=0, rightPadding=0, topPadding=0,
              bottomPadding=0)
doc.addPageTemplates([PageTemplate('first', [frame], onPage=first_page),
                      PageTemplate('later', [frame], onPage=later_page)])
S.insert(0, NextPageTemplate('later'))
doc.build(S)
print('%s: %d KB' % (OUT, os.path.getsize(OUT) // 1024))
