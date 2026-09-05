---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0006 — Split closer-UI and harvest ports

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §5)

## Context

§4 chose two Telegram adapters in one process: Bot API for the closer’s private conversation and a user session for harvest. The app layer talks to the outside world only through ports. Tests fake those ports. A single Telegram port would force every test to stub both jobs even when only one is under test.

## Decision drivers

- Repo ADR-0002: new chat or model vendor is a port + infra adapter; domain and app do not import infra.
- Feature ADR-0003: two adapters, two secrets (bot token vs user session).
- Tests: unit tests at app with fakes at ports.

## Considered options

1. **Four ports** — `CloserUiPort`, `HarvestPort`, `ModelPort`, `PersistencePort`.
2. **Three ports** — one `TelegramPort` plus `ModelPort` and `PersistencePort`.

## Decision outcome

**Chosen:** Option 1. Harvest and closer UI are separate ports so each adapter and each secret can be faked or replaced on its own. Option 2 is fewer files and couples the two Telegram jobs in every test and every future vendor swap.

## Consequences

**Positive**
- Harvest can be faked while testing first-run or save.
- A second harvest source (if a later feature ever needed one) does not rewrite closer UI.

**Negative**
- Four interfaces instead of three; `__main__.py` wires more objects.

**Neutral**
- Method shapes wait for `api` / implement. This ADR locks the split, not the signatures.

## Links

- Spec: [[../spec.md]] US-02, US-03
- SAD: [[../sad.md]] §5
- Related ADR: [[0003-use-bot-ui-and-user-session-harvest]]
