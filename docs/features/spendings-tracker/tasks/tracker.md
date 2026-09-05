# Tracker — spendings-tracker

> Status of every task in the epic. `implement` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| T1 | Promote settings, categories, and shop-mapping migrations | migration | Dell | S | — | done |
| T2 | Promote drafts and draft-lines migration | migration | Dell | S | T1 | done |
| T3 | Promote monthly-close and egress-line migrations | migration | Dell | S | T2 | todo |
| T4 | Encode spend-looking detection and pair splitting | domain | Dell | M | — | done |
| T5 | Encode completed-month, shop-key, and frozen-category rules | domain | Dell | M | — | done |
| T6 | Encode draft, suspect, handle, and total rules | domain | Dell | M | — | done |
| T7 | Persist settings, categories, and shop mappings | infra | Dell | M | T1, T5 | done |
| T8 | Persist drafts, monthly closes, and egress lines | infra | Dell | M | T2, T3, T6, T7 | todo |
| T9 | Add HarvestPort and the user-session harvest adapter | infra | Dell | L | — | done |
| T10 | Add ModelPort that accepts only spend-looking lines | infra | Dell | M | T4 | todo |
| T11 | Implement complete-first-run use case | app | Dell | M | T7, T5 | todo |
| T12 | Implement harvest-month and private-draft pipeline | app | Dell | L | T8, T9, T10, T4, T11 | todo |
| T13 | Implement handle-suspect and shop-map growth | app | Dell | M | T8, T6 | todo |
| T14 | Implement save-monthly-close | app | Dell | M | T8, T6 | todo |
| T15 | Implement resume-on-start | app | Dell | M | T8, T11 | todo |
| T16 | Map first-run and AuthZ onto the closer bot | ports | Dell | M | T11 | todo |
| T17 | Map harvest, draft, handle, and save onto the closer bot | ports | Dell | L | T12, T13, T14, T16 | todo |
| T18 | Wire the process and prove the quality goals | wiring | Dell | M | T15, T17, T9, T10 | todo |

**Total:** 18 tasks, ~16 person-days.
