"""
user_config.py – structured user configuration for the OpenHear pipeline.

This module exposes the YAML/JSON-driven configuration scheme described
in the OpenHear master execution prompt: a single :class:`Config`
dataclass loaded from ``~/.openhear/config.yaml`` (or any other path the
user points at) with sensible defaults if the file is absent.

It is intentionally additive to :mod:`dsp.config`, which holds the
existing module-level constants used at import time by the live DSP
stages (compression, noise reduction, etc.).  The two will continue to
co-exist while the pipeline migrates to runtime configuration; new
features should consume :class:`Config` instead of touching
:mod:`dsp.config` directly.

Key entry points:
    * :func:`load_config` — load and validate a config file with defaults.
    * :func:`Config` — typed dataclass holding every tunable parameter.
    * :func:`default_config_path` — canonical default
      (``~/.openhear/config.yaml``).
    * :func:`Config.to_dict` / :func:`Config.from_dict` — round-trip with
      plain-Python dicts (used internally for JSON Schema validation).

A JSON Schema describing the file format ships alongside this module at
``dsp/config.schema.json``.  The schema is the source of truth for which
fields are accepted; this module mirrors it as a typed dataclass.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

#: Canonical relative location of the user's config file.
DEFAULT_CONFIG_RELATIVE_PATH = Path(".openhear") / "config.yaml"


def default_config_path() -> Path:
    """Return ``~/.openhear/config.yaml`` as a :class:`Path`."""
    return Path.home() / DEFAULT_CONFIG_RELATIVE_PATH


# ── Sub-sections ────────────────────────────────────────────────────────────


@dataclass
class CompressionConfig:
    """Wide Dynamic Range Compression parameters.

    Attributes:
        ratio: Compression ratio above the knee (1.0 = linear).
        knee_db: Input level (dBFS) at which compression engages.
        attack_ms: Time the gain reduction takes to engage.
        release_ms: Time the gain recovers after a loud sound.
    """

    ratio: float = 2.5
    knee_db: float = -40.0
    attack_ms: float = 5.0
    release_ms: float = 50.0


@dataclass
class NoiseConfig:
    """Noise gate and noise-reduction parameters."""

    floor_db: float = -45.0
    reduction_strength: float = 0.6
    gate_enabled: bool = True


@dataclass
class VoiceConfig:
    """Voice (speech band) emphasis parameters."""

    boost_hz: tuple[float, float] = (1000.0, 4000.0)
    boost_db: float = 6.0


@dataclass
class BeamformingConfig:
    """Microphone array beamforming parameters."""

    enabled: bool = False
    width_deg: float = 60.0
    direction_deg: float = 0.0


@dataclass
class SystemConfig:
    """Audio I/O and runtime parameters."""

    sample_rate: int = 16_000
    buffer_size: int = 256
    input_device: int | None = None
    output_device: int | None = None


# ── Top-level Config ────────────────────────────────────────────────────────


@dataclass
class Config:
    """Top-level OpenHear user configuration.

    Attributes:
        audiogram_path: Optional path (with ``~`` expansion) to the
            user's audiogram JSON file.  ``None`` means the pipeline
            should run with a flat (population-average) gain curve.
        compression: WDRC sub-config.
        noise: Noise gate / reduction sub-config.
        voice: Voice emphasis sub-config.
        beamforming: Beamformer sub-config.
        system: Audio I/O sub-config.
    """

    audiogram_path: str | None = None
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    noise: NoiseConfig = field(default_factory=NoiseConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    beamforming: BeamformingConfig = field(default_factory=BeamformingConfig)
    system: SystemConfig = field(default_factory=SystemConfig)

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-Python dict representation suitable for YAML."""
        out = asdict(self)
        # tuples render as lists in YAML/JSON; normalise here too.
        out["voice"]["boost_hz"] = list(self.voice.boost_hz)
        return out

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "Config":
        """Build a :class:`Config` from a parsed dict, applying defaults.

        Unknown top-level keys are ignored with a warning rather than an
        error so older config files keep working as we extend the schema.

        Args:
            data: Parsed mapping (e.g. from ``yaml.safe_load``), or
                ``None`` for "use all defaults".

        Returns:
            A populated :class:`Config`.

        Raises:
            ValueError: If a section is the wrong type (e.g. compression
                provided as a list rather than a mapping) or a required
                numeric field is non-finite/out-of-range.
        """
        if data is None:
            return cls()
        if not isinstance(data, Mapping):
            raise ValueError(
                f"Config root must be a mapping, got {type(data).__name__}."
            )

        known = {
            "audiogram_path", "compression", "noise",
            "voice", "beamforming", "system",
        }
        for key in data.keys():
            if key not in known:
                logger.warning("Ignoring unknown config key: %r", key)

        return cls(
            audiogram_path=_coerce_optional_str(data.get("audiogram_path")),
            compression=_section(CompressionConfig, data.get("compression")),
            noise=_section(NoiseConfig, data.get("noise")),
            voice=_voice_section(data.get("voice")),
            beamforming=_section(BeamformingConfig, data.get("beamforming")),
            system=_system_section(data.get("system")),
        )


