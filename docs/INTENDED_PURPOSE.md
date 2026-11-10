# Intended purpose

This is the only intended-purpose statement for OpenHear. Other files point here.

## Canonical sentence

OpenHear is a research platform that turns the wearer's own audiogram into haptic patterns for environmental sound awareness. It is not a certified medical device, not a hearing aid, and not a replacement for clinical care.

## What that sentence means

- The purpose is awareness of environmental sound through vibration, shaped by the wearer's own thresholds.
- Supported classes in the current code: voice, doorbell, alarm, dog, traffic, media, knock, baby_cry, phone, silence.
- Examples named in this statement (knock, baby cry, alarm, traffic) are classes the code now supports.
- From v1.8.0 the traffic class fires on vehicle warnings only (horns, reversing beeps, skidding, tyre squeal, train horn), not on engines. Bench testing found horn detection weak, so the traffic pattern is not a safety feature and must not be relied on to warn of a vehicle.
- The audiogram stays with the person. It is not uploaded unless the person chooses to paste it into a tool they already use.
- Classification by a regulator is decided by the claim. This file states the claim. It does not assert a Class I or Class IIa status.
- A future clinical claim (for example compensation for reduced hearing) would require this file to be updated first, and every other file to follow it. Until that update, the research sentence is the claim.

## Tinnitus safety notice

OpenHear is not designed to treat or manage tinnitus. If you have tinnitus in one ear only, pulsatile tinnitus, or sudden-onset tinnitus with hearing loss, see a healthcare professional promptly (NICE NG155 section 1.2). If tinnitus is linked to thoughts of self-harm or suicide, seek help urgently. If you think amplification is making your tinnitus worse, speak to your audiologist first. Further information: https://tinnitus.org.uk/how-we-can-help/

## What a pilot must measure

If a study is run, the endpoints must match this sentence. Detection and identification of environmental sound events, plus safety and independence, are the matching endpoints. A comparison with participants' own hearing aids on speech-in-noise tests amplification, not awareness, and does not support this claim.

## Status

Last confirmed 10 November 2026. Public release at that date: v1.8.0. Classifier-only bench results are in [BENCH_RESULTS.md](BENCH_RESULTS.md).
