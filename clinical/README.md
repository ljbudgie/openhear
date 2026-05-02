# OpenHear — Clinical Pathway

> **Status.** Pre-IRB / pre-REC. v0 documents posted May 2026 for
> public review.
>
> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE.** OpenHear is a research
> platform. No human research described in this directory may begin
> until the relevant Research Ethics Committee (REC, in the UK) or
> Institutional Review Board (IRB) has issued written approval and a
> qualified clinical investigator has signed the protocol.

## What is in this directory

| File | Purpose |
|------|---------|
| [`PILOT_PROTOCOL_v1.md`](PILOT_PROTOCOL_v1.md) | n=20 within-subject crossover pilot study comparing OpenHear vs. participant's own commercial hearing aid on speech-in-noise and quality-of-life endpoints. |
| [`SAP_v1.md`](SAP_v1.md) | Pre-registered statistical analysis plan for the pilot. To be uploaded to OSF before recruitment opens. |
| [`CONSENT_TEMPLATE.md`](CONSENT_TEMPLATE.md) | Plain-language consent template encoding the [Burgess Principle](../docs/BURGESS_PRINCIPLE.md): the participant retains a signed copy of all of their own data. |
| [`DATA_MANAGEMENT_SOP.md`](DATA_MANAGEMENT_SOP.md) | Standard Operating Procedure for collection, storage, anonymisation and export of study data. Sovereign by construction. |

## What is **not** here yet, and why

| Artefact | Status | Owner |
|----------|--------|-------|
| Signed Letter of Intent from a UK university audiology partner | Outreach in progress (UCL Ear Institute, Manchester, Southampton ISVR). Phase 1 day-30 deliverable. | Project lead |
| IRB/REC submission cover letter and CV/GCP certificates of investigators | Drafted alongside protocol; submission gated on partner LOI. | Clinical PI (TBC) |
| Protocol PDF (controlled, signed) | The Markdown protocol here is the working draft; the controlled PDF will be generated for submission and stored alongside under version control. | Clinical PI (TBC) |
| Case Report Forms (CRFs) | To be derived from `PILOT_PROTOCOL_v1.md` §8 once endpoints are locked. | Data manager (TBC) |

## How to read this directory

1. Read `PILOT_PROTOCOL_v1.md` first. It defines the question being
   asked, the population, and the endpoints.
2. Then read `SAP_v1.md`. The SAP is deliberately separate so that the
   analysis plan can be locked and time-stamped (by OSF
   pre-registration) before any data is collected, removing the
   degrees of freedom that lead to under-powered or
   garden-of-forking-paths results.
3. `DATA_MANAGEMENT_SOP.md` and `CONSENT_TEMPLATE.md` show how the
   Burgess Principle is operationalised: the participant ends every
   session holding a cryptographically signed bundle of their own
   raw data, and the researcher only ever holds an anonymised
   derivative.

## Contributing

Issues and pull requests against these documents are welcome from
clinicians, ethicists, statisticians, and people who use hearing
aids. The protocol is **not** considered final until at least one
external clinical reviewer who has not contributed code to this
project has signed off in a public review thread.
