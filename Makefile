#!/usr/bin/make -f
# Taj Mahal - top-level build
#
#   make                      build bin/nhe-taj-mahal.lv2 (DSP + TTL + pedal face)
#   make install DESTDIR=...  install into $(DESTDIR)$(PREFIX)/lib/lv2
#   make clean
#
# Cross builds take the usual CC/CXX/CXXFLAGS from the environment, which is
# what mod-plugin-builder and builder.mod.audio pass in.

PREFIX  ?= /usr/local
BUNDLE  := nhe-taj-mahal.lv2

all: plugin bundle

plugin:
	$(MAKE) -C plugins/taj-mahal

bundle: plugin
	cp -r bundle/$(BUNDLE)/. bin/$(BUNDLE)/

install: all
	install -d $(DESTDIR)$(PREFIX)/lib/lv2/$(BUNDLE)
	cp -r bin/$(BUNDLE)/. $(DESTDIR)$(PREFIX)/lib/lv2/$(BUNDLE)/

clean:
	$(MAKE) -C plugins/taj-mahal clean
	rm -rf bin build

.PHONY: all plugin bundle install clean
