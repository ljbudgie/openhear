// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.
//
// openhear_dsp.cpp — Oboe-based real-time DSP engine for OpenHear.
//
// This file implements:
//   1. An Oboe duplex (input + output) audio callback.
//   2. A placeholder DSP chain that mirrors the Python modules in ../../../dsp/.
//   3. JNI glue so the Kotlin OboeEngine class can drive the native engine.
//
// Each DSP stage is marked with a TODO pointing to the Python reference
// implementation so contributors can port the algorithm to C++.

#include <jni.h>
#include <oboe/Oboe.h>
#include <cmath>
#include <algorithm>
#include <cstring>
#include <chrono>
#include <android/log.h>

#define LOG_TAG "OpenHearDSP"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN,  LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------------
// DSP parameter IDs  (keep in sync with OboeEngine.kt)
// ---------------------------------------------------------------------------
static constexpr int PARAM_COMPRESSION_RATIO       = 0;
static constexpr int PARAM_NOISE_FLOOR_DB          = 1;
static constexpr int PARAM_VOICE_EMPHASIS_GAIN_DB  = 2;
static constexpr int PARAM_FEEDBACK_CANCEL_STRENGTH = 3;
static constexpr int PARAM_OWN_VOICE_THRESHOLD     = 4;

// ---------------------------------------------------------------------------
// OpenHearEngine
// ---------------------------------------------------------------------------

class OpenHearEngine : public oboe::AudioStreamDataCallback {
public:
    OpenHearEngine(int32_t sampleRate, int32_t framesPerBuffer)
        : mSampleRate(sampleRate),
          mFramesPerBuffer(framesPerBuffer) {}

    ~OpenHearEngine() {
        stop();
    }

    // --- Stream lifecycle ---------------------------------------------------

    bool start() {
        // Build input (recording) stream
        oboe::AudioStreamBuilder inputBuilder;
        inputBuilder.setDirection(oboe::Direction::Input)
                    .setSampleRate(mSampleRate)
                    .setChannelCount(1)
                    .setFormat(oboe::AudioFormat::Float)
                    .setPerformanceMode(oboe::PerformanceMode::LowLatency)
                    .setSharingMode(oboe::SharingMode::Exclusive)
                    .setFramesPerDataCallback(mFramesPerBuffer);

        oboe::Result result = inputBuilder.openStream(mInputStream);
        if (result != oboe::Result::OK) {
            LOGW("Failed to open input stream: %s", oboe::convertToText(result));
            return false;
        }

        // Build output (playback) stream with this object as callback
        oboe::AudioStreamBuilder outputBuilder;
        outputBuilder.setDirection(oboe::Direction::Output)
                     .setSampleRate(mSampleRate)
                     .setChannelCount(1)
                     .setFormat(oboe::AudioFormat::Float)
                     .setPerformanceMode(oboe::PerformanceMode::LowLatency)
                     .setSharingMode(oboe::SharingMode::Exclusive)
                     .setFramesPerDataCallback(mFramesPerBuffer)
                     .setDataCallback(this);

        result = outputBuilder.openStream(mOutputStream);
        if (result != oboe::Result::OK) {
            LOGW("Failed to open output stream: %s", oboe::convertToText(result));
            return false;
        }

        mInputStream->requestStart();
        mOutputStream->requestStart();
        mRunning = true;
        LOGI("Audio engine started  SR=%d  BUF=%d", mSampleRate, mFramesPerBuffer);
        return true;
    }

    void stop() {
        mRunning = false;
        if (mInputStream) {
            mInputStream->requestStop();
            mInputStream->close();
            mInputStream.reset();
        }
        if (mOutputStream) {
            mOutputStream->requestStop();
            mOutputStream->close();
            mOutputStream.reset();
        }
        LOGI("Audio engine stopped");
    }

    // --- DSP parameter control ----------------------------------------------

