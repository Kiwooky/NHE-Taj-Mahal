/*
 * Taj Mahal - New Horizon Electronics
 * https://github.com/Kiwooky/NHE-Taj-Mahal
 * SPDX-License-Identifier: MIT
 *
 * Chorused hall reverb modelled on the "Taj Mahal" factory preset of a classic
 * 1988 rack multi-effect. See docs/sound-and-design.md for the signal flow and
 * knob mappings.
 */
#include "DistrhoPlugin.hpp"

#include <cmath>
#include <vector>

START_NAMESPACE_DISTRHO

// ---------------------------------------------------------------------------
// Building blocks. All memory is allocated in the constructor, sized for the
// highest sample rate we support, so run() never allocates.

static const double kMaxSampleRate = 96000.0;
static const double kRefRate       = 29761.0;   // Dattorro reference rate
static const float  kAntiDenormal  = 1e-18f;

static uint32_t nextPow2(uint32_t v)
{
    uint32_t p = 1;
    while (p < v) p <<= 1;
    return p;
}

struct DelayLine
{
    std::vector<float> buf;
    uint32_t mask = 0;
    uint32_t pos  = 0;

    void init(uint32_t maxLen)
    {
        const uint32_t size = nextPow2(maxLen + 4);
        buf.assign(size, 0.0f);
        mask = size - 1;
        pos  = 0;
    }
    void clear() { for (float& s : buf) s = 0.0f; pos = 0; }

    // value written 'd' samples ago (d >= 1)
    inline float tap(uint32_t d) const { return buf[(pos - d) & mask]; }

    inline float tapFrac(float d) const
    {
        const uint32_t i = (uint32_t)d;
        const float    f = d - (float)i;
        const float    a = buf[(pos - i) & mask];
        const float    b = buf[(pos - i - 1) & mask];
        return a + (b - a) * f;
    }
    inline void write(float x) { buf[pos & mask] = x; ++pos; }
};

// Schroeder allpass built on a DelayLine, with optional fractional length.
struct Allpass
{
    DelayLine dl;
    inline float process(float x, float len, float g)
    {
        const float d = dl.tapFrac(len);
        const float w = x + g * d;
        dl.write(w);
        return d - g * w;
    }
    inline float processInt(float x, uint32_t len, float g)
    {
        const float d = dl.tap(len);
        const float w = x + g * d;
        dl.write(w);
        return d - g * w;
    }
};

static inline float onePoleCoef(float hz, float sr)
{
    return 1.0f - std::exp(-2.0f * 3.14159265f * hz / sr);
}

// 16-bit rounding, like a fixed-point DSP writing to its delay memory.
static inline float trunc16(float x)
{
    const float s = x * 32768.0f;
    return (float)((int32_t)(s + (s >= 0.0f ? 0.5f : -0.5f))) * (1.0f / 32768.0f);
}

// Cheap sine for slow modulation LFOs, phase in [0, 1).
static inline float fastSin(float ph)
{
    const float x = ph * 2.0f - 1.0f;           // -1..1
    return -4.0f * x * (1.0f - std::fabs(x));   // parabolic approximation
}

// Soft clipper, rational tanh approximation (accurate for |x| < 3).
static inline float softClip(float x)
{
    if (x >  3.0f) return  1.0f;
    if (x < -3.0f) return -1.0f;
    const float x2 = x * x;
    return x * (27.0f + x2) / (27.0f + 9.0f * x2);
}

// ---------------------------------------------------------------------------

