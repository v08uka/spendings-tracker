---
id: T12
title: "Implement harvest-month and private-draft pipeline"
layer: "app"
deps: ["T8", "T9", "T10", "T4", "T11"]
acs: ["AC-03", "AC-04", "AC-05", "AC-07", "AC-10", "AC-15", "AC-16", "AC-17", "AC-18"]
files_hint: ["src/spendings_tracker/app/harvest_month.py", "tests/app/test_harvest_month.py"]
owner: "Dell"
estimate: "L"
status: "todo"
---

# T12 — Implement harvest-month and private-draft pipeline

## Why

Ask for a month is one synchronous pipeline: guards, harvest, on-machine gate, shop map, model, persist draft + egress, return the private draft. [spec §AC-03](../spec.md)–[AC-05](../spec.md), [AC-07](../spec.md), [AC-10](../spec.md), [AC-15](../spec.md)–[AC-18](../spec.md); [sad.md](../sad.md) §6 Critical flow 1 and Harvest empty or large month; [ADR-0004](../adr/0004-run-the-close-pipeline-synchronously.md); [ADR-0005](../adr/0005-apply-the-shop-map-before-the-model.md); [bot-commands.md](../contracts/bot-commands.md) `harvestMonth`.

## What

Add `harvest_month.py` only. Guards: first-run required, incomplete month, draft already in progress, month not obtained. Then split lines (T4), apply map and skip send on a hit, send unmapped spend-looking lines only, persist draft + egress. Empty obtainable month is a successful empty draft. Family-poster wording is accepted as-is. Do not add a background job.

## Definition of Done

- [x] Unit tests with fake `HarvestPort` / `ModelPort` / `PersistencePort` cover `harvest.incomplete_month`, `harvest.draft_in_progress`, `harvest.month_not_obtained`, `harvest.egress_blocked`
- [x] Happy path: several lines from one message, map skip has no egress row, unmapped line is sent and persisted on the egress list
- [x] Empty month: `is_empty` draft, empty default-currency totals, no suspects
- [x] >500 messages: whole month, no silent drop (no 180-second assertion here — that is T18 QG-2)
- [x] lint + vet clean

## Notes

Largest app task — keep it one use case, one PR. Time-to-draft ≤180s for ≤500 messages is T18 QG-2. Draft is never a group reply (T16/T17 enforce transport silence).
