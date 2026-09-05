---
status: Draft
owner: "Dell"
reviewers: ["Tech Lead", "Security Lead"]
updated_at: "2026-09-05"
feature_size: L
info_version: "0.1.0"
---

# Bot command contract — spendings-tracker

Interface contract for the closer’s Telegram command-and-reply conversation. Derived from
`data-model.md` (fields and constraints), `sad.md` §6 (flows and `alt` branches), and `spec.md`
§4 / §5 (stories and outcomes). Command names are this stage’s mapping from those product verbs;
they are not HTTP paths.

**Interface kind.** `sad.md` `target_surfaces: [backend-service]`. Sub-kind is Telegram
command-and-reply (SAD §4 seed 1 and ADR-0003), not HTTP/REST and not gRPC. There is no
`openapi.yaml`: the process long-polls Telegram and does not expose a URL (SAD §7). There is no
`events.md`: every §6 flow is synchronous (ADR-0004).

**Why this contract exists.** Once a month the closer turns already-written family-group
shop-and-amount mentions into a private draft they will save. Family posters are never operators.
Only spend-looking lines may leave the machine for a language-model service.

## Conventions

| Topic | Rule |
|---|---|
| Transport | Telegram Bot API in the closer’s private chat. The family group is harvest source only. |
| AuthZ | After first-run, the Telegram account in `settings.closer_identity` is the only closer. Any other account that addresses the bot gets `auth.not_closer` with no draft or close detail (AC-06, SCR-07). Talk in the family group gets **silence** — no draft, no refusal, no close detail posted there (AC-06). Before first-run, the account that confirms first-run is pinned. |
| Error envelope | Every failure the closer (or a non-closer addressing the bot) can see is `{code, message, details?}`. `code` is `module.error_name` (snake_case). The closer-visible text is `message`. |
| IDs | Persisted row ids are time-sortable ULIDs (`TEXT`, 26 Crockford characters). Pattern: `^[0-7][0-9A-HJKMNP-TV-Z]{25}$`. |
| Month | Completed UTC calendar month `YYYY-MM`. Pattern: `^[0-9]{4}-(0[1-9]|1[0-2])$`. The current incomplete UTC month is refused. |
| Nullability | Optional columns use `string \| null` (OpenAPI 3.1 style). Uncategorized is `category_id: null`, never a `categories` row. |
| Flags | `is_excluded` and `is_handled` are integers `0` or `1`. |
| Lists | One private-chat reply holds the draft (lines, totals, suspects, egress). Cursor pagination is not used — this is not an HTTP list resource. Telegram message splitting is an adapter concern, not a contract cursor. |
| Idempotency | None. §6 flags and ADR-0004 forbid an idempotency key. Harvest is one synchronous wait; a later ask while a draft exists is `harvest.draft_in_progress`. |
| Placeholder data | Examples use `10001`, `Test Shop`, `Groceries`, `2026-08` only. No real PII. |

## Shared types

Schema names are glossary / data-model terms verbatim.

### Error

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `code` | string | `^[a-z_]+\\.[a-z_]+$` | contract convention |
| `message` | string | required | closer-visible reason from the matching AC |
| `details` | object \| omitted | optional structured context | contract convention |

### Settings

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `settings.id` |
| `closer_identity` | string | required, unique | `settings.closer_identity` |
| `default_currency` | string | required; first-run preset `EUR` when the closer keeps it | `settings.default_currency` |
| `created_at` | string | ISO-8601 UTC | `settings.created_at` |

### Category

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `categories.id` |
| `settings_id` | string | ULID, FK | `categories.settings_id` |
| `name` | string | required; unique per settings; Uncategorized is not a name here | `categories.name` |
| `sort_order` | integer | required | `categories.sort_order` |
| `created_at` | string | ISO-8601 UTC | `categories.created_at` |

### ShopMapping

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `shop_mappings.id` |
| `shop_key` | string | required, unique; trim + lowercase of the remaining spelling | `shop_mappings.shop_key` |
| `shop_display` | string | required; last corrected display form | `shop_mappings.shop_display` |
| `category_id` | string \| null | FK; null = mapped to Uncategorized | `shop_mappings.category_id` |
| `created_at` | string | ISO-8601 UTC | `shop_mappings.created_at` |

### Draft

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `drafts.id` |
| `utc_month` | string | `YYYY-MM` | `drafts.utc_month` |
| `created_at` | string | ISO-8601 UTC | `drafts.created_at` |

