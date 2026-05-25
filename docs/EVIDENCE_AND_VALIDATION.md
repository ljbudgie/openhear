# OpenHear Evidence and Validation Checklists

> **Purpose.** Give contributors, clinicians, and reviewers a single
> place to record what has actually been *measured*, as opposed to
> what has been *designed* or *claimed*. Every checklist below is
> deliberately phrased so that a "pass" requires a referenceable
> artefact (a measurement file, a calibration log, an audit note),
> not a developer's belief.

This document is the practical companion to
[`docs/ACCESSIBILITY_STANDARDS.md`](ACCESSIBILITY_STANDARDS.md). The
standards document says *what* OpenHear aligns with; this document
says *how the alignment is to be evidenced*.

OpenHear is experimental and is **not** a medical device. No
checklist below is a regulatory submission template; each is a
research-grade self-audit instrument.

---

## 1. Electroacoustic validation (IEC 60118-inspired)

Apply this checklist any time the DSP pipeline, output limiter, or
hardware MPO chain is changed.

| # | Item | Method (suggested) | Pass criterion | Evidence artefact |
|---|---|---|---|---|
| E1 | Frequency response, full-on gain | Sweep 125–8000 Hz on a 2 cc coupler; record SPL per third-octave. | Response within design target band ±5 dB across 250–6000 Hz. | CSV in `output/electroacoustic/<git_sha>/frequency_response.csv`. |
| E2 | Output SPL (OSPL90-style) | 90 dB SPL input tone, full-on gain, 2 cc coupler. | Within ±3 dB of design target; never exceeds MPO ceiling. | CSV in same directory. |
| E3 | Maximum Power Output (MPO) | Increasing input level until output reaches design MPO. | Output is clamped at design MPO ±2 dB by the hardware limiter; software limiter engages first by ≥ 3 dB margin. | Annotated plot + raw measurement. |
| E4 | Total harmonic distortion | 500, 1000, 2000 Hz input at 70 dB SPL; measure THD. | THD ≤ 5 % at each frequency at nominal gain. | Measurement script output. |
| E5 | Equivalent input noise | Mute input, measure coupler noise floor. | ≤ 28 dB SPL A-weighted (research target only). | Coupler SPL recording. |
| E6 | End-to-end latency | `stream/latency.py` round-trip plus optional acoustic-to-acoustic measurement. | < 20 ms for companion DSP paths; documented if exceeded. | `metrics.csv` from `python -m dsp.pipeline --metrics-csv`. |
| E7 | Feedback stability | Inject sustained pure tones; verify `dsp/feedback_canceller.py` suppresses without oscillation. | No sustained oscillation > 5 s; suppression within 500 ms. | Recorded WAV + log line. |
| E8 | Coupler setup | Document coupler model, microphone, calibration date, ambient noise. | All fields populated. | Free-text record in evidence directory. |
| E9 | Calibration record | Date, operator, equipment serials, environmental conditions. | Signed by builder. | `CALIBRATION.md` in evidence directory. |

Where bench equipment is unavailable, run the available subset and
mark untested rows as "not measured" rather than as pass.

---

## 2. Haptic validation

Apply when the wristband firmware, haptic mapper, or canonical
pattern registry
([`docs/HAPTIC_PATTERN_LIBRARY.md`](HAPTIC_PATTERN_LIBRARY.md))
changes.

| # | Item | Method | Pass criterion | Evidence artefact |
|---|---|---|---|---|
| H1 | Perceptibility threshold | Stepwise intensity decrease until participant misses 50 % of pulses. | Threshold recorded per wrist position and per actuator. | Per-participant CSV. |
| H2 | Comfort threshold | Stepwise increase until participant rates discomfort ≥ 7/10. | Stays below this in normal operation. | Comfort scale log. |
| H3 | Pattern confusion matrix | Present each canonical pattern N times in random order; record identifications. | Per-pattern recognition ≥ 70 % after a defined training interval. | Confusion matrix CSV. |
| H4 | SOVEREIGN vs NULL discrimination | Forced choice between SOVEREIGN and NULL patterns. | ≥ 90 % discrimination after training. | Forced-choice log. |
| H5 | Alarm vs NULL discrimination | Forced choice between safety alarm and NULL patterns. | ≥ 95 % discrimination; no NULL pattern is mistaken for an alarm. | Forced-choice log. |
| H6 | Reaction time | Time from pattern onset to user response on a known cue. | Reported with median + IQR. | Reaction-time CSV. |
| H7 | Fatigue / habituation | Repeat patterns over 60 minutes; track recognition decay. | Decay reported honestly; no claim of sustained performance without data. | Time-series CSV. |
| H8 | Skin reaction | Wear test 8 hours; inspect skin pre and post. | No erythema or irritation persisting > 30 minutes post-removal. | Wear-test log. |
| H9 | Thermal | Continuous worst-case drive for documented duration; thermocouple at strap interface. | Surface temperature ≤ 41 °C at any time. | Thermal log. |
| H10 | Intensity clamp invariant | Inject out-of-range intensity values into mapper. | Output always within `[0, 255]`; no NaN; safety pattern preserved. | Pytest run. |

The "validated haptic perception study" line in
[`docs/ACCESSIBILITY_STANDARDS.md`](ACCESSIBILITY_STANDARDS.md) §4
flips from "gap" to "in progress" only when at least H3, H4, H5, and
H9 are populated with data.

