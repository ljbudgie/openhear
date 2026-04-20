"""
haptic_mapper.py – audiogram-aware haptic intensity mapping for OpenHear.

Turns sovereign audiogram data into the single intensity byte used by the
OpenHear wristband BLE packet.  Each supported sound class has:

  - a stable sound class id,
  - a haptic pattern id for the micro:bit firmware, and
  - a dominant frequency used for audiogram-weighted personalisation.

Usage:
    mapper = HapticMapper("patient.json")
    packet = mapper.build_command("alarm", confidence=0.9)
"""

from __future__ import annotations

from dataclasses import dataclass

from audiogram.loader import get_thresholds, load_audiogram


@dataclass(frozen=True)
class SoundProfile:
    """Definition of one wristband sound class."""

    sound_class_id: int
    pattern_id: int
    dominant_frequency_hz: int | None
    description: str


SOUND_PROFILES: dict[str, SoundProfile] = {
    "silence": SoundProfile(0, 0, None, "No haptic output."),
    "voice": SoundProfile(1, 1, 1000, "Both motors, gentle 200/100 ms pulse x3."),
    "doorbell": SoundProfile(2, 2, 2000, "Both motors, two sharp 50 ms pulses."),
    "alarm": SoundProfile(3, 3, 3150, "Rapid alternating left/right 30 ms x8."),
    "dog": SoundProfile(4, 4, 500, "Right motor single 150 ms pulse."),
    "traffic": SoundProfile(5, 5, 500, "Left motor single 300 ms pulse."),
    "media": SoundProfile(6, 6, 1000, "Both motors slow 500/500 ms pulse x2."),
}


def clamp_uint8(value: float) -> int:
    """Clamp *value* to the 0–255 byte range."""
    return max(0, min(255, int(round(value))))


def threshold_to_scale(threshold_db_hl: float) -> float:
    """Return the OpenHear haptic scale bucket for a threshold in dB HL."""
    if threshold_db_hl > 60:
        return 1.0
    if threshold_db_hl >= 40:
        return 0.75
    if threshold_db_hl >= 20:
        return 0.5
    return 0.25


class HapticMapper:
    """Map sound classes to personalised haptic intensities."""

    def __init__(
        self,
        audiogram_path: str,
        *,
        comfort_scale: float = 1.0,
        ear_strategy: str = "worst",
    ) -> None:
        self._audiogram = load_audiogram(audiogram_path)
        self.comfort_scale = comfort_scale
        self.ear_strategy = ear_strategy
        self._thresholds = {
            "left": get_thresholds(self._audiogram, "left"),
            "right": get_thresholds(self._audiogram, "right"),
        }

    def get_sound_profile(self, sound_key: str) -> SoundProfile:
        """Return the static profile for *sound_key*."""
        try:
            return SOUND_PROFILES[sound_key]
        except KeyError as exc:
            raise KeyError(
                f"Unsupported sound class {sound_key!r}. "
                f"Expected one of: {', '.join(sorted(SOUND_PROFILES))}."
            ) from exc

    def get_threshold(self, frequency_hz: int, ear: str) -> float:
        """Return the interpolated threshold for *ear* at *frequency_hz*."""
        return _interpolate_threshold(self._thresholds[ear], frequency_hz)

    def get_intensity(self, sound_key: str, *, confidence: float = 1.0) -> int:
        """Return the personalised intensity byte for *sound_key*."""
        profile = self.get_sound_profile(sound_key)
        if profile.dominant_frequency_hz is None or sound_key == "silence":
            return 0

        left = self.get_threshold(profile.dominant_frequency_hz, "left")
        right = self.get_threshold(profile.dominant_frequency_hz, "right")
        threshold = _combine_ears(left, right, strategy=self.ear_strategy)
        scaled = 255 * threshold_to_scale(threshold) * self.comfort_scale * max(0.0, confidence)
        return clamp_uint8(scaled)

    def build_command(self, sound_key: str, *, confidence: float = 1.0) -> tuple[int, int, int]:
        """Return ``(sound_class_id, intensity, pattern_id)`` for *sound_key*."""
        profile = self.get_sound_profile(sound_key)
        intensity = self.get_intensity(sound_key, confidence=confidence)
        return (profile.sound_class_id, intensity, profile.pattern_id)


def _combine_ears(left: float, right: float, *, strategy: str) -> float:
    """Reduce left/right thresholds to one haptic-driving threshold."""
    strategy = strategy.lower().strip()
    if strategy == "worst":
        return max(left, right)
    if strategy == "average":
        return (left + right) / 2.0
    if strategy == "better":
        return min(left, right)
    raise ValueError("ear_strategy must be 'worst', 'average', or 'better'.")


def _interpolate_threshold(thresholds: list[tuple[int, int]], target_frequency_hz: int) -> float:
    """Linearly interpolate a threshold at *target_frequency_hz*."""
    if not thresholds:
        raise ValueError("Cannot interpolate from an empty threshold list.")

    if target_frequency_hz <= thresholds[0][0]:
        return float(thresholds[0][1])
    if target_frequency_hz >= thresholds[-1][0]:
        return float(thresholds[-1][1])

    for (freq_a, db_a), (freq_b, db_b) in zip(thresholds, thresholds[1:]):
        if target_frequency_hz == freq_a:
            return float(db_a)
        if freq_a <= target_frequency_hz <= freq_b:
            if freq_a == freq_b:
                return float(db_a)
            position = (target_frequency_hz - freq_a) / (freq_b - freq_a)
            return float(db_a + ((db_b - db_a) * position))

    return float(thresholds[-1][1])
