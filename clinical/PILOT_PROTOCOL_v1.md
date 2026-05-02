# OpenHear Pilot Study Protocol — v1 (DRAFT, pre-IRB)

> **Document status.** Working draft v1, May 2026. Not yet submitted to
> any Research Ethics Committee. **No participants may be recruited or
> consented under this document.**
>
> **Related artefacts.**
> [`SAP_v1.md`](SAP_v1.md) (statistical analysis plan),
> [`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md),
> [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md),
> [`docs/BURGESS_PRINCIPLE.md`](../docs/BURGESS_PRINCIPLE.md).

## 1. Title

**Pilot evaluation of the OpenHear sovereign DSP pipeline against
participants' own commercially fitted hearing aids: a single-centre,
within-subject crossover study.**

## 2. Background and rationale

Commercial hearing aids deliver good speech-in-noise performance but
ship as closed, vendor-controlled platforms: the wearer cannot
inspect or modify the algorithms processing their own perception, and
their audiogram and fitting are not portable across vendors. The
[Burgess Principle](../docs/BURGESS_PRINCIPLE.md) frames this as a
sovereignty problem: the user's audiogram is a measurement of their
body and should belong to them.

OpenHear is an open-source DSP pipeline (Python today, C++/Rust on
the Phase 1 roadmap) that runs the user's own audiogram and
configuration on commodity hardware, with no cloud dependency and full
algorithmic transparency. Before any claims of clinical equivalence
can be made, an honest measurement is required: **does OpenHear, when
fitted to the same audiogram a clinician used to fit the
participant's own commercial aid, deliver speech-in-noise performance
within a pre-specified non-inferiority margin?**

This pilot does not seek to demonstrate superiority and is **not
powered to**. It seeks (a) feasibility, (b) safety signal, (c) a
realistic effect-size estimate to power a Phase 2 RCT.

## 3. Objectives and hypotheses

**Primary objective.** Estimate the difference in QuickSIN SNR loss
(dB) between OpenHear and the participant's own commercial hearing aid.

**Primary hypothesis (descriptive).** The 95 % confidence interval of
the within-participant difference in QuickSIN SNR loss
(OpenHear − own aid) will be reported. Pre-specified non-inferiority
margin: **+3 dB** (a difference larger than this is considered
clinically meaningful in favour of the commercial aid).

**Secondary objectives.**

1. Quality-of-life: change scores on the SSQ-12 and IOI-HA after
   one week of OpenHear use.
2. Subjective preference: forced-choice preference at the end of
   each block.
3. Safety: any reported adverse events, including loud-sound
   exposure, feedback whistling, ear fatigue, or skin reactions.
4. Sovereignty acceptability: a 5-item bespoke questionnaire on
   participants' perceived control over their hearing data.

There is no inferential hypothesis test on any secondary endpoint;
all analyses are estimative with 95 % CIs (see SAP §3).

## 4. Study design

* **Type.** Single-centre, open-label, within-subject crossover.
* **Arms.** (A) Participant's own commercial hearing aid, optimally
  programmed by their usual audiologist within the last 12 months.
  (B) OpenHear pipeline running on a Raspberry Pi 5 with the
  participant's own audiogram (imported via the standard OpenHear
  audiogram JSON path), output routed to a clinical-grade open
  receiver-in-canal (RIC) module.
* **Order.** Randomised 1:1 block order (AB / BA) using a
  pre-generated sealed-envelope sequence.
* **Washout.** 24 hours between blocks, both blocks completed within
  a single calendar week.
* **Blinding.** Outcome assessors (audiologists scoring QuickSIN
  responses) are blinded to arm. Participants cannot be blinded
  (different physical hardware).

## 5. Population

**Inclusion criteria.**

1. Age ≥ 18.
2. Self-reported, audiologist-confirmed bilateral mild-to-moderate
   sensorineural hearing loss (PTA 26–55 dB HL).
3. Currently fitted with bilateral commercial hearing aids
   (any manufacturer) and using them ≥ 4 hours/day.
4. Native or fluent speaker of the language of the QuickSIN materials
   (English, in the UK pilot).
5. Capacity to give informed consent.

**Exclusion criteria.**

1. Conductive or mixed hearing loss.
2. Cochlear implant.
3. Active otologic disease, recent ear surgery, or unstable hearing
   threshold (> 10 dB shift in past 6 months).
4. Inability to attend two in-person sessions in one week.

**Sample size.** n = 20. This is a feasibility pilot, not a
hypothesis-testing trial; n = 20 is sufficient to estimate the
within-subject SD of QuickSIN SNR loss with reasonable precision
(see SAP §4) and to surface usability and safety issues. Power
calculations for the Phase 2 RCT will be derived from this pilot.

## 6. Setting and recruitment

* **Site.** A single UK university audiology clinic (partner TBC;
  see [`README.md`](README.md)).
* **Recruitment.** Existing clinic patient list, with an opt-in
  letter and study information sheet. No advertising to the general
  public until the partner site has authorised it.

## 7. Interventions

### 7.1 Arm A — own commercial hearing aid

The participant uses their own bilateral hearing aids at the
manufacturer-and-clinician-set program. No reprogramming is performed
for the study.

### 7.2 Arm B — OpenHear pipeline

* **Hardware.** Reference build from `HARDWARE.md`: Raspberry Pi 5,
  USB audio interface, RIC receivers loaned by the partner clinic.
* **Software.** A pinned commit of the `dsp/` Python pipeline
  (`git_sha` recorded in every session's data export — see
  [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md)).
* **Fitting.** The participant's existing audiogram is imported via
  the standard JSON format and a single fitting session is performed
  by the study audiologist using the OpenHear self-fitting flow,
  with manual override available. The fitting parameters are
  exported as a signed bundle (see SOP §4).
* **Safety.** All output levels are limited via the
  `mpo_calculator` MPO ceiling derived from the participant's own
  audiogram. The participant is given a clearly-marked **kill
  switch** (single hardware button on the Pi) that immediately mutes
  the output.

## 8. Assessments and endpoints

| Time-point | Assessment | Notes |
|------------|-----------|-------|
| Baseline   | Demographics, audiogram, hearing-aid history | Audiogram is imported, not re-measured. |
| End of block 1 | QuickSIN (3 lists, randomly assigned), SSQ-12, IOI-HA, preference, AE log | Lists not re-used between blocks. |
| End of block 2 | QuickSIN (3 different lists), SSQ-12, IOI-HA, preference, AE log, sovereignty questionnaire | |
| Day 7 follow-up | AE log only | Phone call. |

**Primary endpoint.** Mean within-participant difference in QuickSIN
SNR loss (dB) between Arm B and Arm A.

**Secondary endpoints.** SSQ-12 total and subscale scores; IOI-HA
total and item scores; forced-choice preference (binary);
sovereignty questionnaire summary score; safety event rate.

## 9. Safety monitoring

* Real-time MPO limiting on Arm B (see §7.2).
* Participant kill switch on Arm B.
* Adverse-event log at every contact; any serious AE pauses the
  study and is reported to the REC within 7 days.
* The Chief Investigator may halt the study at any time; an
  Independent Safety Monitor (TBC) reviews after the first 5
  participants.

## 10. Data management — the Burgess Principle in practice

See [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md) for full
detail. In summary, every participant leaves their final session with
a USB stick containing a SHA-256-signed bundle of their own raw data
(audiogram, fitting, QuickSIN responses, questionnaire responses,
session metadata). The investigator's database holds only an
anonymised, de-identified derivative. Cloud storage of raw data is
prohibited.

## 11. Statistical analysis

See [`SAP_v1.md`](SAP_v1.md). The SAP is locked and timestamped on
OSF before recruitment opens.

## 12. Ethical considerations

* Approval from the partner site's REC is mandatory before any
  recruitment.
* Consent is obtained per [`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md).
* Participants are explicitly told that OpenHear is **not** a
  certified medical device and that this study is research, not
  clinical care. Their existing hearing aids and clinical care are
  unaffected by participation.
* Participants may withdraw at any time. On withdrawal, their data
  bundle is returned to them; the de-identified derivative may be
  retained for analysis only with their continued consent.

## 13. Dissemination

* Results, *positive, null or negative*, will be posted to medRxiv
  within 60 days of database lock and submitted to a peer-reviewed
  journal within 6 months.
* Anonymised raw data will be deposited on Zenodo under CC-BY 4.0
  with participant consent.
* The pre-registration (this protocol + SAP) will be linked from
  the published paper.

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
