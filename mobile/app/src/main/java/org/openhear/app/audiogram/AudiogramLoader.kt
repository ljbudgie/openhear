// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app.audiogram

import org.json.JSONObject

/**
 * Audiogram data for both ears.
 *
 * Frequency keys are in Hz (250, 500, 1000, 2000, 4000, 8000).
 * Threshold values are in dB HL (hearing level).
 *
 * JSON format (matches Python audiogram/loader.py):
 * ```json
 * {
 *   "left":  { "250": 20, "500": 25, "1000": 30, "2000": 40, "4000": 55, "8000": 60 },
 *   "right": { "250": 15, "500": 20, "1000": 25, "2000": 35, "4000": 50, "8000": 55 }
 * }
 * ```
 */
data class Audiogram(
    val left: Map<Int, Float>,
    val right: Map<Int, Float>
)

/**
 * DSP parameters that can be derived from an audiogram or adjusted by the
 * Learn module.  This is a shared value object used across the app.
 */
data class DspParams(
    val compressionRatio: Float = 2.0f,
    val noiseFloorDb: Float = -50.0f,
    val voiceEmphasisGainDb: Float = 3.0f,
    val feedbackCancelStrength: Float = 0.01f,
    val ownVoiceThreshold: Float = 0.5f,
    val perFrequencyGain: Map<Int, Float> = emptyMap()
)

/**
 * Loads and interprets audiogram JSON.
 *
 * Reference implementation: Python `audiogram/loader.py` in this repository.
 * Keep the two in sync when adding new features.
 */
object AudiogramLoader {

    /** Standard audiometric frequencies (Hz). */
    private val STANDARD_FREQUENCIES = listOf(250, 500, 1000, 2000, 4000, 8000)

    /** Frequencies used for Pure Tone Average (PTA). */
    private val PTA_FREQUENCIES = listOf(500, 1000, 2000)

    // --- Public API ---------------------------------------------------------

    /**
     * Parse an audiogram JSON string into an [Audiogram].
     *
     * @param jsonString  JSON with "left" and "right" objects mapping
     *                    frequency (Hz) → threshold (dB HL).
     * @throws org.json.JSONException on malformed input.
     */
    fun loadAudiogram(jsonString: String): Audiogram {
        val root = JSONObject(jsonString)
        return Audiogram(
            left  = parseEar(root.getJSONObject("left")),
            right = parseEar(root.getJSONObject("right"))
        )
    }

    /**
     * Compute per-frequency insertion gains for one ear using the
     * **half-gain rule**: gain ≈ threshold / 2.
     *
     * This is a simplified prescription; real fitting uses NAL-NL2 or DSLv5.
     *
     * @param ear  "left" or "right".
     * @return Map of frequency (Hz) → recommended gain (dB).
     */
    fun getGainProfile(audiogram: Audiogram, ear: String): Map<Int, Float> {
        val thresholds = when (ear) {
            "left"  -> audiogram.left
            "right" -> audiogram.right
            else    -> throw IllegalArgumentException("ear must be 'left' or 'right'")
        }
        // Half-gain rule: gain = threshold / 2, clamped to [0, 60] dB.
        return thresholds.mapValues { (_, threshold) ->
            (threshold / 2.0f).coerceIn(0.0f, 60.0f)
        }
    }

    /**
     * Pure Tone Average — the mean threshold at 500, 1000, and 2000 Hz.
     *
     * @param ear  "left" or "right".
     * @return PTA in dB HL, or 0 if the required frequencies are missing.
     */
    fun getPTA(audiogram: Audiogram, ear: String): Float {
        val thresholds = when (ear) {
            "left"  -> audiogram.left
            "right" -> audiogram.right
            else    -> throw IllegalArgumentException("ear must be 'left' or 'right'")
        }
        val ptaValues = PTA_FREQUENCIES.mapNotNull { thresholds[it] }
        if (ptaValues.isEmpty()) return 0.0f
        return ptaValues.sum() / ptaValues.size
    }

    // --- Helpers ------------------------------------------------------------

    private fun parseEar(obj: JSONObject): Map<Int, Float> {
        val map = mutableMapOf<Int, Float>()
        for (freq in STANDARD_FREQUENCIES) {
            val key = freq.toString()
            if (obj.has(key)) {
                map[freq] = obj.getDouble(key).toFloat()
            }
        }
        return map
    }
}
