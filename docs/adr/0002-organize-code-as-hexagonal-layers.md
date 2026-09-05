---
status: Accepted
owner: Dell
reviewers: []
updated_at: 2026-09-05
feature_size: ""
ticket: ""
---

# 0002 — Organize code as hexagonal layers

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (foundation session, guided-default)

## Context

The first product has three edges that must not leak into domain rules: Telegram, language-model vendors, and the on-disk store. The brief forbids locking a vendor and forbids sending the whole chat off-machine. No design document exists yet — this ADR locks how folders and dependencies run so every later feature lands in the same shape.

## Decision drivers

- Vendor-not-locked is a product rule (idea brief §1 / §7), not an implementation detail.
- Only spend-looking lines may leave the machine (idea brief §5) — that filter is a domain/app rule, not a Telegram helper.
- One deployable (ADR-0001): a second process or a “scripts vs bot” split would fight start/stop.

## Considered options

1. **Hexagonal layers in one package** — `domain` → `app` → `ports` → `infra` under `src/spendings_tracker`. Domain does not import Telegram or a vendor SDK.
2. **Flat package** — a few modules next to the entry point, no port boundary. Faster to start; vendor lock sneaks in on day one.
3. **Multiple services** — bot, worker, store as separate processes. Rejected: the closer runs one box, once a month.

## Decision outcome

**Chosen:** Option 1. One Python package with hexagonal layers. New model vendors and a new chat adapter appear only under `infra` and `ports`. Option 2 was the implicit alternative in the bundle; option 3 contradicts ADR-0001.

## Consequences

**Positive**
- A second language-model vendor is an adapter, not a rewrite of the close-a-month use case.
- Tests can fake Telegram and the model at the ports.

**Negative**
- More folders than a two-file bot; overkill if the project never grows a second vendor.
- New contributors must learn “domain does not import infra.”

**Neutral**
- Layer names are the convention; hexagons are not a religion — skip extra packages until a second bounded context appears.
- Exact port interfaces wait for `design` / `specify` of the first feature.

## Links

- Idea brief: [docs/idea-brief.md](../idea-brief.md) §5 / §7
- Architecture map: [docs/architecture-map.md](../architecture-map.md)
- Related ADR: [0001 — Use Python 3.12, a Telegram bot process, and Compose](0001-use-python-telegram-bot-and-compose.md)
- Related ADR: [0003 — Persist state in a SQLite file](0003-persist-state-in-a-sqlite-file.md)
