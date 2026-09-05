---
id: T10
title: "Add ModelPort that accepts only spend-looking lines"
layer: "infra"
deps: ["T4"]
acs: ["AC-07"]
files_hint: ["src/spendings_tracker/ports/model.py", "src/spendings_tracker/infra/language_model.py", "tests/infra/test_language_model.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T10 — Add ModelPort that accepts only spend-looking lines

## Why

Unmapped spend-looking lines may be filed by a language-model service; other talk must never leave. [spec §AC-07](../spec.md); [sad.md](../sad.md) QG-1; [ADR-0002](../adr/0002-persist-every-egress-line-for-closer-review.md); [ADR-0006](../adr/0006-split-closer-ui-and-harvest-ports.md).

## What

Fold `ModelPort` into this task. Adapter re-checks T4’s spend-looking rule before any send and translates vendor failure to `AppError`. First vendor may stay unnamed; the port is the lock. It files into the frozen list or Uncategorized — it does not invent names ([ADR-0001](../adr/0001-freeze-the-category-list-after-first-run.md)).

## Definition of Done

- [x] Tests refuse non-spend-looking text before any send (`harvest.egress_blocked` / named invariant)
- [x] Tests pass only spend-looking lines to the fake/vendor client
- [x] lint + vet clean

## Notes

Mapped shops never reach this port ([ADR-0005](../adr/0005-apply-the-shop-map-before-the-model.md)) — that skip lives in T12, not here.
