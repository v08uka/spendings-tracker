---
status: Accepted
owner: "Dell"
reviewers: ["Tech Lead"]
updated_at: "2026-09-05"
feature_size: L
ticket: ""
---

# 0001 — Freeze the category list after first-run

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Dell (design walk, §1)

## Context

On first-run the closer confirms a short category list. Later monthly closes must file spend-looking lines into that list or Uncategorized. Spec §8 asked whether the closer may later replace or extend the list. Saved monthly closes will accumulate against the names that existed at save time, so the rule must be locked before schema and filing use cases are designed.

## Decision drivers

- Spec §3 non-goal: classification must not invent new category names on later monthly closes.
- Spec §8 default: the list stays frozen; Uncategorized absorbs new kinds of spend.
- Recoverability quality goal: settings that survive a stop must have a stable meaning.
- Changing a list after saved closes exist would need a versioned list and a rule for historical months.

## Considered options

1. **Freeze the list after first-run confirm** — later closes file only into confirmed names or Uncategorized.
2. **Allow the closer to extend the list later** — new names appear on later drafts; already-saved closes keep their old names.
3. **Allow full replace or edit of the list after first-run** — names can be renamed or removed; historical closes need a mapping.

## Decision outcome

**Chosen:** Option 1. The list the closer confirms on first-run is frozen. Uncategorized remains the always-available bucket and does not count as a confirmed category. Options 2 and 3 defer product change until a later feature; they would force versioned categories in v1.

## Consequences

**Positive**
- Filing rules stay one list for every later monthly close.
- Schema and first-run use case do not need category versioning in v1.

**Negative**
- New kinds of spend land in Uncategorized (always a suspect line) until a later product decision reopens the list.

**Neutral**
- Uncategorized is not a member of the confirmed list (spec AC-14).
- Reopening the list later is a new feature with a migration, not a settings tweak.

## Links

- Spec: [[../spec.md]] US-01, AC-01, AC-14, §3, §8
- SAD: [[../sad.md]] §1
- Related ADR: [[0002-persist-every-egress-line-for-closer-review]]
