---
id: T2
title: "Promote drafts and draft-lines migration"
layer: "migration"
deps: ["T1"]
acs: ["AC-05", "AC-11", "AC-18"]
files_hint: ["docs/features/spendings-tracker/migrations/03_create_drafts.up.sql", "docs/features/spendings-tracker/migrations/03_create_drafts.down.sql"]
owner: "Dell"
estimate: "S"
status: "todo"
---

# T2 — Promote drafts and draft-lines migration

## Why

The private draft and its lines (including handles that must survive a stop) need tables. [data-model.md](../data-model.md) `drafts` / `draft_lines`; [spec §AC-05](../spec.md); [spec §AC-11](../spec.md); [spec §AC-18](../spec.md).

## What

Promote `docs/features/spendings-tracker/migrations/03_create_drafts.*`. App, not a CHECK, refuses a second `drafts` row (AC-18). No unique on `utc_month` — a saved close for the same month may already exist (AC-19).

## Definition of Done

- [x] Staged 03 is a live Alembic revision
- [x] `alembic upgrade head` / `alembic downgrade` through this revision apply and revert cleanly
- [x] lint + vet clean

## Notes

Serialized after T1. Empty month is a `drafts` row with zero lines ([data-model.md](../data-model.md) `draft_lines` note).
