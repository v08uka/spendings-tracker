"""Synchronous harvest → private draft pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from spendings_tracker.app.complete_first_run import require_first_run
from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.draft import is_suspect, make_draft_line
from spendings_tracker.domain.month import is_completed_utc_month
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
    if not is_completed_utc_month(utc_month, now=now):
        raise AppError(
            INCOMPLETE, "Only a completed UTC month can be requested."
        )
    if persistence.load_draft() is not None:
        raise AppError(
            BUSY, "Finish or replace the in-progress close first."
        )
    messages = harvest.harvest_month(utc_month)
    pairs: list[tuple[str, str]] = []
    for message in messages:
        for line in extract_spend_looking_lines(message.text):
            pairs.append((message.id, line.text))
    id_by_name = {category.name: category.id for category in settings.categories}
    to_send: list[str] = []
    pending: list[tuple[str, str, str, str | None, str]] = []
    for message_id, text in pairs:
        shop, amount, currency = _shop_and_amount(text, settings.default_currency)
        mapping = persistence.find_shop_mapping(shop)
        if mapping is not None:
            pending.append(
                (message_id, text, shop, mapping.category_id, currency)
            )
            continue
        to_send.append(text)
        pending.append((message_id, text, shop, None, currency))
    filed: dict[str, str | None] = {}
    if to_send:
        _ensure_spend_looking(to_send)
        names = model.classify(
            to_send, [category.name for category in settings.categories]
        )
        for text, name in zip(to_send, names, strict=True):
            filed[text] = id_by_name.get(name)
    lines: list[NewDraftLine] = []
    for index, (message_id, text, shop, mapped_id, currency) in enumerate(pending):
        category_id = mapped_id if mapped_id is not None else filed.get(text)
        shop_display, amount, parsed_currency = _shop_and_amount(
            text, settings.default_currency
        )
        lines.append(
            NewDraftLine(
                source_message_id=message_id,
                source_line_index=index,
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
            raise AppError(
                EGRESS_BLOCKED,
                "Only spend-looking lines may leave the machine.",
            )


def _shop_and_amount(
    text: str, default_currency: str
) -> tuple[str, str | None, str]:
    match = _AMOUNT.search(text)
    amount = match.group(0) if match else None
    shop = text[: match.start()].strip() if match else text.strip()
    currency = default_currency
    for token in text.replace(",", " ").split():
        if token.isalpha() and len(token) == 3 and token.upper() == token:
            currency = token
    return shop, amount, currency
