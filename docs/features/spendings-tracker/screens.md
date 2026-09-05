---
status: draft
feature_size: "L"
tool: "code"
updated_at: "2026-09-05"
---

# Screens — spendings-tracker

> The canonical **screen manifest** — every screen in every state — produced by `screens` (between
> `api` and `tasks`) and read by `tasks` (each `ui` task cites SCR ids + states), `implement`
> (builds the screen to the declared states) and `review` (the built screen must match this).
> Downstream stages reference **only this manifest** — never a raw design file.

`sad.md` `target_surfaces: [backend-service]`. Telegram is the closer’s command-and-reply UI
(SAD §4 seed 1, ADR-0003; `ux-flows.md` SCR-01–07). This stage was invoked directly. There is no
web / mobile / desktop surface and no `docs/design-system.md` — all components are `NEW:` pending
`/sdd:design-system`.

## Source

- **Tool:** code (default — `docs/design-system.md` absent; not an MCP degradation)
- **File:** inline wireframes below

## Screens

### SCR-01 — First-run setup

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | Closer starts the bot with first-run unfinished (US-01). Sequential wizard: default currency (preset EUR), then edit/confirm the once-proposed category list. | NEW: BotReply, NEW: ChoiceKeyboard | wireframe below |
| validation | Confirm with no categories (AC-14, `first_run.empty_category_list`). First-run stays unfinished; Uncategorized does not count. | NEW: ErrorReply, NEW: ChoiceKeyboard | wireframe below |
| error | Ask for a month before first-run finishes (AC-02, `first_run.still_required`). Close does not start. | NEW: ErrorReply, NEW: BotReply | wireframe below |
| loading | N/A: first-run writes settings locally; no harvest or model wait. | — | — |
| empty | N/A: an empty category list is **validation**, not an empty landing. The wizard always offers EUR and a proposed list. | — | — |
| success | N/A: a valid confirm **exits to SCR-02** (AC-01). | — | — |

```text
+--------------------------------------+
| SCR-01 default                       |
| First-run setup                      |
|                                      |
| Default currency: EUR                |
| [ Keep EUR ]  [ Change… ]            |
|                                      |
| Categories (edit if you wish):       |
|  • Groceries                         |
|  • Transport                         |
| [ Confirm list ]                     |
|                                      |
| Monthly closes start after confirm.  |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-01 validation                    |
| At least one category is required.   |
| Uncategorized does not count.        |
|                                      |
| Categories:                          |
|  (none)                              |
| [ Edit list ]                        |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-01 error                         |
| First-run setup is still required.   |
| That close did not start.            |
|                                      |
| Continue setup:                      |
| Default currency → category list.    |
+--------------------------------------+
```

### SCR-02 — Ready

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | First-run finished and no in-progress draft: closer can ask for a completed UTC month. Entry from AC-01, AC-11 resume-without-draft, return from SCR-03, or after SCR-06. Shows default currency and that the frozen list is in force. | NEW: BotReply, NEW: CommandHint | wireframe below |
| loading | Closer asked for a completed UTC month; harvest runs synchronously (ADR-0004). Closer waits until the draft is visible (time-to-draft ≤ 180 s when the month has ≤ 500 family-group messages; AC-17 still harvests in full with no 180 s promise). | NEW: BotReply | wireframe below |
| error | Current incomplete UTC month requested (AC-15, `harvest.incomplete_month`). Close does not start; stay on Ready. | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| error (no draft) | `/save` with no draft in progress (AC-13, `save.no_draft`). Stay on Ready. | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| error (egress) | A send would take other talk off the machine (AC-07, `harvest.egress_blocked`). No draft is shown; stay on Ready. | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| empty | N/A: Ready is a command prompt, not a list. Surviving saved closes are not a Ready listing (no “compare months” UI). | — | — |
| success | N/A: a successful harvest **exits to SCR-04**. Harvest failure **exits to SCR-03**. `harvest.draft_in_progress` (AC-18) stays on **SCR-04**, not here. | — | — |

```text
+--------------------------------------+
| SCR-02 default                       |
| Ready                                |
|                                      |
| Default currency: EUR                |
| Category list: frozen                |
| Monthly closes can start.            |
|                                      |
| /close YYYY-MM                       |
| /save   (only with a draft)          |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-02 loading                       |
| Obtaining 2026-08…                   |
| Reading the family group.            |
| Only spend-looking lines may leave.  |
|                                      |
| Wait — draft appears here when ready.|
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-02 error (incomplete month)      |
| Only a completed UTC month can be    |
| requested.                           |
|                                      |
| /close YYYY-MM                       |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-02 error (no draft)              |
| There is no draft to save.           |
|                                      |
| /close YYYY-MM                       |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-02 error (egress)                |
| Only spend-looking lines may leave   |
| the machine.                         |
| That close did not start.            |
|                                      |
| /close YYYY-MM                       |
+--------------------------------------+
```

