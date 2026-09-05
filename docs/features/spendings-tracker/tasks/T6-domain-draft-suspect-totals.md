---
id: T6
title: "Encode draft, suspect, handle, and total rules"
layer: "domain"
deps: []
acs: ["AC-08", "AC-09"]
files_hint: ["src/spendings_tracker/domain/draft.py", "tests/domain/test_draft.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T6 — Encode draft, suspect, handle, and total rules

## Why

Save is blocked while a suspect is unhandled; save accepts default-currency totals only. [spec §AC-08](../spec.md); [spec §AC-09](../spec.md); [sad.md](../sad.md) §6 Critical flow 2; handle set in [bot-commands.md](../contracts/bot-commands.md) `HandleChoice`.

## What

Add `src/spendings_tracker/domain/draft.py`: suspect = missing amount, other currency, or Uncategorized; handle choices (`enter_amount`, `assign_category`, `confirm_uncategorized`, `leave_other_currency`, `exclude`); default-currency totals omit excluded and other-currency lines.

## Definition of Done

- [x] Unit tests classify suspect versus clean
- [x] Unit tests accept each handle choice and require every remaining suspect handled before save is allowed
- [x] Unit tests keep other-currency lines listed separately and omit excluded lines from totals
- [x] lint + vet clean

## Notes

A clean line is not a promise the line is factually correct ([CONTEXT.md](../CONTEXT.md)). No separate accept step before save.
