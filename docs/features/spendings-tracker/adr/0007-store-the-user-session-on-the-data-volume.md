---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0007 — Store the user session on the data volume

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §8)

## Context

Harvest uses a Telegram user session (ADR-0003). That session is a login for the closer’s account and can read the family group. It must survive a stop (same as settings and saved closes) and must not leak into the family group or off the machine.

## Decision drivers

- Recoverability quality goal: settings survive a stop.
- Spec §6.1: household-confidential data; local-only, no hosting on someone else’s computers.
- One Compose volume already holds the SQLite file (repo ADR-0003).
- The bot token is a different secret and can live in the environment (`TELEGRAM_BOT_TOKEN` or equivalent).

## Considered options

1. **Store the user session on the data volume** next to the SQLite file — same backup story as state.
2. **OS keychain / secret store** — better isolation; another moving part on a once-a-month tool.
3. **Environment variable or env file only** — easy to leak in shell history; awkward for a multi-file session.

## Decision outcome

**Chosen:** Option 1. The user session lives on `spendings-state` beside the database. The bot token stays in the environment. Option 2 is safer on a shared laptop and can be a later hardening. Option 3 is a poor fit for a session blob.

## Consequences

**Positive**
- Stop/start restores harvest access without a new login every month (after first session create).
- Backup is “copy the volume.”

**Negative**
- Anyone who can read the volume can impersonate the closer on Telegram.
- Volume permissions and laptop disk encryption become part of the security story.

**Neutral**
- First-run must still create the session once (how the closer logs in is implement detail).
- Security review (spec §6.1) must look at this file.

## Links

- Spec: [[../spec.md]] US-06, §6.1
- SAD: [[../sad.md]] §8
- Related ADR: [[0003-use-bot-ui-and-user-session-harvest]]
