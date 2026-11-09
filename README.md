<p align="center">
  <img src="https://github.com/user-attachments/assets/0857d69a-a8ad-45cd-87c1-6dadb0097708" alt="OpenHear hero" width="100%">
</p>

# OpenHear

**First time here?** Start at <a href="START_HERE.md">START_HERE.md</a> — phone, audiogram, ten minutes. You do not need GitHub after that.

### Your senses. Your data. Your world.

[![Licence: Apache 2.0](https://img.shields.io/badge/licence-Apache%202.0-blue.svg)](LICENSE)

**Built on the Burgess Principle** — see [docs/BURGESS_PRINCIPLE.md](docs/BURGESS_PRINCIPLE.md).
→ <a href="docs/index.md">Full documentation index</a>

> **⚠️ EXPERIMENTAL — NOT A MEDICAL DEVICE**
> OpenHear is a research platform and public build log, not a certified hearing aid.
> Start at low volume, validate every configuration on your own hardware, and do
> not treat any module in this repository as a substitute for clinical care.
>
> The only intended-purpose statement is in [docs/INTENDED_PURPOSE.md](docs/INTENDED_PURPOSE.md):
> *OpenHear is a research platform that turns the wearer's own audiogram into haptic patterns for environmental sound awareness. It is not a certified medical device, not a hearing aid, and not a replacement for clinical care.*

OpenHear is an open-source research platform for environmental sound awareness. It recognises a small set of everyday sounds and turns each sound class into a short, distinct vibration pattern on the wrist. The patterns are weighted by the wearer's own audiogram. Recognition runs on the device. Nothing is sent to a cloud. The audiogram stays with the person.

It is designed to work alongside existing hearing aids, or when aids are out. It does not amplify sound. The current claim is awareness only.

The repository also contains exploratory architecture notes on longer-term ideas (including wrist-native processing and hardware concepts). Those notes are not the present claim. Any reviewer should start with [docs/INTENDED_PURPOSE.md](docs/INTENDED_PURPOSE.md) and [START_HERE.md](START_HERE.md).

> *Your audiogram is a measurement of your body. It belongs to you.*
> *OpenHear keeps it on the device and uses it to shape awareness patterns.*

---

## Contents

- <a href="START_HERE.md">Start here</a>
- [Why OpenHear in 2026](#why-openhear-in-2026)
- [What this is](#what-this-is)
- [The Burgess Principle](#the-burgess-principle)
- [The problem](#the-problem)
- [What OpenHear does](#what-openhear-does)
- [OpenHear Wristband — Active Environmental Intelligence](#openhear-wristband--active-environmental-intelligence)
- [Exploratory notes](#exploratory-notes)
- [Getting started — three paths](#getting-started--three-paths)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Legal](#legal)
- [Author](#author)

---

## Why OpenHear in 2026

Many people with severe or profound loss, and people who remove their aids, miss everyday environmental sounds: a knock, an alarm, a child calling from another room, traffic. Phone alerts need the phone in reach. Fixed transmitters need one device per source. OpenHear is an open-source attempt to close that gap with short, distinct wrist vibration patterns weighted by the person's own audiogram. Licensed under Apache 2.0 (see [`LICENSE`](LICENSE)).

---

## What this is

OpenHear is an open-source research platform for environmental sound awareness through haptic patterns on the wrist. It is not a hearing aid and not a certified medical device. The canonical intended-purpose statement is in [docs/INTENDED_PURPOSE.md](docs/INTENDED_PURPOSE.md).

It can be used alongside aids the person already owns. The wristband (in development) scans for sounds the aids may not deliver and translates recognised classes into vibration. Recognition and the audiogram stay on the device.

**Tested on:**
- Phonak Naída M70-SP (Marvel platform)
- Signia Insio 7AX (Augmented Xperience platform)

**Required hardware for the current path:**

Path 1 does not need specialist fitting hardware. See START_HERE.md.

- iPhone or Android
- OpenHear Wristband *(in development)* — continuous-wear haptic patterns for recognised sound classes. See the OpenHear Wristband section below.

---

## The Burgess Principle

The Burgess Principle is the ethical root from which OpenHear grows. It is a framework, authored by Lewis James Burgess, for sovereign handling of clinical audiology data so that a person can hold an independent, verifiable, offline record of what was committed to and by whom.

It rests on five commitments, enforced in this repository (see `advocacy/gate.py`, `advocacy/adapters.py`, and `NOTICE`):

1. **Sovereign facts belong to the person they describe.** The audiogram is never transmitted without that person's explicit consent.
2. **Every clinical commitment is cryptographically verifiable.** A SHA-256 commitment over a canonical serialisation is the only value intended to leave the device.
3. **Trust is binary: `SOVEREIGN` or `NULL`.** A named human reviewing the specific facts produces `SOVEREIGN`; pure automation produces `NULL`.
4. **Raw audio is not a clinical fact.** Any attempt to commit raw audio into a facts payload raises an error before a commitment is produced.
5. **Schema ownership is singular.** The schema family is owned by this repository.

The full statement is in [`docs/BURGESS_PRINCIPLE.md`](docs/BURGESS_PRINCIPLE.md).

---

## The problem

Modern hearing aids are extraordinary pieces of engineering. They are also, deliberately, black boxes for the data they hold and the decisions they make in real time.

The audiogram stored in a hearing aid is a measurement of the person's hearing. In many systems it is not straightforward for the person to hold a plain, portable copy that travels with them and shapes other tools they choose to use. OpenHear keeps that copy on the device and uses it only to weight vibration patterns for environmental awareness.

---

## What OpenHear does

```
World → On-device classifier → Sound class → Short vibration pattern on the wrist
         (weighted by the person's audiogram, held on the device)
```

**Current claim:** detection and identification of a small set of everyday environmental sound classes, delivered as distinct haptic patterns. Not speech recognition. Not amplification. Not a replacement for clinical care.

**Audiogram module** — the person's own thresholds stay on the device and weight the patterns. See the Living Hearing Profile.

**Wristband** *(in development)* — continuous-wear haptic delivery of the recognised classes. Designed to work alongside aids or when aids are out.

---

## OpenHear Wristband — Active Environmental Intelligence

The wristband scans the environment on the wrist and delivers short, distinct vibration patterns for recognised sound classes. It is designed to work *alongside* hearing aids, not replace them.

```
World → Wrist microphone → On-device classifier → Haptic pattern → Wrist
```

**On-device classification** — recognition runs on the device. Nothing is sent to a cloud.

**Haptic patterns** — different sound classes produce different short vibration signatures, weighted by the person's audiogram.

**Local only** — the audiogram and the recognition stay on the device.

### How it relates to existing devices

Neosensory Buzz was a commercial haptic wristband that converted sound into vibration. OpenHear is open-source, keeps the audiogram on the device, and limits the claim to awareness of recognised environmental classes.

---

## Exploratory notes

The repository contains longer-term architecture notes (including ideas about wrist-native processing and hardware concepts). These are exploratory. They are not the present intended purpose. The only claim a reviewer should use is the sentence in [docs/INTENDED_PURPOSE.md](docs/INTENDED_PURPOSE.md).

---

## Getting started — three paths

See [START_HERE.md](START_HERE.md).

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

---

## Contributing

Contributions are welcome under the Apache 2.0 licence. Please start with the intended-purpose statement so that changes do not expand the claim without an explicit update to docs/INTENDED_PURPOSE.md.

---

## Legal

OpenHear is experimental software and a public build log. It is not a certified medical device. Do not use it as a substitute for clinical care. Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).

---

## Author

Lewis James Burgess  
OpenHear | https://github.com/ljbudgie/openhear  
The Burgess Principle | UK Certification Mark UK00004343685
