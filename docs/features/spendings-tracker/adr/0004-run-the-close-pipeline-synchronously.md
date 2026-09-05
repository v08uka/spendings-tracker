---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0004 — Run the close pipeline synchronously

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §4)

## Context

After the closer asks for a completed UTC month, the system must harvest, keep only spend-looking lines on the machine, apply the shop-to-category map, call the language-model port for unmapped lines, persist the draft and the egress list, and show the private draft. Spec §6 budgets ≤ 180 seconds for a month with at most 500 family-group messages. A second process is forbidden (repo ADR-0001).

## Decision drivers

- Spec §6 time-to-draft: ≤ 180 seconds for ≤500 messages, closer wall-clock from ask until the draft is visible.
- One process, in-process calls only (repo ADR-0001 / ADR-0002).
- Simplicity for an on-demand tool the closer starts and stops.

## Considered options

1. **Synchronous in-process pipeline** — the ask-for-month use case runs harvest through persist and then shows the draft.
2. **In-process background build** — the ask returns “building”; a same-process job later opens the draft. Still one process.

A second worker service was not considered: it is excluded by the one-process constraint.

## Decision outcome

**Chosen:** Option 1. The closer waits, then sees the draft. Option 2 would add a “building” state to survive a stop mid-harvest; that is extra machinery for a monthly tool with a 180-second budget.

## Consequences

**Positive**
- One use case, one success path, easy to test against the 180-second budget.
- No job table or “building” conversation state.

**Negative**
- A stop during the wait loses an unfinished harvest (the in-progress draft does not exist until persist). The closer asks again.
- A month with more than 500 messages has no 180-second promise and may block the process for a long time (AC-17 still requires a full harvest).

**Neutral**
- Unplanned-stop NFR (< 1 in 10 starts) is about the process dying, not about cancelling a mid-harvest wait.
- `sequences` will draw this as one flow with harvest-failed and egress-block branches.

## Links

- Spec: [[../spec.md]] US-02, US-03, AC-03, AC-17, §6
- SAD: [[../sad.md]] §4
- Related ADR: [[0003-use-bot-ui-and-user-session-harvest]]
- Related ADR: [[0005-apply-the-shop-map-before-the-model]]
