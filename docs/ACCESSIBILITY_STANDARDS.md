# OpenHear Accessibility and Standards Alignment

> **Conformance language.** OpenHear is *aligned with*, *inspired by*,
> and *supports the principles of* the standards listed in this
> document. Nothing in this repository constitutes a claim of
> certification, conformance, or regulatory clearance against any of
> them. Where evidence is missing it is named as a gap, not glossed.

This document is the single accessibility and standards anchor for
the OpenHear project. It complements — it does **not** replace — the
safety, clinical, and Burgess Principle documents already in the
repository:

- [`hardware/safety/README.md`](../hardware/safety/README.md) — hardware
  safety, MPO limiter, calibration, risk register.
- [`docs/BURGESS_PRINCIPLE.md`](BURGESS_PRINCIPLE.md) — sovereignty
  commitments.
- [`docs/EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md) —
  electroacoustic, haptic, accessibility, and clinical validation
  checklists.
- [`docs/HAPTIC_PATTERN_LIBRARY.md`](HAPTIC_PATTERN_LIBRARY.md) —
  canonical haptic pattern registry and SOVEREIGN/NULL semantics.
- [`clinical/README.md`](../clinical/README.md) — pilot study
  documents.

---

## 1. Status and scope

OpenHear is experimental research infrastructure. It is **not**
certified medical equipment, **not** a regulated assistive listening
device, **not** an audited piece of accessible ICT, and **not**
operating under a quality management system. The standards mapped
below are used as design references, evidence targets, and
contributor checklists — not as compliance claims.

The project spans five domains, and the appropriate standards differ
for each:

| Domain | What it covers in OpenHear | Primary standards reference |
|---|---|---|
| Software accessibility | Documentation, mobile UI, audiogram tools, multimodal alerts. | WCAG 2.2, EN 301 549. |
| Assistive technology research | Audiogram sovereignty, wristband alerting, environmental awareness. | ISO 9999, ADA assistive listening principles. |
| Hearing-device electroacoustics | DSP pipeline, output limiter, hardware MPO limiter, Tympan integration. | IEC 60118 series. |
| Haptic sensory substitution | Wristband patterns, v0 encoder, 24/64/128 actuator research. | Internal evidence rubric (see `docs/HAPTIC_PRIOR_ART.md`) plus general human-factors literature. |
| Clinical / research evidence | Pilot protocol, consent template, data management SOP. | UK GDPR, GCP-aligned research practice, ISO 13485 only as a forward reference. |

If a feature does not yet have an obvious mapping, that is recorded
as a gap in §4, not silently omitted.

---

## 2. Standards map

### 2.1 WCAG 2.2 — Web Content Accessibility Guidelines

**Why it applies.** OpenHear is used through documentation
(Markdown), through the Android scaffold (`mobile/`), through CLI
tools, and through visual artefacts (audiograms, plots). All of these
must be perceivable, operable, understandable, and robust for users
with disabilities — including, crucially, the deaf and hard-of-hearing
users the project exists to serve.

**Where OpenHear maps to it.**

- **Documentation.** Markdown is screen-reader friendly when
  headings are nested correctly, link text is descriptive, tables
  have headers, and images carry alternative text. Contributors must
  preserve these properties when editing repository docs.
- **Mobile UI.** Compose surfaces in `mobile/` must expose semantic
  roles, labels, scalable text, sufficient colour contrast (target
  4.5:1 for body text, 3:1 for large text/UI), and large touch
  targets (target ≥ 44 × 44 dp).
- **Visual audiogram tooling.** Plots produced by `audiogram/visualiser.py`
  must remain readable when printed in greyscale; relying on colour
  alone to distinguish left/right ears is a WCAG 1.4.1 failure.
- **Multimodal alerts.** Any critical signal (loud-sound warning,
  feedback alarm, kill-switch confirmation) must be available via at
  least two of {visual, haptic, text}. Audio-only critical alerts
  are explicitly disallowed because the target users may not hear
  them.
- **Keyboard / navigation.** CLI tools accept input without pointing
  devices. Future GUIs must remain fully keyboard-operable.

**Haptic perceivability as a project-specific extension.** OpenHear
treats wristband haptics as a first-class multimodal channel. This is
a deliberate extension of the WCAG principles to a domain WCAG itself
does not directly cover; the project does not claim WCAG conformance
for the wristband hardware.

### 2.2 EN 301 549 — Accessibility requirements for ICT

**Why it applies.** EN 301 549 is the European baseline for public
procurement of accessible ICT. Even where OpenHear is not publicly
procured, EN 301 549's checklists are a strong, jurisdiction-aware
overlay on top of WCAG and a useful reference for any organisation
wishing to redistribute OpenHear builds.

**Working checklist for OpenHear surfaces.**

- UI controls expose name, role, value to assistive technologies.
- Captions and text alternatives exist for any audio or video
  content (currently the project ships no video; this remains a
  contributor obligation if that changes).
- Documentation is structured so that screen readers can navigate
  by heading and landmark.
- Assistive-technology compatibility is preserved — in particular,
  Android TalkBack on the `mobile/` scaffold must reach every
  interactive control.
- Documentation, where it describes hardware, describes alternative
  non-auditory feedback (LED + haptic + visual log).

### 2.3 ISO 9999 — Assistive products classification

**Why it applies.** ISO 9999 is the international vocabulary for
assistive products. Using its language helps clinicians, regulators,
funders, and procurement teams place OpenHear's components in a
recognisable taxonomy without forcing the project into the regulatory
class of a single category.

**Working classification.**

| OpenHear component | ISO 9999 family (informational mapping) |
|---|---|
| Audiogram sovereignty tools (`audiogram/`, `core/`) | Aids for information management related to hearing care. |
| DSP pipeline (`dsp/`) | Aids for hearing — sound processing research code (not a hearing aid). |
| Hardware ITE / wristband prototypes (`hardware/`) | Personal-use assistive product research artefacts. |
| Environmental alerting wristband (`stream/`, `wristband/`, `hardware/wristband/`) | Alerting and indicating products for environmental sound awareness. |
| Tactile sensory substitution prototype (24/64/128 actuator research) | Tactile substitution research devices (no recognised ISO 9999 leaf class for general acoustic-to-tactile substitution). |

These mappings are *informational* and do not constitute
classification under any regulatory regime.

### 2.4 IEC 60118 — Electroacoustics of hearing devices

**Why it applies.** IEC 60118 (multi-part) defines how hearing-device
acoustic performance is *measured*. OpenHear is not certified against
it, but every safety claim the project makes about output level, gain,
distortion, or feedback should be testable in IEC-60118-compatible
ways.

**Where OpenHear maps to it.**

| Concept | OpenHear surface | Notes |
|---|---|---|
| Maximum output SPL (OSPL90 / MPO) | [`hardware/safety/README.md`](../hardware/safety/README.md), [`hardware/safety/mpo_calculator.py`](../hardware/safety/mpo_calculator.py), `dsp/output_limiter.py`, `core/safety.py` | Hardware zener clamp + software limiter + safety gate. |
| Frequency response | `dsp/filters.py`, `dsp/audiogram_profile.py`, Tympan templates in `hardware/tympan/` | Measurable on a 2 cc coupler per IEC 60318-style coupler practice. |
| Total harmonic distortion | Implicit in DSP and limiter design | No formal IEC 60118 distortion report yet — gap. |
| Latency | `stream/latency.py` | Latency budget tooling exists; per-stage budgets to be formalised. |
| Feedback stability | `dsp/feedback_canceller.py` | Stability checks via test tones; no IEC 60118-aligned report yet — gap. |
| Coupler measurement procedure | [`hardware/safety/README.md`](../hardware/safety/README.md) §4 | Calibration procedure references a 2 cc coupler. |

See [`docs/EVIDENCE_AND_VALIDATION.md`](EVIDENCE_AND_VALIDATION.md)
for the project's IEC-60118-inspired electroacoustic checklist.

### 2.5 ISO 13485 — Quality management for medical devices

**Why it is referenced at all.** Because the *forward* roadmap
includes hardware that could one day fall under medical-device
regulation, contributors need a shared vocabulary for the design
controls that would be required *if* OpenHear ever pursued that path.

**Current status.** OpenHear does **not** operate an ISO 13485
quality management system. None of the modules in this repository may
be relied upon as if they did.

**What would be required to move toward ISO 13485, if the community
ever chose to.** Design controls, requirements traceability, formal
risk management (ISO 14971-style), supplier controls, complaint
handling, post-market surveillance, verification and validation
records, software lifecycle process (IEC 62304-style), and a
document control system. This list exists so that contributors can
*recognise* the gap, not to imply work is underway.

### 2.6 ADA — Americans with Disabilities Act, assistive listening principles

**Why it applies.** Even though OpenHear is not a US-regulated
assistive listening system, the ADA's principles for assistive
listening — effective communication, user control, non-discrimination,
venue compatibility, interoperability — are exactly the principles
the Burgess Principle codifies for individual users.

**Mapping.**

| ADA principle | OpenHear realisation |
|---|---|
| Effective communication | Multimodal output (audio + haptic + visual). Sound classification + wristband alerts for users who cannot rely on audio alone. |
| User control | Sovereign audiogram, sovereign DSP config, no vendor lock-in. |
| Non-discrimination | Open-source, free to use, free to inspect, free to modify. No clinic gate, no subscription. |
| Venue compatibility | Bluetooth and BLE Audio paths, Auracast on the roadmap; aim is to receive shared streams in public venues. |
| Interoperability | Open audiogram JSON, open fitting JSON, open haptic packet contract, open advocacy bundle schema. |

Auracast / LE Audio support (see `docs/roadmap.md`) is the most
direct future tie-in with the ADA assistive listening principles for
public venues; it is currently planned, not implemented.

---

## 3. Feature-to-standard matrix

| Feature | Accessibility benefit | Relevant standard(s) | Current implementation | Evidence / gap | Next action |
|---|---|---|---|---|---|
| Audiogram JSON ownership | User holds their hearing data. | ADA principle of user control; ISO 9999 (information management for hearing care). | `audiogram/` module, open JSON format, validation, export, compare, manual entry. | Format documented and tested; no external accessibility audit of the visualiser. | Add greyscale-safe palette and alt-text generator for plots. |
| Local-first processing | Removes cloud dependency that excludes low-connectivity users. | WCAG (robustness), EN 301 549, Burgess Principle. | Entire `dsp/`, `stream/`, `learn/`, `advocacy/` chain runs locally. | Strong as design property; no third-party privacy audit. | Document offline-mode test plan in `docs/EVIDENCE_AND_VALIDATION.md`. |
| DSP safety limiter | Prevents acute over-amplification. | IEC 60118 concepts (OSPL90 / MPO), WCAG (predictable behaviour). | `dsp/output_limiter.py`, `core/safety.py`. | Unit tests exist; no formal IEC-60118-style report. | Generate per-config measurement report. |
| Hardware MPO limiter | Unconditional acoustic safety. | IEC 60118 (output measurement), risk management principles. | `hardware/safety/README.md`, zener clamp, `mpo_calculator.py`. | Design documented; lacks bench measurement archive. | Add calibration-report template to `docs/EVIDENCE_AND_VALIDATION.md`. |
| Haptic wristband alerts | Non-audio access to environmental sound. | ADA, WCAG (multimodal alternatives), ISO 9999 (alerting products). | `stream/haptic_mapper.py`, `wristband/openhear_firmware.py`, `hardware/wristband/firmware/haptic_mapper.py`, v0 encoder. | Seven-class prototype tested; no validated perception study. | Run pattern recognition + SOVEREIGN/NULL discrimination study (see `docs/HAPTIC_PATTERN_LIBRARY.md`). |
| SOVEREIGN / NULL tagging | Distinguishes human-verified facts from automation. | Burgess Principle; cross-cuts ADA principle of user control. | `advocacy/gate.py`, `advocacy/adapters.py`, `advocacy/bundle.py`. | Schema locked; haptic semantics now defined in `docs/HAPTIC_PATTERN_LIBRARY.md`. | Wire canonical SOVEREIGN/NULL haptic patterns into firmware. |
| Clinical pilot docs | Frames evidence generation transparently. | ISO 13485 (forward reference only), GCP-aligned practice, UK GDPR. | `clinical/PILOT_PROTOCOL_v1.md`, `clinical/CONSENT_TEMPLATE.md`, `clinical/DATA_MANAGEMENT_SOP.md`, `clinical/SAP_v1.md`. | Documented; not yet IRB-submitted. | Add explicit standards references and adverse-event categories (done in this iteration). |
| Mobile scaffold | Phone-based access path. | WCAG 2.2, EN 301 549. | `mobile/` Compose scaffold + JNI/Oboe engine. | Scaffold only; no accessibility audit. | Add accessibility checklist to `mobile/README.md` (done) and back it with tests. |
| Documentation | All-audiences access to project. | WCAG 2.2 (documents), EN 301 549. | Markdown across `README.md`, `docs/`, module READMEs. | No automated docs accessibility check. | Add docs accessibility checklist to `docs/EVIDENCE_AND_VALIDATION.md`. |

---

## 4. Known gaps

These are tracked here so that no implicit claim of conformance is
made anywhere else in the repository.

- No formal WCAG 2.2 audit of documentation, mobile UI, or visual
  audiogram tooling.
- No EN 301 549 test report for the mobile scaffold.
- No published IEC 60118-style electroacoustic measurement package
  for the DSP pipeline, output limiter, or hardware MPO limiter.
- No ISO 13485 quality management system.
- No ADA venue integration guide (Auracast / LE Audio reception in
  public venues is on the roadmap, not implemented).
- No validated haptic perception study (the project relies on the
  prior-art anchor in [`docs/HAPTIC_PRIOR_ART.md`](HAPTIC_PRIOR_ART.md)
  and pre-registers any future study as research, not product
  claim).
- No accessibility section in the pull request template (planned).
- No automated checks for documentation alt-text or heading
  structure (planned).

---

## 5. Conformance language

When writing about OpenHear's relationship to these standards, use
the following vocabulary and **avoid** the second column.

| Use | Avoid |
|---|---|
| "Aligned with WCAG 2.2 principles." | "WCAG 2.2 compliant." |
| "Inspired by IEC 60118 measurement practice." | "IEC 60118 certified." |
| "Supports the principles of EN 301 549." | "EN 301 549 conformant." |
| "Uses ISO 9999 vocabulary informally." | "Classified under ISO 9999." |
| "ISO 13485 is a forward reference for the project." | "ISO 13485 quality system." |
| "Designed in line with ADA assistive listening principles." | "ADA compliant." |
| "Future evidence target." | "Evidence demonstrates …" (unless an actual evidence artefact is cited). |

If you cannot honestly use the left-hand phrase yet, leave the claim
out of the documentation and add a row to §4 instead.

---

## 6. How to use this document

- **Contributors** should consult §2 before adding any user-facing
  feature, and update §3 if their change moves a row.
- **Reviewers** should reject documentation or marketing copy that
  uses the language in §5's right-hand column without a verifiable
  evidence artefact.
- **Auditors and clinicians** should treat §4 as the authoritative
  list of what OpenHear has *not* demonstrated.
- **Users** should remember that nothing here changes the project's
  experimental, non-medical-device status.
