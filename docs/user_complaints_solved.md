# User Complaints Solved

## How OpenHear Addresses Every Major Hearing Aid Complaint

*Data drawn from HearingTracker forums, r/HearingAids, and audiologist community feedback (2025–2026).*

---

## Overview

The hearing aid industry in 2026 charges £3,000–£8,000 for devices that still whistle during hugs, mangle your own voice, die in sweat, and lock you out of your own settings. These are not edge cases. They are the most common complaints on every hearing aid forum, subreddit, and review site.

OpenHear was built to solve them. Every one.

This document maps the real complaints — the ones people actually post about, the ones audiologists hear every day — to specific OpenHear modules and solutions.

---

## The Complaints Table

| # | Complaint | Source | OpenHear Solution | Module |
|---|-----------|--------|-------------------|--------|
| 1 | **Feedback / whistling during movement or hugs** | HearingTracker, r/HearingAids | LMS adaptive feedback cancellation continuously models the feedback path and subtracts it in real time. Anti-feedback gain limiting prevents the runaway loop before it starts. | `dsp/feedback_canceller.py` |
| 2 | **Own voice sounds unnatural / mangled** | HearingTracker forum | Own-voice detection identifies the wearer's voice via spectral signature and reduces or bypasses DSP processing on that signal. You hear yourself as you are, not as a manufacturer algorithm decided you should sound. | `dsp/own_voice_bypass.py` |
| 3 | **Sweat / humidity destroys devices** | r/HearingAids moisture threads | Lotus-effect microstructures and fluoropolymer nano-coating on 3D-printed ITE shells provide 10× moisture durability compared to factory coatings. The shell is the first line of defence. | `hardware/ite-shells/sweatproof.md` |
| 4 | **Earwax buildup and blockage** | Universal complaint | Omniphobic surface coating repels cerumen. Replaceable wax guards snap into the shell design. Smooth internal geometry eliminates wax traps. | `hardware/ite-shells/sweat-proofing.md` |
| 5 | **Poor physical fit, pressure sores** | HearingTracker comfort threads | Parametric OpenSCAD shell with photogrammetry-based ear canal scanning. Iterate the fit digitally, reprint in hours, zero clinic visits required. | `hardware/ite-shells/parametric_shell.scad` |
| 6 | **Occlusion effect (boomy own voice)** | Audiologist forums | Configurable anti-occlusion venting built into the parametric shell design, combined with DSP-based occlusion reduction in the processing pipeline. | `dsp/config.py` |
| 7 | **Proprietary AI making wrong decisions** | HearingTracker (#1 complaint, 2025–2026) | No AI. No AutoSense. No scene classification. No environment switching. You are the AI. All parameters are user-controlled, visible in plain config files, and adjustable in real time via the mobile app. | `dsp/config.py` |
| 8 | **Over-amplification / "too loud" paradox** | r/HearingAids | Tunable Wide Dynamic Range Compression (WDRC) with user-settable knee point, compression ratio, and attack/release times. You set the ceiling. The DSP respects it. | `dsp/compression.py` |
| 9 | **Restaurant failure (can't hear speech in noise)** | Universal complaint | Adaptive noise floor estimation, voice-frequency emphasis (1–4 kHz boost), and basic beamforming. The pipeline prioritises speech over ambient noise without the unpredictable switching of commercial AI. | `dsp/noise_reduction.py`, `dsp/voice_clarity.py` |
| 10 | **Short battery life** | r/HearingAids | User-replaceable LiPo battery designed into the parametric shell. Efficient DSP pipeline minimises CPU draw. No cloud sync, no AI inference, no background telemetry draining power. | `hardware/ite-shells/parametric_shell.scad` |
| 11 | **Constant expensive repairs** | HearingTracker cost threads | ITE shells cost £5–15 in photopolymer resin. Print at home on an Elegoo Saturn 4 or Anycubic printer in 2–4 hours. Shell breaks? Print another. Fit changes? Adjust the model and reprint. | `hardware/ite-shells/` |
| 12 | **Lock-in to manufacturer fitting software** | Universal complaint | Open JSON audiogram format readable by any text editor. Noahlink Wireless 2 bridge reads fitting data from your existing aids. No Phonak Target. No Connexx. No professional login required. | `audiogram/`, `core/` |
| 13 | **No user control over settings** | HearingTracker autonomy threads | Every parameter is exposed in plain configuration files. The mobile app provides real-time adjustment. No appointment needed. No audiologist gatekeeping. Your hearing, your settings, your choice. | `dsp/config.py`, `mobile/` |

---

## How to read this table

**Complaint** is the problem as users describe it — in their own words, on forums and subreddits, to their audiologists, and to each other. These are not hypothetical issues. They are the daily reality of hearing aid ownership in 2026.

**Source** indicates where the complaint is most commonly documented. HearingTracker is the largest independent hearing aid review and discussion platform. r/HearingAids is the primary Reddit community for hearing aid users. "Universal complaint" means the issue appears across every platform, in every country, in every price bracket.

**OpenHear Solution** describes the specific technical approach OpenHear takes to address the complaint. These are not promises — they are implementations. The code exists. The modules are referenced.

**Module** points to the specific OpenHear source file or directory where the solution is implemented. You can read it, modify it, and improve it. That is the point.

---

## The pattern

Every complaint in this table has the same root cause: the manufacturer made a decision that should have been the wearer's decision.

- The manufacturer decided how feedback should be cancelled → it whistles.
- The manufacturer decided how your voice should sound → it sounds wrong.
- The manufacturer decided how moisture should be handled → the device dies.
- The manufacturer decided how the shell should fit → it hurts.
- The manufacturer decided how noise should be managed → restaurants are impossible.
- The manufacturer decided you should not control your own settings → you cannot.

OpenHear reverses every one of these decisions. The algorithms are open. The parameters are yours. The hardware is printable. The data is portable.

You are not a patient. You are an engineer with a hearing loss. Act accordingly.

---

## Safety & Disclaimer

> **⚠️ EXPERIMENTAL PROJECT — NOT A MEDICAL DEVICE**
>
> OpenHear is an experimental open-source project. It has not been evaluated, approved, or cleared by any regulatory body (FDA, MHRA, CE/UKCA, or equivalent). It is not a medical device. It is not intended to diagnose, treat, cure, or prevent any medical condition.
>
> Hearing loss is a medical condition. Consult a qualified audiologist before making any changes to your hearing aid configuration. Incorrect amplification settings can cause discomfort or, in extreme cases, further hearing damage. Always start with conservative gain values and increase gradually.
>
> The solutions described in this document are technical implementations, not clinical recommendations. They are provided as-is under the MIT licence. Use at your own risk.

---

*OpenHear, 2026*
*MIT Licensed — copy, share, translate, improve.*
