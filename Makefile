#!/usr/bin/make -f
# Taj Mahal - top-level build, used by the package files in mod-plugin-builder/ (and by you).
#
#   make                                  build bin/nhe-taj-mahal.lv2 (DSP + TTL + pedal face)
#   make NAME=nhe-taj-mahal-stereo        Taj Mahal Stereo (same source, same face)
#   make desktop                          VST3 + CLAP in bin/, plus the AU (.component) on macOS
#   make desktop NAME=nhe-taj-mahal-stereo   the same for Taj Mahal Stereo
#   make install DESTDIR=...              install into $(DESTDIR)$(PREFIX)/lib/lv2
#   make X11UI=1                          also build the X11 GUI (Linux: Zynthian, Carla...);
#                                         needs libx11-dev, libimlib2-dev, lv2-dev. Pass X11UI=1 to
#                                         `make install` as well. MOD builds leave it off.
#   make clean
#
# Cross builds take the usual CC/CXX/CXXFLAGS from the environment, which is
# what mod-plugin-builder and builder.mod.audio pass in.

PREFIX  ?= /usr/local
NAME    ?= nhe-taj-mahal
BUNDLE  := $(NAME).lv2
# the mono plugin's folder predates the plugins/<bundle name> convention
PLUGDIR := $(if $(filter nhe-taj-mahal,$(NAME)),taj-mahal,$(NAME))

# Optional X11 GUI (plugins/taj-mahal/x11ui/, contributed by Maarten for Zynthian).
# One source for both plugins: the stereo plugin has one more audio input, so its
# control ports sit one higher.
X11UI   ?= 0
X11_SRC := plugins/taj-mahal/x11ui/nhe-taj-mahal_x11ui.c
X11_SO  := bin/$(BUNDLE)/$(NAME)_x11ui.so
X11_URI := https://github.com/Kiwooky/NHE-Taj-Mahal$(if $(filter nhe-taj-mahal-stereo,$(NAME)),/stereo)
X11_OFS := $(if $(filter nhe-taj-mahal-stereo,$(NAME)),1,0)

all: plugin bundle

plugin:
	$(MAKE) -C plugins/$(PLUGDIR)

bundle: plugin
	# the stereo bundle borrows the mono face; its own modgui/ files (panel with the STEREO
	# badge, screenshot, thumbnail), if any, then go over the top
	[ "$(NAME)" = nhe-taj-mahal ] || cp -r bundle/nhe-taj-mahal.lv2/modgui bin/$(BUNDLE)/
	cp -r bundle/$(BUNDLE)/. bin/$(BUNDLE)/
ifeq ($(X11UI),1)
	@pkg-config --exists x11 imlib2 lv2 || { echo "X11UI=1 needs libx11-dev, libimlib2-dev and lv2-dev"; exit 1; }
	$(CC) -shared -fPIC -O2 -Wall -o $(X11_SO) $(X11_SRC) \
		-DNHE_PORT_OFFSET=$(X11_OFS) '-DNHE_UI_URI="$(X11_URI)#X11UI"' \
		$$(pkg-config --cflags --libs x11 imlib2)
	sed -e 's|@PLUGIN_URI@|$(X11_URI)|g' -e 's|@BUNDLE@|$(NAME)|g' \
		plugins/taj-mahal/x11ui/manifest-x11ui.ttl.in >> bin/$(BUNDLE)/manifest.ttl
endif

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
