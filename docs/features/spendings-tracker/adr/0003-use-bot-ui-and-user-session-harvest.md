---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0003 — Use Bot UI and user-session harvest

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §4)

## Context

The closer needs a private command conversation and, separately, a harvest of a completed UTC month’s already-existing family-group history after the tool was off, using the closer’s access and no export file. Official Bot API cannot read a month of group history it did not store while running. Always-on storage of every group message contradicts the on-demand shape and “while the tool is off, nothing is written locally.”

## Decision drivers

- Spec AC-03 / harvest definition: read already-existing history on demand, no export file.
- Spec non-goal: not an always-on collector.
- Quality goal: recoverability after an on-demand stop — history must be readable on a cold start.
- Spec AC-06: never post draft or close detail to the family group.
- Repo ADR-0001: one Telegram-facing process; library choice was left to this feature.

## Considered options

1. **Bot API for closer UI + user-session (MTProto) for harvest** — two adapters in one process.
2. **One user-session adapter for both harvest and the closer conversation** — one Telegram integration; closer UI is not a bot chat.

Bot-only harvest was not considered: it is excluded by AC-03 plus the on-demand constraint.

## Decision outcome

**Chosen:** Option 1. The closer talks to a bot in a private chat. Harvest uses a user session that can read the family group with the closer’s access. Option 2 is simpler operationally but loses bot-command UX and mixes the closer’s personal session with operator UI.

## Consequences

**Positive**
- Cold-start harvest of a completed month is possible.
- Closer UI stays a normal bot conversation (`ux-flows.md` SCR-01–07).
- The family group can stay unanswered.

**Negative**
- Two Telegram adapters and two kinds of secrets (bot token + user session).
- The user session on disk is household-sensitive; §8 must treat it as a secret.

**Neutral**
- Concrete libraries (for example python-telegram-bot vs Telethon) stay an implementation choice inside the adapters.
- Telegram terms for user-session clients are a §11 risk, not a product veto here.

## Links

- Spec: [[../spec.md]] US-02, US-03, AC-03, AC-06
- SAD: [[../sad.md]] §4
- Related ADR: [[0004-run-the-close-pipeline-synchronously]]
