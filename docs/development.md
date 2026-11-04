# Development

How Taj Mahal is built, tested and changed. The same process applies to every New Horizon plugin.

## Toolchain

```sh
apt-get install g++ g++-arm-linux-gnueabihf g++-aarch64-linux-gnu qemu-user lilv-utils
pip install numpy scipy pillow playwright
gcc -O2 -Idpf/distrho/src -Idpf/distrho/src/lv2 tools/lv2host.c -o tools/lv2host -ldl
```

## The loop for every change

1. **Decide the behaviour first.** Faithful to the original by default; any deliberate difference goes in the CHANGELOG.
2. **Edit the sources** (`plugins/`, `bundle/`). The LV2 metadata is hand-written: keep port order, ranges and the URI in step with `DistrhoPluginInfo.h` and `initParameter()`.
3. **Build three ways:** native (`make`), Duo (`CC=arm-linux-gnueabihf-gcc CXX=arm-linux-gnueabihf-g++ CXXFLAGS="-mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard" make`), Duo X / Dwarf (`CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++ make`). Set CC as well as CXX: DPF picks its CPU flags from CC, and an x86 CC adds `-msse` to an ARM build. Warnings are bugs.
4. **Check the metadata:** build DPF's `lv2_ttl_generator` and compare its output port by port with `bundle/nhe-taj-mahal.lv2/nhe-taj-mahal.ttl`; then `LV2_PATH=bin lv2info https://github.com/Kiwooky/NHE-Taj-Mahal`.
5. **Run the audio suite:** `python3 tools/tmtest.py` natively, then the ARM builds under qemu:
   `TM_SO=<arm .so> TM_HOST="qemu-arm -L /usr/arm-linux-gnueabihf <arm lv2host>" python3 tools/tmtest.py`.
   **Taj Mahal Stereo:** `make NAME=nhe-taj-mahal-stereo`, then `python3 tools/tmtest_stereo.py`
   (it needs both builds: it checks that the same signal on both inputs equals the mono plugin
   exactly). Under qemu, also pass `TM_SO_MONO=<arm mono .so>`. Any change to
   `plugins/taj-mahal/TajMahalPlugin.cpp` changes both plugins, so run both suites and bump both
   versions (each `DistrhoPluginInfo.h` has its own `TAJ_VERSION`, matched in its TTL).
   It checks pre-delay, RT60 at every sample rate, the Decay range, levels, Dry at unity, first-run behaviour, bypass with Tails on and off (clicks, dry at unity, clean restart), a pre-delay sweep, a max-everything torture run at 44.1/48/96 kHz and silence. **Every reported bug gets a test that fails first.**
6. **Face changes:** test the template against mod-ui's own `html/js/modgui.js` and its jQuery 1.9.1 in headless Chromium, clicking with a little mouse wobble. Then `make && python3 tools/render.py && make` to refresh the screenshot and thumbnail.
7. **Bump the version** in `TAJ_VERSION` (`DistrhoPluginInfo.h`) and the TTL together (`d_version(1,0,N)` ↔ `lv2:minorVersion 2 ; lv2:microVersion N`). MOD caches plugin data per version: an unchanged version shows stale faces.
8. **Commit, update `NHE_TAJ_MAHAL_VERSION`** in the package file to the new commit, build on builder.mod.audio and check on hardware: face, sound, footswitches, bypass, CPU meter.

## Desktop builds (VST3, AU, CLAP)

`make desktop` builds `bin/nhe-taj-mahal.vst3` and `.clap`; on macOS also the Audio Unit,
`bin/nhe-taj-mahal.component` (needs Xcode's command-line tools). Add `NAME=nhe-taj-mahal-stereo`
for the stereo plugin. To try the AU: copy the `.component` into `~/Library/Audio/Plug-Ins/Components`,
run `auval -v aufx TjMh Nhzn` (stereo: `TjMs`), then relaunch the host. GarageBand only rescans on launch.

- The IDs in each `DistrhoPluginInfo.h` (`Nhzn`, `TjMh`/`TjMs`, the CLAP ids) are permanent once a desktop build ships.
- Factory presets live twice: `presets.ttl` for MOD, `kPresets` in `TajMahalPlugin.cpp` for everything else.
- Steinberg's VST3 validator passes everything except "Bypass persistence", which fails for any DPF
  plugin with a bypass parameter (checked with a bare test plugin): a DPF issue, not ours.
- No desktop face yet: hosts show generic controls.

## Rules learned the hard way

- **DPF needs `opts:options` and `urid:map`** declared as required features.
- **Parameters arrive with the first `run()`**, not before `activate()`: snap smoothers to their targets on the first run.
- **Buttons and footswitches use `mod-widget="switch"`.** The default film widget ignores a click if the mouse moves a couple of pixels.
- **The bypass widget's classes are inverted:** `on` = bypassed, `off` = active. Style the On/Off LED accordingly.
- **Knob strips:** `python3 tools/knob_filmstrip.py assets/source/knob_body.png assets/source/knob_marker.png bundle/nhe-taj-mahal.lv2/modgui/knob.png 65 270`, then quantise to 256 colours (about 400 KB → 47 KB). The knurl turns, the lighting stays put.
- **Once public, ports are frozen.** Never remove, reorder or rename ports, and never change the URI: saved pedalboards depend on them.
