# Hardware Roadmap

From documentation to sovereign device. Five phases, each building on the last.

---

## Phase 1: Documentation (Current)

**Status:** In progress

Lay the groundwork. Every decision documented. Every component specified. Every safety measure designed before a single wire is soldered.

- [x] Bill of materials with three build tiers
- [x] Tympan bridge script (audiogram JSON → Arduino sketch)
- [x] Safety module with MPO limiter design, calibration procedure, and risk register
- [x] Assembly guide for all three tiers
- [x] 3D printing guide for custom ear moulds
- [x] Parametric mould template documentation
- [ ] Community review of safety module
- [ ] Audiologist review of MPO calculations

**Exit criteria:** All documentation peer-reviewed. Safety module reviewed by at least one audiologist.

---

## Phase 2: Validated Build

**Status:** Not started

Build the first complete Tier 2 system. Document everything. Prove it works.

- [ ] First complete Tier 2 build documented with photos at every step
- [ ] Calibration data published (SPL measurements at all audiometric frequencies)
- [ ] MPO limiter verified with calibration microphone and 2cc coupler
- [ ] 30-day wear test with daily logs (comfort, battery life, audio quality, issues)
- [ ] Audiogram-driven gain verified against target (measured vs. expected at each frequency)
- [ ] Community feedback incorporated into documentation
- [ ] Known issues and limitations documented honestly
- [ ] Second build by a different person to validate instructions

**Exit criteria:** Two independent builders have completed Tier 2 builds. Calibration data published. 30-day wear test completed without safety incidents.

---

## Phase 3: Custom PCB

**Status:** Not started

Move from the Tympan development board to a custom PCB designed specifically for OpenHear. Smaller. Cheaper. Purpose-built.

- [ ] Custom PCB design for OpenHear (KiCad, open-source EDA)
- [ ] Smaller BTE form factor (target: 40mm × 12mm × 8mm)
- [ ] Integrated MPO limiter on-board (no external circuit needed)
- [ ] Same Teensy 4.1 processor or equivalent ARM Cortex-M7
- [ ] Lower power consumption through optimised power management
- [ ] Open hardware licence: CERN OHL-P (permissive)
- [ ] Gerber files published for community fabrication
- [ ] PCB cost target: under £40 per board at quantity 10
- [ ] Tympan Library compatibility maintained (same Arduino sketch runs on both)

**Exit criteria:** Custom PCB fabricated, assembled, and validated against Tympan Rev F performance. Open hardware files published under CERN OHL-P.

---

## Phase 4: Miniaturisation

**Status:** Not started

Shrink the device. Extend the battery. Add wireless connectivity.

- [ ] Target ITE (In-The-Ear) form factor
- [ ] Custom ASIC or FPGA for ultra-low-power DSP (target: <10mW active)
- [ ] Wireless charging (Qi standard)
- [ ] Bluetooth LE Audio for direct phone streaming (Auracast compatible)
- [ ] Full OpenHear mobile app integration (audiogram management, real-time tuning, session logging)
- [ ] Battery life target: 16+ hours on single charge
- [ ] Total device weight target: under 5g per ear
- [ ] Maintain hardware MPO limiter — never removed regardless of form factor

**Exit criteria:** ITE prototype demonstrated. Battery life exceeds 16 hours. Bluetooth LE Audio streaming validated.

---

## Phase 5: Sovereign Device

**Status:** Not started

The endgame. A complete, self-contained hearing aid with no external dependencies. You print it, you build it, you upload your audiogram, you hear.

- [ ] Complete self-contained hearing aid
- [ ] No proprietary components or firmware
- [ ] User prints shell, sources commodity components, uploads audiogram, hears
- [ ] Total cost target: under £100 for a binaural system at scale (quantity 100+)
- [ ] One-click audiogram-to-device pipeline (web app: upload audiogram → download firmware → flash device)
- [ ] Community-maintained component database with verified suppliers worldwide
- [ ] Regulatory pathway explored for CE/FDA classification (if community desires)
- [ ] Published peer-reviewed paper on open-source hearing aid performance vs. commercial devices

**Exit criteria:** 100 devices built by community members worldwide. Cost under £100 per binaural system. Performance within 5 dB of commercial hearing aids at matched price point.

---

## Principles

These apply to every phase:

1. **Safety first.** Hardware MPO limiter is never removed, regardless of form factor or cost pressure.
2. **Open everything.** Hardware designs, firmware, software, calibration data — all open-source, always.
3. **Sovereignty.** The user owns every layer. No cloud dependency. No subscription. No lock-in.
4. **Honesty.** Document what works, what doesn't, and what we don't know yet.
5. **Accessibility.** Instructions written for people without engineering backgrounds. Technical terms explained on first use.
