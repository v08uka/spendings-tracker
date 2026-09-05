---
id: T18
title: "Wire the process and prove the quality goals"
layer: "wiring"
deps: ["T15", "T17", "T9", "T10"]
acs: ["AC-07", "AC-11"]
files_hint: ["src/spendings_tracker/__main__.py", "compose.yaml", "tests/test_smoke.py", "tests/app/test_quality_goals.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T18 — Wire the process and prove the quality goals

## Why

The process must construct adapters, inject them at ports, and run until the closer stops. Quality goals in [sad.md](../sad.md) §10 must be testable: spend-looking-only egress, time-to-draft, recoverability. [spec §AC-07](../spec.md); [spec §AC-11](../spec.md); [spec.md](../spec.md) §6; [ADR-0007](../adr/0007-store-the-user-session-on-the-data-volume.md).

## What

Replace boot-and-exit in `__main__.py` with composition: SQLite, harvest, model, bot. Compose volume already mounts `/data`; add bot-token and session-path env as needed. Do not start a second service or a second writer.

## Definition of Done

- [x] Smoke test: process imports, constructs adapters, and is ready to accept closer commands (time-to-ready path)
- [x] QG-1: mixed-talk harvest fixture — persisted egress list equals lines passed to `ModelPort` and contains no other talk
- [x] QG-2: timed app-layer test with fake `HarvestPort` of 500 messages and fake `ModelPort` asserts ≤180s; a separate >500 case asserts completeness, not the bound
- [x] QG-3: stop/start against a real SQLite file restores settings, map, saved close, and in-progress draft
- [x] lint + vet clean

## Notes

Unplanned-stop rate (<1 in 10 starts) is the closer’s own count, not an automated flake quota ([sad.md](../sad.md) §10 QG-3). Security review of the session file remains a human gate (spec §6.1).
