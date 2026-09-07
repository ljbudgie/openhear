# Systemic Context Layer

**Status:** Design principle  
**Date:** 2026-09-07  
**Composes with:** `openhear-living-profile-v1` (clinical core, preference, context map, haptic layer, history)

## Inclusion criterion (hard boundary)

A systemic factor is included only if it directly modulates sensory experience or access to sensory healthcare. This is a hard boundary, not a suggestion.

### Included by this rule

- **Fatigue** — modulates cognitive load, which affects auditory processing and speech-in-noise performance.
- **Housebound status** — modulates acoustic environment exposure and clinic access.
- **Transport barriers** — modulate access to audiologist appointments and hearing-aid maintenance.
- **Medications with known ototoxic or auditory-processing effects** — modulate hearing function directly.

### Excluded by this rule

- **Renal function**, unless the specific medication prescribed for it is ototoxic (then the medication is included, not the renal diagnosis).
- **Housing, finances, energy, legal cases** — these live in the citizen's private records, not in the public systemic-context architecture, unless they directly create a sensory access barrier (for example, energy poverty preventing hearing-aid battery purchase).

Inflammation bands, metabolic bands, and laboratory values are not fields of this layer. They do not by themselves modulate hearing or clinic access.

## Design rationale

The Systemic Context Layer is not a general life-tracking system. It is a bounded extension of the Living Hearing Profile that captures environmental and bodily context only where it intersects with sensory function or sensory healthcare access. This preserves the layer's integrity, prevents scope creep, and keeps the public architecture focused on its purpose: sovereign hearing data with the context that makes it meaningful.

## Composition with the Living Hearing Profile

`openhear-living-profile-v1` already holds:

1. Clinical core (locked thresholds)
2. Preference layer
3. Context map
4. Haptic layer
5. Append-only history

The Systemic Context Layer is an optional sixth surface. It does not mutate the clinical core. Fatigue-aware DSP and haptic comfort ceilings may read declared fields (`fatigue`, `housebound`, `transport_barrier`, `ototoxic_medication`) only when the user has opted the layer on. History records that the layer was declared or updated; it does not ingest diagnoses.

## Declaration, not inference

Fields are declared by the user, consistent with the accessibility-profile architecture (autism, cerebral palsy, sensory-processing). The system does not infer systemic context from lab PDFs, NHS App records, or correspondence. No clinical inference engine. No automatic diagnosis.

## Suggested local-only fields

- `systemic_context.version`
- `captured` (ISO date)
- `fatigue` — user-declared: none / present / severe
- `housebound` — user-declared boolean
- `transport_barrier` — user-declared boolean plus optional short note on the sensory-access effect
- `ototoxic_or_auditory_processing_medication` — user-declared list of names they choose to record, or empty
- `sensory_access_barrier` — optional free text limited to a barrier that blocks hearing care (for example, inability to obtain batteries)

## What the public repository will not contain

Identifiable pathology results, NHS numbers, surgery letterheads, named individuals, or live-case dates. Those stay with the person. The public tree holds only the shape of the layer and this boundary.

## Sovereignty

This layer is personal data. Local-first. No cloud sync. User-declared. No commit of raw identifiable results to the public tree.
