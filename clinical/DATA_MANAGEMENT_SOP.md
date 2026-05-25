# OpenHear Pilot — Data Management SOP v1

> **Status.** Draft v1, May 2026. Operationalises the
> [Burgess Principle](../docs/BURGESS_PRINCIPLE.md) for the pilot
> study described in [`PILOT_PROTOCOL_v1.md`](PILOT_PROTOCOL_v1.md).
> All study staff must follow this SOP; any deviation must be logged
> and reported to the Chief Investigator.

## 1. Scope

This SOP covers the lifecycle of every datum collected during the
OpenHear pilot study, from consent to publication:

* Audiogram (imported from the participant's clinical record).
* OpenHear fitting parameters (the JSON exported by the OpenHear
  fitting flow).
* QuickSIN responses (per-list scores).
* SSQ-12, IOI-HA and sovereignty-questionnaire responses.
* Adverse-event log entries.
* Session metadata (date, site, study-ID, code git_sha).

It does **not** cover the participant's clinical record at the partner
site, which is governed by the partner's existing clinical
record-keeping policies.

## 2. Roles

| Role | Responsibility |
|------|----------------|
| Chief Investigator (CI) | Overall accountability; approves SOP and any deviation. |
| Data Manager | Day-to-day implementation; key custodian; signs bundles. |
| Study Audiologist | Consent, fitting, QuickSIN administration. |
| Project Lead (OpenHear) | Maintains the bundle-export tool; provides hardware. |

## 3. Identifiers

* Each participant is assigned a **study ID** of the form
  `OH1-NNN` where `NNN` is a sequential 3-digit number.
* The mapping from study ID → name is held in a **single** AES-256
  encrypted file on the partner site's secure clinical network. The
  passphrase is held only by the CI and Data Manager.
* No name, NHS number, address, date of birth or other directly
  identifying information ever leaves the partner site's secure
  network.

## 4. The participant bundle (Burgess Principle artefact)

At the end of every participant's final session, the Data Manager
generates the **participant bundle**:

1. A directory containing one JSON file per data type listed in §1.
2. A `MANIFEST.json` with the SHA-256 of every file, the study
   git_sha, the SOP version, and a UTC timestamp.
3. The directory is bundled into a `tar.gz` and a SHA-256 of the
   archive is appended to a `BUNDLE.sha256` file inside the bundle.
4. The archive is signed using the OpenHear `advocacy/gate.py`
   tooling (or an equivalent OpenSSL signature against the project's
   published key) so that any third party can verify it.

The bundle is written to two USB sticks:

* **Participant copy.** Given to the participant. They are
  encouraged to keep it; it is theirs.
* **Site copy.** Filed in the partner site's secure clinical
  storage, retained per the partner site's clinical-record
  retention policy.

A third copy is **not** made and the bundle is **not** uploaded to
any cloud service.

## 5. The research dataset (anonymised derivative)

In parallel, the Data Manager produces an **anonymised derivative
dataset** containing only:

* Study ID.
* The numeric values of all endpoints listed in
  [`SAP_v1.md`](SAP_v1.md) §3.
* Demographic strata used by the SAP (age band, baseline PTA band).

This is the *only* dataset that leaves the partner site. It is
stored in a version-controlled private repository on the partner
site's research infrastructure until database lock, then released
publicly per §8.

## 6. Withdrawal

If a participant withdraws:

1. Their participant bundle remains theirs (it never left them).
2. The Data Manager flags their study ID for exclusion. The Data
   Manager and CI jointly delete the corresponding row from the
   anonymised derivative dataset, **unless** the participant has
   given specific written permission for the anonymised data to be
   retained.
3. The deletion is logged in a dated entry in the study log.

## 7. Cloud and third-party services — the negative space

The following are **prohibited** under this SOP:

* Storing raw participant data in any cloud service.
* Sending raw participant data over email.
* Processing raw participant data in any LLM, "AI assistant" or
  third-party analytics service.
* Sharing the study ID ↔ name mapping over any channel other than
  the partner site's internal secure network.
* Using a USB stick for the participant bundle that has previously
  been used on a network without write protection (sticks are
  freshly formatted per participant).

These prohibitions are not bureaucratic. They are the operational
form of the Burgess Principle: a participant's data sovereignty
cannot survive a single careless cloud upload.

A suspected breach of any of the above is logged as an **AE-P**
adverse event per
[`docs/EVIDENCE_AND_VALIDATION.md`](../docs/EVIDENCE_AND_VALIDATION.md)
§5 and reported to the CI within 24 hours.

## 7a. Standards posture

This SOP is *aligned with* — not certified against — the standards
catalogued in
[`docs/ACCESSIBILITY_STANDARDS.md`](../docs/ACCESSIBILITY_STANDARDS.md).
In particular:

* It supports UK GDPR / GCP-aligned research practice for data
  handling.
* It uses **ISO 13485** only as a forward reference; OpenHear does
  not operate a certified quality management system.
* The clinical/research validation checklist in
  [`docs/EVIDENCE_AND_VALIDATION.md`](../docs/EVIDENCE_AND_VALIDATION.md)
  §4 (C1–C7) is the self-audit instrument every Data Manager applies
  before database lock.

## 8. Database lock and publication

* When the final participant has completed the day-7 follow-up, the
  CI declares **database lock**. The anonymised derivative dataset
  is frozen and tagged in the partner site's research repository.
* The pre-registered analyses (SAP v1) are run against the locked
  dataset. The analysis script and its output (figures, tables) are
  archived alongside the dataset.
* On acceptance of the pre-print or paper, the **anonymised**
  derivative dataset and analysis code are deposited on Zenodo
  under CC-BY 4.0, with a DOI. Participant consent for this open
  release is the relevant tick-box on the consent form
  ([`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md)).
* The participant bundles are **not** released — they belong to
  individual participants, not to the research team.

## 9. Audit and review

This SOP is reviewed by the CI and Data Manager:

* Before each new participant cohort.
* On any change to the OpenHear bundle-export tooling.
* On any change to relevant data-protection law (UK GDPR, etc.).

Each review is recorded in the version-history table below; SOP
changes increment the version number and are circulated to all
study staff.

## 10. Version history

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v1 (draft) | 2026-05-XX | OpenHear team | Initial public draft. |
