######################################
#
# nhe-taj-mahal
#
# Taj Mahal by New Horizon Electronics
# https://github.com/Kiwooky/NHE-Taj-Mahal
#
# This file is the plugin's package for mod-plugin-builder
# (plugins/package/nhe-taj-mahal/nhe-taj-mahal.mk). The same file can be
# uploaded to https://builder.mod.audio/buildroot to get an install link.
#
# Set NHE_TAJ_MAHAL_VERSION to the full hash of the commit to build.
#
######################################

NHE_TAJ_MAHAL_VERSION = COMMIT_HASH_HERE
NHE_TAJ_MAHAL_SITE = $(call github,Kiwooky,NHE-Taj-Mahal,$(NHE_TAJ_MAHAL_VERSION))
NHE_TAJ_MAHAL_BUNDLES = nhe-taj-mahal.lv2

NHE_TAJ_MAHAL_TARGET_MAKE = $(TARGET_MAKE_ENV) $(TARGET_CONFIGURE_OPTS) $(MAKE) NOOPT=true -C $(@D)

define NHE_TAJ_MAHAL_BUILD_CMDS
	$(NHE_TAJ_MAHAL_TARGET_MAKE)
endef

define NHE_TAJ_MAHAL_INSTALL_TARGET_CMDS
	$(NHE_TAJ_MAHAL_TARGET_MAKE) install DESTDIR=$(TARGET_DIR) PREFIX=/usr
endef

$(eval $(generic-package))
