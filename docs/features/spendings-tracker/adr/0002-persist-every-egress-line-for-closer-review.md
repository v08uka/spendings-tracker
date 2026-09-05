---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0002 — Persist every egress line for closer review

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §1)

## Context

Spec §6 requires that 100% of text sent off the machine for classification is spend-looking lines, measured by the closer reviewing what left for that close. Spec §8 asked whether that review is every line or a count plus a sample. The privacy quality goal is the first of the SAD top-3; the review shape decides what we persist on each harvest.

## Decision drivers

- Spec §6 NFR: Spend-looking-only egress = 100% of text sent off the machine for classification is spend-looking lines; measurement is closer review of what left for that close.
- Spec §6.1 abuse case: non-spend talk leaving the machine must be blockable and nameable.
- Spec §8 default: every line that left.
- A sample cannot prove a specific family-group aside did not leave.

## Considered options

1. **Persist and show every spend-looking line that left** — the closer can scroll the full egress list for that close.
2. **Show a count plus a sample** — shorter review; the closer cannot check an arbitrary line.
3. **Show only a count** — cheapest; does not meet the spec’s “review what left” measurement.

## Decision outcome

**Chosen:** Option 1. For each close, persist every spend-looking line that was sent to a language-model service and show that full list to the closer. Option 2 can be a later presentation filter over the same store. Option 3 fails the NFR measurement.

## Consequences

**Positive**
- The closer can check any line that left for that close.
- A later “sample” view can hide rows without losing them.

**Negative**
- Egress text is stored locally (household-confidential) in addition to the draft lines.
- Large months add storage and a longer review list.

**Neutral**
- Non-spend talk must never be in this list (the on-machine gate stays upstream).
- Switching to a sample-only *store* later would drop history we then no longer have — do not do that without a new decision.

## Links

- Spec: [[../spec.md]] US-08, AC-07, §6, §6.1, §8
- SAD: [[../sad.md]] §1
- Related ADR: [[0001-freeze-the-category-list-after-first-run]]
