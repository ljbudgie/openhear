"""
tempo_channel.py – performer's beat channel.

:mod:`therapy.entrainment` renders a *fixed* therapeutic rhythm — pick a
frequency, pick a duration, get a deterministic isochronic pulse train for a
clinical session.  A musician on stage needs the same shape of signal driven
by a different source: the *live* tempo of the band.  Set the wrist throbbing
at 120 BPM, then 124, then 122 as the drummer drifts, and the hard-of-hearing
performer feels the pulse locked to the room rather than guessing it from
visual cues alone.

This module adapts entrainment's idea to that live-tempo case by routing it
through the v2 :class:`~stream.haptic_primitive.HapticPrimitive` vocabulary
instead of the v1 fixed therapy packet.  That brings two practical wins:

* The same intensity / spatial balance / sharpness axes that crowd-arousal
  uses are available here, so the tempo channel can be sharp (click on the
  downbeat) or soft (gentle pulse), centred or biased to one side.
* The musical concept of a *bar* is first-class: ``beats_per_bar`` and an
  ``accent_intensity`` boost let the downbeat punch harder than the offbeats
  so the performer can also feel *where in the bar* they are, not just the
  raw pulse rate.

The module is delivery-agnostic (no I/O), pure Python plus the existing
haptic-primitive plumbing, and unit-testable.  Like every other haptic path
in OpenHear, the emitted packets go through
:mod:`stream.haptic_packet`, so any firmware that already speaks the v1
wire format will also respond to a TempoChannel without firmware changes.

Usage::

    channel = TempoChannel(intensity=170, sharpness=0.85, beats_per_bar=4)
    while session_active:
        bpm = tempo_tracker.current_bpm()      # from any source
        channel.update(bpm)
        events = channel.events_for_window(duration_s=1.0)
        send_to_wristband(events)

OpenHear is **not** a metronome substitute for users who need clinical
intervention; it is a sovereign, inspectable channel for performers who
want the room's pulse on their wrist.
"""

from __future__ import annotations

from dataclasses import dataclass

from stream.haptic_primitive import (
    PULSE_RATE_MAX_HZ,
    PULSE_RATE_MIN_HZ,
    SILENCE_PACKET,
    HapticPrimitive,
    PrimitiveEvent,
)

# ── Tempo bounds ──────────────────────────────────────────────────────────────

#: Slowest tempo the channel will accept, in beats per minute.
#:
#: Below ~30 BPM the gaps between pulses exceed two seconds and the wrist
#: stops perceiving the train as a rhythm — it just feels like isolated
#: taps.  Matches the lower end of the practical musical range
#: (very slow ballads, largo tempi).
MIN_BPM: float = 30.0

#: Fastest tempo the channel will accept, in beats per minute.
#:
#: At 300 BPM the period is 200 ms, still cleanly perceivable as discrete
#: pulses.  Above that the wrist starts to feel a continuous buzz rather
#: than a beat, which defeats the point of a tempo channel.
MAX_BPM: float = 300.0

#: Default per-pulse intensity for the tempo channel.  Strong enough to be
#: unambiguous on stage without saturating headroom for any simultaneous
#: alert primitive on a louder class.
DEFAULT_INTENSITY: int = 170

#: Default sharpness for tempo pulses.  A tempo cue feels best as a crisp
#: click rather than a soft throb, so we default toward the sharp end of
#: the axis.
DEFAULT_SHARPNESS: float = 0.85

#: Default smoothing factor (0.0 means "pass live tempo straight through").
#: Values in ``(0, 1)`` apply an exponential moving average to ``set_bpm``
#: updates so a jittery live tempo tracker does not yank the haptic rate
#: around between every audio frame.
DEFAULT_SMOOTHING: float = 0.0


# ── Public helpers ────────────────────────────────────────────────────────────


def bpm_to_pulse_rate_hz(bpm: float) -> float:
    """Convert *bpm* (beats per minute) to a haptic pulse rate in Hz.

    ``120 BPM → 2.0 Hz``.  Raises :class:`ValueError` if *bpm* is outside
    the supported range :data:`MIN_BPM`–:data:`MAX_BPM`.
    """
    _validate_bpm(bpm)
    return bpm / 60.0


def pulse_rate_hz_to_bpm(pulse_rate_hz: float) -> float:
    """Convert a haptic pulse rate in Hz to BPM.

    ``2.0 Hz → 120 BPM``.  Raises :class:`ValueError` if *pulse_rate_hz*
    is outside the :data:`~stream.haptic_primitive.PULSE_RATE_MIN_HZ`–
    :data:`~stream.haptic_primitive.PULSE_RATE_MAX_HZ` haptic-primitive
    range.
    """
    if not PULSE_RATE_MIN_HZ <= pulse_rate_hz <= PULSE_RATE_MAX_HZ:
        raise ValueError(
            f"pulse_rate_hz must be in [{PULSE_RATE_MIN_HZ}, {PULSE_RATE_MAX_HZ}], "
            f"got {pulse_rate_hz!r}."
        )
    return pulse_rate_hz * 60.0