---

## 3. Accessibility validation

Apply to documentation, the mobile scaffold, and any future GUI.

| # | Item | Method | Pass criterion | Evidence artefact |
|---|---|---|---|---|
| A1 | WCAG 2.2 self-audit (docs) | Walk through each repository Markdown file with a heading/alt-text checker. | Headings monotonically nested, every image has alt text, link text is descriptive. | `output/accessibility/docs_audit.md`. |
| A2 | WCAG 2.2 self-audit (mobile) | TalkBack walk-through of every Compose screen. | Every interactive control announces name + role + state. | Recorded walk-through notes. |
| A3 | EN 301 549 self-audit (mobile) | Map each EN 301 549 chapter 11 (software) clause to a Compose surface. | Each clause is either satisfied or recorded as gap. | Mapping spreadsheet. |
| A4 | Screen reader compatibility | NVDA on desktop (for docs site, when built); TalkBack on Android. | No element is unreachable. | Per-platform notes. |
| A5 | Keyboard navigation | Operate all current CLIs and any future GUIs without a pointing device. | All flows reachable; documented escape from interactive prompts. | Walk-through notes. |
| A6 | Documentation readability | Reading-grade check on `README.md`, `CLINICIAN_GUIDE.md`, consent template. | Reading grade ≤ 12; technical terms defined on first use. | Tool output (e.g. `pyflakes`-equivalent for prose). |
| A7 | Colour-contrast (visuals) | Inspect plot palettes used by `audiogram/visualiser.py` and any mobile theme. | Contrast ratios ≥ 4.5:1 (body) / 3:1 (large text and UI). | Contrast measurement. |
| A8 | Non-audio alternatives | Verify every critical alert in the system is also rendered visually or haptically. | No audio-only critical alert exists. | Audit table. |
| A9 | Captions / text alternatives | Audit every audio or video asset (currently expected to be empty). | Empty or each asset has captions / transcript. | Asset register. |

---

## 4. Clinical / research validation

Apply to anything routed through `clinical/`.

| # | Item | Method | Pass criterion | Evidence artefact |
|---|---|---|---|---|
| C1 | Consent | Use [`CONSENT_TEMPLATE.md`](../clinical/CONSENT_TEMPLATE.md) after site adaptation and REC approval. | Signed consent on file before any data collection. | Per-participant signed form. |
| C2 | Adverse-event logging | Use the AE categories listed in §5 below at every contact. | Every contact has an AE log entry, even if "none". | AE log per study ID. |
| C3 | Protocol version control | Cite the protocol git_sha in every session bundle. | Bundle metadata includes `protocol_sha`. | Bundle manifest. |
| C4 | Anonymisation | Apply [`DATA_MANAGEMENT_SOP.md`](../clinical/DATA_MANAGEMENT_SOP.md) §5. | Anonymised dataset contains no direct identifiers. | Audit by Data Manager. |
| C5 | Null-result publication | Publish all pre-registered analyses, including null and negative results. | Published or pre-print regardless of direction. | DOI on Zenodo / OSF. |
| C6 | Privacy posture | Verify no raw data left the partner site. | Network logs + SOP §7 prohibitions respected. | Audit log. |
| C7 | Standards posture | Confirm the consent and protocol still cite [`ACCESSIBILITY_STANDARDS.md`](ACCESSIBILITY_STANDARDS.md). | Citation present and current. | Doc cross-check. |

---

## 5. Adverse-event categories

Use the following minimum category set for every contact:

| Code | Category | Examples |
|---|---|---|
| AE-A | Acoustic discomfort | Sudden loudness, distortion, transient whistle, perceived over-amplification. |
| AE-H | Haptic discomfort | Itching, pain, persistent erythema, motor too strong, motor too localised, thermal sensation. |
| AE-P | Privacy concern | Suspected raw audio leak, unexpected log file, device pairing with unknown peer, lost USB bundle. |
| AE-M | Misclassification of critical sounds | Alarm not signalled, doorbell not signalled, voice of named person not signalled, false alarm. |
| AE-G | General medical event | Anything else reportable as adverse for the participant, including events unrelated to OpenHear. |

Each entry must record: study ID, timestamp, category, free-text
description, severity (1–4), action taken, and whether the event
required pausing the session.

Serious adverse events (severity 4, or any event leading to medical
attention) trigger the protocol's stop rule and are reported per
[`clinical/PILOT_PROTOCOL_v1.md`](../clinical/PILOT_PROTOCOL_v1.md)
§9 within 7 days.

---

## 6. Evidence directory layout

Recommended on-disk layout for any evidence produced under this
document:

```text
output/
  electroacoustic/<git_sha>/
    frequency_response.csv
    ospl.csv
    mpo.csv
    distortion.csv
    latency.csv
    CALIBRATION.md
  haptic/<study_id>/
    perceptibility.csv
    confusion_matrix.csv
    sovereign_vs_null.csv
    alarm_vs_null.csv
    reaction_time.csv
    fatigue.csv
    wear_log.md
    thermal.csv
  accessibility/
    docs_audit.md
    mobile_audit.md
    en_301_549_mapping.md
  clinical/<study_id>/
    consent.pdf  (kept on partner site, not in repo)
    ae_log.csv
    session_metadata.json
```

Nothing under `output/` should be committed unless it is itself
anonymised and the participant or contributor has explicitly
consented to publication.
