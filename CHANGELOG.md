# Changelog

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
