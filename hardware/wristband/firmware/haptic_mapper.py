"""OpenHear wristband v1 haptic skin-mapping library.

Code licence: MIT OR Apache-2.0. The mapper converts Bark-band energies,
audiogram JSON data, and optional IMU pose into deterministic actuator events for
24-, 64-, or 128-channel wrist arrays. It is local-only by design: no cloud or
phone is needed for the acoustic-to-skin path.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, exp, floor, pi
from typing import Iterable, Mapping, Sequence

BARK_BAND_CENTRES_HZ: tuple[int, ...] = (
    50,
    150,
    250,
    350,
    450,
    570,
    700,
    840,
    1000,
    1170,
    1370,
    1600,
    1850,
    2150,
    2500,
    2900,
    3400,
    4000,
    4800,
    5800,
    7000,
    8500,
    10500,
    13500,
)

COMMON_PATTERNS: dict[str, int] = {
    "silence": 0,
    "voice": 1,
    "alarm": 2,
    "directional_speech": 3,
    "music": 4,
    "doorbell": 5,
    "traffic": 6,
    "overhead": 7,
    "v0_compat": 240,
}


@dataclass(frozen=True)
class ImuPose:
    """Minimal arm-pose state used to stabilise world azimuth on the wrist."""

    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0


@dataclass(frozen=True)
class HapticEvent:
    """One scheduled actuator event."""

    actuator_index: int
    ring: int
    column: int
    drive_frequency_hz: int
    intensity: int
    start_ms: int
    duration_ms: int
    pattern_id: int


@dataclass(frozen=True)
class WristbandLayout:
    """Physical lattice geometry for a wristband build."""

    actuator_count: int = 24
    ring_count: int | None = None

    def __post_init__(self) -> None:
        if self.actuator_count not in (24, 64, 128):
            raise ValueError("actuator_count must be 24, 64, or 128")

    @property
    def rings(self) -> int:
        if self.ring_count is not None:
            return self.ring_count
        if self.actuator_count == 24:
            return 1
        if self.actuator_count == 64:
            return 4
        return 8

    @property
    def columns(self) -> int:
        return self.actuator_count // self.rings

    def index(self, ring: int, column: int) -> int:
        return (ring % self.rings) * self.columns + (column % self.columns)


class HapticSkinMapper:
    """Map acoustic features onto the OpenHear wrist skin lattice."""

    def __init__(self, layout: WristbandLayout | None = None, comfort_scale: float = 1.0) -> None:
        self.layout = layout or WristbandLayout()
        self.comfort_scale = max(0.0, min(1.0, comfort_scale))

    def render_bark_frame(
        self,
        bark_energies: Sequence[float],
        audiogram: Mapping[str, object] | None = None,
        imu_pose: ImuPose | None = None,
        *,
        azimuth_deg: float = 0.0,
        elevation_deg: float = 0.0,
        distance_m: float = 1.0,
        pattern: str = "voice",
    ) -> list[HapticEvent]:
        """Return actuator events for one low-latency Bark-band frame."""
        if not bark_energies:
            return []
        weighted = [
            self._weight_band(i, energy, audiogram) for i, energy in enumerate(bark_energies)
        ]
        max_energy = max(weighted) or 1.0
        origin_column = self.azimuth_to_column(azimuth_deg, imu_pose)
        ring = self.elevation_to_ring(elevation_deg)
        decay = self.distance_decay(distance_m)
        pattern_id = COMMON_PATTERNS.get(pattern, COMMON_PATTERNS["voice"])
        events: list[HapticEvent] = []
        for band, energy in enumerate(weighted[: len(BARK_BAND_CENTRES_HZ)]):
            if energy <= 0:
                continue
            column = (origin_column + self.band_to_column(band)) % self.layout.columns
            intensity = self._intensity_byte((energy / max_energy) * decay)
            if intensity == 0:
                continue
            events.append(
                HapticEvent(
                    actuator_index=self.layout.index(ring, column),
                    ring=ring,
                    column=column,
                    drive_frequency_hz=self.band_to_drive_frequency(band),
                    intensity=intensity,
                    start_ms=(band % 4) * 2,
                    duration_ms=8 if pattern in {"voice", "directional_speech"} else 12,
                    pattern_id=pattern_id,
                )
            )
        return events

    def render_spatial_cue(
        self,
        azimuth_deg: float,
        elevation_deg: float,
        distance_m: float,
        imu_pose: ImuPose | None = None,
        *,
        intensity: float = 1.0,
        pattern: str = "directional_speech",
    ) -> list[HapticEvent]:
        """Render apparent motion/funnelling for a 360° spatial cue."""
        origin = self.azimuth_to_column(azimuth_deg, imu_pose)
        ring = self.elevation_to_ring(elevation_deg)
        base = self._intensity_byte(intensity * self.distance_decay(distance_m))
        pattern_id = COMMON_PATTERNS.get(pattern, COMMON_PATTERNS["directional_speech"])
        events = []
        for step, offset in enumerate((0, 1, -1, 2, -2)):
            column = (origin + offset) % self.layout.columns
            events.append(
                HapticEvent(
                    actuator_index=self.layout.index(ring, column),
                    ring=ring,
                    column=column,
                    drive_frequency_hz=180 + 20 * step,
                    intensity=max(0, base - step * 28),
                    start_ms=step * 4,
                    duration_ms=14,
                    pattern_id=pattern_id,
                )
            )
        return events

    def v0_compat_packet(self, events: Iterable[HapticEvent]) -> tuple[int, int, int]:
        """Compress v1 events into the legacy 3-byte micro:bit packet."""
        event_list = list(events)
        if not event_list:
            return (0, 0, 0)
        strongest = max(event_list, key=lambda event: event.intensity)
        sound_class_id = 1 if strongest.pattern_id in (1, 3) else min(6, strongest.pattern_id)
        return (sound_class_id, strongest.intensity, COMMON_PATTERNS["v0_compat"])

    def azimuth_to_column(self, azimuth_deg: float, imu_pose: ImuPose | None = None) -> int:
        pose_yaw = imu_pose.yaw_deg if imu_pose else 0.0
        corrected = (azimuth_deg - pose_yaw) % 360.0
        return int(floor((corrected / 360.0) * self.layout.columns)) % self.layout.columns

    def elevation_to_ring(self, elevation_deg: float) -> int:
        normalised = max(-90.0, min(90.0, elevation_deg))
        return int(round(((normalised + 90.0) / 180.0) * (self.layout.rings - 1)))

    def band_to_column(self, band: int) -> int:
        return int(
            round((band / max(1, len(BARK_BAND_CENTRES_HZ) - 1)) * (self.layout.columns - 1))
        )

    def band_to_drive_frequency(self, band: int) -> int:
        phase = band / max(1, len(BARK_BAND_CENTRES_HZ) - 1)
        return int(round(20 + (600 - 20) * (0.5 - 0.5 * cos(pi * phase))))

    def distance_decay(self, distance_m: float) -> float:
        return max(0.08, min(1.0, exp(-max(0.0, distance_m - 0.5) / 5.0)))

    def _weight_band(
        self, band: int, energy: float, audiogram: Mapping[str, object] | None
    ) -> float:
        threshold = _threshold_for_band(band, audiogram)
        if threshold >= 90:
            gain = 1.8
        elif threshold >= 60:
            gain = 1.45
        elif threshold >= 40:
            gain = 1.2
        elif threshold >= 20:
            gain = 1.0
        else:
            gain = 0.75
        return max(0.0, float(energy)) * gain

    def _intensity_byte(self, normalised: float) -> int:
        shaped = max(0.0, min(1.0, normalised)) ** 0.65
        return max(0, min(255, int(round(255 * shaped * self.comfort_scale))))


def _threshold_for_band(band: int, audiogram: Mapping[str, object] | None) -> float:
    if not audiogram:
        return 40.0
    thresholds = audiogram.get("thresholds") or audiogram.get("ears") or audiogram
    values: list[float] = []
    if isinstance(thresholds, Mapping):
        for ear_data in thresholds.values():
            if isinstance(ear_data, Mapping):
                values.extend(_values_from_threshold_mapping(ear_data))
            elif isinstance(ear_data, Sequence) and not isinstance(ear_data, (str, bytes)):
                values.extend(float(v) for v in ear_data if isinstance(v, (int, float)))
    if not values:
        return 40.0
    return values[min(len(values) - 1, band)]


def _values_from_threshold_mapping(mapping: Mapping[object, object]) -> list[float]:
    pairs: list[tuple[float, float]] = []
    for key, value in mapping.items():
        if isinstance(value, (int, float)):
            try:
                pairs.append((float(key), float(value)))
            except (TypeError, ValueError):
                pairs.append((float(len(pairs)), float(value)))
    return [value for _, value in sorted(pairs)]
