// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app.audio

/**
 * Kotlin wrapper around the native Oboe audio engine.
 *
 * The actual DSP processing lives in C++ (openhear_dsp.cpp) and is invoked
 * through JNI.  This class provides a clean Kotlin API:
 *
 *   val engine = OboeEngine()
 *   engine.start()          // opens mic → DSP → output stream
 *   engine.latencyMs()      // poll round-trip latency
 *   engine.setDspParam(…)   // tweak compression, noise floor, etc.
 *   engine.stop()           // tears down streams
 *
 * The native library "openhear_dsp" is loaded once via the companion object.
 */
class OboeEngine {

    // Handle returned by nativeCreateEngine — 0 means "not initialised".
    private var engineHandle: Long = 0L

    // Default audio parameters (Oboe will negotiate the actual values).
    private val defaultSampleRate = 48_000
    private val defaultFramesPerBuffer = 256 // ~5.3 ms at 48 kHz

    // -- Public API ----------------------------------------------------------

    /**
     * Create the native engine and start the audio streams.
     * Requires RECORD_AUDIO permission to have been granted already.
     */
    fun start() {
        if (engineHandle != 0L) return // already running
        engineHandle = nativeCreateEngine(defaultSampleRate, defaultFramesPerBuffer)
        if (engineHandle != 0L) {
            nativeStartEngine(engineHandle)
        }
    }

    /** Stop audio streams and release native resources. */
    fun stop() {
        if (engineHandle == 0L) return
        nativeStopEngine(engineHandle)
        nativeDestroyEngine(engineHandle)
        engineHandle = 0L
    }

    /** True when the native engine is actively streaming audio. */
    fun isRunning(): Boolean = engineHandle != 0L

    /**
     * Retrieve the most recent round-trip latency estimate (ms).
     * Target is < 80 ms for usable hearing assistance.
     */
    fun latencyMs(): Float {
        if (engineHandle == 0L) return 0f
        return nativeGetLatencyMs(engineHandle)
    }

    /**
     * Set a DSP parameter on the native engine.
     *
     * Parameter IDs (defined in openhear_dsp.cpp):
     *   0 = compression ratio
     *   1 = noise floor threshold (dB)
     *   2 = voice emphasis gain (dB)
     *   3 = feedback cancellation strength
     *   4 = own-voice detection threshold
     *
     * This mapping will be replaced by an enum / sealed class as the
     * parameter set stabilises.
     */
    fun setDspParam(paramId: Int, value: Float) {
        if (engineHandle == 0L) return
        nativeSetDspParam(engineHandle, paramId, value)
    }

    // -- JNI declarations ----------------------------------------------------
    // These map 1-to-1 to the functions in openhear_dsp.cpp.

    private external fun nativeCreateEngine(sampleRate: Int, framesPerBuffer: Int): Long
    private external fun nativeStartEngine(engineHandle: Long): Boolean
    private external fun nativeStopEngine(engineHandle: Long)
    private external fun nativeDestroyEngine(engineHandle: Long)
    private external fun nativeSetDspParam(engineHandle: Long, paramId: Int, value: Float)
    private external fun nativeGetLatencyMs(engineHandle: Long): Float

    companion object {
        init {
            // Loads libopenhear_dsp.so built by CMake / ndk-build.
            System.loadLibrary("openhear_dsp")
        }
    }
}
