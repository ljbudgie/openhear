# Optional systemic context layer

**Status:** Design note  
**Date:** 2026-09-07  
**Purpose:** Record that a Living Hearing Profile may hold *user-owned* general-health context that affects listening effort, fatigue, and clinic attendance — without putting identifiable pathology results in the public repository.

## Why this belongs near hearing

Hearing is not only thresholds in a booth. Listening effort, recruitment, and the ability to attend appointments sit inside a wider body: inflammation, metabolic risk, renal function, energy, and whether the person can leave the house. Proprietary hearing systems ignore that. A citizen-owned profile should be allowed to hold it *locally*, under the same sovereignty rules as the audiogram.

## What the public repo will not contain

Named blood results, NHS numbers, surgery letterheads, or identifiable PDFs. Those stay with the person. The architecture only records the *shape* of an optional layer.

## Suggested optional fields (local-only)

- `systemic_context.version`
- `captured` (ISO date)
- `inflammation` — e.g. CRP / ESR band: low / raised / unknown
- `metabolic` — e.g. HbA1c band: low-risk / watch / unknown
- `renal` — e.g. eGFR band or “repeat flagged by lab”
- `energy_and_access` — housebound / limited travel / full mobility (user-declared)
- `notes` — free text the user chooses to keep

No clinical inference engine. No automatic diagnosis. The layer is a reminder that fatigue and access are first-class, not an NHS replacement.

## Design implications

- Fatigue-aware DSP and haptic comfort ceilings can read `energy_and_access` if the user opts in.
- Study questionnaires should ask whether systemic context exists, not scrape lab PDFs.
- Email remains a valid channel for a person to *hold* their own results. “View it on the NHS App” is not equivalent for everyone.

## Sovereignty

This layer is personal data. Local-first. No cloud sync. No commit of raw identifiable results to the public tree.
