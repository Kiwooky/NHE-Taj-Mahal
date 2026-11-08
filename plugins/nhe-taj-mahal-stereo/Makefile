#!/usr/bin/make -f
# DSP-only LV2 build. NAME = the bundle name; the binary is <NAME>_dsp.so.
# The source is the mono plugin's (included by TajMahalStereoPlugin.cpp).
NAME = nhe-taj-mahal-stereo
FILES_DSP = TajMahalStereoPlugin.cpp
include ../../dpf/Makefile.plugins.mk
TARGETS = lv2_dsp
all: $(TARGETS)

# desktop formats: VST3 + CLAP everywhere, AU on macOS
DESKTOP_TARGETS = vst3 clap
ifeq ($(MACOS),true)
DESKTOP_TARGETS += au
endif
desktop: $(DESKTOP_TARGETS)
.PHONY: desktop
