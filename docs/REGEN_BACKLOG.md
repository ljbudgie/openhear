# Regeneration Support — Short-Term Backlog (Issue-Ready)

> Companion to [`REGEN_VISION.md`](../REGEN_VISION.md) §7 (short-term, 3–6
> months) and [`REGEN_LOGGING_SPEC.md`](REGEN_LOGGING_SPEC.md). Each card
> below is structured so it can be opened as a GitHub issue with minimal
> editing. All cards are **[OPENHEAR]** assistive work; none implies any
> biological capability.

**How to read a card.** Each card has: *Goal*, *Context*, *Scope (in / out)*,
*Acceptance criteria*, *Dependencies*, *Estimate band* (S/M/L —
qualitative only, no calendar promise), *Suggested labels*.

---

## #1 — Add `REGEN_VISION.md`, spec, and backlog to docs index

**Goal.** Make the regeneration documents discoverable from the same
entry points as the rest of the project docs.

**Context.** `REGEN_VISION.md` and `docs/REGEN_LOGGING_SPEC.md` exist;
this card just makes them first-class in navigation.

**Scope (in).**
- Cross-links between `REGEN_VISION.md`, `docs/REGEN_LOGGING_SPEC.md`,
  and `docs/REGEN_BACKLOG.md`.
- `docs/index.md` entry routing readers to the regeneration vision.
- A README pointer in the "New north-star documents" list.

**Scope (out).** Any new content beyond cross-links.

**Acceptance criteria.**
- All three documents link to each other.
- `docs/index.md` has a regeneration section.
- README north-star list includes the vision document.

**Dependencies.** None.

**Estimate band.** S.

**Suggested labels.** `docs`, `regen`.

---

## #2 — Define `regen-*-v1` record schemas in code

**Goal.** Land the four record families from
[`REGEN_LOGGING_SPEC.md`](REGEN_LOGGING_SPEC.md) §2 as typed structures.

**Context.** Currently the schemas exist only in prose. Encoding them
in code makes them testable and validates §5 refusal rules.

**Scope (in).**
- A new `regen/` package with a `schemas.py` module declaring the four
  record types and the shared fields from §2.5.
- A `validate(record)` function enforcing every refusal case in §5,
  raising distinct exception subclasses where they aid debugging.
- Unit tests for each refusal case and each happy path.

