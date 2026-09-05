---
id: T14
title: "Implement save-monthly-close"
layer: "app"
deps: ["T8", "T6"]
acs: ["AC-08", "AC-09", "AC-13", "AC-19"]
files_hint: ["src/spendings_tracker/app/save_monthly_close.py", "tests/app/test_save_monthly_close.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T14 — Implement save-monthly-close

## Why

Save is how the closer accepts default-currency totals. [spec §AC-08](../spec.md); [spec §AC-09](../spec.md); [spec §AC-13](../spec.md); [spec §AC-19](../spec.md); [sad.md](../sad.md) §6 Critical flow 2; [bot-commands.md](../contracts/bot-commands.md) `saveMonthlyClose`.

## What

Add `save_monthly_close.py`. No separate accept step. Copy non-excluded lines and egress onto the monthly close, delete the draft, replace by `utc_month` when a close already exists. Other-currency lines stay listed, not converted.

## Definition of Done

- [x] Unit tests save when every suspect is handled and confirm default-currency totals (excluded omitted)
- [x] `save.no_draft` and `save.unhandled_suspect` refuse the write
- [x] A second save for the same month sets `replaced` and leaves one close row
- [x] lint + vet clean

## Notes

Parallel with T13 after T8. Empty draft (AC-16) is a valid save — covered when T12’s empty draft is passed in.
