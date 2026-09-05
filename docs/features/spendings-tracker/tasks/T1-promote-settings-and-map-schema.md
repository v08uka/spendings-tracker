---
id: T1
title: "Promote settings, categories, and shop-mapping migrations"
layer: "migration"
deps: []
acs: ["AC-01", "AC-12"]
files_hint: ["docs/features/spendings-tracker/migrations/01_create_settings.up.sql", "docs/features/spendings-tracker/migrations/01_create_settings.down.sql", "docs/features/spendings-tracker/migrations/02_create_shop_mappings.up.sql", "docs/features/spendings-tracker/migrations/02_create_shop_mappings.down.sql"]
owner: "Dell"
estimate: "S"
status: "todo"
---

# T1 — Promote settings, categories, and shop-mapping migrations

## Why

First-run and the shop map need tables before any persist adapter can run. Schema is already staged — [data-model.md](../data-model.md) entities `settings`, `categories`, `shop_mappings`; [spec §AC-01](../spec.md); [spec §AC-12](../spec.md); [ADR-0001](../adr/0001-freeze-the-category-list-after-first-run.md).

## What

Promote the staged pairs `docs/features/spendings-tracker/migrations/01_create_settings.*` and `02_create_shop_mappings.*` into live Alembic revisions after the empty `0001`. Do not edit the staged SQL unless a promotion tool requires a wrapper. Uncategorized is not a `categories` row.

## Definition of Done

- [x] Staged 01 and 02 are live Alembic revisions
- [x] `alembic upgrade head` and `alembic downgrade` through these revisions apply and revert cleanly
- [x] lint + vet clean

## Notes

Migration lane — serialized with T2 and T3. One writer on the SQLite file ([docs/adr/0003-persist-state-in-a-sqlite-file.md](../../../adr/0003-persist-state-in-a-sqlite-file.md)).
