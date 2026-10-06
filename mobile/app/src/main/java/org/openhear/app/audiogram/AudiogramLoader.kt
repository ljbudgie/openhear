// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app.audiogram

import android.content.Context
import org.json.JSONObject
import java.io.FileNotFoundException

/**
 * Audiogram data for both ears.
 *
 * Frequency keys are in Hz.
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

    /** Frequencies supported by OpenHear's sample graph and legacy JSON format. */
    private val SUPPORTED_FREQUENCIES =
        listOf(250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000)

    /** Frequencies used for Pure Tone Average (PTA). */
    private val PTA_FREQUENCIES = listOf(500, 1000, 2000)

    const val PRIVATE_GRAPH_FILENAME = "audiogram.json"
    const val SAMPLE_ASSET_NAME = "sample_audiogram.json"

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
        val left = parseEar(root, "left", "left_ear")
        val right = parseEar(root, "right", "right_ear")
        require(left.isNotEmpty() && right.isNotEmpty()) {
            "A graph must include thresholds for both ears."
        }
        return Audiogram(
            left = left,
            right = right
        )
    }

    /**
     * Load a previously selected graph from app-private internal storage.
     * No external storage permission or network access is used.
     */
    fun loadStoredGraph(context: Context): Audiogram? {
        return try {
            context.openFileInput(PRIVATE_GRAPH_FILENAME)
                .bufferedReader()
                .use { loadAudiogram(it.readText()) }
        } catch (_: FileNotFoundException) {
            null
        }
    }

    /**
     * Validate a graph before replacing the app-private copy.
     */
    fun saveGraph(context: Context, jsonString: String): Audiogram {
        val audiogram = loadAudiogram(jsonString)
        context.openFileOutput(PRIVATE_GRAPH_FILENAME, Context.MODE_PRIVATE)
            .bufferedWriter()
            .use { it.write(jsonString) }
        return audiogram
    }

    /**
     * A short, approximate description of the graph and speech cues that may
     * sit above its thresholds. This describes the graph; it is not a diagnosis.
     */
    fun describeGraph(audiogram: Audiogram): String {
        val low = meanThreshold(audiogram, LOW_FREQUENCIES)
        val high = meanThreshold(audiogram, HIGH_FREQUENCIES)
        val slope = if (low != null && high != null) high - low else null
        val shape = when {
            slope == null -> "The graph needs more low- and high-pitch points to show its shape"
            slope >= 10f -> "The graph slopes toward higher pitches"
            slope <= -10f -> "The graph slopes toward lower pitches"
            else -> "The graph is fairly level from low to high pitches"
        }

        val speechCues = mutableListOf<String>()
        if (worseEarMean(audiogram, LOW_FREQUENCIES)?.let { it >= SPEECH_CUE_THRESHOLD_DB } == true) {
            speechCues += "lower vowels and voice sounds"
        }
        if (worseEarMean(audiogram, MID_FREQUENCIES)?.let { it >= SPEECH_CUE_THRESHOLD_DB } == true) {
            speechCues += "/sh/, /t/ and /k/"
        }
        if (worseEarMean(audiogram, HIGH_FREQUENCIES)?.let { it >= SPEECH_CUE_THRESHOLD_DB } == true) {
            speechCues += "/s/, /f/ and /th/"
        }

        val cueDescription = if (speechCues.isEmpty()) {
            "This simplified view doesn't flag a speech-sound group above the line"
        } else {
            "${speechCues.joinToString(", ")} may sit above the line"
        }
        return "$shape; $cueDescription (graph description only, not a diagnosis)."
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

    private fun parseEar(root: JSONObject, legacyKey: String, sampleKey: String): Map<Int, Float> {
        val map = mutableMapOf<Int, Float>()
        val legacy = root.optJSONObject(legacyKey)
        if (legacy != null) {
            for (freq in SUPPORTED_FREQUENCIES) {
                val key = freq.toString()
                if (legacy.has(key)) {
                    map[freq] = validatedThreshold(freq, legacy.getDouble(key).toFloat())
                }
            }
            return map
        }

        val sampleEar = root.optJSONObject(sampleKey)
            ?: throw IllegalArgumentException("Graph is missing $legacyKey thresholds.")
        val thresholds = sampleEar.optJSONArray("thresholds")
            ?: throw IllegalArgumentException("$sampleKey is missing its thresholds list.")
        for (index in 0 until thresholds.length()) {
            val point = thresholds.getJSONObject(index)
            val frequency = point.getInt("freq_hz")
            if (frequency in SUPPORTED_FREQUENCIES) {
                map[frequency] = validatedThreshold(frequency, point.getDouble("db_hl").toFloat())
            }
        }
        return map
    }

    private fun validatedThreshold(frequency: Int, threshold: Float): Float {
        require(frequency > 0 && threshold.isFinite() && threshold in -20f..140f) {
            "Graph contains an invalid threshold."
        }
        return threshold
    }

    private fun meanThreshold(audiogram: Audiogram, frequencies: List<Int>): Float? {
        val values = (audiogram.left.valuesFor(frequencies) + audiogram.right.valuesFor(frequencies))
        return values.takeIf { it.isNotEmpty() }?.average()?.toFloat()
    }

    private fun worseEarMean(audiogram: Audiogram, frequencies: List<Int>): Float? {
        return listOf(
            audiogram.left.valuesFor(frequencies),
            audiogram.right.valuesFor(frequencies)
        ).mapNotNull { values ->
            values.takeIf { it.isNotEmpty() }?.average()?.toFloat()
        }.maxOrNull()
    }

    private fun Map<Int, Float>.valuesFor(frequencies: List<Int>): List<Float> =
        frequencies.mapNotNull { this[it] }

    private val LOW_FREQUENCIES = listOf(250, 500, 750)
    private val MID_FREQUENCIES = listOf(1000, 1500, 2000, 3000)
    private val HIGH_FREQUENCIES = listOf(4000, 6000, 8000)
    private const val SPEECH_CUE_THRESHOLD_DB = 25f
}
