// ⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE
// Consult an audiologist before using any hearing device.
// Use at your own risk. MIT Licensed.

package org.openhear.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.openhear.app.audio.OboeEngine

/**
 * Main entry point for the OpenHear Android app.
 *
 * Architecture:
 *   MainActivity (Compose UI)
 *       └─► OboeEngine (Kotlin wrapper)
 *               └─► openhear_dsp.cpp via JNI (Oboe audio callback)
 *
 * Navigation stubs:
 *   - AudiogramScreen  → load / edit audiogram JSON
 *   - DspSettingsScreen → adjust compression, noise, voice emphasis
 *   - LearnScreen       → thumbs-up / thumbs-down preference learning
 */
class MainActivity : ComponentActivity() {

    private val engine = OboeEngine()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        showSafetyDisclaimerOnce()

        setContent {
            MaterialTheme {
                OpenHearApp(engine)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        engine.stop()
    }

    // --- Safety disclaimer shown exactly once per install -------------------

    private fun showSafetyDisclaimerOnce() {
        val prefs = getSharedPreferences("openhear", MODE_PRIVATE)
        if (!prefs.getBoolean("disclaimer_shown", false)) {
            Toast.makeText(
                this,
                "⚠️ EXPERIMENTAL — NOT a medical device. Consult an audiologist.",
                Toast.LENGTH_LONG
            ).show()
            prefs.edit().putBoolean("disclaimer_shown", true).apply()
        }
    }
}

// ---------------------------------------------------------------------------
// Compose UI
// ---------------------------------------------------------------------------

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OpenHearApp(engine: OboeEngine) {
    // Current screen — swap this out for a real NavHost when adding navigation.
    var currentScreen by remember { mutableStateOf("home") }
    var isRunning by remember { mutableStateOf(false) }
    var latencyMs by remember { mutableFloatStateOf(0f) }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("OpenHear") })
        }
    ) { innerPadding ->
        when (currentScreen) {
            // Placeholder screens — each will become its own @Composable file.
            "audiogram" -> PlaceholderScreen("Audiogram") { currentScreen = "home" }
            "dsp"       -> PlaceholderScreen("DSP Settings") { currentScreen = "home" }
            "learn"     -> PlaceholderScreen("Learn") { currentScreen = "home" }
            else        -> HomeScreen(
                modifier    = Modifier.padding(innerPadding),
                isRunning   = isRunning,
                latencyMs   = latencyMs,
                onToggle    = {
                    if (isRunning) {
                        engine.stop()
                    } else {
                        engine.start()
                    }
                    isRunning = engine.isRunning()
                    latencyMs = engine.latencyMs()
                },
                onNavigate  = { currentScreen = it }
            )
        }
    }
}

@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    isRunning: Boolean,
    latencyMs: Float,
    onToggle: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // --- Start / Stop button -------------------------------------------
        Button(onClick = onToggle) {
            Text(if (isRunning) "Stop Audio" else "Start Audio")
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Latency readout -----------------------------------------------
        // Target: < 80 ms round-trip. Updated after each toggle.
        Text(
            text = "Latency: ${"%.1f".format(latencyMs)} ms",
            style = MaterialTheme.typography.bodyLarge
        )

        Spacer(modifier = Modifier.height(32.dp))

        // --- Navigation to sub-screens -------------------------------------
        // TODO: Replace with Jetpack Navigation component.
        TextButton(onClick = { onNavigate("audiogram") }) {
            Text("Audiogram")
        }
        TextButton(onClick = { onNavigate("dsp") }) {
            Text("DSP Settings")
        }
        TextButton(onClick = { onNavigate("learn") }) {
            Text("Learn (thumbs up/down)")
        }
    }
}

/** Temporary placeholder for screens that haven't been built yet. */
@Composable
fun PlaceholderScreen(title: String, onBack: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(title, style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        TextButton(onClick = onBack) { Text("← Back") }
    }
}