# ── Loading ────────────────────────────────────────────────────────────────


def load_config(path: str | Path | None = None) -> Config:
    """Load an OpenHear user config from disk, falling back to defaults.

    The lookup order is:

    1. Explicit ``path`` argument, if provided.
    2. :func:`default_config_path` (``~/.openhear/config.yaml``).
    3. Built-in defaults (no file required).

    Both YAML (``.yaml`` / ``.yml``) and JSON (``.json``) extensions are
    supported.  YAML support requires the ``PyYAML`` dependency listed
    in ``requirements.txt``; if it is unavailable and the user supplied
    a YAML file, a clear :class:`RuntimeError` is raised.

    Args:
        path: Optional explicit config path.  When ``None``, the
            canonical default location is consulted.

    Returns:
        A populated :class:`Config`.  If neither an explicit path nor
        the default path exists, returns ``Config()`` (all defaults).
    """
    target = Path(path) if path is not None else default_config_path()
    if not target.exists():
        if path is not None:
            raise FileNotFoundError(f"Config file not found: {target}")
        logger.info("No user config at %s; using built-in defaults.", target)
        return Config()

    text = target.read_text(encoding="utf-8")
    suffix = target.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = _load_yaml(text, target)
    elif suffix == ".json":
        data = json.loads(text) if text.strip() else {}
    else:
        # Best-effort: try YAML first (it's a JSON superset), then JSON.
        try:
            data = _load_yaml(text, target)
        except RuntimeError:
            data = json.loads(text)

    return Config.from_dict(data)


# ── Internal helpers ────────────────────────────────────────────────────────


def _load_yaml(text: str, target: Path) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            f"Cannot load YAML config {target}: install PyYAML "
            "(pip install pyyaml)."
        ) from exc
    return yaml.safe_load(text) or {}


def _section(cls: type, data: Any) -> Any:
    """Instantiate a sub-dataclass from a mapping, applying defaults."""
    if data is None:
        return cls()
    if not isinstance(data, Mapping):
        raise ValueError(
            f"{cls.__name__} section must be a mapping, got "
            f"{type(data).__name__}."
        )
    valid_fields = {f for f in cls.__dataclass_fields__}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    for key in data.keys():
        if key not in valid_fields:
            logger.warning(
                "Ignoring unknown %s key: %r", cls.__name__, key,
            )
    return cls(**filtered)


def _voice_section(data: Any) -> VoiceConfig:
    """Voice section needs special handling for the ``boost_hz`` tuple."""
    if data is None:
        return VoiceConfig()
    if not isinstance(data, Mapping):
        raise ValueError(
            f"voice section must be a mapping, got {type(data).__name__}."
        )
    boost_hz = data.get("boost_hz", VoiceConfig.boost_hz)
    if isinstance(boost_hz, (list, tuple)):
        if len(boost_hz) != 2:
            raise ValueError(
                "voice.boost_hz must be a 2-element list [low_hz, high_hz]."
            )
        boost_hz = (float(boost_hz[0]), float(boost_hz[1]))
        if boost_hz[0] >= boost_hz[1]:
            raise ValueError(
                "voice.boost_hz low edge must be strictly below high edge."
            )
    else:
        raise ValueError(
            "voice.boost_hz must be a list/tuple, got "
            f"{type(boost_hz).__name__}."
        )
    return VoiceConfig(
        boost_hz=boost_hz,
        boost_db=float(data.get("boost_db", VoiceConfig.boost_db)),
    )


def _system_section(data: Any) -> SystemConfig:
    """System section maps ``null`` device IDs to Python ``None``."""
    if data is None:
        return SystemConfig()
    if not isinstance(data, Mapping):
        raise ValueError(
            f"system section must be a mapping, got {type(data).__name__}."
        )
    sample_rate = int(data.get("sample_rate", SystemConfig.sample_rate))
    buffer_size = int(data.get("buffer_size", SystemConfig.buffer_size))
    if sample_rate <= 0:
        raise ValueError(f"system.sample_rate must be positive, got {sample_rate}.")
    if buffer_size <= 0:
        raise ValueError(f"system.buffer_size must be positive, got {buffer_size}.")
    return SystemConfig(
        sample_rate=sample_rate,
        buffer_size=buffer_size,
        input_device=_coerce_optional_int(data.get("input_device")),
        output_device=_coerce_optional_int(data.get("output_device")),
    )


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _coerce_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
