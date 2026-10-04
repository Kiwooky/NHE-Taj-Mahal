#ifndef DISTRHO_PLUGIN_INFO_H_INCLUDED
#define DISTRHO_PLUGIN_INFO_H_INCLUDED

#define DISTRHO_PLUGIN_BRAND       "New Horizon"
#define DISTRHO_PLUGIN_NAME        "Taj Mahal"
#define DISTRHO_PLUGIN_URI         "https://github.com/Kiwooky/NHE-Taj-Mahal"

#define DISTRHO_PLUGIN_HAS_UI       0
#define DISTRHO_PLUGIN_IS_RT_SAFE   1
#define DISTRHO_PLUGIN_NUM_INPUTS   1
#define DISTRHO_PLUGIN_NUM_OUTPUTS  2

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