### SCR-03 — Harvest failed

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | Closer asked for a completed UTC month the system cannot obtain — no family-group messages in that month, or the month cannot be read (AC-04, `harvest.month_not_obtained`). This is **not** an empty successful draft. Offer return to Ready. | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| loading | N/A: this screen is shown only after harvest has already failed. | — | — |
| empty | N/A: an obtainable month with zero spend-looking lines is SCR-04 `empty` (AC-16), not this screen. | — | — |
| error | N/A: this screen’s **default** already is the AC-04 failure. No further error class lands here. | — | — |
| success | N/A: a successful harvest never opens this screen. | — | — |
| validation | N/A: no closer input is collected here. | — | — |

```text
+--------------------------------------+
| SCR-03 default                       |
| Harvest failed                       |
|                                      |
| That month could not be obtained.    |
| This is not a successful empty close.|
|                                      |
| Back to Ready.                       |
| /close YYYY-MM                       |
+--------------------------------------+
```

### SCR-04 — Private draft

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | Month obtained and draft built (AC-03, AC-05): filed lines (one source message may be several lines), default-currency category totals, other-currency list, remaining suspects, full egress list (ADR-0002). Resume of an in-progress draft including handles already made (AC-11). Mapped shops appear as ordinary filed lines (AC-12), not a separate state. | NEW: DraftSummary, NEW: ChoiceKeyboard, NEW: CommandHint | wireframe below |
| empty | Obtainable month with zero spend-looking lines (AC-16): `is_empty`, empty default-currency totals, no suspects; closer may `/save`. | NEW: DraftSummary, NEW: CommandHint | wireframe below |
| error | `/save` while an unhandled suspect remains (AC-09, `save.unhandled_suspect`). Stay on the draft. | NEW: ErrorReply, NEW: DraftSummary, NEW: ChoiceKeyboard | wireframe below |
| error (busy) | Ask to start another monthly close while this draft exists (AC-18, `harvest.draft_in_progress`). Second draft does not start; stay here. | NEW: ErrorReply, NEW: DraftSummary, NEW: CommandHint | wireframe below |
| loading | N/A: harvest wait is SCR-02 `loading`. A handle returns an updated `default`/`empty`. | — | — |
| success | N/A: save **exits to SCR-06**. A handle stays on this screen as updated `default`. | — | — |
| validation | N/A: draft view collects no fields; handle input is SCR-05. | — | — |

```text
+--------------------------------------+
| SCR-04 default                       |
| Private draft  2026-08               |
|                                      |
| Lines                                |
|  Test Shop  12.00 EUR  Groceries     |
|  Cafe       8.00  USD  (other)       |
|  Unknown    —     EUR  Uncategorized |
|                                      |
| Totals (EUR only)                    |
|  Groceries   12.00                   |
|                                      |
| Other currencies (listed, not mixed) |
|  Cafe  8.00 USD                      |
|                                      |
| Suspects remaining: 2                |
|  [ Handle: Unknown ]                 |
|  [ Handle: Cafe ]                    |
|                                      |
| Egress (every line that left)        |
|  • Test Shop 12.00                   |
|                                      |
| /save  when suspects are handled     |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-04 empty                         |
| Private draft  2026-08               |
|                                      |
| No spend-looking lines.              |
| Totals (EUR): empty                  |
| Suspects: none                       |
| Egress: none                         |
|                                      |
| You may /save and accept empty totals|
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-04 error                         |
| Every suspect line must be handled   |
| before save.                         |
|                                      |
| (draft body unchanged)               |
| Suspects remaining: 2                |
|  [ Handle: … ]                       |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-04 error (busy)                  |
| Finish or replace the in-progress    |
| close first.                         |
|                                      |
| (same draft — no second close)       |
| /save after suspects                 |
+--------------------------------------+
```

The family group never receives this screen (AC-05, AC-06). A family-poster bot attempt is SCR-07,
not a state here. The contract does not define a replace operation for AC-18 — this state only
refuses; how the closer replaces an in-progress draft remains the `api` sequence gap.

### SCR-05 — Handle suspect line

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | Closer picked a remaining suspect from SCR-04 (AC-09), or is overriding a line’s category for a shop (AC-12). Shows that one line and the five `HandleChoice` actions. `assign_category` then offers the frozen category list; `enter_amount` then asks for the amount. Success **returns to SCR-04**. | NEW: BotReply, NEW: ChoiceKeyboard | wireframe below |
| validation | `enter_amount` without `amount`, or `assign_category` without a confirmed `category_id` (contract request rules). Stay on this screen. | NEW: ErrorReply, NEW: ChoiceKeyboard | wireframe below |
| error | `draft_line_id` is not on the in-progress draft (`draft.line_not_found` — contract; sequence gap). | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| error (no draft) | Handle attempted with no `drafts` row (`save.no_draft`, AC-13 same invariant). No handle is stored; closer is sent back toward Ready. | NEW: ErrorReply, NEW: CommandHint | wireframe below |
| empty | N/A: this screen opens only with a picked line. A draft with zero suspects never enters here (closer may `/save` on SCR-04 `empty` / `default`). | — | — |
| loading | N/A: handle is a local persist; no harvest or model wait. | — | — |
| success | N/A: a completed handle **exits to SCR-04** with the updated draft. | — | — |