### DraftLine

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `draft_lines.id` |
| `draft_id` | string | ULID, FK | `draft_lines.draft_id` |
| `source_message_id` | string | required | `draft_lines.source_message_id` |
| `source_line_index` | integer | required; 0-based pair index inside that message | `draft_lines.source_line_index` |
| `line_text` | string | required; spend-looking text on the private draft | `draft_lines.line_text` |
| `shop_display` | string | required | `draft_lines.shop_display` |
| `shop_key` | string | required; trim + lowercase | `draft_lines.shop_key` |
| `amount` | string \| null | null = missing amount (suspect) | `draft_lines.amount` |
| `currency` | string | required; default currency when the line names none | `draft_lines.currency` |
| `category_id` | string \| null | FK; null = Uncategorized (suspect until handled) | `draft_lines.category_id` |
| `is_excluded` | integer | `0` or `1` | `draft_lines.is_excluded` |
| `is_handled` | integer | `0` or `1` | `draft_lines.is_handled` |
| `created_at` | string | ISO-8601 UTC | `draft_lines.created_at` |

A **suspect line** is a non-excluded draft line that is missing an amount, uses a currency other
than `settings.default_currency`, or has `category_id: null`. A **clean line** is a spend-looking
line that is not a suspect line.

### MonthlyClose

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `monthly_closes.id` |
| `utc_month` | string | `YYYY-MM`, unique; a later save replaces the row | `monthly_closes.utc_month` |
| `default_currency` | string | snapshot of settings at save | `monthly_closes.default_currency` |
| `created_at` | string | ISO-8601 UTC of the save | `monthly_closes.created_at` |

### MonthlyCloseLine

Same shape as `DraftLine` without `is_excluded` / `is_handled` (excluded lines are omitted on
save). Origin: `monthly_close_lines.*`.

### EgressLine

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `id` | string | ULID | `egress_lines.id` |
| `draft_id` | string \| null | set while the close is in progress | `egress_lines.draft_id` |
| `monthly_close_id` | string \| null | set on copies written at save | `egress_lines.monthly_close_id` |
| `line_text` | string | exact text that left the machine | `egress_lines.line_text` |
| `created_at` | string | ISO-8601 UTC of the send | `egress_lines.created_at` |

Exactly one of `draft_id` / `monthly_close_id` is set. Mapped shops are not sent and do not get a
row (ADR-0005).

### CategoryTotal (computed)

Default-currency totals only. Not a stored table — computed from child lines
(`data-model.md` → `monthly_closes`: “Default-currency totals are computed from child lines, not
stored”).

| Field | Type | Origin |
|---|---|---|
| `category_id` | string \| null | `draft_lines.category_id` / `monthly_close_lines.category_id` (null = Uncategorized) |
| `category_name` | string \| null | `categories.name`; null when `category_id` is null |
| `total_amount` | string | sum of `amount` for lines in the default currency; excluded draft lines omitted |

### PrivateDraftView

The closer-visible private draft (SCR-04). Never posted to the family group.

| Field | Type | Origin |
|---|---|---|
| `draft` | Draft | `drafts` |
| `lines` | DraftLine[] | `draft_lines` for that draft; one source message may yield several lines (AC-05) |
| `category_totals` | CategoryTotal[] | computed; default-currency only |
| `other_currency_lines` | DraftLine[] | `draft_lines` whose `currency` ≠ settings default currency |
| `suspects` | DraftLine[] | remaining unhandled suspect lines (`is_handled = 0` and still suspect) |
| `egress_lines` | EgressLine[] | every spend-looking line that left for this close (ADR-0002, QG-1) |
| `is_empty` | boolean | true when `lines` is empty (AC-16 successful empty draft) |

### ReadyView

| Field | Type | Origin |
|---|---|---|
| `settings` | Settings | `settings` singleton |
| `categories` | Category[] | frozen list (ADR-0001) |
| `has_in_progress_draft` | boolean | false on Ready; resume uses `PrivateDraftView` instead when a draft row exists |

### HandleChoice

Closed set from AC-09 (no column — the closer’s action on one draft line):

| Value | Meaning | Writes |
|---|---|---|
| `enter_amount` | enter a missing amount | `draft_lines.amount`; `is_handled = 1` |
| `assign_category` | assign a confirmed category | `draft_lines.category_id`; upsert `shop_mappings` (AC-12); `is_handled = 1` |
| `confirm_uncategorized` | confirm leaving the line Uncategorized | `category_id` stays null; `is_handled = 1` |
| `leave_other_currency` | leave a non-default-currency line listed without converting | no currency change; `is_handled = 1` |
| `exclude` | omit the line from the close | `is_excluded = 1`; `is_handled = 1` |

