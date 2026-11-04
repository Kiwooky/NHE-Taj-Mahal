#!/usr/bin/make -f
# Taj Mahal - top-level build, used by the package files in mod-plugin-builder/ (and by you).
#
#   make                                  build bin/nhe-taj-mahal.lv2 (DSP + TTL + pedal face)
#   make NAME=nhe-taj-mahal-stereo        Taj Mahal Stereo (same source, same face)
#   make desktop                          VST3 + CLAP in bin/, plus the AU (.component) on macOS
#   make desktop NAME=nhe-taj-mahal-stereo   the same for Taj Mahal Stereo
#   make install DESTDIR=...              install into $(DESTDIR)$(PREFIX)/lib/lv2
#   make clean
#
# Cross builds take the usual CC/CXX/CXXFLAGS from the environment, which is
# what mod-plugin-builder and builder.mod.audio pass in.

PREFIX  ?= /usr/local
NAME    ?= nhe-taj-mahal
BUNDLE  := $(NAME).lv2
# the mono plugin's folder predates the plugins/<bundle name> convention
PLUGDIR := $(if $(filter nhe-taj-mahal,$(NAME)),taj-mahal,$(NAME))

all: plugin bundle

plugin:
	$(MAKE) -C plugins/$(PLUGDIR)

bundle: plugin
	# the stereo bundle borrows the mono face; its own modgui/ files (panel with the STEREO
	# badge, screenshot, thumbnail), if any, then go over the top
	[ "$(NAME)" = nhe-taj-mahal ] || cp -r bundle/nhe-taj-mahal.lv2/modgui bin/$(BUNDLE)/
	cp -r bundle/$(BUNDLE)/. bin/$(BUNDLE)/

desktop:
	$(MAKE) -C plugins/$(PLUGDIR) desktop

install: all
	install -d $(DESTDIR)$(PREFIX)/lib/lv2/$(BUNDLE)
	cp -r bin/$(BUNDLE)/. $(DESTDIR)$(PREFIX)/lib/lv2/$(BUNDLE)/

clean:
	$(MAKE) -C plugins/taj-mahal clean
	$(MAKE) -C plugins/nhe-taj-mahal-stereo clean
	rm -rf bin build

.PHONY: all plugin bundle desktop install clean
