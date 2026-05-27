# Phase 5: Sovereign Device implementation plan

Phase 5 is the software and hardware bridge from OpenHear's current Tympan and
shell work toward a complete self-contained device. The repository can complete
the software scaffold now without claiming that the physical 100-device exit
criteria, cost proof, peer-reviewed comparison, or regulatory pathway have been
completed.

## Scope completed in this phase

1. **Local one-click bundle generation**
   - Input: an `openhear-audiogram-v1` JSON audiogram.
   - Output: generated firmware plus `manifest.json` in a user-selected local
     directory.
   - Constraint: no network dependency, no cloud upload, and no raw audio.

2. **Sovereign build manifest**
   - Stores firmware, audiogram, and component-database hashes.
   - Records safety requirements and regulatory status.
   - Records cost-target status without embedding audiogram thresholds.

3. **Community component database**
   - Uses an explicit schema version.
   - Requires verified suppliers for every required device role.
   - Rejects proprietary components or proprietary firmware dependencies.
   - Tracks an under-£100 binaural target at quantity 100.

4. **CLI entry point**
   - `openhear-phase5-device <audiogram.json> <output-dir>`
   - Defaults to binaural output; `--single-ear --ear left|right` is available
     for one-ear firmware checks.

5. **Tests**
   - Validate database schema and cost target.
   - Validate manifest privacy and safety fields.
   - Validate generated firmware and CLI behavior.
   - Validate rejection of proprietary component database entries.

## Boundaries

- The pipeline is experimental and does not make a medical-device claim.
- The passive hardware MPO limiter remains mandatory.
- Generated firmware must be calibrated on the user's actual hardware before
  listening.
- The component database is a community verification scaffold, not a purchase
  guarantee.

## Future completion gates

The hardware roadmap exit criteria still require real-world work outside this
software scaffold:

- 100 community-built devices worldwide.
- Published calibration and performance data.
- Binaural cost under £100 at quantity 100+ using verified suppliers.
- Performance within 5 dB of matched commercial devices.
- Community decision on whether to pursue CE/FDA/UK MDR classification.
