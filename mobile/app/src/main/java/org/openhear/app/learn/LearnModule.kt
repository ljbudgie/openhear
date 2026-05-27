// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app.learn

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import org.openhear.app.audiogram.DspParams

/**
 * v1 "Learn" module — on-device preference learning via thumbs-up / thumbs-down.
 *
 * How it works:
 *   1. The user rates the current sound quality (UP = good, DOWN = bad).
 *   2. The module records the current DSP parameters alongside the rating.
 *   3. When the same acoustic environment is detected again, the module
 *      suggests parameters by averaging all user-approved (UP) snapshots.
 *
 * Storage: SharedPreferences (JSON-encoded).  Simple and offline-only.
 *
 * Roadmap (v2): Replace simple averaging with a tinyML model trained
 * on-device (e.g. TFLite) that predicts preferred parameters from
 * environment features (noise level, SNR, reverb estimate).
 */

/** User feedback on current sound quality. */
enum class ThumbsFeedback { UP, DOWN }

/**
 * A single feedback record.
 */
data class FeedbackRecord(
    val environment: String,
    val feedback: ThumbsFeedback,
    val params: DspParams,
    val timestampMs: Long = System.currentTimeMillis()
)

/**
 * On-device preference learner.
 *
 * Usage:
 * ```
 * val learn = LearnModule(context)
 * learn.recordFeedback("noisy_cafe", ThumbsFeedback.UP, currentParams)
 * val suggested = learn.suggestAdjustment("noisy_cafe")
 * ```
 */
class LearnModule(context: Context) {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    // -- Public API ----------------------------------------------------------

    /**
     * Record a thumbs-up or thumbs-down for the current DSP settings in
     * the given acoustic environment.
     */
    fun recordFeedback(
        environment: String,
        feedback: ThumbsFeedback,
        currentParams: DspParams
    ) {
        val records = loadRecords(environment).toMutableList()
        records.add(FeedbackRecord(environment, feedback, currentParams))
        saveRecords(environment, records)
    }

    /**
     * Suggest DSP parameters for [environment] by averaging all
     * user-approved (thumbs-up) parameter snapshots.
     *
     * Returns default [DspParams] if there are no approved records.
     */
    fun suggestAdjustment(environment: String): DspParams {
        val approved = loadRecords(environment).filter { it.feedback == ThumbsFeedback.UP }
        if (approved.isEmpty()) return DspParams()

        // Simple arithmetic mean of each scalar parameter.
        val n = approved.size.toFloat()
        return DspParams(
            compressionRatio      = approved.sumOf { it.params.compressionRatio.toDouble() }.toFloat() / n,
            noiseFloorDb          = approved.sumOf { it.params.noiseFloorDb.toDouble() }.toFloat() / n,
            voiceEmphasisGainDb   = approved.sumOf { it.params.voiceEmphasisGainDb.toDouble() }.toFloat() / n,
            feedbackCancelStrength = approved.sumOf { it.params.feedbackCancelStrength.toDouble() }.toFloat() / n,
            ownVoiceThreshold     = approved.sumOf { it.params.ownVoiceThreshold.toDouble() }.toFloat() / n
        )
    }

    /**
     * Clear all feedback records for a given environment.
     */
    fun clearRecords(environment: String) {
        prefs.edit().remove(keyFor(environment)).apply()
    }

    // -- Persistence (SharedPreferences + JSON) ------------------------------

    private fun keyFor(environment: String) = "learn_$environment"

    private fun loadRecords(environment: String): List<FeedbackRecord> {
        val json = prefs.getString(keyFor(environment), null) ?: return emptyList()
        val array = JSONArray(json)
        val result = mutableListOf<FeedbackRecord>()
        for (i in 0 until array.length()) {
            val obj = array.getJSONObject(i)
            result.add(
                FeedbackRecord(
                    environment = obj.getString("env"),
                    feedback    = ThumbsFeedback.valueOf(obj.getString("fb")),
                    params      = jsonToParams(obj.getJSONObject("params")),
                    timestampMs = obj.optLong("ts", 0L)
                )
            )
        }
        return result
    }

    private fun saveRecords(environment: String, records: List<FeedbackRecord>) {
        val array = JSONArray()
        for (r in records) {
            val obj = JSONObject().apply {
                put("env", r.environment)
                put("fb", r.feedback.name)
                put("params", paramsToJson(r.params))
                put("ts", r.timestampMs)
            }
            array.put(obj)
        }
        prefs.edit().putString(keyFor(environment), array.toString()).apply()
    }

    private fun paramsToJson(p: DspParams) = JSONObject().apply {
        put("cr", p.compressionRatio.toDouble())
        put("nf", p.noiseFloorDb.toDouble())
        put("ve", p.voiceEmphasisGainDb.toDouble())
        put("fc", p.feedbackCancelStrength.toDouble())
        put("ov", p.ownVoiceThreshold.toDouble())
    }

    private fun jsonToParams(obj: JSONObject) = DspParams(
        compressionRatio       = obj.optDouble("cr", 2.0).toFloat(),
        noiseFloorDb           = obj.optDouble("nf", -50.0).toFloat(),
        voiceEmphasisGainDb    = obj.optDouble("ve", 3.0).toFloat(),
        feedbackCancelStrength = obj.optDouble("fc", 0.01).toFloat(),
        ownVoiceThreshold      = obj.optDouble("ov", 0.5).toFloat()
    )

    companion object {
        private const val PREFS_NAME = "openhear_learn"
    }
}
