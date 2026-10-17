# OpenHear Pilot Study Protocol — v1 (DRAFT, pre-IRB)

> **Document status.** Working draft v1, May 2026, amended 17 October 2026
> to match the canonical intended purpose. Not yet submitted to any
> Research Ethics Committee. **No participants may be recruited or
> consented under this document.**
>
> **Related artefacts.**
> [`SAP_v1.md`](SAP_v1.md) (statistical analysis plan),
> [`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md),
> [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md),
> [`docs/INTENDED_PURPOSE.md`](../docs/INTENDED_PURPOSE.md),
> [`docs/BURGESS_PRINCIPLE.md`](../docs/BURGESS_PRINCIPLE.md).

## 1. Title

**Pilot evaluation of OpenHear haptic environmental sound awareness:
a single-centre, within-subject study.**

## 2. Background and rationale

The canonical intended purpose is in
[`docs/INTENDED_PURPOSE.md`](../docs/INTENDED_PURPOSE.md). OpenHear is a
research platform that turns the wearer's own audiogram into haptic
patterns for environmental sound awareness. It is not a certified
medical device, not a hearing aid, and not a replacement for clinical
care.

A comparison with participants' own hearing aids on speech-in-noise
tests amplification. That does not support the claim. This pilot
therefore measures whether a wearer can detect and identify classes of
environmental sound from a wrist pattern.

This pilot does not seek to demonstrate clinical equivalence and is
**not powered to**. It seeks (a) feasibility, (b) safety signal, (c) a
realistic effect-size estimate to power a later study.

## 3. Objectives and hypotheses

**Primary objective.** Estimate the rate at which a wearer correctly
identifies the sound class from the haptic pattern (hit rate), and the
false-alert rate.

**Primary hypothesis (descriptive).** Hit rate and false-alert rate will
be reported with 95 % confidence intervals. No non-inferiority margin
against a hearing aid is pre-specified, because the claim is not
amplification.

**Secondary objectives.**

1. QuickSIN SNR loss, if collected, is a secondary descriptive measure
   only. It is not the primary endpoint.
2. Quality-of-life: change scores on the SSQ-12 after one week of use.
3. Subjective preference: forced-choice preference for the pattern set.
4. Safety: any reported adverse events, including skin reactions or
   excessive vibration.
5. Sovereignty acceptability: a 5-item bespoke questionnaire on
   participants' perceived control over their hearing data.

There is no inferential hypothesis test on any secondary endpoint;
all analyses are estimative with 95 % CIs (see SAP §3).

## 4. Study design

* **Type.** Single-centre, open-label, within-subject.
* **Condition.** OpenHear haptic patterns on a wristband, driven by the
  participant's own audiogram. No comparison arm against a commercial
  hearing aid for the primary endpoint.
* **Sessions.** Two sessions in one calendar week: familiarisation, then
  a logged awareness session.
* **Blinding.** Outcome assessors scoring named classes are blinded to
  the system label where feasible. Participants cannot be blinded.

## 5. Population

**Inclusion criteria.**

1. Age ≥ 18.
2. Self-reported, audiologist-confirmed bilateral mild-to-moderate
   sensorineural hearing loss (PTA 26–55 dB HL), or profound loss with
   residual tactile awareness.
3. Capacity to give informed consent.
4. Able to wear a wristband for the session duration.

**Exclusion criteria.**

1. Active skin condition at the wrist that would make vibration unsafe.
2. Inability to attend two in-person sessions in one week.

**Sample size.** n = 20. This is a feasibility pilot, not a
hypothesis-testing trial; n = 20 is sufficient to estimate hit rate and
false-alert rate with reasonable precision (see SAP §4) and to surface
usability and safety issues.

## 6. Setting and recruitment

* **Site.** A single UK university audiology clinic (partner TBC;
  see [`README.md`](../README.md)).
* **Recruitment.** Existing clinic patient list, with an opt-in
  letter and study information sheet. No advertising to the general
  public until the partner site has authorised it.

## 7. Intervention

* **Hardware.** OpenHear wristband (v1.5 no-solder or v2 build).
* **Software.** A pinned commit of the haptic pipeline (`git_sha`
  recorded in every session's data export — see
  [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md)).
* **Fitting.** The participant's existing audiogram is imported via the
  standard JSON format and used to shape the haptic mapping. The mapping
  is exported as a signed bundle (see SOP §4).
* **Safety.** Vibration intensity is limited. The participant is given a
  clearly-marked **kill switch** that immediately stops output.

## 8. Assessments and endpoints

| Time-point | Assessment | Notes |
|------------|-----------|-------|
| Baseline   | Demographics, audiogram | Audiogram is imported, not re-measured. |
| Session 1  | Familiarisation with the seven sound classes | Door, traffic, alarm, voice-present, animal, media, silence. |
| Session 2  | Logged awareness session: named class vs system class; false alerts; misses | Primary data. |
| Day 7 follow-up | AE log only | Email. |

**Primary endpoint.** Hit rate (correct class named from the pattern)
and false-alert rate.

**Secondary endpoints.** QuickSIN SNR loss if collected (descriptive
only); SSQ-12 total and subscale scores; forced-choice preference;
sovereignty questionnaire summary score; safety event rate.

## 9. Safety monitoring

* Intensity limit on the wristband.
* Participant kill switch.
* Adverse-event log at every contact; any serious AE pauses the study
  and is reported to the REC within 7 days.
* The Chief Investigator may halt the study at any time; an Independent
  Safety Monitor (TBC) reviews after the first 5 participants.

## 10. Data management — the Burgess Principle in practice

See [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md) for full detail.
In summary, every participant leaves their final session with a USB
stick containing a SHA-256-signed bundle of their own raw data
(audiogram, mapping, named classes, questionnaire responses, session
metadata). The investigator's database holds only an anonymised,
de-identified derivative. Cloud storage of raw data is prohibited.

## 11. Statistical analysis

See [`SAP_v1.md`](SAP_v1.md). The SAP is locked and timestamped on OSF
before recruitment opens.

## 12. Ethical considerations

* Approval from the partner site's REC is mandatory before any
  recruitment.
* Consent is obtained per [`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md).
* Participants are explicitly told that OpenHear is **not** a certified
  medical device and that this study is research, not clinical care.
  Their existing hearing aids and clinical care are unaffected by
  participation.
