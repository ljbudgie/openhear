# Start here

You do not need to install anything.

OpenHear is a research project, not a certified hearing aid. It does not replace your audiologist. Start quiet if you later try any sound path. Your graph is yours. Nothing here should upload it to a company cloud unless *you* choose to paste it into a tool you already use.

## What this is, in one sentence

A way to turn your audiogram into a **Living Hearing Profile** — a plain-English page you keep, that can travel to the next appointment, and that can later drive a phone filter or a wrist vibration if you want that.

## Ten minutes with a phone

1. Get a copy of your audiogram (paper photo or PDF is fine).
2. Open ChatGPT, Claude, Gemini, or Grok.
3. Attach the graph and paste this:

```
This is my audiogram. Build a Living Hearing Profile in plain English.

Include:
- the shape of the loss (flat, sloping, cookie-bite, cliff, or mixed)
- roughly how loud quiet speech and group noise will feel
- which speech sounds (the letters printed on many graphs) sit above my thresholds
- what a second channel (lip-reading those specific shapes, or wrist vibration when aids are out) would be for

Do not diagnose.
Do not recommend a brand of hearing aid.
Keep it as a record I can take to my audiologist.
Do not invent thresholds that are not on the page.
```

4. Save the reply somewhere you control. That is the profile. You can bring it back next year and say what has changed (tinnitus on the test day, fatigue, new rooms).

You can stop here. Most people should.

## If you want the same words from this repository

People who already use Python can run the open explainer on a JSON audiogram:

```bash
python -m dsp.explain_cli examples/sample_audiogram.json
```

That uses `dsp/explain.py`. It is an explanation of a fitting you own, not a medical device.

## Three doors after that

| I am… | Go here |
|---|---|
| A person with hearing loss | This page. Then email lewisjames@theburgessprinciple.com if you want to be on the lived-experience list. Email only. |
| Someone who writes code | `docs/ARCHITECTURE.md` then `docs/INTEGRATORS.md` |
| Someone who funds or partners | `docs/FUNDING_AND_PARTNERSHIPS.md` and `docs/GO_TO_MARKET.md` |

The long README under this file is the build log and the vision. It is not the first step.

## What OpenHear is not asking you to buy

- Not a £3,000 aid.
- Not Noahlink (that is only for people who already own certain Phonak/Signia aids and want to read their own fitting).
- Not a tooth device.
- Not an app store login.

If funding lands, some people on the list may try a wristband prototype. That is later. The profile comes first.