`assign_category` on a later override of a clean or mapped line is the same write (AC-12).

## Operations

Auth on every operation after first-run: the Telegram user id must equal
`settings.closer_identity`. Failure: `auth.not_closer` (bot DM only). Family-group inbound is not
an operation — silence.

### `completeFirstRun` — `/start` (first-run unfinished)

**Story:** US-01. **Screens:** SCR-01 → SCR-02. **Flow:** Complete first-run setup.

Triggered when the closer starts the bot and settings do not exist yet. Sequential wizard: default
currency (preset EUR), then edit the once-proposed category list if wished, then confirm.

**Request**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `default_currency` | string | yes | closer-chosen; omit-or-keep means write `EUR` |
| `categories` | `{name, sort_order}[]` | yes | at least one `name`; Uncategorized must not appear and does not count |

**Success** — first-run finished; monthly closes can start (AC-01). Body: `ReadyView` plus the
settings row just written (closer pin = this Telegram account).

**Errors**

| `code` | When | §6 branch / AC |
|---|---|---|
| `first_run.empty_category_list` | confirm with no categories | confirm empty list / AC-14 |
| `first_run.still_required` | `/close` (or any close ask) before confirm | ask for a month before first-run finishes / AC-02 |

**Example — request**

```json
{
  "default_currency": "EUR",
  "categories": [
    {"name": "Groceries", "sort_order": 0},
    {"name": "Transport", "sort_order": 1}
  ]
}
```

**Example — success**

```json
{
  "settings": {
    "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    "closer_identity": "10001",
    "default_currency": "EUR",
    "created_at": "2026-09-05T12:00:00Z"
  },
  "categories": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "settings_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "name": "Groceries",
      "sort_order": 0,
      "created_at": "2026-09-05T12:00:00Z"
    }
  ],
  "has_in_progress_draft": false
}
```

**Example — error**

```json
{
  "code": "first_run.empty_category_list",
  "message": "At least one category is required. Uncategorized does not count."
}
```

The once-proposed list is ephemeral first-run copy. It is not a persisted entity; only the
confirmed `categories` rows are stored (ADR-0001).

### `harvestMonth` — `/close <utc_month>`

**Story:** US-02, US-03, US-05, US-08. **Screens:** SCR-02 → SCR-04 or SCR-03. **Flows:** Critical
flow 1; Harvest empty or large month; Receive a private draft; Family poster stays a source.

Synchronous pipeline (ADR-0004): load settings → refuse incomplete / busy / unreadable month →
read that month’s already-existing family-group history (no export file) → keep only spend-looking
lines on the machine → apply shop-to-category map (skip send on a hit, ADR-0005) → send unmapped
spend-looking lines only → persist draft + egress → show `PrivateDraftView` only to the closer.

**Request**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `utc_month` | string | yes | `YYYY-MM`, completed UTC month |

**Success** — `PrivateDraftView` (AC-03, AC-05, AC-16). An obtainable month with zero spend-looking
lines is a successful empty draft (`is_empty: true`, empty totals, no suspects); the closer may
`/save`. A month with more than 500 family-group messages is still obtained in full; the 180-second
time-to-draft target does not apply (AC-17). Family-poster shop-and-amount lines from the group can
appear as draft lines; the poster is not asked to change how they write and does not receive the
draft (AC-10).

**Errors**

| `code` | When | §6 branch / AC |
|---|---|---|
| `first_run.still_required` | settings missing | first-run flow / AC-02 |
| `auth.not_closer` | other account addresses the bot | non-closer asks for the draft / AC-06 |
| `harvest.incomplete_month` | current incomplete UTC month | current incomplete UTC month / AC-15 |
| `harvest.draft_in_progress` | a `drafts` row already exists | in-progress draft already exists / AC-18 |
| `harvest.month_not_obtained` | no family-group messages in that month, or the month cannot be read | harvest cannot obtain the month / AC-04 |
| `harvest.egress_blocked` | a send would take other talk off the machine | a send would take other talk off the machine / AC-07 |

`harvest.draft_in_progress` explains that the in-progress close must be finished (`/save` after
suspects) or replaced first. This contract does **not** define a replace operation — AC-18 and the
sequence only specify the refusal. See the sync report sequence gap.

**Example — request**

```json
{ "utc_month": "2026-08" }
```

**Example — success (one clean line, one mapped skip, one egress row)**

