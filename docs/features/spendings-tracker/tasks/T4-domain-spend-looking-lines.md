---
id: T4
title: "Encode spend-looking detection and pair splitting"
layer: "domain"
deps: []
acs: ["AC-07", "AC-05", "AC-10"]
files_hint: ["src/spendings_tracker/domain/spend_looking.py", "tests/domain/test_spend_looking.py"]
owner: "Dell"
estimate: "M"
status: "todo"
---

# T4 — Encode spend-looking detection and pair splitting

## Why

The on-machine gate decides what may leave, and one family-group message may hold several shop-and-amount pairs. [spec §AC-07](../spec.md); [spec §AC-05](../spec.md); [spec §AC-10](../spec.md); [sad.md](../sad.md) §6 Critical flow 1 and Receive a private draft.

## What

Add `src/spendings_tracker/domain/spend_looking.py`: a line is spend-looking when it contains an amount-like number plus other non-numeric text; split one message into several lines. No Telegram, no model vendor, no DB driver.

## Definition of Done

- [x] Unit tests accept spend-looking lines and reject other talk
- [x] Unit tests split one message with several shop-and-amount pairs into several lines
- [x] Ordinary shop-and-amount wording (family-poster habit) is accepted without a special syntax
- [x] lint + vet clean

## Notes

The language-model service must not decide what may leave. T10 and T12 call this rule; they do not re-implement it.
