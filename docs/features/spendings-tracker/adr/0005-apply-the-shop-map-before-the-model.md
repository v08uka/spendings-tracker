---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0005 — Apply the shop map before the model

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §4)

## Context

The shop-to-category map starts empty and grows from the closer’s corrections. AC-12 says a later spend-looking line that matches a shop (trim + case, exact remaining spelling) uses the mapped category unless the closer overrides it. The spec does not say whether that line still leaves the machine for the language-model service.

## Decision drivers

- Quality goal: spend-looking-only egress — send as little as possible, and never non-spend talk.
- Quality goal: time-to-draft ≤ 180 seconds for ≤500 messages.
- AC-12: mapped category wins on the draft unless the closer overrides.
- ADR-0002 (this feature): every line that *does* leave is persisted for closer review — skipping a send also skips an egress row.

## Considered options

1. **Apply the map first; skip the send on a hit** — mapped lines stay on the machine.
2. **Always send; treat the map as a hint** — more egress; the draft would still use the mapped category.
3. **Send first; apply the map only if the model returns Uncategorized** — more egress; map is a fallback.

## Decision outcome

**Chosen:** Option 1. A map hit files the line locally and does not call the language-model port. Options 2 and 3 send text we already know how to file.

## Consequences

**Positive**
- Less household text leaves the machine after the map has grown.
- Fewer model calls on later months, which helps the 180-second budget.

**Negative**
- A stale map keeps filing a shop into an old category until the closer overrides (then the map grows again).
- The model never sees mapped shops, so it cannot “correct” a map silently — only the closer can.

**Neutral**
- Unmapped spend-looking lines still go to the model (and into the egress list).
- “Lidl Express” vs “Lidl” remain different shops (spec non-goal).

## Links

- Spec: [[../spec.md]] US-07, AC-12, §6
- SAD: [[../sad.md]] §4
- Related ADR: [[0002-persist-every-egress-line-for-closer-review]]
- Related ADR: [[0004-run-the-close-pipeline-synchronously]]