class TajMahalPlugin : public Plugin
{
public:
    TajMahalPlugin()
        : Plugin(kParameterCount, 0, 0)
    {
        fParams[kPredelay]       = 81.0f;
        fParams[kDecay]          = 72.0f;
        fParams[kDiffusion]      = 9.0f;
        fParams[kChorusSpeed]    = 61.0f;
        fParams[kChorusDepth]    = 31.0f;
        fParams[kChorusFeedback] = 20.0f;
        fParams[kDirect]         = 0.0f;
        fParams[kReverbLevel]    = 99.0f;
        fParams[kVintage]        = 1.0f;
        fParams[kTails]          = 1.0f;
        fParams[kBypass]         = 0.0f;

        const double k = kMaxSampleRate / kRefRate;
        const uint32_t mod = (uint32_t)(32.0 * k) + 8;

        fChorus.init((uint32_t)(0.030 * kMaxSampleRate));
        fPreL.init((uint32_t)(0.150 * kMaxSampleRate));
        fPreR.init((uint32_t)(0.150 * kMaxSampleRate));

        for (int i = 0; i < 4; ++i) {
            fInL[i].dl.init((uint32_t)(kInLen[i] * k));
            fInR[i].dl.init((uint32_t)(kInLen[i] * k));
        }
        fApA1.dl.init((uint32_t)(672.0 * k) + mod);
        fApB1.dl.init((uint32_t)(908.0 * k) + mod);
        fDlA1.init((uint32_t)(4453.0 * k));
        fDlB1.init((uint32_t)(4217.0 * k));
        fApA2.dl.init((uint32_t)(1800.0 * k));
        fApB2.dl.init((uint32_t)(2656.0 * k));
        fDlA2.init((uint32_t)(3720.0 * k));
        fDlB2.init((uint32_t)(3163.0 * k));

        activate();
    }

protected:
    const char* getLabel()       const override { return "TajMahal"; }
    const char* getDescription() const override { return "Huge chorused hall reverb modelled on the Taj Mahal preset of a classic 1988 rack reverb."; }
    const char* getMaker()       const override { return "New Horizon Electronics"; }
    const char* getHomePage()    const override { return "https://github.com/Kiwooky/NHE-Taj-Mahal"; }
    const char* getLicense()     const override { return "MIT"; }
    uint32_t    getVersion()     const override { return d_version(1, 0, 1); }
    int64_t     getUniqueId()    const override { return d_cconst('T', 'j', 'M', 'h'); }

    void initParameter(uint32_t index, Parameter& p) override
    {
        p.hints = kParameterIsAutomatable | kParameterIsInteger;
        p.ranges.min = 0.0f;
        p.ranges.max = 99.0f;

        switch (index) {
        case kPredelay:
            p.name = "Pre-delay"; p.symbol = "predelay"; p.unit = "ms";
            p.ranges.max = 140.0f; p.ranges.def = 81.0f;
            break;
        case kDecay:
            p.name = "Decay"; p.symbol = "decay";
            p.ranges.min = 1.0f; p.ranges.def = 72.0f;
            break;
        case kDiffusion:
            p.name = "Diffusion"; p.symbol = "diffusion";
            p.ranges.max = 9.0f; p.ranges.def = 9.0f;
            break;
        case kChorusSpeed:
            p.name = "Chorus Speed"; p.symbol = "chorus_speed";
            p.ranges.def = 61.0f;
            break;
        case kChorusDepth:
            p.name = "Chorus Depth"; p.symbol = "chorus_depth";
            p.ranges.def = 31.0f;
            break;
        case kChorusFeedback:
            p.name = "Chorus Feedback"; p.symbol = "chorus_feedback"; p.unit = "%";
            p.ranges.def = 20.0f;
            break;
        case kDirect:
            p.name = "Direct"; p.symbol = "direct";
            p.ranges.def = 0.0f;
            break;
        case kReverbLevel:
            p.name = "Reverb Level"; p.symbol = "reverb_level";
            p.ranges.def = 99.0f;
            break;
        case kVintage:
            p.hints |= kParameterIsBoolean;
            p.name = "Vintage"; p.symbol = "vintage";
            p.ranges.max = 1.0f; p.ranges.def = 1.0f;
            break;
        case kTails:
            p.hints |= kParameterIsBoolean;
            p.name = "Tails"; p.symbol = "tails";
            p.ranges.max = 1.0f; p.ranges.def = 1.0f;
            break;
        case kBypass:
            // DPF exposes this as the LV2 'enabled' port (inverted), which
            // MOD's footswitch drives instead of hard-bypassing the plugin.
            p.initDesignation(kParameterDesignationBypass);
            break;
        }
    }

