# voice/ — Vocal Frequency Analysis for OpenHear 🎙️

### Your voice. Your frequencies. Your development.

---

## What this is

This module provides real-time vocal frequency analysis for hearing aid users who want to develop their voice using accurate auditory feedback — possibly for the first time.

If you have sensorineural hearing loss, you have never heard your own voice through a clean, unprocessed signal.  Every adjustment you have ever made to your pitch, tone, or resonance was based on incomplete information.  Your brain has been guessing.

This module replaces the guessing with measurement.

---

## What this is not

This is **not** a voice cloner.  The reference comparison is a training target, not an imitation target.  The goal is not to sound like someone else — it is to understand your own vocal frequency profile and develop control over it.

The reference is a **mirror**, not a master.

---

## How it works

### The audiogram connection

The `audiogram/` module tells you which frequencies your ears cannot monitor.  This module tells you what your voice is doing in those exact frequency ranges.

If your audiogram shows a 60 dB loss at 4 kHz, you have never been able to hear whether your voice has energy at 4 kHz.  This module shows you — in real time — whether it does.

### The neuroplasticity principle

The brain develops vocal control through feedback loops.  Hearing listeners adjust their voice constantly based on what they hear.  If you cannot hear certain frequencies, you cannot adjust them.

Consistent, accurate visual feedback in those missing ranges allows the brain to build new motor-auditory associations.  This is not speculation — it is the same principle behind cochlear implant rehabilitation, speech therapy with spectrograms, and vocal training with real-time pitch displays.

The difference here is that you own the tool, you own the data, and you decide the target.

---

## Components

### `config.py` — User-tunable parameters

All analysis settings are plain Python constants.  Open the file, change a value, save.

| Parameter | Default | Purpose |
|---|---|---|
| `MIC_DEVICE_INDEX` | `None` | PyAudio device index (None = system default) |
| `SAMPLE_RATE` | `44100` | Capture sample rate in Hz |
| `FRAME_BUFFER` | `1024` | Samples per analysis frame |
| `REFERENCE_BANDPASS` | `(80, 8000)` | Vocal frequency isolation range (Hz) |
| `FORMANT_PEAKS` | `3` | Number of formant peaks to extract (F1, F2, F3) |
| `MATCH_TOLERANCE_DB` | `3.0` | Energy match threshold for green highlighting |
| `GAP_THRESHOLD_DB` | `6.0` | Energy gap threshold for red highlighting |

### `analyser.py` — Real-time vocal frequency analyser

Captures microphone input and extracts vocal features from each frame:
- **Fundamental frequency (F0):** your pitch in Hz
- **Formants (F1, F2, F3):** the resonant peaks that define vowel quality and vocal timbre
- **Spectral envelope:** the overall shape of your vocal energy across all frequencies
- **Harmonic-to-noise ratio (HNR):** how clear and periodic your voice is (higher = cleaner)
- **Energy (dBFS):** how loud the frame is

```python
from voice.analyser import open_mic_stream, capture_snapshot
from voice import config

# Open the microphone.
pa, stream = open_mic_stream()

try:
    # Capture and analyse one frame.
    snapshot = capture_snapshot(stream)

    print(f"Fundamental: {snapshot.fundamental_frequency_hz:.1f} Hz")
    print(f"Formants: {snapshot.formants}")
    print(f"HNR: {snapshot.hnr_db:.1f} dB")
    print(f"Energy: {snapshot.energy_db:.1f} dBFS")
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
```

You can also analyse samples directly without a microphone:

```python
import numpy as np
from voice.analyser import analyse_frame

# Analyse a buffer of float32 samples.
samples = np.random.randn(1024).astype(np.float32) * 0.1
snapshot = analyse_frame(samples, sample_rate=44100)
```

### `reference.py` — Reference artist frequency profile loader

Loads a lossless recording (WAV or FLAC), isolates vocal frequencies, and computes an average spectral profile.  Export a track from your DAW or rip a lossless copy of an artist you want to study.

```python
from voice.reference import load_reference

# Load a reference track.
profile = load_reference("path/to/reference.wav", artist_name="Target Voice")

print(f"Artist: {profile.artist_name}")
print(f"Average formants: {profile.avg_formants}")
print(f"Dominant range: {profile.dominant_frequency_range}")
```

### `compare.py` — Real-time comparison engine

Compares your live voice against a reference profile across three frequency bands:
- **Low (80–300 Hz):** fundamental, chest resonance
- **Mid (300–2000 Hz):** vowel formants, vocal body
- **High (2000–8000 Hz):** consonant articulation, sibilance

```python
from voice.compare import compare

# Compare a live snapshot against the reference.
result = compare(snapshot, profile)

print(f"Band differences: {result.band_differences}")
print(f"Underused formants: {result.underused_formants}")
print(f"Similarity: {result.similarity_score:.0%}")
```

### `feedback.py` — Terminal-based real-time visual feedback

Renders a live frequency spectrum in the terminal with colour-coded comparison against the reference:

- 🟩 **Green bars:** your energy matches the reference within 3 dB
- 🟥 **Red bars:** your energy is more than 6 dB below the reference
- **Yellow `│`:** reference target line

```python
from voice.analyser import open_mic_stream, capture_snapshot
from voice.reference import load_reference
from voice.compare import compare
from voice.feedback import run_live
import numpy as np

# Load reference.
profile = load_reference("reference.wav")

# Open mic.
pa, stream = open_mic_stream()

def snapshot_gen():
    """Yield snapshots from the mic."""
    try:
        while True:
            yield capture_snapshot(stream)
    except KeyboardInterrupt:
        return

def compare_fn(snap):
    return compare(snap, profile)

try:
    run_live(snapshot_gen(), profile.spectral_envelope, compare_fn)
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
```

---

## Dependencies

All dependencies are already in `requirements.txt`:
- **PyAudio** — microphone capture
- **NumPy** — FFT and array operations
- **SciPy** — peak detection, bandpass filtering, resampling
- **soundfile** *(optional)* — required only for FLAC file loading

---

## Data sovereignty

Your voice data never leaves your machine.  There is no cloud processing, no upload, no telemetry.  The microphone stream is analysed locally in real time and discarded after each frame unless you explicitly save it.

The reference profile is computed locally from a file you provide.  No reference data is bundled, downloaded, or scraped.

You own your voice.  This module helps you understand it.