    void setParam(int paramId, float value) {
        switch (paramId) {
            case PARAM_COMPRESSION_RATIO:        mCompressionRatio      = value; break;
            case PARAM_NOISE_FLOOR_DB:           mNoiseFloorDb          = value; break;
            case PARAM_VOICE_EMPHASIS_GAIN_DB:   mVoiceEmphasisGainDb   = value; break;
            case PARAM_FEEDBACK_CANCEL_STRENGTH: mFeedbackCancelStrength = value; break;
            case PARAM_OWN_VOICE_THRESHOLD:      mOwnVoiceThreshold     = value; break;
            default: LOGW("Unknown param ID %d", paramId); break;
        }
    }

    float getLatencyMs() const { return mLatencyMs; }

    // --- Oboe audio callback ------------------------------------------------

    oboe::DataCallbackResult onAudioReady(
            oboe::AudioStream *outputStream,
            void *audioData,
            int32_t numFrames) override {

        auto callbackStart = std::chrono::high_resolution_clock::now();

        auto *output = static_cast<float *>(audioData);

        // Read from the input (mic) stream into the output buffer directly.
        if (mInputStream) {
            auto readResult = mInputStream->read(output, numFrames, 0);
            if (readResult.error() != oboe::Result::OK) {
                std::memset(output, 0, sizeof(float) * numFrames);
            }
        } else {
            std::memset(output, 0, sizeof(float) * numFrames);
        }

        // ---------------------------------------------------------------
        // DSP chain — each stage is a placeholder.
        // Port the real algorithms from the Python dsp/ modules.
        // ---------------------------------------------------------------

        // Stage 1 — Adaptive noise reduction
        // TODO: Port dsp/noise.py  — spectral subtraction / Wiener filter.
        applyNoiseReduction(output, numFrames);

        // Stage 2 — Multi-band compression (WDRC)
        // TODO: Port dsp/compressor.py — per-band wide dynamic range compression.
        applyCompression(output, numFrames);

        // Stage 3 — Voice emphasis
        // TODO: Port dsp/voice.py — bandpass boost around 1–4 kHz.
        applyVoiceEmphasis(output, numFrames);

        // Stage 4 — Feedback cancellation (LMS adaptive filter)
        // TODO: Port dsp/feedback.py — normalised LMS.
        applyFeedbackCancellation(output, numFrames);

        // Stage 5 — Own-voice detection bypass
        // TODO: Detect own-voice via accelerometer / dual-mic correlation
        //       and reduce gain to avoid occlusion amplification.
        applyOwnVoiceBypass(output, numFrames);

        // Stage 6 — Safety limiter (MANDATORY — never remove)
        // Hard-clip every sample to [-1.0, +1.0]  (0 dBFS).
        applySafetyLimiter(output, numFrames);

        // ---------------------------------------------------------------
        // Latency measurement
        // ---------------------------------------------------------------
        auto callbackEnd = std::chrono::high_resolution_clock::now();
        float processingUs = std::chrono::duration<float, std::micro>(
                callbackEnd - callbackStart).count();

        // Approximate round-trip: input buffer + processing + output buffer.
        float bufferMs = (static_cast<float>(numFrames) / mSampleRate) * 1000.0f;
        mLatencyMs = 2.0f * bufferMs + (processingUs / 1000.0f);

        return oboe::DataCallbackResult::Continue;
    }

private:
    // --- Placeholder DSP stages --------------------------------------------

    void applyNoiseReduction(float *buf, int32_t n) {
        // Placeholder: gate samples below the noise floor.
        float threshold = std::pow(10.0f, mNoiseFloorDb / 20.0f);
        for (int32_t i = 0; i < n; ++i) {
            if (std::fabs(buf[i]) < threshold) {
                buf[i] *= 0.1f; // soft gate
            }
        }
    }

    void applyCompression(float *buf, int32_t n) {
        // Placeholder: simple soft-knee compressor (single band).
        float ratio = std::max(mCompressionRatio, 1.0f);
        float thresholdLin = 0.5f; // ~-6 dBFS knee
        for (int32_t i = 0; i < n; ++i) {
            float mag = std::fabs(buf[i]);
            if (mag > thresholdLin) {
                float over = mag - thresholdLin;
                float compressed = thresholdLin + over / ratio;
                buf[i] = std::copysign(compressed, buf[i]);
            }
        }
    }

