---
id: T3
title: "Promote monthly-close and egress-line migrations"
layer: "migration"
deps: ["T2"]
acs: ["AC-07", "AC-08", "AC-19"]
files_hint: ["docs/features/spendings-tracker/migrations/04_create_monthly_closes.up.sql", "docs/features/spendings-tracker/migrations/04_create_monthly_closes.down.sql", "docs/features/spendings-tracker/migrations/05_create_egress_lines.up.sql", "docs/features/spendings-tracker/migrations/05_create_egress_lines.down.sql"]
owner: "Dell"
estimate: "S"
status: "todo"
---

# T3 — Promote monthly-close and egress-line migrations

## Why

Save and closer egress review need `monthly_closes`, `monthly_close_lines`, and `egress_lines`. [data-model.md](../data-model.md); [spec §AC-08](../spec.md); [spec §AC-19](../spec.md); [ADR-0002](../adr/0002-persist-every-egress-line-for-closer-review.md).

## What

Promote `docs/features/spendings-tracker/migrations/04_create_monthly_closes.*` and `05_create_egress_lines.*`. Unique `utc_month` on `monthly_closes` is the replace key. Exactly one of `egress_lines.draft_id` / `monthly_close_id` is an app invariant.

## Definition of Done

- [x] Staged 04 and 05 are live Alembic revisions
- [x] `alembic upgrade head` / `alembic downgrade` through these revisions apply and revert cleanly
- [x] lint + vet clean

## Notes

Last migration in the ordered sequence. Mapped shops are not sent and do not get an egress row ([ADR-0005](../adr/0005-apply-the-shop-map-before-the-model.md)).
