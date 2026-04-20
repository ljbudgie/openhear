# OpenHear Architecture

High-level map of the codebase.  Read this first if you want to know
*where* something lives; for *why* each stage exists see
`docs/TUNING_GUIDE.md`.

```
openhear/
├── audiogram/   ← Read, write, compare, visualise user audiograms.
│                  Canonical dataclass in audiogram/audiogram.py.
│
├── dsp/         ← Real-time DSP stages: noise reduction, WDRC
│                  compression, voice clarity, feedback cancellation,
│                  own-voice bypass, biquad filter bank, beamforming,
│                  audiogram → prescription, runtime metrics.
│                  Entry point: python -m dsp.pipeline
│
├── stream/      ← Audio I/O and transport: Bluetooth output, virtual
│                  audio cable detection, round-trip latency test,
│                  raw/processed recorder.
│
├── core/        ← Noahlink Wireless 2 bridge: HID wrapper
│                  (core/noahlink.py), framing parser (core/protocol.py),
│                  fitting dataclasses (core/fitting_data.py), read /
│                  write / backup CLIs.  See docs/PROTOCOL_NOTES.md.
│
├── hardware/    ← Out-of-tree open hearing-aid hardware: Tympan SDK
│                  integration, shell manufacturing notes, safety docs.
│
├── learn/       ← Listener preference capture and adaptive tuning
│                  (Phase 6 scaffolding — every function is currently
│                  a documented NotImplementedError).
│
├── voice/       ← Legacy voice-reference / analysis helpers.
├── wristband/   ← Prototype haptic wristband transport.
├── examples/    ← Sample config, sample audiogram, offline demo.
└── tests/       ← pytest suite — 500+ tests, no real hardware needed.
```

## Data flow (live-fitting mode)

```
microphone
   │
   ▼
┌──────────────────────┐
│  stream.recorder     │─── optional raw.wav
└──────────┬───────────┘
           ▼
┌──────────────────────────────────────────────┐
│  dsp.pipeline                                │
│    SpectralSubtractor  → WDRCompressor       │
│    → VoiceClarityEnhancer                    │
│    → FeedbackCanceller → OwnVoiceBypass      │
└──────────┬───────────────────────────────────┘
           ▼ processed audio
┌──────────────────────┐
│  stream.bluetooth    │──→ paired hearing aid (A2DP / MFi)
└──────────────────────┘
```

The DSP chain is driven by a user `config.yaml` parsed by
`dsp.user_config` against `dsp/config.schema.json`.  An
`Audiogram` dataclass flows through `dsp.audiogram_profile.prescribe()`
to produce per-band gains and compression ratios.

## Data flow (fitting read / write)

```
core.noahlink.NoahlinkDevice
     │ send GET_FITTING frame
     ▼
core.protocol.decode_session
     │ produces ParsedFrame objects
     ▼
core.fitting_data.FittingSession
     │
     ├──→ core.backup.write_backup  (safety net)
     │
     └──→ core.write_fitting.write_safe_parameters
               (allow-list gated, transmit=True not yet implemented)
```

## Stability guarantees

* Public API surface is the `Audiogram`, `FittingSession`,
  `DeviceInfo`, `GainTable`, `CompressionProfile`, `MPOProfile`,
  `ProgrammeSlot`, `MetricsLogger`, `BluetoothAudioOutput`,
  `NoahlinkDevice`, and the CLI entry points registered in
  `pyproject.toml`.
* Anything in an internal `_helper` module or named with a leading
  underscore may change without notice.
