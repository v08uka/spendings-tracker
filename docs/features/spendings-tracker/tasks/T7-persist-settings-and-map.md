---
id: T7
title: "Persist settings, categories, and shop mappings"
layer: "infra"
deps: ["T1", "T5"]
acs: ["AC-01", "AC-11", "AC-12"]
files_hint: ["src/spendings_tracker/ports/persistence.py", "src/spendings_tracker/infra/sqlite.py", "src/spendings_tracker/infra/ulid.py", "tests/infra/test_sqlite_settings.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T7 — Persist settings, categories, and shop mappings

## Why

First-run and resume need a singleton settings row, frozen categories, and shop-key lookup. [data-model.md](../data-model.md); [spec §AC-01](../spec.md); [spec §AC-11](../spec.md); [spec §AC-12](../spec.md); [ADR-0006](../adr/0006-split-closer-ui-and-harvest-ports.md) (`PersistencePort`).

## What

Introduce `PersistencePort` here (first implementer — not a standalone contract task) with settings / categories / shop-mapping methods. Implement `infra/sqlite.py` and a ULID helper. Vendor failures become `AppError`. Domain and app do not import this package.

## Definition of Done

- [x] Tests against a temp SQLite file insert settings + categories once and refuse a second settings row
- [x] Shop mapping upserts by `shop_key` and loads by trim + case
- [x] Persisted ids are time-sortable ULIDs
- [x] lint + vet clean

## Notes

Compile-coupled with T8 — both list `ports/persistence.py` and `infra/sqlite.py`. Implement serializes the pair. One writer.