* Participants may withdraw at any time. On withdrawal, their data
  bundle is returned to them; the de-identified derivative may be
  retained for analysis only with their continued consent.

## 13. Dissemination

* Results, *positive, null or negative*, will be posted to medRxiv
  within 60 days of database lock and submitted to a peer-reviewed
  journal within 6 months.
* Anonymised raw data will be deposited on Zenodo under CC-BY 4.0 with
  participant consent.
* The pre-registration (this protocol + SAP) will be linked from the
  published paper.

## 14. Roles and responsibilities

| Role | Holder | Responsibility |
|------|--------|----------------|
| Chief Investigator | TBC (partner audiology lead) | Scientific & ethical oversight, REC submission. |
| Sponsor | TBC (partner university) | Regulatory & legal sponsor. |
| Project Lead (OpenHear) | Lewis Burgess | Software, hardware, data SOP. |
| Statistician | TBC | Pre-registers SAP, performs analysis. |
| Data Manager | TBC | CRFs, anonymisation, data export. |
| Independent Safety Monitor | TBC | Reviews safety after first n=5. |

## 15. Version history

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v1 (draft) | 2026-05-XX | OpenHear team | Initial public draft for partner review. |
| v1 amended | 2026-10-17 | OpenHear team | Primary endpoint changed from QuickSIN vs own aid to hit rate and false-alert rate, to match docs/INTENDED_PURPOSE.md. |
