---
status: Accepted
owner: Dell
reviewers: []
updated_at: 2026-09-05
feature_size: ""
ticket: ""
---

# 0003 — Persist state in a SQLite file

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (foundation session, guided-default)

## Context

Settings, the optional shop→category map, and saved monthly reports must survive “kill the bot.” The brief wants local-only operation and no always-on process. No design document exists yet — this ADR locks where that state lives so Compose and migrations have one answer.

## Decision drivers

- State outlives the bot process (idea brief §1 / §5).
- One operator, one computer, for now — no second writer, no cloud host (idea brief §5).
- Fewer moving parts than a separate database box for a monthly close.

## Considered options

1. **SQLite file on a named Compose volume** — one file; kill the app container; the volume stays. Recommended and confirmed.
2. **Postgres in a second container** — easier later if two machines or a host appear; extra box to keep healthy for a once-a-month job.

## Decision outcome

**Chosen:** Option 1. SQLite as a file on a named volume; schema changes via Alembic. Option 2 was offered and declined.

## Consequences

**Positive**
- Compose can be “app + volume,” not “app + database + volume.”
- Backup is copy-the-file.

**Negative**
- Two bot copies writing the same file at once is unsafe — acceptable because the closer runs one instance.
- Moving to a server database later needs a dump/load, not a config flip.

**Neutral**
- IDs are time-sortable (ULID) as part of the same foundation bundle; table shapes wait for `data-model`.
- The file path and volume name are scaffold details.

## Links

- Idea brief: [docs/idea-brief.md](../idea-brief.md) §5
- Architecture map: [docs/architecture-map.md](../architecture-map.md)
- Related ADR: [0001 — Use Python 3.12, a Telegram bot process, and Compose](0001-use-python-telegram-bot-and-compose.md)
- Related ADR: [0002 — Organize code as hexagonal layers](0002-organize-code-as-hexagonal-layers.md)
