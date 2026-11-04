#ifndef DISTRHO_PLUGIN_INFO_H_INCLUDED
#define DISTRHO_PLUGIN_INFO_H_INCLUDED

// Taj Mahal Stereo: the same source as plugins/taj-mahal, built with two inputs.
// Rename these together with the TTL (bundle/nhe-taj-mahal-stereo.lv2).
// The parameter enum must stay identical to the mono plugin's.
#define DISTRHO_PLUGIN_BRAND       "New Horizon"
#define DISTRHO_PLUGIN_NAME        "Taj Mahal Stereo"
#define DISTRHO_PLUGIN_URI         "https://github.com/Kiwooky/NHE-Taj-Mahal-Stereo"
#define TAJ_LABEL                  "TajMahalStereo"
#define TAJ_DESCRIPTION            "Huge chorused hall reverb, stereo in: modelled on the Taj Mahal preset of a classic 1988 rack reverb."
#define TAJ_HOMEPAGE               "https://github.com/Kiwooky/NHE-Taj-Mahal"
#define TAJ_LICENSE                "MIT"
#define TAJ_VERSION                1, 0, 0   // d_version: = lv2:minorVersion 2, microVersion 0
#define TAJ_UNIQUE_ID              d_cconst('T', 'j', 'M', 's')

#define DISTRHO_PLUGIN_HAS_UI       0
#define DISTRHO_PLUGIN_IS_RT_SAFE   1
#define DISTRHO_PLUGIN_NUM_INPUTS   2   // stereo in: L feeds tank half A, R feeds half B
#define DISTRHO_PLUGIN_NUM_OUTPUTS  2
#define DISTRHO_PLUGIN_WANT_PROGRAMS 1

// Desktop formats (VST3 / AU / CLAP). These IDs are permanent once a build
// ships: hosts use them to find the plugin in saved projects. Don't change.
#define DISTRHO_PLUGIN_BRAND_ID     Nhzn      // AU manufacturer code (needs a capital)
#define DISTRHO_PLUGIN_UNIQUE_ID    TjMs      // AU subtype, matches TAJ_UNIQUE_ID
#define DISTRHO_PLUGIN_AU_TYPE      aufx      // kAudioUnitType_Effect
#define DISTRHO_PLUGIN_VST3_CATEGORIES "Fx|Reverb"
#define DISTRHO_PLUGIN_CLAP_ID      "nz.newhorizon.taj-mahal-stereo"
#define DISTRHO_PLUGIN_CLAP_FEATURES "audio-effect", "reverb", "stereo"

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
