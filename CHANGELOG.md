# Changelog

## Desktop builds — unreleased (both plugins)

- DPF updated to 4238e1c (Oct 2025), which adds the AU target.
- `make desktop` builds VST3 and CLAP, plus AU on macOS (`make desktop NAME=nhe-taj-mahal-stereo`
  for the stereo plugin). `make` still builds the LV2 for MOD.
- Factory presets are also built into the plugin source, so VST3, AU and CLAP hosts list them.
  MOD keeps reading `presets.ttl`; `tools/tmtest.py` fails if the two drift apart.
- Buffers are sized for the host's actual sample rate (up to 384 kHz). Before, anything above
  96 kHz was clamped, which halved the pre-delay and decay at 176.4/192 kHz.
  LV2 output at 44.1, 48 and 96 kHz is bit-identical to 1.0.2.
- Permanent desktop IDs: maker `Nhzn`; plugins `TjMh` (mono) and `TjMs` (stereo).

## Taj Mahal Stereo 1.0.0 — unreleased

- New plugin in the same repo: **Taj Mahal Stereo** (`https://github.com/Kiwooky/NHE-Taj-Mahal/stereo`,
  bundle `nhe-taj-mahal-stereo.lv2`), stereo in, stereo out, with its own package file
  `mod-plugin-builder/nhe-taj-mahal-stereo/nhe-taj-mahal-stereo.mk`.
- Same source as the mono plugin (`#if DISTRHO_PLUGIN_NUM_INPUTS == 2`): one chorus line per input,
  left into tank half A, right into half B, dry kept per side. The same signal on both inputs gives
  the mono plugin's output exactly, so there's no input-mode switch.
- Same controls and seven factory presets; the face is Niels's stereo panel (STEREO badge by the maker name).
- Free and MIT like the mono plugin. `tools/tmtest_stereo.py` tests it (native and Duo).
- The mono plugin's output is unchanged (checked bit for bit against 1.0.2); its strings moved into
  `DistrhoPluginInfo.h` so both builds share one source.

## 1.0.2 — 2026-10-11

- Retina face: every image is now 2x and full colour, drawn at the same 600 x 350 size.
  - Knob: 65 frames of 124 px built from the new static body and moving knurl/marker layers
    (`assets/source/knob_*@2x.png`, `tools/knob_strip_layers.py`). Replaces the 256-colour strip.
  - Background: face v4 at 1200 x 700. Buttons: v2 at 2x (strip 380 x 58).
  - Screenshot and thumbnail re-rendered in full colour; `tools/render.py` no longer reduces to 256 colours.

## 1.0.1 — 2026-10-04

- Seven factory presets: Taj Mahal (1988 factory), The size of the universe, Big empty room,
  Negative reflections, Houses of Worship, No place too big, Spacy strummer. They set every
  knob and switch except bypass, so loading one never switches the effect on or off.

## 1.0.0 — 2026-10-04

First release under its own identity (URI `https://github.com/Kiwooky/NHE-Taj-Mahal`,
bundle `nhe-taj-mahal.lv2`, maker New Horizon Electronics). Carries everything from the
cookbook prototype (`urn:mod-cookbook:taj-mahal`, v1.0.0–1.0.2):

- Chorused hall reverb modelled on the "Taj Mahal" factory preset: stereo triangle-LFO chorus
  with feedback, pre-delay up to 140 ms, diffused figure-eight tank, knobs on the original's
  0–99 / 0–9 scales with the preset as defaults.
- Vintage mode: 16-bit tank storage and gentle saturation (about 1 % THD at full scale).
- Bypass handled in the plugin, with a Tails switch: ring out, or cut and clear.
- Pedal face (600 × 350) with a knurled knob that turns under fixed lighting.

Changes since the prototype:

- Controls now take effect from the very first audio block: no pre-delay glide or bypass
  fade when a pedalboard loads.
- Vintage and Tails use MOD's switch widget, so a click always toggles them.
