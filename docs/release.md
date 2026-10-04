# Release checklist: builder link → beta store → official

As of October 2026, MOD publishes community plugins in three steps.

1. **Builder link.** Upload `mod-plugin-builder/nhe-taj-mahal/nhe-taj-mahal.mk` to builder.mod.audio. A good build gives a shareable install link for forum testers. No MOD approval needed.
2. **Beta store.** Pull request to [mod-audio/mod-plugin-builder](https://github.com/mod-audio/mod-plugin-builder) adding `plugins/package/nhe-taj-mahal/nhe-taj-mahal.mk`, pinned to a commit. MOD staff review it.
3. **Official (stable).** MOD's 2026 "Beta no more" criteria: UI, documentation (a PDF behind the "See documentation" button), testing on Dwarf, Duo X and Duo, balanced audio where it applies; presets and demos help ([survey results](https://forum.mod.audio/t/beta-no-more-survey-results/13396), [test procedure](https://forum.mod.audio/t/plugin-test-procedure/13345)).

| Item | Status |
| --- | --- |
| Public repo, MIT code licence | Done |
| Artwork licence | Placeholder; Niels to confirm |
| Own identity (URI, maker, bundle name) | Done in 1.0.0 |
| mod-plugin-builder package | Written and test-built locally; first builder.mod.audio build pending |
| Pedal face | Done (cookbook prototype verified on a Duo; 1.0.0 switches Vintage/Tails to the switch widget) |
| Manual PDF + `modgui:documentation` line | To do |
| Presets | Done in 1.0.1: seven factory presets (the 1988 original plus six by Niels) |
| Tested on Duo | Cookbook prototype (v1.0.2) on hardware; 1.0.0 to check |
| Tested on Duo X and Dwarf | To do (forum volunteers) |
| CPU load on Duo | To read from the CPU meter |
| Assignments: footswitches, knobs, MIDI | To check on hardware |
| Demo audio/video | To do |
| Forum thread with builder link | To do |