```json
{
  "draft": {
    "id": "01ARZ3NDEKTSV4RRFFQ69G5FC0",
    "utc_month": "2026-08",
    "created_at": "2026-09-05T12:01:00Z"
  },
  "lines": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FD0",
      "draft_id": "01ARZ3NDEKTSV4RRFFQ69G5FC0",
      "source_message_id": "20001",
      "source_line_index": 0,
      "line_text": "Test Shop 12.00",
      "shop_display": "Test Shop",
      "shop_key": "test shop",
      "amount": "12.00",
      "currency": "EUR",
      "category_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "is_excluded": 0,
      "is_handled": 0,
      "created_at": "2026-09-05T12:01:00Z"
    }
  ],
  "category_totals": [
    {
      "category_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "category_name": "Groceries",
      "total_amount": "12.00"
    }
  ],
  "other_currency_lines": [],
  "suspects": [],
  "egress_lines": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FE0",
      "draft_id": "01ARZ3NDEKTSV4RRFFQ69G5FC0",
      "monthly_close_id": null,
      "line_text": "Test Shop 12.00",
      "created_at": "2026-09-05T12:01:00Z"
    }
  ],
  "is_empty": false
}
```

**Example — error**

```json
{
  "code": "harvest.incomplete_month",
  "message": "Only a completed UTC month can be requested.",
  "details": { "utc_month": "2026-09" }
}
```

### `handleSuspect` — conversation on one draft line (SCR-05)

**Story:** US-04, US-07. **Screens:** SCR-04 → SCR-05 → SCR-04. **Flows:** Critical flow 2
(unhandled-suspect branch); Remember shop corrections.

Not a slash command. The closer picks a remaining suspect (or overrides a line’s category) and
sends one `HandleChoice`.

**Request**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `draft_line_id` | string | yes | ULID of a `draft_lines` row on the in-progress draft |
| `choice` | HandleChoice | yes | enum above |
| `amount` | string | when `enter_amount` | written to `draft_lines.amount` |
| `category_id` | string | when `assign_category` | must be a confirmed `categories.id` |

**Success** — updated `PrivateDraftView` (handle persisted). `assign_category` upserts
`shop_mappings` (`shop_key` = trim + lowercase of that line’s remaining spelling). A later harvest
that matches that `shop_key` files from the map and does not send the line (AC-12, ADR-0005). A
different remaining spelling is a different shop.

**Errors**

| `code` | When | §6 branch / AC |
|---|---|---|
| `auth.not_closer` | other account | AC-06 |
| `save.no_draft` | no `drafts` row (same invariant as save-without-draft) | no draft in progress / AC-13 |
| `draft.line_not_found` | `draft_line_id` is not on the in-progress draft | supporting — needed by this operation; no dedicated §6 branch (sequence gap) |

**Example — request**

```json
{
  "draft_line_id": "01ARZ3NDEKTSV4RRFFQ69G5FD0",
  "choice": "assign_category",
  "category_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0"
}
```

**Example — success:** same `PrivateDraftView` shape as `harvestMonth`, with that line’s
`category_id` set, `is_handled: 1`, and a `ShopMapping` row written (not necessarily echoed).

**Example — error**

```json
{
  "code": "draft.line_not_found",
  "message": "That line is not on the in-progress draft."
}
```

### `saveMonthlyClose` — `/save`

**Story:** US-04. **Screens:** SCR-04 → SCR-06 → SCR-02. **Flow:** Critical flow 2.

Save is acceptance of the default-currency category totals. There is no separate accept step
(AC-08). Other-currency lines stay listed separately. Excluded lines are omitted. Egress rows are
copied onto the saved close, then the draft (and its egress) is deleted (`data-model.md` →
`egress_lines` aggregate note). If a saved close already exists for that `utc_month`, this save
replaces it (AC-19).

**Request:** none. Uses the single in-progress `drafts` row.

**Success** — monthly close recorded; closer confirmed; then Ready (AC-08, AC-19).

| Field | Type | Origin |
|---|---|---|
| `monthly_close` | MonthlyClose | `monthly_closes` |
| `lines` | MonthlyCloseLine[] | `monthly_close_lines` (non-excluded snapshot) |
| `category_totals` | CategoryTotal[] | computed, default-currency only |
| `other_currency_lines` | MonthlyCloseLine[] | snapshot lines whose `currency` ≠ the close’s `default_currency` |
| `egress_lines` | EgressLine[] | copies with `monthly_close_id` set (ADR-0002) |
| `replaced` | boolean | true when a previous close for that month was replaced (AC-19) |

**Errors**

