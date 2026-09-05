---
status: Accepted
owner: Dell
reviewers: []
updated_at: 2026-09-05
feature_size: ""
ticket: ""
---

# 0001 — Use Python 3.12, a Telegram bot process, and Compose

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (foundation session, guided-default)

## Context

The repo is empty. The idea brief describes a local, on-demand Telegram monthly close: start the bot, harvest a family group, call a language-model service, audit a private draft, save state, stop. No design document exists yet — this ADR records the stack picked in `survey` so scaffold has a locked language and runtime. Changing language later is a rewrite.

## Decision drivers

- Telegram is both the archive and the closer’s UI (idea brief §7).
- Language-model vendor must stay swappable (idea brief §1 / §7).
- The closer starts and stops the process; state must survive (idea brief §5, “not always-on”).
- A personal monthly tool should use the ecosystem where Telegram and model clients are boring, not novel.

## Considered options

1. **Python 3.12 + one bot process + Compose + uv / pytest / ruff** — recommended bundle; Telegram and model clients are first-class; start/stop matches the brief.
2. **TypeScript / Node, same shape** — one language if the owner already lives there; weaker default for bots and model clients.
3. **Same Python shape, but a server database container** — rejected as a *stack* overlay; persistence is ADR-0003. Not chosen here.

## Decision outcome

**Chosen:** Option 1. Python 3.12 with a single bot process packaged in Compose, toolchain `uv` / `pytest` / `ruff`. Option 2 was declined in the confirm. Option 3 is a persistence choice, not a language choice.

## Consequences

**Positive**
- Scaffold can generate a conventional Python package and Compose file without a second language debate.
- Ports for Telegram and model vendors sit on libraries that already exist.

**Negative**
- Contributors who only write TypeScript pay a language tax.
- Compose is another moving part for a once-a-month close (still cheaper than inventing a second runtime).

**Neutral**
- Switching to TypeScript later is a rewrite, not a migration.
- Exact Telegram library (e.g. which client wrapper) is left to scaffold / the first feature — this ADR locks the language and process shape only.

## Links

- Idea brief: [docs/idea-brief.md](../idea-brief.md) §7
- Architecture map: [docs/architecture-map.md](../architecture-map.md)
- Related ADR: [0002 — Organize code as hexagonal layers](0002-organize-code-as-hexagonal-layers.md)
- Related ADR: [0003 — Persist state in a SQLite file](0003-persist-state-in-a-sqlite-file.md)