**Scope (out).**
- Commit/verify integration (covered by #3).
- Storage and indexing (covered by #4).
- Any UI.

**Acceptance criteria.**
- All four families validate at least one minimal valid example.
- Every refusal case in §5 has a test that verifies the adapter
  correctly rejects the invalid input.
- `make ci` passes.

**Dependencies.** None.

**Estimate band.** M.

**Suggested labels.** `regen`, `schema`, `tests`.

---

## #3 — Add `regen/commit.py` adapters over the existing advocacy gate

**Goal.** Implement the four adapter functions from
[`REGEN_LOGGING_SPEC.md`](REGEN_LOGGING_SPEC.md) §3.1 so any regen record
can be committed and exported through the existing
`openhear-advocacy-v1` schema family.

**Context.** The advocacy layer already exposes
`commit(label, facts, tags)`, `export_record`, `RawAudioRejectedError`,
and the canonical serialisation. This card adds thin adapters; it must
not introduce a new schema family (Burgess commitment 5).

**Scope (in).**
- `audiogram_record_commitment`, `speech_in_noise_record_commitment`,
  `haptic_perception_record_commitment`,
  `functional_log_record_commitment`.
- Tag merging via the existing `_merge_tags` helper (or its equivalent).
- Raw-audio rejection via the existing walk.
- Round-trip tests: write → commit → `export_record` → offline `verify`
  for each family.

**Scope (out).**
- Any change to `openhear-advocacy-v1` schema identifiers.
- Network I/O.
- Receipt UI.

**Acceptance criteria.**
- Bundles produced for each family verify offline using the existing
  `verify` path.
- A `bytes` / `bytearray` / `memoryview` / `numpy.ndarray` placed anywhere
  in a record raises `RawAudioRejectedError`.
- `make ci` passes.

**Dependencies.** #2.

**Estimate band.** M.

**Suggested labels.** `regen`, `advocacy`, `tests`.

---

## #4 — Local-first record storage and index

**Goal.** Persist records per
[`REGEN_LOGGING_SPEC.md`](REGEN_LOGGING_SPEC.md) §4: append-only,
one-file-per-record, with a derived index that can be rebuilt.

**Scope (in).**
- A `regen/store.py` with `save(record)`, `load(record_id)`,
  `list_records(filter=...)`, `rebuild_index()`, `delete(record_id)`.
- Atomic write + rename.
- Tests covering atomicity, idempotent rebuild, and deletion semantics.

**Scope (out).** Cloud sync, multi-user, encryption-at-rest (a separate
card if/when required by the user).

**Acceptance criteria.**
- Killing the process mid-write never produces a half-written record.
- `rebuild_index()` from a deleted index file produces the same listing
  as the previous index.
- `make ci` passes.

**Dependencies.** #2.

**Estimate band.** M.

**Suggested labels.** `regen`, `storage`, `tests`.

---

## #5 — Pre/post training-mode flag in existing protocols

**Goal.** Add a `phase` parameter (`"pre" | "post" | "general"`) and a
`fatigue_cap` parameter to the existing protocol/training configuration
in `therapy/` and `learn/`, with conservative defaults and rest logic.

**Context.** `REGEN_VISION.md` §7 short-term milestone "Pre/post
training-mode flag in existing protocols". Aligns with
[`docs/RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md) Q5 (onboarding) and
Q9–Q10 (therapeutic safety and scheduling).

**Scope (in).**
- Config schema additions and validation.
- At least two protocol variants exposing the flag (one general, one
  designated as a "post-intervention adaptation" variant for users with
  changing peripheral hearing).
- Fatigue scoring already present in the user's reported flow, surfaced
  into the new `fatigue_cap` with explicit rest scheduling.
- Tests.

**Scope (out).**
- Any biological-outcome claim.
- New protocols beyond variants of existing ones.

**Acceptance criteria.**
- The two variants can be selected and exercise different rest logic.
- Defaults are conservative (low cap, mandatory rest after threshold).
- `make ci` passes.

**Dependencies.** None (but benefits from #2 if logging is wired in).

**Estimate band.** M.

**Suggested labels.** `regen`, `therapy`, `safety`.

---

## #6 — Claim-language lint check

**Goal.** A CI-friendly check that flags disallowed phrasings in
OpenHear-authored documentation and user-facing strings related to
regeneration.

**Context.** `REGEN_VISION.md` §8.2 hard rules. The check protects
future contributors (including AI coding agents) from drifting into
biological-cure language.

**Scope (in).**
- A small script (Python preferred for consistency with the existing
  toolchain) that scans `docs/`, `REGEN_VISION.md`, and any opted-in
  source globs for disallowed phrases (e.g. `regenerate`, `regrow`,
  `cure`, `restore hearing`) **unless** the same paragraph also contains
  one of the approved scope tags (`[APPROVED]`, `[CLINICAL]`,
  `[PRECLINICAL]`, `[OPENHEAR]`, `[ASPIRATION]`) or an explicit
  "OpenHear does not" disclaimer.
- A Makefile target (e.g. `make claim-lint`) and a CI hook.
- Tests for the check itself (passing and failing fixtures).

**Scope (out).**
- Linting external dependencies or third-party docs.
- Auto-fix; the check reports only.

**Acceptance criteria.**
- The check passes on `REGEN_VISION.md` and `docs/REGEN_LOGGING_SPEC.md`
  unchanged.
- The check fails on a fixture that contains a disallowed phrase with
  no scope tag.
- `make ci` (or a new `make ci-docs`) runs the check.

**Dependencies.** None.

**Estimate band.** S–M.

**Suggested labels.** `regen`, `docs`, `ci`.

---

## #7 — Reviewer sign-off milestone

**Goal.** Satisfy the `REGEN_VISION.md` §7 short-term milestone
"`REGEN_VISION.md` reviewed by user + ≥1 clinician".

**Context.** Per Burgess commitment 3, a SOVEREIGN tag requires a named
human reviewer applying judgement to the specific facts. The vision
document and this short-term tranche of cards benefit from the same
discipline.

**Scope (in).**
- Identify the named clinical reviewer (open question §10.3 of the
  vision).
- Record the review outcome (acceptance, requested changes, or NULL) in
  a reviewer log file (`clinical/REGEN_VISION_REVIEW.md`).
- Apply any agreed changes to `REGEN_VISION.md`.

**Scope (out).** Any change that weakens claim discipline.

**Acceptance criteria.**
- The reviewer log exists with the reviewer's name, date, and outcome.
- Outstanding requested changes (if any) are tracked as follow-up
  issues.

**Dependencies.** None blocking, but ideally follows #1.

**Estimate band.** S (excluding the reviewer's own time, which is
outside this project).

**Suggested labels.** `regen`, `governance`.

---

## Execution order suggestion

1. **#1** (docs wiring) — unblocks everything else cheaply.
2. **#2** (schemas) → **#3** (advocacy adapters) → **#4** (storage).
3. **#5** (training-mode flag) and **#6** (claim-lint) in parallel with
   #3/#4 since they touch independent paths.
4. **#7** (reviewer sign-off) once the vision and spec are stable.

Medium- and long-term milestones from `REGEN_VISION.md` §7 are
deliberately not turned into cards yet; they should be cut once the
short-term tranche above is in place and we have real data on how the
record families are being used.
