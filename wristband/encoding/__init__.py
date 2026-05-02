"""Falsifiable haptic-encoding reference implementations for the OpenHear wristband.

This package contains *specifications* and *reference encoders* — not
production firmware. Each version (``v0``, ``v1``, ...) is a frozen,
documented mapping from acoustic input to per-motor drive signals so
that psychoacoustic experiments and replication studies can target an
unambiguous artifact.

See ``v0_spec.md`` for the full specification of the v0 baseline encoder.
"""

from wristband.encoding.v0 import V0Encoder, V0EncoderConfig

__all__ = ["V0Encoder", "V0EncoderConfig"]