# ── Result type for events_for_window ─────────────────────────────────────────


@dataclass(frozen=True)
class WindowedBeats:
    """Output of :meth:`TempoChannel.events_for_window`.

    Attributes:
        events:   Chronologically ordered :class:`PrimitiveEvent` list for
                  the window, relative to the window start (``at_ms = 0``
                  is the first sample of the window).
        bar_starts_ms: Times within the window at which a new bar starts
                       (i.e. a beat with ``beat_in_bar == 0``).  Empty when
                       ``beats_per_bar`` is unset.
    """

    events: list[PrimitiveEvent]
    bar_starts_ms: list[float]


# ── TempoChannel ──────────────────────────────────────────────────────────────


class TempoChannel:
    """Live-tempo beat channel for the wristband.

    Maps a stream of BPM updates onto a sequence of
    :class:`~stream.haptic_primitive.HapticPrimitive` pulses.  Phase is
    tracked across calls to :meth:`events_for_window` so back-to-back
    windows form one continuous beat train even when *bpm* changes.

    Args:
        intensity: On-pulse intensity, 0–255.  Default
            :data:`DEFAULT_INTENSITY`.
        sharpness: Pulse sharpness, 0.0 (soft throb) to 1.0 (sharp click).
            Default :data:`DEFAULT_SHARPNESS`.
        spatial_balance: −1.0 (left only) to +1.0 (right only).  Default
            0.0 (centre — both wrists, room-omnidirectional pulse).
        smoothing: Exponential-moving-average weight applied to incoming
            BPM updates, ``[0, 1)``.  ``0.0`` (default) passes live tempo
            through unchanged; ``0.5`` averages each new reading 50/50
            with the prior smoothed value.
        beats_per_bar: When set (>= 1), the channel marks downbeats — the
            first beat of every bar is emitted at *accent_intensity*
            instead of *intensity*.  ``None`` (default) means every beat is
            equal.
        accent_intensity: Intensity used for the downbeat when
            *beats_per_bar* is set.  Defaults to ``min(255, intensity + 50)``
            so the accent is unambiguously stronger than the offbeats.
    """

    def __init__(
        self,
        *,
        intensity: int = DEFAULT_INTENSITY,
        sharpness: float = DEFAULT_SHARPNESS,
        spatial_balance: float = 0.0,
        smoothing: float = DEFAULT_SMOOTHING,
        beats_per_bar: int | None = None,
        accent_intensity: int | None = None,
    ) -> None:
        if not 0 <= intensity <= 255:
            raise ValueError(f"intensity must be in [0, 255], got {intensity!r}.")
        if not 0.0 <= sharpness <= 1.0:
            raise ValueError(f"sharpness must be in [0, 1], got {sharpness!r}.")
        if not -1.0 <= spatial_balance <= 1.0:
            raise ValueError(f"spatial_balance must be in [-1, 1], got {spatial_balance!r}.")
        if not 0.0 <= smoothing < 1.0:
            raise ValueError(f"smoothing must be in [0, 1), got {smoothing!r}.")
        if beats_per_bar is not None and beats_per_bar < 1:
            raise ValueError(f"beats_per_bar must be >= 1 when set, got {beats_per_bar!r}.")
        if accent_intensity is not None and not 0 <= accent_intensity <= 255:
            raise ValueError(f"accent_intensity must be in [0, 255], got {accent_intensity!r}.")

        self._intensity = int(intensity)
        self._sharpness = float(sharpness)
        self._spatial_balance = float(spatial_balance)
        self._smoothing = float(smoothing)
        self._beats_per_bar = beats_per_bar
        self._accent_intensity = (
            int(accent_intensity) if accent_intensity is not None else min(255, int(intensity) + 50)
        )
        self._bpm: float | None = None
        # Milliseconds since the most recent emitted beat onset.  ``None``
        # means no beat has been emitted yet (initial state / post-reset),
        # so the next call to :meth:`events_for_window` fires at ``t = 0``.
        self._ms_since_last_beat: float | None = None
        # Index of the next beat within its bar (0 == downbeat).
        self._beat_in_bar: int = 0

    # ── Configuration ─────────────────────────────────────────────────────────

    @property
    def bpm(self) -> float | None:
        """Most recent (post-smoothing) BPM, or ``None`` if never set."""
        return self._bpm

    @property
    def beats_per_bar(self) -> int | None:
        """Bar length in beats, or ``None`` when downbeat accenting is off."""
        return self._beats_per_bar

    def update(self, bpm: float) -> HapticPrimitive:
        """Push a new live-tempo reading and return the current primitive.

        Args:
            bpm: New tempo, beats per minute.  Must satisfy
                :data:`MIN_BPM` ≤ ``bpm`` ≤ :data:`MAX_BPM`.

        Returns:
            The :class:`HapticPrimitive` for the *offbeat* pulse at the
            (post-smoothing) tempo.  Downbeat accenting is applied only
            when rendering events via :meth:`events_for_window`.
        """
        _validate_bpm(bpm)
        if self._smoothing > 0.0 and self._bpm is not None:
            self._bpm = (1.0 - self._smoothing) * float(bpm) + self._smoothing * self._bpm
        else:
            self._bpm = float(bpm)
        return self._primitive(self._intensity)

    def to_primitive(self) -> HapticPrimitive:
        """Return the current offbeat :class:`HapticPrimitive`.

        Raises:
            RuntimeError: If :meth:`update` has not yet been called — the
                channel has no live tempo to render.
        """
        if self._bpm is None:
            raise RuntimeError("TempoChannel has no BPM set; call update(bpm) first.")
        return self._primitive(self._intensity)

    def reset(self) -> None:
        """Clear tempo, phase and bar position.  Call between songs."""
        self._bpm = None
        self._ms_since_last_beat = None
        self._beat_in_bar = 0

    # ── Rendering ─────────────────────────────────────────────────────────────

    def events_for_window(self, duration_s: float) -> WindowedBeats:
        """Render the next *duration_s* of beats at the current tempo.

        Phase is tracked across calls, so a sequence of
        ``events_for_window(0.25)`` calls produces a single continuous beat
        train even when :meth:`update` changes the tempo between windows.

        Args:
            duration_s: Length of the window in seconds.  Zero or negative
                returns an empty :class:`WindowedBeats`.

        Returns:
            A :class:`WindowedBeats` whose ``events`` carry on/off edges
            relative to the window start (``at_ms = 0``) and whose
            ``bar_starts_ms`` lists the downbeat times in the window
            (empty when :attr:`beats_per_bar` is unset).

        Raises:
            RuntimeError: If :meth:`update` has not yet been called.
        """
        if self._bpm is None:
            raise RuntimeError("TempoChannel has no BPM set; call update(bpm) first.")
        if duration_s <= 0:
            return WindowedBeats(events=[], bar_starts_ms=[])

        period_ms = 60_000.0 / self._bpm
        duty = 0.5 - 0.4 * self._sharpness  # mirrors HapticPrimitive.duty_cycle
        on_ms = period_ms * duty
        total_ms = float(duration_s) * 1000.0

        # When does the next beat fire?  No prior beat → fire immediately at
        # t = 0.  Otherwise fire when one full period has elapsed since the
        # previous beat; if that moment has already passed (e.g. the tempo
        # just slowed dramatically) clamp to t = 0 so the beat is on time
        # for the next window rather than being silently dropped.
        if self._ms_since_last_beat is None:
            next_onset = 0.0
        else:
            next_onset = max(0.0, period_ms - self._ms_since_last_beat)

        events: list[PrimitiveEvent] = []
        bar_starts: list[float] = []
        beat_in_bar = self._beat_in_bar
        accenting = self._beats_per_bar is not None
        last_onset: float | None = None

        t = next_onset
        while t < total_ms:
            is_downbeat = accenting and beat_in_bar == 0
            pulse_intensity = self._accent_intensity if is_downbeat else self._intensity
            pkt = self._primitive(pulse_intensity).to_packet()
            events.append(PrimitiveEvent(at_ms=t, packet=pkt, kind="on"))
            off_t = min(t + on_ms, total_ms)
            events.append(PrimitiveEvent(at_ms=off_t, packet=SILENCE_PACKET, kind="off"))
            if is_downbeat:
                bar_starts.append(t)
            last_onset = t
            t += period_ms
            if accenting:
                assert self._beats_per_bar is not None  # guarded by `accenting`
                beat_in_bar = (beat_in_bar + 1) % self._beats_per_bar

        # Update persistent state so the next window picks up exactly where
        # this one left off, regardless of any tempo change in between.
        if last_onset is not None:
            self._ms_since_last_beat = total_ms - last_onset
            self._beat_in_bar = beat_in_bar
        elif self._ms_since_last_beat is not None:
            # No beat fired this window — phase advances by the full window.
            self._ms_since_last_beat += total_ms

        return WindowedBeats(events=events, bar_starts_ms=bar_starts)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _primitive(self, intensity: int) -> HapticPrimitive:
        assert self._bpm is not None  # callers guard this
        return HapticPrimitive(
            pulse_rate_hz=round(self._bpm / 60.0, 6),
            intensity=intensity,
            spatial_balance=self._spatial_balance,
            sharpness=self._sharpness,
        )


# ── Private helpers ───────────────────────────────────────────────────────────


def _validate_bpm(bpm: float) -> None:
    if not MIN_BPM <= bpm <= MAX_BPM:
        raise ValueError(f"bpm must be in [{MIN_BPM}, {MAX_BPM}], got {bpm!r}.")
