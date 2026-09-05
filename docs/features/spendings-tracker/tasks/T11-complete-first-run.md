---
id: T11
title: "Implement complete-first-run use case"
layer: "app"
deps: ["T7", "T5"]
acs: ["AC-01", "AC-02", "AC-14"]
files_hint: ["src/spendings_tracker/app/complete_first_run.py", "src/spendings_tracker/app/errors.py", "tests/app/test_complete_first_run.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T11 — Implement complete-first-run use case

## Why

Until first-run finishes, no monthly close may start; the account that confirms is the only closer. [spec §AC-01](../spec.md); [spec §AC-02](../spec.md); [spec §AC-14](../spec.md); [sad.md](../sad.md) §6 Complete first-run setup; [bot-commands.md](../contracts/bot-commands.md) `completeFirstRun`.

## What

Add `complete_first_run.py`. Extend `AppError` here with `code` / `message` / `details` so later use cases raise contract codes without editing this file. Preset default currency `EUR`. Proposed list is ephemeral; only the confirmed list is persisted. Pin `closer_identity`.

## Definition of Done

- [x] Unit tests with a fake `PersistencePort` write settings + frozen categories and report that monthly closes can start
- [x] Confirm with no categories returns `first_run.empty_category_list` (Uncategorized does not count)
- [x] Asking to start a close before confirm returns `first_run.still_required` and does not start a draft
- [x] lint + vet clean

## Notes

Later app tasks raise `AppError` with new codes; do not add `errors.py` to their `files_hint` (avoids serializing the whole app lane).
