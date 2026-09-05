---
id: T5
title: "Encode completed-month, shop-key, and frozen-category rules"
layer: "domain"
deps: []
acs: ["AC-15", "AC-12", "AC-14"]
files_hint: ["src/spendings_tracker/domain/month.py", "src/spendings_tracker/domain/shop.py", "src/spendings_tracker/domain/categories.py", "tests/domain/test_month.py", "tests/domain/test_shop.py", "tests/domain/test_categories.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T5 — Encode completed-month, shop-key, and frozen-category rules

## Why

Harvest may only request a completed UTC month; shop match is trim + case then exact remaining spelling; the confirmed list cannot be empty and Uncategorized is not a member. [spec §AC-15](../spec.md); [spec §AC-12](../spec.md); [spec §AC-14](../spec.md); [ADR-0001](../adr/0001-freeze-the-category-list-after-first-run.md).

## What

Add `month.py` (`YYYY-MM`, refuse current incomplete UTC month), `shop.py` (`shop_key` = trim + lowercase), `categories.py` (confirm at least one name; Uncategorized is not a row). Domain only.

## Definition of Done

- [x] Unit tests refuse the current incomplete UTC month and accept a completed one
- [x] Unit tests match `Lidl` / ` lidl ` and treat `Lidl Express` as a different shop
- [x] Unit tests refuse an empty confirmed list; Uncategorized does not count
- [x] lint + vet clean

## Notes

List stays frozen after confirm — no later extend/replace in these types ([ADR-0001](../adr/0001-freeze-the-category-list-after-first-run.md)).
