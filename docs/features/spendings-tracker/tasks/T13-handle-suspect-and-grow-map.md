---
id: T13
title: "Implement handle-suspect and shop-map growth"
layer: "app"
deps: ["T8", "T6"]
acs: ["AC-09", "AC-12"]
files_hint: ["src/spendings_tracker/app/handle_suspect.py", "tests/app/test_handle_suspect.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T13 — Implement handle-suspect and shop-map growth

## Why

The closer handles one suspect (or overrides a category) and the shop map grows from that correction. [spec §AC-09](../spec.md); [spec §AC-12](../spec.md); [sad.md](../sad.md) §6 Remember shop corrections; [ADR-0005](../adr/0005-apply-the-shop-map-before-the-model.md); [bot-commands.md](../contracts/bot-commands.md) `handleSuspect`.

## What

Add `handle_suspect.py`. Persist the `HandleChoice`. `assign_category` upserts `shop_mappings` by `shop_key`. Codes: `save.no_draft`, `draft.line_not_found`, `auth.not_closer` when identity does not match settings.

## Definition of Done

- [x] Unit tests persist each handle choice and return an updated draft view
- [x] `assign_category` upserts the shop map; a later different remaining spelling does not use that mapping
- [x] Missing draft or unknown line returns the contract codes
- [x] lint + vet clean

## Notes

Can start in parallel with T14 / T15 once T8 is done. Override of a clean/mapped line is the same write as `assign_category`.
