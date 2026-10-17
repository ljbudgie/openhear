# OpenHear Pilot — Statistical Analysis Plan v1

> **Status.** Draft v1, May 2026, amended 17 October 2026 to match the
> canonical intended purpose. To be locked and timestamped on the Open
> Science Framework (OSF) before any participant is recruited.
> Companion to [`PILOT_PROTOCOL_v1.md`](PILOT_PROTOCOL_v1.md) and
> [`docs/INTENDED_PURPOSE.md`](../docs/INTENDED_PURPOSE.md).

## 1. Purpose

This SAP fully specifies, in advance, every analysis that will be
performed on data from the OpenHear pilot study. It exists to remove
analyst degrees of freedom (the so-called "garden of forking paths")
and to make the published results interpretable as a single,
pre-specified analysis rather than the best of many post-hoc looks.

If an analysis is not described here, it is exploratory and will be
labelled as such in the report.

## 2. Datasets

* **Full Analysis Set (FAS).** All consented participants who complete
  at least one awareness session.
* **Per-Protocol Set (PPS).** Participants in FAS who complete both
  sessions within the protocol window (one calendar week) without major
  deviations.

The primary analysis uses FAS with multiple imputation for missing data
(see §6); the PPS analysis is a sensitivity analysis only.

## 3. Endpoints and analysis methods

### 3.1 Primary endpoint — hit rate and false-alert rate

* **Quantity.** Per participant: hit rate (correct sound class named
  from the haptic pattern) and false-alert rate.
* **Estimator.** Mean hit rate and mean false-alert rate across
  participants, each with a 95 % bias-corrected and accelerated (BCa)
  bootstrap confidence interval (10 000 resamples, fixed seed
  `0xB00715`).
* **Decision rule.** No formal hypothesis test. The CIs are reported.
  There is no non-inferiority margin against a hearing aid.

### 3.2 Secondary endpoints

| Endpoint | Estimator | CI method |
|----------|-----------|-----------|
| QuickSIN SNR loss (if collected) | Mean, descriptive only | BCa bootstrap |
| SSQ-12 total change | Mean within-participant change | BCa bootstrap |
| Forced-choice preference | Proportion preferring the pattern set | Wilson 95 % CI |
| Sovereignty questionnaire | Mean total | BCa bootstrap |
| Adverse event rate | Events per participant-week | Exact Poisson 95 % CI |

No multiplicity adjustment is applied to the secondary endpoints —
they are exploratory and will be reported as such, with all CIs
visible. QuickSIN is not the primary endpoint.

## 4. Sample size justification

This is a feasibility pilot. With n = 20, the confidence intervals on
hit rate and false-alert rate are wide enough to inform a later study
and narrow enough to be informative about feasibility. Power
calculations for a later study will be derived from this pilot.

## 5. Pre-specified subgroup analyses

None. With n = 20, subgroup analyses are uninterpretable. Any subgroup
observation made post-hoc will be clearly labelled as exploratory.

## 6. Handling of missing data

* Missing primary-endpoint values: multiple imputation (5 imputations)
  using a regression on age and baseline PTA. Rubin's rules used to
  combine point estimates and variances.
* Missing secondary-endpoint items within a scale: the published
  scale-specific scoring rules are followed; if undefined, the item is
  treated as missing and the participant is excluded from that scale's
  analysis only.
* Withdrawn participants whose data they wish destroyed: their data is
  excluded from all analyses (per SOP §6).

## 7. Pilot-driven estimates feeding a later study

The pilot will be used to estimate:

1. The hit rate and false-alert rate, and their within-subject
   variability.
2. The drop-out rate.
3. The expected mean difference on any secondary measure (point
   estimate only).

These will be reported transparently in the manuscript, with the caveat
that pilot-driven effect-size estimates are well known to be inflated.

## 8. Software and reproducibility

* All analyses performed in Python (numpy, scipy, statsmodels).
* Analysis code is committed to a public repository before the database
  lock and tagged with the SAP version.
* The random seed for the bootstrap (`0xB00715`) is fixed in the code.
* All results, including the analysis script and the anonymised
  dataset, will be published on Zenodo at the time of pre-print posting.

## 9. Version history

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v1 (draft) | 2026-05-XX | OpenHear team | Initial public draft. |
| v1 amended | 2026-10-17 | OpenHear team | Primary endpoint changed from QuickSIN vs own aid to hit rate and false-alert rate. |
