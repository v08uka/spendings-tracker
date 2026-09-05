"""Draft line, suspect, handle, and default-currency total rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import StrEnum


class HandleChoice(StrEnum):
    ENTER_AMOUNT = "enter_amount"
    ASSIGN_CATEGORY = "assign_category"
    CONFIRM_UNCATEGORIZED = "confirm_uncategorized"
    LEAVE_OTHER_CURRENCY = "leave_other_currency"
    EXCLUDE = "exclude"


@dataclass(frozen=True)
class DraftLine:
    amount: str | None
    currency: str
    category_id: str | None
    is_excluded: bool = False
    is_handled: bool = False


def make_draft_line(
    *,
    amount: str | None,
    currency: str,
    category_id: str | None,
    is_excluded: bool = False,
    is_handled: bool = False,
) -> DraftLine:
    return DraftLine(
        amount=amount,
        currency=currency,
        category_id=category_id,
        is_excluded=is_excluded,
        is_handled=is_handled,
    )


def parse_amount(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    normalised = text.replace(",", ".", 1)
    try:
        value = Decimal(normalised)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    return f"{value:.2f}"


def is_suspect(line: DraftLine, *, default_currency: str) -> bool:
    if line.is_excluded:
        return False
    return (
        line.amount is None
        or line.currency != default_currency
        or line.category_id is None
    )


def is_clean(line: DraftLine, *, default_currency: str) -> bool:
    return not is_suspect(line, default_currency=default_currency)


def apply_handle(
    line: DraftLine,
    choice: HandleChoice,
    *,
    amount: str | None = None,
    category_id: str | None = None,
) -> DraftLine:
    if choice is HandleChoice.ENTER_AMOUNT:
        parsed = parse_amount(amount)
        if parsed is None:
            return replace(line, is_handled=False)
        return replace(line, amount=parsed, is_handled=True)
    if choice is HandleChoice.ASSIGN_CATEGORY:
        return replace(line, category_id=category_id, is_handled=True)
    if choice is HandleChoice.CONFIRM_UNCATEGORIZED:
        return replace(line, category_id=None, is_handled=True)
    if choice is HandleChoice.LEAVE_OTHER_CURRENCY:
        return replace(line, is_handled=True)
    return replace(line, is_excluded=True, is_handled=True)


def can_save(lines: list[DraftLine], *, default_currency: str) -> bool:
    for line in lines:
        if line.is_excluded:
            continue
        if line.amount is None:
            return False
        if is_suspect(line, default_currency=default_currency) and not line.is_handled:
            return False
    return True


def default_currency_totals(
    lines: list[DraftLine], *, default_currency: str
) -> dict[str | None, str]:
    totals: dict[str | None, Decimal] = {}
    for line in lines:
        if line.is_excluded or line.currency != default_currency:
            continue
        parsed = parse_amount(line.amount)
        if parsed is None:
            continue
        totals[line.category_id] = totals.get(line.category_id, Decimal("0")) + Decimal(
            parsed
        )
    return {category_id: f"{total:.2f}" for category_id, total in totals.items()}


def other_currency_lines(
    lines: list[DraftLine], *, default_currency: str
) -> list[DraftLine]:
    return [
        line
        for line in lines
        if not line.is_excluded and line.currency != default_currency
    ]
