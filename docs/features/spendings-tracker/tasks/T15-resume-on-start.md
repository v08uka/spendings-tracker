---
id: T15
title: "Implement resume-on-start"
layer: "app"
deps: ["T8", "T11"]
acs: ["AC-11"]
files_hint: ["src/spendings_tracker/app/resume.py", "tests/app/test_resume.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T15 — Implement resume-on-start

## Why

An on-demand stop must not wipe settings, the map, saved closes, or an in-progress draft. [spec §AC-11](../spec.md); [sad.md](../sad.md) §6 Stop and resume with state; [bot-commands.md](../contracts/bot-commands.md) `resumeOnStart`; [sad.md](../sad.md) QG-3 (app-level here; process-level in T18).

## What

Add `resume.py`: load the SQLite file; if a `drafts` row exists return `PrivateDraftView` including handles; else `ReadyView`. Missing settings is first-run, not a resume error.

## Definition of Done

- [x] Unit tests with a real or fake store return the same settings, frozen list, shop map, and saved close after a new load
- [x] In-progress draft including handles already made is returned without first-run re-entry
- [x] lint + vet clean

## Notes

Telegram session restore is T9 / T18 (volume file), not this use case.
