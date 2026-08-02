"""
accessibility – motor and sensory access profiles for OpenHear.

An audiogram describes what a user hears.  It says nothing about a limb
whose muscle tone shifts through the day, a startle response, or speech
that varies widely between repetitions — all of which change what the
right haptic, alerting and voice settings actually are.

This package holds that second half of the fit as bounded, declared data
(:mod:`accessibility.profiles`) and the single place it is turned into
behaviour (:mod:`accessibility.adapt`).  The first bundled profile is
``cerebral_palsy``.

Nothing in here is inferred, stored or transmitted: the user declares a
profile or there is none.
"""

from accessibility.adapt import (
    SAFETY_INTENSITY_FLOOR,
    InputGate,
    policy_config_for,
    scale_intensity,
    voice_match_tolerance_db,
)
from accessibility.profiles import (
    ACCESS_PROFILES,
    CEREBRAL_PALSY,
    NEUTRAL,
    AccessProfile,
    get_access_profile,
)

__all__ = [
    "ACCESS_PROFILES",
    "CEREBRAL_PALSY",
    "NEUTRAL",
    "AccessProfile",
    "InputGate",
    "SAFETY_INTENSITY_FLOOR",
    "get_access_profile",
    "policy_config_for",
    "scale_intensity",
    "voice_match_tolerance_db",
]
