#ifndef DISTRHO_PLUGIN_INFO_H_INCLUDED
#define DISTRHO_PLUGIN_INFO_H_INCLUDED

// Rename these together with the TTL. Taj Mahal Stereo has its own copy of this
// file in plugins/nhe-taj-mahal-stereo (same enum, two inputs).

#define DISTRHO_PLUGIN_BRAND       "New Horizon"
#define DISTRHO_PLUGIN_NAME        "Taj Mahal"
#define DISTRHO_PLUGIN_URI         "https://github.com/Kiwooky/NHE-Taj-Mahal"
#define TAJ_LABEL                  "TajMahal"
#define TAJ_DESCRIPTION            "Huge chorused hall reverb modelled on the Taj Mahal preset of a classic 1988 rack reverb."
#define TAJ_HOMEPAGE               "https://github.com/Kiwooky/NHE-Taj-Mahal"
#define TAJ_LICENSE                "MIT"
#define TAJ_VERSION                1, 0, 2   // d_version: = lv2:minorVersion 2, microVersion 2
#define TAJ_UNIQUE_ID              d_cconst('T', 'j', 'M', 'h')

#define DISTRHO_PLUGIN_HAS_UI       0
#define DISTRHO_PLUGIN_IS_RT_SAFE   1
#define DISTRHO_PLUGIN_NUM_INPUTS   1
#define DISTRHO_PLUGIN_NUM_OUTPUTS  2
#define DISTRHO_PLUGIN_WANT_PROGRAMS 1

// Desktop formats (VST3 / AU / CLAP). These IDs are permanent once a build
// ships: hosts use them to find the plugin in saved projects. Don't change.
#define DISTRHO_PLUGIN_BRAND_ID     Nhzn      // AU manufacturer code (needs a capital)
#define DISTRHO_PLUGIN_UNIQUE_ID    TjMh      // AU subtype, matches TAJ_UNIQUE_ID
#define DISTRHO_PLUGIN_AU_TYPE      aufx      // kAudioUnitType_Effect
#define DISTRHO_PLUGIN_VST3_CATEGORIES "Fx|Reverb"
#define DISTRHO_PLUGIN_CLAP_ID      "nz.newhorizon.taj-mahal"
#define DISTRHO_PLUGIN_CLAP_FEATURES "audio-effect", "reverb", "mono"

enum Parameters {
    kPredelay = 0,
    kDecay,
    kDiffusion,
    kChorusSpeed,
    kChorusDepth,
    kChorusFeedback,
    kDirect,
    kReverbLevel,
    kVintage,
    kTails,
    kBypass,
    kParameterCount
};

#endif