    void applyVoiceEmphasis(float *buf, int32_t n) {
        // Placeholder: apply a flat gain boost.
        // A real implementation would use a bandpass filter (1–4 kHz).
        float gain = std::pow(10.0f, mVoiceEmphasisGainDb / 20.0f);
        for (int32_t i = 0; i < n; ++i) {
            buf[i] *= gain;
        }
    }

    void applyFeedbackCancellation(float * /*buf*/, int32_t /*n*/) {
        // Placeholder: LMS adaptive filter would subtract the estimated
        // feedback path from the mic signal.  No-op for now.
    }

    void applyOwnVoiceBypass(float * /*buf*/, int32_t /*n*/) {
        // Placeholder: when own-voice is detected (e.g. via accelerometer
        // or dual-mic correlation), reduce gain to prevent occlusion effect.
    }

    void applySafetyLimiter(float *buf, int32_t n) {
        // MANDATORY — hard clip at 0 dBFS.  Never remove this stage.
        for (int32_t i = 0; i < n; ++i) {
            buf[i] = std::clamp(buf[i], -1.0f, 1.0f);
        }
    }

    // --- State --------------------------------------------------------------
    int32_t mSampleRate;
    int32_t mFramesPerBuffer;
    bool    mRunning = false;
    float   mLatencyMs = 0.0f;

    // DSP parameters (sensible defaults)
    float mCompressionRatio       = 2.0f;
    float mNoiseFloorDb           = -50.0f;
    float mVoiceEmphasisGainDb    = 3.0f;
    float mFeedbackCancelStrength = 0.01f;
    float mOwnVoiceThreshold     = 0.5f;

    // Oboe streams
    std::shared_ptr<oboe::AudioStream> mInputStream;
    std::shared_ptr<oboe::AudioStream> mOutputStream;
};

// ---------------------------------------------------------------------------
// JNI entry points  (called from OboeEngine.kt)
// ---------------------------------------------------------------------------

extern "C" {

JNIEXPORT jlong JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeCreateEngine(
        JNIEnv * /*env*/, jobject /*thiz*/,
        jint sampleRate, jint framesPerBuffer) {
    auto *engine = new OpenHearEngine(sampleRate, framesPerBuffer);
    return reinterpret_cast<jlong>(engine);
}

JNIEXPORT jboolean JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeStartEngine(
        JNIEnv * /*env*/, jobject /*thiz*/, jlong engineHandle) {
    auto *engine = reinterpret_cast<OpenHearEngine *>(engineHandle);
    return engine ? static_cast<jboolean>(engine->start()) : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeStopEngine(
        JNIEnv * /*env*/, jobject /*thiz*/, jlong engineHandle) {
    auto *engine = reinterpret_cast<OpenHearEngine *>(engineHandle);
    if (engine) engine->stop();
}

JNIEXPORT void JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeDestroyEngine(
        JNIEnv * /*env*/, jobject /*thiz*/, jlong engineHandle) {
    auto *engine = reinterpret_cast<OpenHearEngine *>(engineHandle);
    delete engine;
}

JNIEXPORT void JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeSetDspParam(
        JNIEnv * /*env*/, jobject /*thiz*/,
        jlong engineHandle, jint paramId, jfloat value) {
    auto *engine = reinterpret_cast<OpenHearEngine *>(engineHandle);
    if (engine) engine->setParam(paramId, value);
}

JNIEXPORT jfloat JNICALL
Java_org_openhear_app_audio_OboeEngine_nativeGetLatencyMs(
        JNIEnv * /*env*/, jobject /*thiz*/, jlong engineHandle) {
    auto *engine = reinterpret_cast<OpenHearEngine *>(engineHandle);
    return engine ? engine->getLatencyMs() : 0.0f;
}

} // extern "C"