| `code` | When | §6 branch / AC |
|---|---|---|
| `auth.not_closer` | other account | AC-06 |
| `save.no_draft` | no `drafts` row | no draft in progress / AC-13 |
| `save.unhandled_suspect` | a remaining suspect has `is_handled = 0` | unhandled suspect remains / AC-09 |

**Example — success**

```json
{
  "monthly_close": {
    "id": "01ARZ3NDEKTSV4RRFFQ69G5FF0",
    "utc_month": "2026-08",
    "default_currency": "EUR",
    "created_at": "2026-09-05T12:05:00Z"
  },
  "lines": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FG0",
      "monthly_close_id": "01ARZ3NDEKTSV4RRFFQ69G5FF0",
      "source_message_id": "20001",
      "source_line_index": 0,
      "line_text": "Test Shop 12.00",
      "shop_display": "Test Shop",
      "shop_key": "test shop",
      "amount": "12.00",
      "currency": "EUR",
      "category_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "created_at": "2026-09-05T12:05:00Z"
    }
  ],
  "category_totals": [
    {
      "category_id": "01ARZ3NDEKTSV4RRFFQ69G5FB0",
      "category_name": "Groceries",
      "total_amount": "12.00"
    }
  ],
  "other_currency_lines": [],
  "egress_lines": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FH0",
      "draft_id": null,
      "monthly_close_id": "01ARZ3NDEKTSV4RRFFQ69G5FF0",
      "line_text": "Test Shop 12.00",
      "created_at": "2026-09-05T12:01:00Z"
    }
  ],
  "replaced": false
}
```

**Example — error**

```json
{
  "code": "save.unhandled_suspect",
  "message": "Every suspect line must be handled before save."
}
```

### `resumeOnStart` — process start (not a slash command)

**Story:** US-06. **Screens:** SCR-04 or SCR-02. **Flow:** Stop and resume with state.

The closer starts the tool again. The process loads the SQLite file and the Telegram session from
the data volume (ADR-0007). No first-run re-entry.

**Request:** none.

**Success**

| Variant | When | Body | AC |
|---|---|---|---|
| private draft | a `drafts` row exists | `PrivateDraftView` including handles already made | AC-11 |
| Ready | no draft row | `ReadyView` — default currency, frozen list, shop-to-category map, and saved monthly closes still on disk | AC-11 |

**Errors:** none on this flow. A missing settings row is first-run (`completeFirstRun`), not a
resume error.

## Error catalog

No error registry exists in the repo yet (`AppError` is an empty translation type). These codes
are the contract’s proposal; reconcile when the app layer defines them.

| `code` | Closer-visible `message` (English) | Operations |
|---|---|---|
| `first_run.still_required` | First-run setup is still required. | `completeFirstRun` (close ask), `harvestMonth` |
| `first_run.empty_category_list` | At least one category is required. Uncategorized does not count. | `completeFirstRun` |
| `auth.not_closer` | You cannot use this bot. | every closer command after pin (no draft or close detail in `message` or `details`) |
| `harvest.incomplete_month` | Only a completed UTC month can be requested. | `harvestMonth` |
| `harvest.draft_in_progress` | Finish or replace the in-progress close first. | `harvestMonth` |
| `harvest.month_not_obtained` | That month could not be obtained. | `harvestMonth` |
| `harvest.egress_blocked` | Only spend-looking lines may leave the machine. | `harvestMonth` |
| `save.no_draft` | There is no draft to save. | `saveMonthlyClose`, `handleSuspect` |
| `save.unhandled_suspect` | Every suspect line must be handled before save. | `saveMonthlyClose` |
| `draft.line_not_found` | That line is not on the in-progress draft. | `handleSuspect` |
| `model.unavailable` | The language-model service is unavailable. | `harvestMonth` |
| `handle.invalid_amount` | Amount is required for this handle. | `handleSuspect` |
| `handle.unknown_category` | That category is not on the confirmed list. | `handleSuspect` |
| `handle.unknown_choice` | That is not a recognised handle choice. | `handleSuspect` |

Family-group silence is **not** a code sent to the group.

## Non-operations

| Behaviour | Why it is not a command |
|---|---|
| Family poster writes shop-and-amount lines in the group (US-05) | Harvest source only; no product UI (ux-flows out of scope). Covered by `harvestMonth` success (AC-10). |
| On-machine spend-looking gate (US-08) | Internal to `harvestMonth`. Visible failure is `harvest.egress_blocked` (AC-07). |
| Shop map applied before the model (ADR-0005) | Internal to `harvestMonth`. Mapped lines have no `EgressLine`. |
| Stop the tool | Process exit. State stays on the volume. Covered by `resumeOnStart`. |
