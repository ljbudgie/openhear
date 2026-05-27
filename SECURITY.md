# Security Policy

OpenHear is a research platform that processes audio for and around the human
ear. Security and safety bugs in this repository can have real physical
consequences (e.g. excessive sound pressure, loss of feedback control, leaking
of sensitive audiometric data). We take both classes of issue seriously.

## Supported versions

OpenHear is pre-1.0 (`0.x`). Only the latest commit on the `main` branch
receives security fixes. There is no LTS branch yet.

| Version | Supported |
| ------- | --------- |
| `main`  | ✅        |
| Older   | ❌        |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Use one of the following private channels instead:

1. **Preferred:** open a private vulnerability report through GitHub Security
   Advisories — <https://github.com/ljbudgie/openhear/security/advisories/new>.
2. If you cannot use GitHub Security Advisories, contact the maintainer via
   their GitHub profile (<https://github.com/ljbudgie>) and request a private
   disclosure channel before sharing any details.

When reporting, please include:

- A clear description of the issue and its impact (software vulnerability,
  hearing-safety issue, data-handling issue, supply-chain issue, etc.).
- Steps to reproduce, including OS, Python version, hardware (hearing aid
  model, fitting interface, wristband prototype, etc.) where relevant.
- The commit SHA the report applies to.
- Any proposed mitigation, if you have one.

## What to expect

- We aim to acknowledge new reports within **5 working days**.
- We aim to provide a remediation plan or assessment within **30 days**.
- Coordinated disclosure is preferred. We will agree a disclosure date with
  the reporter and credit reporters who wish to be named.

## Scope

In scope:

- All code in this repository (`dsp/`, `core/`, `stream/`, `voice/`,
  `audiogram/`, `wristband/`, `hardware/`, `learn/`, `examples/`, top-level
  scripts, CI workflows).
- Build and packaging configuration (`pyproject.toml`, `requirements.txt`,
  GitHub Actions workflows).
- Documentation that, if followed, would create a security or hearing-safety
  risk (e.g. unsafe MPO recommendations, insecure fitting steps).

Out of scope:

- Vulnerabilities in third-party hearing aids, fitting software, or
  proprietary firmware. Please report those to the manufacturer.
- Theoretical issues without a credible attack path.

## Hearing-safety reports

OpenHear is **not** a medical device. If you believe a configuration, default,
or code path in this repository can produce sound pressure levels that risk
hearing damage, please report it through the same private channel above and
flag it as a **safety** issue. We treat hearing-safety bugs with the same
priority as security vulnerabilities.
