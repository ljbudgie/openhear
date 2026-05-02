# OpenHear Pilot — Statistical Analysis Plan v1

> **Status.** Draft v1, May 2026. To be locked and timestamped on the
> Open Science Framework (OSF) before any participant is recruited.
> Companion to [`PILOT_PROTOCOL_v1.md`](PILOT_PROTOCOL_v1.md).

## 1. Purpose

This SAP fully specifies, in advance, every analysis that will be
performed on data from the OpenHear pilot study. It exists to remove
analyst degrees of freedom (the so-called "garden of forking paths")
and to make the published results interpretable as a single,
pre-specified test rather than the best of many post-hoc looks.

If an analysis is not described here, it is exploratory and will be
labelled as such in the report.

## 2. Datasets

* **Full Analysis Set (FAS).** All consented participants who
  complete at least one block of testing.
* **Per-Protocol Set (PPS).** Participants in FAS who complete both
  blocks within the protocol window (one calendar week) without
  major deviations.

The primary analysis uses FAS with multiple imputation for missing
data (see §6); the PPS analysis is a sensitivity analysis only.

## 3. Endpoints and analysis methods

### 3.1 Primary endpoint — QuickSIN SNR loss

* **Quantity.** Within-participant difference in QuickSIN SNR loss
  (dB), computed as
  `delta_i = SNR_loss_OpenHear_i − SNR_loss_OwnAid_i` for participant `i`.
* **Estimator.** Mean of `delta` across participants, with a 95 %
  bias-corrected and accelerated (BCa) bootstrap confidence interval
  (10 000 resamples, fixed seed `0xB00715`).
* **Decision rule.** No formal hypothesis test. The CI is reported.
  The *clinical interpretation* in the manuscript will be:
    * Upper CI bound ≤ +3 dB → **non-inferiority signal**.
    * Upper CI bound > +3 dB or CI crosses 0 → **inconclusive**.
    * Mean and full CI < 0 → **superiority signal** (not powered for).

### 3.2 Secondary endpoints

| Endpoint | Estimator | CI method |
|----------|-----------|-----------|
| SSQ-12 total change | Mean within-participant change | BCa bootstrap |
| SSQ-12 subscales (Speech / Spatial / Quality) | Mean change | BCa bootstrap |
| IOI-HA total | Mean Arm B − Arm A | BCa bootstrap |
| Forced-choice preference | Proportion preferring OpenHear | Wilson 95 % CI |
| Sovereignty questionnaire | Mean total | BCa bootstrap |
| Adverse event rate | Events per participant-week | Exact Poisson 95 % CI |

No multiplicity adjustment is applied to the secondary endpoints —
they are exploratory and will be reported as such, with all CIs
visible.

### 3.3 Order / period effects

A pre-specified Wilcoxon signed-rank test is performed on
`delta` stratified by randomisation order (AB vs. BA) to detect a
period effect. If p < 0.10 *and* the absolute mean difference between
strata exceeds 1 dB, a period-adjusted estimate using a linear
mixed-effects model with random participant intercept and fixed
effects for arm and period is reported as a sensitivity analysis.

## 4. Sample size justification

This is a feasibility pilot. With n = 20 paired observations and
assuming an SD of within-participant QuickSIN SNR loss difference of
2.5 dB (literature-supported, but to be re-estimated in §7), the
half-width of a 95 % CI on the mean difference is approximately
1.17 dB. This is sufficiently narrow to inform the Phase 2 RCT power
calculation without being so wide as to render the pilot
uninformative.

## 5. Pre-specified subgroup analyses

None. With n = 20, subgroup analyses are uninterpretable. Any
subgroup observation made post-hoc will be clearly labelled as
exploratory.

## 6. Handling of missing data

* Missing primary-endpoint values: multiple imputation (5 imputations)
  using a regression on age, baseline PTA and baseline SSQ-12. Rubin's
  rules used to combine point estimates and variances.
* Missing secondary-endpoint items within a scale: the published
  scale-specific scoring rules are followed; if undefined, the item
  is treated as missing and the participant is excluded from that
  scale's analysis only.
* Withdrawn participants whose data they wish destroyed: their data
  is excluded from all analyses (per SOP §6).

## 7. Pilot-driven estimates feeding Phase 2 design

The pilot will be used to estimate, for the Phase 2 RCT power
calculation:

1. The within-subject SD of QuickSIN SNR-loss difference.
2. The drop-out rate.
3. The expected mean difference (point estimate only — Phase 2 is
   not justified by an underpowered pilot estimate).

These will be reported transparently in the manuscript, with the
caveat that pilot-driven effect-size estimates are well known to be
inflated.

## 8. Software and reproducibility

* All analyses performed in Python (numpy, scipy, statsmodels) and R
  (for the mixed-effects sensitivity analysis only).
* Analysis code is committed to a public repository before the
  database lock and tagged with the SAP version.
* The random seed for the bootstrap (`0xB00715`) is fixed in the
  code.
* All results, including the analysis script and the anonymised
  dataset, will be published on Zenodo at the time of pre-print
  posting.

## 9. Version history

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v1 (draft) | 2026-05-XX | OpenHear team | Initial public draft. |
