---
id: T9
title: "Add HarvestPort and the user-session harvest adapter"
layer: "infra"
deps: []
acs: ["AC-03", "AC-04", "AC-17"]
files_hint: ["src/spendings_tracker/ports/harvest.py", "src/spendings_tracker/infra/telegram_harvest.py", "tests/infra/test_telegram_harvest.py"]
owner: "Dell"
estimate: "L"
status: "todo"
---

# T9 — Add HarvestPort and the user-session harvest adapter

## Why

A completed UTC month must be read from already-existing family-group history with the closer’s access and no export file. [spec §AC-03](../spec.md); [spec §AC-04](../spec.md); [spec §AC-17](../spec.md); [ADR-0003](../adr/0003-use-bot-ui-and-user-session-harvest.md); [ADR-0006](../adr/0006-split-closer-ui-and-harvest-ports.md); [ADR-0007](../adr/0007-store-the-user-session-on-the-data-volume.md).

## What

Fold `HarvestPort` into this task. Implement the user-session (MTProto) adapter. Session file lives on the `spendings-state` volume next to the SQLite file, not in a table. Translate unreadable / empty-of-messages months to `AppError` `harvest.month_not_obtained`. Do not post anything to the family group.

## Definition of Done

- [x] Adapter returns the whole month’s family-group messages (including >500) with no silent drop
- [x] Unreadable month or a month with no family-group messages becomes `harvest.month_not_obtained`
- [x] No export-file parameter exists on the port
- [x] lint + vet clean

## Notes

Starts with no deps — [sad.md](../sad.md) §11 High risk: prove harvest on a real completed month before other use cases rely on it. Bot token stays in the environment; session is a different secret.