    float getParameterValue(uint32_t index) const override
    {
        return (index < kParameterCount) ? fParams[index] : 0.0f;
    }

    void setParameterValue(uint32_t index, float value) override
    {
        if (index < kParameterCount) fParams[index] = value;
    }

    void activate() override
    {
        fSr = (float)getSampleRate();
        if (fSr <= 0.0f) fSr = 48000.0f;
        if (fSr > (float)kMaxSampleRate) fSr = (float)kMaxSampleRate;
        fK = fSr / (float)kRefRate;

        clearState();
        fCleared = false;
        fFirstRun = true;

        // start in whatever state the switches are in, without a fade
        const bool bypassed = fParams[kBypass] > 0.5f;
        fInGain  = bypassed ? 0.0f : 1.0f;
        fWetGain = (bypassed && fParams[kTails] < 0.5f) ? 0.0f : 1.0f;
        fDryGain = bypassed ? 1.0f : fParams[kDirect] / 99.0f;

        fLfoPhase = 0.0f; fModPhaseA = 0.0f; fModPhaseB = 0.25f;
        fPreSmooth = fParams[kPredelay] * 0.001f * fSr - 0.008f * fSr;
        if (fPreSmooth < 0.0f) fPreSmooth = 0.0f;

        fBwCoef   = onePoleCoef(9000.0f, fSr);
        fDampCoef = onePoleCoef(5000.0f, fSr);
    }

    void clearState()
    {
        fChorus.clear(); fPreL.clear(); fPreR.clear();
        for (int i = 0; i < 4; ++i) { fInL[i].dl.clear(); fInR[i].dl.clear(); }
        fApA1.dl.clear(); fApB1.dl.clear(); fApA2.dl.clear(); fApB2.dl.clear();
        fDlA1.clear(); fDlB1.clear(); fDlA2.clear(); fDlB2.clear();
        fBwL = fBwR = fDampA = fDampB = 0.0f;
    }

