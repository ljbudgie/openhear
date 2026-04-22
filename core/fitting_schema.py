"""
fitting_schema.py – dataclass schema for hearing aid fitting profiles.

Defines typed Python dataclasses that represent the fitting parameters for
Phonak Naída M70-SP (Marvel platform) and Signia Insio 7AX (AX platform)
hearing aids.  These dataclasses act as the canonical in-memory representation
used throughout the pipeline; JSON from read_fitting.py is deserialized into
one of these structures before being consumed by dsp/config.py or
audiogram/reader.py.

Why dataclasses:
  - Zero dependencies, no ORM or serialization library required.
  - Field names and types are self-documenting.
  - Easy to extend with default_factory for mutable defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# ── Shared sub-structures ────────────────────────────────────────────────────

@dataclass
class GainTable:
    """Frequency-specific gain values (dB SPL) at a set of standard audiometric
    frequencies.  The `frequencies_hz` and `gains_db` lists must have the same
    length.
    """
    frequencies_hz: List[int] = field(default_factory=lambda: [
        250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000
    ])
    gains_db: List[float] = field(default_factory=lambda: [0.0] * 9)


@dataclass
class CompressionChannel:
    """WDRC parameters for a single frequency channel."""
    center_frequency_hz: int = 1000
    compression_ratio: float = 2.0    # linear ratio, e.g. 2.0 = 2:1
    knee_point_db: float = 50.0       # input SPL at which compression engages
    attack_ms: float = 5.0            # attack time in milliseconds
    release_ms: float = 50.0          # release time in milliseconds
    max_output_db: float = 110.0      # output SPL ceiling (MPO)


# ── Device-specific fitting profiles ────────────────────────────────────────

@dataclass
class PhonakFittingProfile:
    """Fitting profile for Phonak Naída M70-SP (Marvel platform, size 13 BTE).

    Fields map as closely as possible to the SoundRecover2 / Target fitting
    concepts without using any proprietary SDK or data format.

    Attributes:
        device_serial:       Serial number read from the aid.
        program_name:        Name of the active listening program (e.g. 'AutoSense').
        gain_table:          Prescribed gain by frequency.
        compression_channels:
                             Per-channel WDRC settings (typically 20 channels on
                             Marvel platform; fewer here for tractable representation).
        treble_boost_db:     Additional high-frequency lift applied by SoundRecover2
                             frequency lowering (stored as a net boost for simulation).
        noise_reduction_active:
                             Whether automatic noise reduction is enabled.
        directional_mode:    Microphone directional strategy ('omni', 'cardioid',
                             'super-cardioid').
        bluetooth_enabled:   Whether Marvel Bluetooth Classic streaming is active.
    """
    device_serial: str = ""
    program_name: str = "AutoSense OS 4.0"
    gain_table: GainTable = field(default_factory=GainTable)
    compression_channels: List[CompressionChannel] = field(
        default_factory=lambda: [
            CompressionChannel(center_frequency_hz=f)
            for f in [500, 1000, 2000, 4000, 6000]
        ]
    )
    treble_boost_db: float = 0.0
    noise_reduction_active: bool = True
    directional_mode: str = "cardioid"
    bluetooth_enabled: bool = True


@dataclass
class SigniaFittingProfile:
    """Fitting profile for Signia Insio 7AX (AX platform, ITC custom mould).

    The AX platform uses a split-processing architecture ('Augmented Xperience')
    where speech and background noise are processed on separate signal paths.
    Fields below represent the outcome parameters, not the internal split-
    processing state.

    Attributes:
        device_serial:       Serial number read from the aid.
        program_name:        Name of the active program (e.g. 'Universal').
        gain_table:          Prescribed gain by frequency.
        compression_channels:
                             Per-channel WDRC settings.
        own_voice_processing:
                             Whether 'Own Voice Processing' (OVP) is enabled.
        noise_reduction_level:
                             Noise reduction aggressiveness: 0 (off) – 3 (strong).
        directional_mode:    Microphone strategy ('omni', 'narrow', 'super-narrow').
        mfi_bluetooth_enabled:
                             Whether Made-for-iPhone (MFi) BLE streaming is active.
        vent_type:           Vent configuration of the custom mould ('closed',
                             'small', 'medium', 'large', 'open').
    """
    device_serial: str = ""
    program_name: str = "Universal"
    gain_table: GainTable = field(default_factory=GainTable)
    compression_channels: List[CompressionChannel] = field(
        default_factory=lambda: [
            CompressionChannel(center_frequency_hz=f)
            for f in [500, 1000, 2000, 4000, 6000]
        ]
    )
    own_voice_processing: bool = True
    noise_reduction_level: int = 2
    directional_mode: str = "narrow"
    mfi_bluetooth_enabled: bool = True
    vent_type: str = "closed"


# ── Factory helpers ──────────────────────────────────────────────────────────

def phonak_profile_from_dict(data: dict) -> PhonakFittingProfile:
    """Deserialise a plain dict (e.g. loaded from JSON) into a
    :class:`PhonakFittingProfile`.

    Unknown keys are silently ignored so that newer firmware payloads do not
    break older pipeline builds.
    """
    profile = PhonakFittingProfile()
    profile.device_serial = data.get("device_serial", "")
    profile.program_name = data.get("program_name", profile.program_name)
    profile.treble_boost_db = float(data.get("treble_boost_db", 0.0))
    profile.noise_reduction_active = bool(data.get("noise_reduction_active", True))
    profile.directional_mode = data.get("directional_mode", profile.directional_mode)
    profile.bluetooth_enabled = bool(data.get("bluetooth_enabled", True))

    if "gain_table" in data:
        gt = data["gain_table"]
        profile.gain_table = GainTable(
            frequencies_hz=gt.get("frequencies_hz", profile.gain_table.frequencies_hz),
            gains_db=gt.get("gains_db", profile.gain_table.gains_db),
        )

    if "compression_channels" in data:
        profile.compression_channels = [
            CompressionChannel(**ch) for ch in data["compression_channels"]
        ]

    return profile


def signia_profile_from_dict(data: dict) -> SigniaFittingProfile:
    """Deserialise a plain dict (e.g. loaded from JSON) into a
    :class:`SigniaFittingProfile`.
    """
    profile = SigniaFittingProfile()
    profile.device_serial = data.get("device_serial", "")
    profile.program_name = data.get("program_name", profile.program_name)
    profile.own_voice_processing = bool(data.get("own_voice_processing", True))
    profile.noise_reduction_level = int(data.get("noise_reduction_level", 2))
    profile.directional_mode = data.get("directional_mode", profile.directional_mode)
    profile.mfi_bluetooth_enabled = bool(data.get("mfi_bluetooth_enabled", True))
    profile.vent_type = data.get("vent_type", profile.vent_type)

    if "gain_table" in data:
        gt = data["gain_table"]
        profile.gain_table = GainTable(
            frequencies_hz=gt.get("frequencies_hz", profile.gain_table.frequencies_hz),
            gains_db=gt.get("gains_db", profile.gain_table.gains_db),
        )

    if "compression_channels" in data:
        profile.compression_channels = [
            CompressionChannel(**ch) for ch in data["compression_channels"]
        ]

    return profile
