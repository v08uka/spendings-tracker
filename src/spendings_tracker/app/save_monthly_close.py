"""Save a monthly close when every remaining suspect is handled."""

from __future__ import annotations

from dataclasses import dataclass

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.draft import (
    can_save,
    default_currency_totals,
    make_draft_line,
)
from spendings_tracker.ports.persistence import PersistencePort, StoredMonthlyClose


@dataclass(frozen=True)
class SaveResult:
    close: StoredMonthlyClose
    totals: dict[str | None, str]
    replaced: bool


def save_monthly_close(persistence: PersistencePort) -> SaveResult:
    settings = persistence.load_settings()
    if settings is None:
        raise AppError("save.no_draft", "There is no draft to save.")
    draft = persistence.load_draft()
    if draft is None:
        raise AppError("save.no_draft", "There is no draft to save.")
    domain_lines = [
        make_draft_line(
            amount=line.amount,
            currency=line.currency,
            category_id=line.category_id,
            is_excluded=line.is_excluded,
            is_handled=line.is_handled,
        )
        for line in draft.lines
    ]
    if not can_save(domain_lines, default_currency=settings.default_currency):
        raise AppError(
            "save.unhandled_suspect",
            "Every suspect line must be handled before save.",
        )
    existing = persistence.load_monthly_close(draft.utc_month)
    close = persistence.save_monthly_close(
        default_currency=settings.default_currency
    )
    totals = default_currency_totals(
        domain_lines, default_currency=settings.default_currency
    )
    return SaveResult(close=close, totals=totals, replaced=existing is not None)
