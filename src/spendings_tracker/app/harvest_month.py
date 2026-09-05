"""Synchronous harvest → private draft pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from spendings_tracker.app.complete_first_run import require_first_run
from spendings_tracker.app.errors import CATALOG, AppError, catalog_error
from spendings_tracker.domain.draft import is_suspect, make_draft_line, parse_amount
from spendings_tracker.domain.month import is_completed_utc_month, is_utc_month
from spendings_tracker.domain.shop import shop_key
from spendings_tracker.domain.spend_looking import (
    extract_spend_looking_lines,
    is_spend_looking,
)
from spendings_tracker.ports.harvest import HarvestPort
from spendings_tracker.ports.model import ModelPort
from spendings_tracker.ports.persistence import (
    NewDraftLine,
    PersistencePort,
    StoredDraft,
)

_AMOUNT = re.compile(r"\d+(?:[.,]\d{1,2})?")
_ISO_CURRENCIES = frozenset(
    {
        "AED",
        "AUD",
        "BGN",
        "BRL",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "HUF",
        "ILS",
        "INR",
        "JPY",
        "KRW",
        "MXN",
        "NOK",
        "NZD",
        "PLN",
        "RON",
        "RUB",
        "SEK",
        "SGD",
        "THB",
        "TRY",
        "UAH",
        "USD",
        "ZAR",
    }
)
INCOMPLETE = "harvest.incomplete_month"
BUSY = "harvest.draft_in_progress"
EGRESS_BLOCKED = "harvest.egress_blocked"


@dataclass(frozen=True)
class HarvestResult:
    draft: StoredDraft
    is_empty: bool
    posted_to_group: bool
    suspect_count: int


def harvest_month(
    persistence: PersistencePort,
    harvest: HarvestPort,
    model: ModelPort,
    utc_month: str,
    *,
    now: datetime | None = None,
) -> HarvestResult:
    settings = require_first_run(persistence)
    if not is_utc_month(utc_month):
        raise catalog_error(INCOMPLETE, {"utc_month": utc_month})
    if not is_completed_utc_month(utc_month, now=now):
        raise catalog_error(INCOMPLETE, {"utc_month": utc_month})
    if persistence.load_draft() is not None:
        raise catalog_error(BUSY)
    messages = harvest.harvest_month(utc_month)
    pairs: list[tuple[str, str, int]] = []
    for message in messages:
        for line in extract_spend_looking_lines(message.text):
            pairs.append((message.id, line.text, line.source_line_index))
    id_by_name = {category.name: category.id for category in settings.categories}
    to_send: list[str] = []
    pending: list[tuple[str, str, int, str, str | None, str]] = []
    for message_id, text, source_index in pairs:
        shop, amount, currency = _shop_and_amount(text, settings.default_currency)
        mapping = persistence.find_shop_mapping(shop)
        if mapping is not None:
            pending.append(
                (message_id, text, source_index, shop, mapping.category_id, currency)
            )
            continue
        to_send.append(text)
        pending.append((message_id, text, source_index, shop, None, currency))
    filed: dict[str, str | None] = {}
    if to_send:
        _ensure_spend_looking(to_send)
        names = model.classify(
            to_send, [category.name for category in settings.categories]
        )
        if len(names) != len(to_send):
            raise catalog_error("model.unavailable")
        for text, name in zip(to_send, names, strict=True):
            filed[text] = id_by_name.get(name)
    lines: list[NewDraftLine] = []
    for message_id, text, source_index, shop, mapped_id, currency in pending:
        category_id = mapped_id if mapped_id is not None else filed.get(text)
        shop_display, amount, parsed_currency = _shop_and_amount(
            text, settings.default_currency
        )
        lines.append(
            NewDraftLine(
                source_message_id=message_id,
                source_line_index=source_index,
                line_text=text,
                shop_display=shop_display,
                shop_key=shop_key(shop_display),
                amount=amount,
                currency=parsed_currency,
                category_id=category_id,
            )
        )
    draft = persistence.create_draft(utc_month, lines, to_send)
    suspects = sum(
        1
        for line in draft.lines
        if is_suspect(
            make_draft_line(
                amount=line.amount,
                currency=line.currency,
                category_id=line.category_id,
                is_excluded=line.is_excluded,
                is_handled=line.is_handled,
            ),
            default_currency=settings.default_currency,
        )
    )
    return HarvestResult(
        draft=draft,
        is_empty=len(draft.lines) == 0,
        posted_to_group=False,
        suspect_count=suspects,
    )


def _ensure_spend_looking(lines: list[str]) -> None:
    for line in lines:
        if not is_spend_looking(line):
            raise AppError(EGRESS_BLOCKED, CATALOG[EGRESS_BLOCKED])


def _shop_and_amount(
    text: str, default_currency: str
) -> tuple[str, str | None, str]:
    match = _AMOUNT.search(text)
    if match is None:
        return text.strip(), None, default_currency
    amount = parse_amount(match.group(0))
    before = text[: match.start()].strip()
    after = text[match.end() :].strip()
    currency = default_currency
    adjacent_after = after.split(None, 1)
    adjacent_before = before.rsplit(None, 1)
    glued_after = re.match(r"^([A-Za-z]{3})\b", after)
    glued_before = re.search(r"\b([A-Za-z]{3})$", before)
    candidates: list[tuple[str, str]] = []
    if glued_after is not None:
        candidates.append(("after", glued_after.group(1)))
    if adjacent_after and adjacent_after[0].isalpha() and len(adjacent_after[0]) == 3:
        candidates.append(("after", adjacent_after[0]))
    if glued_before is not None:
        candidates.append(("before", glued_before.group(1)))
    before_token = adjacent_before[-1] if adjacent_before else ""
    if before_token.isalpha() and len(before_token) == 3:
        candidates.append(("before", before_token))
    for side, token in candidates:
        code = token.upper()
        if code in _ISO_CURRENCIES:
            currency = code
            if side == "after":
                after = after[len(token) :].strip()
            else:
                before = before[: -len(token)].strip()
            break
    shop = before if before else after
    return shop, amount, currency
