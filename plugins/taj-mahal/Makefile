#!/usr/bin/make -f
# DSP-only LV2 build of Taj Mahal with DPF (git submodule) in ../../dpf
NAME = nhe-taj-mahal
FILES_DSP = TajMahalPlugin.cpp
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