    void run(const float** inputs, float** outputs, uint32_t frames) override
    {
        const float* in   = inputs[0];
        float*       outL = outputs[0];
        float*       outR = outputs[1];

        const float sr = fSr, k = fK;

        // --- map hardware-style knob values to DSP coefficients ---------
        const float rt60  = 0.3f * std::pow(60.0f, fParams[kDecay] / 99.0f);
        const float loopT = 21589.0f / (float)kRefRate;           // full tank loop, s
        float g = std::pow(10.0f, -3.0f * loopT / (4.0f * rt60));
        if (g > 0.98f) g = 0.98f;

        const float diff = fParams[kDiffusion] / 9.0f;
        const float gin1 = 0.75f  * diff;
        const float gin2 = 0.625f * diff;
        const float gdd1 = 0.35f + 0.35f * diff;
        const float gdd2 = 0.5f;

        const float lfoHz  = 0.1f * std::pow(100.0f, fParams[kChorusSpeed] / 99.0f);
        const float lfoInc = lfoHz / sr;
        const float chBase = 0.008f * sr;
        const float chDep  = 0.004f * sr * (fParams[kChorusDepth] / 99.0f);
        float chFb = fParams[kChorusFeedback] / 100.0f;
        if (chFb > 0.95f) chFb = 0.95f;

        // the chorus already delays by chBase, so subtract it from pre-delay
        float preTarget = fParams[kPredelay] * 0.001f * sr - chBase;
        if (preTarget < 0.0f) preTarget = 0.0f;
        const float preCoef   = onePoleCoef(8.0f, sr);

        const float direct  = fParams[kDirect] / 99.0f;
        const float level   = fParams[kReverbLevel] / 99.0f;
        const bool  vintage = fParams[kVintage] > 0.5f;

        // --- bypass / tails: targets for three smoothed gains -------------
        const bool bypassed = fParams[kBypass] > 0.5f;
        const bool tails    = fParams[kTails]  > 0.5f;
        const float inTarget  = bypassed ? 0.0f : 1.0f;             // feed the reverb?
        const float wetTarget = (bypassed && !tails) ? 0.0f : level; // hear the reverb?
        const float dryTarget = bypassed ? 1.0f : direct;           // dry at unity when bypassed
        const float fadeCoef  = onePoleCoef(1.0f / (2.0f * 3.14159265f * 0.010f), sr); // ~10 ms

        if (fFirstRun) {
            // controls arrive with the first run(), not before activate():
            // start exactly there, with no glides or fades
            fFirstRun = false;
            fPreSmooth = preTarget;
            fInGain = inTarget; fWetGain = wetTarget; fDryGain = dryTarget;
        }

        // Tails off: once the fade-out has finished, wipe the reverb so it
        // starts clean when re-engaged (like a hard bypass would).
        if (bypassed && !tails && fWetGain < 1e-4f && !fCleared) {
            clearState();
            fCleared = true;
        }
        if (!bypassed) fCleared = false;

        const float modExc = 16.0f * k;
        const float modInA = 0.5f / sr, modInB = 0.7f / sr;

        const uint32_t lenIn[4] = { (uint32_t)(kInLen[0]*k), (uint32_t)(kInLen[1]*k), (uint32_t)(kInLen[2]*k), (uint32_t)(kInLen[3]*k) };
        const float lenA1 = 672.0f * k, lenB1 = 908.0f * k;
        const uint32_t dA1 = (uint32_t)(4453.0f * k), dB1 = (uint32_t)(4217.0f * k);
        const uint32_t lenA2 = (uint32_t)(1800.0f * k), lenB2 = (uint32_t)(2656.0f * k);
        const uint32_t dA2 = (uint32_t)(3720.0f * k), dB2 = (uint32_t)(3163.0f * k);

        #define TAP(n) ((uint32_t)((n) * k) + 1)

        for (uint32_t i = 0; i < frames; ++i)
        {
            const float x = in[i];

            fInGain  += fadeCoef * (inTarget  - fInGain);
            fWetGain += fadeCoef * (wetTarget - fWetGain);
            fDryGain += fadeCoef * (dryTarget - fDryGain);
            const float xr = x * fInGain;      // what the chorus/reverb hears

            // --- stereo chorus: triangle LFO, taps 180 deg apart ------------
            fLfoPhase += lfoInc;
            if (fLfoPhase >= 1.0f) fLfoPhase -= 1.0f;
            const float triL = 4.0f * std::fabs(fLfoPhase - 0.5f) - 1.0f;
            const float triR = -triL;
            const float cL = fChorus.tapFrac(chBase + chDep * triL);
            const float cR = fChorus.tapFrac(chBase + chDep * triR);
            fChorus.write(xr + chFb * cL + kAntiDenormal);
            const float chL = 0.5f * (xr + cL);
            const float chR = 0.5f * (xr + cR);

            // --- pre-delay (smoothed, so knob moves glide instead of click) --
            fPreSmooth += preCoef * (preTarget - fPreSmooth);
            fPreL.write(chL);
            fPreR.write(chR);
            float pL = fPreL.tapFrac(fPreSmooth + 1.0f);
            float pR = fPreR.tapFrac(fPreSmooth + 1.0f);

            // --- input bandwidth + diffusers -------------------------------
            fBwL += fBwCoef * (pL - fBwL);
            fBwR += fBwCoef * (pR - fBwR);
            pL = fBwL + kAntiDenormal;
            pR = fBwR + kAntiDenormal;
            pL = fInL[0].processInt(pL, lenIn[0], gin1);
            pL = fInL[1].processInt(pL, lenIn[1], gin1);
            pL = fInL[2].processInt(pL, lenIn[2], gin2);
            pL = fInL[3].processInt(pL, lenIn[3], gin2);
            pR = fInR[0].processInt(pR, lenIn[0], gin1);
            pR = fInR[1].processInt(pR, lenIn[1], gin1);
            pR = fInR[2].processInt(pR, lenIn[2], gin2);
            pR = fInR[3].processInt(pR, lenIn[3], gin2);

            // --- figure-eight tank -----------------------------------------
            fModPhaseA += modInA; if (fModPhaseA >= 1.0f) fModPhaseA -= 1.0f;
            fModPhaseB += modInB; if (fModPhaseB >= 1.0f) fModPhaseB -= 1.0f;
            const float mA = modExc * (1.0f + fastSin(fModPhaseA));
            const float mB = modExc * (1.0f + fastSin(fModPhaseB));

            const float fbToA = fDlB2.tap(dB2) * g;
            const float fbToB = fDlA2.tap(dA2) * g;

            // half A
            float a = fApA1.process(pL + fbToA, lenA1 + mA, -gdd1);
            fDlA1.write(vintage ? trunc16(a) : a);
            a = fDlA1.tap(dA1);
            fDampA += fDampCoef * (a - fDampA);
            a = fApA2.processInt(fDampA * g, lenA2, gdd2);
            fDlA2.write(vintage ? trunc16(a) : a);

            // half B
            float b = fApB1.process(pR + fbToB, lenB1 + mB, -gdd1);
            fDlB1.write(vintage ? trunc16(b) : b);
            b = fDlB1.tap(dB1);
            fDampB += fDampCoef * (b - fDampB);
            b = fApB2.processInt(fDampB * g, lenB2, gdd2);
            fDlB2.write(vintage ? trunc16(b) : b);

            // --- output taps (Dattorro 1997) -------------------------------
            float wl = fDlB1.tap(TAP(266)) + fDlB1.tap(TAP(2974))
                     - fApB2.dl.tap(TAP(1913)) + fDlB2.tap(TAP(1996))
                     - fDlA1.tap(TAP(1990)) - fApA2.dl.tap(TAP(187))
                     - fDlA2.tap(TAP(1066));
            float wr = fDlA1.tap(TAP(353)) + fDlA1.tap(TAP(3627))
                     - fApA2.dl.tap(TAP(1228)) + fDlA2.tap(TAP(2673))
                     - fDlB1.tap(TAP(2111)) - fApB2.dl.tap(TAP(335))
                     - fDlB2.tap(TAP(121));
            wl *= 0.95f;   // Dattorro's 0.6, plus ~4 dB so Level 99 sits near unity
            wr *= 0.95f;

            if (vintage) {
                // about 1 % THD at full scale, like the original's spec
                wl = softClip(0.35f * wl) / 0.35f;
                wr = softClip(0.35f * wr) / 0.35f;
            }

            outL[i] = fDryGain * x + fWetGain * wl;
            outR[i] = fDryGain * x + fWetGain * wr;
        }

        #undef TAP
    }

private:
    static constexpr float kInLen[4] = { 142.0f, 107.0f, 379.0f, 277.0f };

    float fParams[kParameterCount];

    DelayLine fChorus, fPreL, fPreR;
    Allpass   fInL[4], fInR[4];
    Allpass   fApA1, fApB1, fApA2, fApB2;
    DelayLine fDlA1, fDlB1, fDlA2, fDlB2;

    float fSr = 48000.0f, fK = 1.0f;
    float fBwL = 0.0f, fBwR = 0.0f, fDampA = 0.0f, fDampB = 0.0f;
    float fBwCoef = 0.0f, fDampCoef = 0.0f;
    float fLfoPhase = 0.0f, fModPhaseA = 0.0f, fModPhaseB = 0.0f;
    float fPreSmooth = 0.0f;
    float fInGain = 1.0f, fWetGain = 1.0f, fDryGain = 0.0f;
    bool  fCleared = true;
    bool  fFirstRun = true;

    DISTRHO_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(TajMahalPlugin)
};

constexpr float TajMahalPlugin::kInLen[4];

Plugin* createPlugin() { return new TajMahalPlugin(); }

END_NAMESPACE_DISTRHO