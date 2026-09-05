---
id: T8
title: "Persist drafts, monthly closes, and egress lines"
layer: "infra"
deps: ["T2", "T3", "T6", "T7"]
acs: ["AC-05", "AC-08", "AC-11", "AC-19"]
files_hint: ["src/spendings_tracker/ports/persistence.py", "src/spendings_tracker/infra/sqlite.py", "tests/infra/test_sqlite_draft.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T8 — Persist drafts, monthly closes, and egress lines

## Why

Harvest persist, handle, save, and resume all go through the same store. [data-model.md](../data-model.md); [spec §AC-05](../spec.md); [spec §AC-08](../spec.md); [spec §AC-11](../spec.md); [spec §AC-19](../spec.md); [ADR-0002](../adr/0002-persist-every-egress-line-for-closer-review.md).

## What

Extend `PersistencePort` + `infra/sqlite.py` with draft, draft-line, monthly-close, and egress methods. One draft row max. Save copies egress onto the close then deletes the draft (and its egress). Replace by `utc_month`.

## Definition of Done

- [x] Tests persist a draft with several lines from one source message and load it after a new connection (stop/start)
- [x] Tests replace a monthly close for the same `utc_month` and copy egress rows onto the saved close
- [x] A second `drafts` insert is refused
- [x] lint + vet clean

## Notes

Compile-coupled with T7 (shared port + sqlite adapter). App invariant: exactly one of `egress_lines.draft_id` / `monthly_close_id`.
