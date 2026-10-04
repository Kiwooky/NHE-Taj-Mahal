# Sound and design

## The source

The "Taj Mahal" factory preset of a classic 1988 rack multi-effect, as reported by owners:

| Setting | Value |
| --- | --- |
| Algorithm | Hall reverb |
| Decay | 72 / 99 |
| Pre-delay | 81 ms |
| Diffusion | 9 / 9 (maximum) |
| EQ | low 200 Hz, mid 2 kHz, high 8 kHz (gains not known, so left out) |
| Modulation | stereo chorus, triangle LFO, speed 61 / 99, depth 31 / 99, feedback 20 % |
| Mix | direct 0 / 99 (100 % wet), reverb level 99 / 99 |

The original runs on a custom DSP whose program was never published, so this is an emulation by ear and by design, not a bit-exact copy. Alesis-era reverbs were built from allpass loops with mostly 0.5 coefficients, which gives a slow, "building" swell; the design below aims for that character.

## Signal flow

mono in → **stereo chorus** (triangle LFO, left and right taps 180° apart, feedback) → **pre-delay** (smoothed; the chorus's own 8 ms base delay is subtracted so 81 ms means 81 ms) → **input bandwidth filter** (9 kHz) and **four input diffusers per side** → **figure-eight tank** (Dattorro topology: modulated allpasses, delays, 5 kHz damping; left feeds half A, right feeds half B) → **Dattorro output taps** → optional **Vintage** colour → dry/wet with the bypass and tails gains → stereo out.

## Knob mappings

The hardware's 0–99 scales aren't documented in seconds or hertz, so these are chosen to sound right and land the preset in a sensible place:

| Knob | Mapping | Preset value |
| --- | --- | --- |
| Decay | RT60 = 0.3 × 60^(Decay/99) s (measured slightly shorter because of damping) | 72 → about 5.6 s |
| Diffusion | input diffuser coefficients 0.75 and 0.625, scaled by Diffusion/9; tank allpass 0.35–0.7 | 9 → full |
| Speed | 0.1 × 100^(Speed/99) Hz | 61 → 1.7 Hz |
| Depth | ±4 ms × Depth/99 around an 8 ms centre | 31 → ±1.25 ms |
| Feedback | 0–95 % (capped) | 20 % |
| Dry / Reverb Level | linear, value/99 | 0 / 99 |

Delay lengths are scaled from Dattorro's 29 761 Hz reference to the running sample rate, so the sound is the same at 44.1, 48 and 96 kHz (RT60 within ±0.1 s across rates).

## Vintage

- The four tank delay lines store values rounded to 16 bits, like a fixed-point DSP writing to memory. Rounding (not truncation) keeps the decay time intact while the very end of the tail falls to zero.
- The wet signal passes a soft clipper (rational tanh approximation) scaled for about 1 % THD at full scale, the original's distortion spec.

## Bypass and tails

The plugin handles bypass itself (`lv2:enabled` port), so MOD keeps calling it while bypassed. Three gains fade over about 10 ms:

| State | Reverb input | Reverb output | Dry |
| --- | --- | --- | --- |
| On | 1 | Reverb Level | Dry Level |
| Bypassed, Tails on | 0 | Reverb Level (tail rings out) | 1 |
| Bypassed, Tails off | 0 | 0, then the tank is cleared | 1 |

Controls arrive with the first `run()`, so that first block snaps pre-delay and all three gains to their targets: no glide or fade when a pedalboard loads.

## Duo CPU notes

Fixed delays use whole-sample taps; only the modulated allpasses, chorus and pre-delay interpolate. Slow LFOs use a parabolic sine, and the soft clipper a rational approximation, to keep the 32-bit Cortex-A7 happy. Buffers are sized once for 96 kHz.