The five choices are **actions on `default`**, not five screen states: enter a missing amount;
assign a confirmed category (upserts the shop map); confirm Uncategorized; leave a
non-default-currency line listed without converting; exclude the line.

```text
+--------------------------------------+
| SCR-05 default                       |
| Handle suspect                       |
|                                      |
| Unknown  —  EUR  Uncategorized       |
|                                      |
| [ Enter amount ]                     |
| [ Assign category ]                  |
| [ Confirm Uncategorized ]            |
| [ Leave other currency listed ]      |
| [ Exclude from the close ]           |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-05 default (assign follow-up)    |
| Assign a confirmed category          |
|                                      |
| Shop: Lidl                           |
|  [ Groceries ]                       |
|  [ Transport ]                       |
| Uncategorized is not on this list.   |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-05 validation                    |
| Amount is required for this handle.  |
|                                      |
| [ Enter amount ]                     |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-05 error                         |
| That line is not on the in-progress  |
| draft.                               |
|                                      |
| /save or open the draft again        |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-05 error (no draft)              |
| There is no draft to save.           |
|                                      |
| /close YYYY-MM                       |
+--------------------------------------+
```

Missing `amount` / `category_id` have no named contract `code` — they are request-field
validation, not a new `module.error_name`.

### SCR-06 — Monthly close saved

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | Closer saved a draft with no unhandled suspects. Save **is** acceptance of the default-currency totals (AC-08). Other-currency lines stay listed separately; excluded lines are omitted. Then Ready (SCR-02). | NEW: BotReply, NEW: CommandHint | wireframe below |
| replaced | A saved close already existed for that UTC month; this save replaces it (AC-19, `replaced: true`). Same confirmation, plus that the previous close for the month is gone. | NEW: BotReply, NEW: CommandHint | wireframe below |
| error | N/A: `save.unhandled_suspect` stays on SCR-04; `save.no_draft` stays on SCR-02. This screen never opens on a failed save. | — | — |
| empty | N/A: an empty-draft save (AC-16) still uses `default` — confirmation that empty totals were accepted, not an empty landing. | — | — |
| loading | N/A: save is a local persist; no harvest wait. | — | — |
| success | N/A: this screen’s **default** already is the save confirmation. There is no separate accept step (AC-08). | — | — |
| validation | N/A: `/save` takes no fields. | — | — |

```text
+--------------------------------------+
| SCR-06 default                       |
| Monthly close saved                  |
|                                      |
| 2026-08 recorded.                    |
| Save accepted the EUR totals:        |
|  Groceries   12.00                   |
| Other currencies listed, not mixed.  |
|                                      |
| Ready.                               |
| /close YYYY-MM                       |
+--------------------------------------+
```

```text
+--------------------------------------+
| SCR-06 replaced                      |
| Monthly close saved                  |
|                                      |
| 2026-08 recorded.                    |
| This save replaced the previous      |
| close for that month.                |
| Save accepted the EUR totals:        |
|  Groceries   15.00                   |
|                                      |
| Ready.                               |
| /close YYYY-MM                       |
+--------------------------------------+
```

### SCR-07 — Unauthorized

| State | Trigger / condition | Components (from the inventory) | Source-ref |
|---|---|---|---|
| default | An account that is not the pinned closer addresses the bot after first-run (AC-06, `auth.not_closer`). Reply is only in that private chat. `message` and `details` contain **no** draft or close detail. Ends there; no path into SCR-04. | NEW: ErrorReply | wireframe below |
| error | N/A: this screen’s **default** already is the refusal. | — | — |
| empty | N/A: family-group talk about a monthly close is **silence** — no bot message, not this screen (AC-06). | — | — |
| loading | N/A: authz check is immediate. | — | — |
| success | N/A: a closer never sees this screen. | — | — |
| validation | N/A: no input is collected. | — | — |

```text
+--------------------------------------+
| SCR-07 default                       |
| (private chat with the non-closer)   |
|                                      |
| You cannot use this bot.             |
|                                      |
| (no month, no totals, no line text)  |
+--------------------------------------+
```

Family-group silence is not a product screen (ux-flows out of scope). Before first-run this
screen does not exist — the account that confirms the category list becomes the closer.

## New components

| Component | Why no existing primitive fits | Registered in design-system |
|---|---|---|
| BotReply | Telegram’s unit of UI is a private-chat text reply. No Page / Card / Form inventory exists (`docs/design-system.md` absent). | pending |
| ChoiceKeyboard | Closed choices (currency, confirm list, HandleChoice, suspect pick, frozen categories) are Telegram reply or inline buttons, not a web Button. | pending |
| ErrorReply | Contract `{code, message}` shown as closer-visible private text. No toast / ErrorBanner inventory. | pending |
| CommandHint | Slash-command affordances (`/close`, `/save`). No nav bar or route list; Telegram navigation is commands in the reply. | pending |
| DraftSummary | One private reply for `PrivateDraftView` (lines, default-currency totals, other-currency list, suspects, egress). No table / card inventory; the contract says one reply holds the draft. | pending |
