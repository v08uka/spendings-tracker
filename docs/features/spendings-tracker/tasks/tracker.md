# Tracker — spendings-tracker

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Promote settings, categories, and shop-mapping migrations | migration | Dell | S | — | done |
| T2 | Promote drafts and draft-lines migration | migration | Dell | S | T1 | done |
| T3 | Promote monthly-close and egress-line migrations | migration | Dell | S | T2 | done |
| T4 | Encode spend-looking detection and pair splitting | domain | Dell | M | — | done |
| T5 | Encode completed-month, shop-key, and frozen-category rules | domain | Dell | M | — | done |
| T6 | Encode draft, suspect, handle, and total rules | domain | Dell | M | — | done |
| T7 | Persist settings, categories, and shop mappings | infra | Dell | M | T1, T5 | done |
| T8 | Persist drafts, monthly closes, and egress lines | infra | Dell | M | T2, T3, T6, T7 | done |
| T9 | Add HarvestPort and the user-session harvest adapter | infra | Dell | L | — | done |
| T10 | Add ModelPort that accepts only spend-looking lines | infra | Dell | M | T4 | done |
| T11 | Implement complete-first-run use case | app | Dell | M | T7, T5 | done |
| T12 | Implement harvest-month and private-draft pipeline | app | Dell | L | T8, T9, T10, T4, T11 | done |
| T13 | Implement handle-suspect and shop-map growth | app | Dell | M | T8, T6 | done |
| T14 | Implement save-monthly-close | app | Dell | M | T8, T6 | done |
| T15 | Implement resume-on-start | app | Dell | M | T8, T11 | done |
| T16 | Map first-run and AuthZ onto the closer bot | ports | Dell | M | T11 | done |
| T17 | Map harvest, draft, handle, and save onto the closer bot | ports | Dell | L | T12, T13, T14, T16 | done |
| T18 | Wire the process and prove the quality goals | wiring | Dell | M | T15, T17, T9, T10 | done |

**Total:** 18 tasks, ~16 person-days.

## Review follow-up — 2026-09-05

| # | Cluster | Status |
|---|---|---|
| R1 | Handle invariants, parse, contracts (S1-05, S1-08–S1-10, S2-01–S2-03) | done |
| R2 | Closer-visible bot UI (S1-02–S1-04, S1-06, S1-07) | done |
| R3 | Hygiene + tests (S2-04, S2-05) | done |
| R4 | Runnable process / long-poll (S1-01) | done |

## Review follow-up — 2026-09-05 re-review

| # | Cluster | Status |
|---|---|---|
| R5 | SCR-04 Handle picks (S1-01) | done |
| R6 | SCR-05 assign follow-up + AC-12 on the bot (S1-02) | done |

## Review follow-up — 2026-09-05 re-review 2

| # | Cluster | Status |
|---|---|---|
| R7 | SCR-05 enter_amount follow-up (S1-01) | done |

## Review follow-up — 2026-09-05 re-review 3

| # | Cluster | Status |
|---|---|---|
| R8 | Clear leftover amount-prompt state (S2-01) | done |
