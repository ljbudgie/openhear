// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app

import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.openhear.app.audiogram.Audiogram
import org.openhear.app.audiogram.AudiogramLoader

/**
 * Main entry point for the OpenHear Android app.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                OpenHearApp()
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Compose UI
// ---------------------------------------------------------------------------

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OpenHearApp() {
    val context = LocalContext.current
    var audiogram by remember(context) {
        mutableStateOf(runCatching { AudiogramLoader.loadStoredGraph(context) }.getOrNull())
    }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val graphPicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            try {
                val json = context.contentResolver.openInputStream(uri)
                    ?.bufferedReader()
                    ?.use { it.readText() }
                    ?: throw IllegalArgumentException("The selected file could not be opened.")
                audiogram = AudiogramLoader.saveGraph(context, json)
                errorMessage = null
            } catch (_: Exception) {
                errorMessage = "Couldn't load that file. Choose a JSON graph with left and right ear thresholds."
            }
        }
    }

    if (audiogram == null) {
        FirstRunScreen(
            errorMessage = errorMessage,
            onUseSample = {
                try {
                    val json = context.assets.open(AudiogramLoader.SAMPLE_ASSET_NAME)
                        .bufferedReader()
                        .use { it.readText() }
                    audiogram = AudiogramLoader.saveGraph(context, json)
                    errorMessage = null
                } catch (_: Exception) {
                    errorMessage = "The bundled sample graph couldn't be opened."
                }
            },
            onLoadFromPhone = {
                graphPicker.launch(arrayOf("application/json", "text/json", "text/plain", "*/*"))
            }
        )
    } else {
        GraphReadyScreen(
            audiogram = audiogram!!,
            onLoadAnotherGraph = {
                graphPicker.launch(arrayOf("application/json", "text/json", "text/plain", "*/*"))
            },
            onClearGraph = {
                AudiogramLoader.clearStoredGraph(context)
                audiogram = null
                errorMessage = null
            },
            errorMessage = errorMessage
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FirstRunScreen(
    errorMessage: String?,
    onUseSample: () -> Unit,
    onLoadFromPhone: () -> Unit
) {
    Scaffold { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.Start,
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            Text(
                "Research build. Not a hearing aid. Not a medical device.",
                style = MaterialTheme.typography.bodyLarge
            )
            Text("This phone can vibrate for sounds you cannot hear.")
            Button(onClick = onUseSample, modifier = Modifier.fillMaxWidth()) {
                Text("Use the sample graph")
            }
            Button(onClick = onLoadFromPhone, modifier = Modifier.fillMaxWidth()) {
                Text("Load a graph from this phone")
            }
            if (errorMessage != null) {
                Text(errorMessage, color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GraphReadyScreen(
    audiogram: Audiogram,
    onLoadAnotherGraph: () -> Unit,
    onClearGraph: () -> Unit,
    errorMessage: String?
) {
    val context = LocalContext.current
    val vibrator = context.getSystemService(Vibrator::class.java)
    val scope = rememberCoroutineScope()
    var isTesting by remember { mutableStateOf(false) }
    var activePattern by remember { mutableStateOf<String?>(null) }
    var vibrationUnavailable by remember { mutableStateOf(false) }

    DisposableEffect(vibrator) {
        onDispose { vibrator?.cancel() }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("OpenHear") }) }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.Start,
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            Text("Your graph is loaded", style = MaterialTheme.typography.headlineMedium)
            Text(
                AudiogramLoader.describeGraph(audiogram),
                style = MaterialTheme.typography.bodyLarge
            )

            Button(
                onClick = {
                    if (vibrator == null || !vibrator.hasVibrator()) {
                        vibrationUnavailable = true
                    } else {
                        vibrationUnavailable = false
                        scope.launch {
                            isTesting = true
                            try {
                                HAPTIC_PATTERNS.forEach { pattern ->
                                    activePattern = pattern.label
                                    vibrator.cancel()
                                    vibrator.vibrate(pattern.toEffect())
                                    delay(pattern.durationMs + HAPTIC_GAP_MS)
                                }
                            } finally {
                                vibrator.cancel()
                                activePattern = null
                                isTesting = false
                            }
                        }
                    }
                },
                enabled = !isTesting,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Test vibration")
            }

            Text("Door — one short pulse, then one long pulse")
            Text("Traffic — a slow double pulse")
            Text("Alarm — three short pulses")

            Text(
                text = activePattern?.let { "Now vibrating: $it" }
                    ?: "The test plays Door, Traffic, then Alarm.",
                style = MaterialTheme.typography.bodyLarge
            )
            if (vibrationUnavailable) {
                Text("Vibration isn't available on this phone.", color = MaterialTheme.colorScheme.error)
            }
            if (errorMessage != null) {
                Text(errorMessage, color = MaterialTheme.colorScheme.error)
            }

            TextButton(onClick = onLoadAnotherGraph) {
                Text("Load a different graph from this phone")
            }
            TextButton(onClick = onClearGraph) {
                Text("Clear graph from this phone")
            }
        }
    }
}

private data class HapticPattern(
    val label: String,
    private val timingsMs: LongArray,
    private val amplitude: Int = MODEST_HAPTIC_AMPLITUDE
) {
    val durationMs: Long = timingsMs.sum()

    fun toEffect(): VibrationEffect {
        val amplitudes = IntArray(timingsMs.size) { index ->
            if (index % 2 == 0) 0 else amplitude
        }
        return VibrationEffect.createWaveform(timingsMs, amplitudes, -1)
    }
}

private const val MODEST_HAPTIC_AMPLITUDE = 40
private const val HAPTIC_GAP_MS = 240L

private val HAPTIC_PATTERNS = listOf(
    HapticPattern(
        label = "Door",
        timingsMs = longArrayOf(0, 100, 100, 240)
    ),
    HapticPattern(
        label = "Traffic",
        timingsMs = longArrayOf(0, 180, 200, 180)
    ),
    HapticPattern(
        label = "Alarm",
        timingsMs = longArrayOf(0, 70, 80, 70, 80, 70)
    )
)
