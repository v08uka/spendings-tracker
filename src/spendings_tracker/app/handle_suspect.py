"""Handle one suspect line and grow the shop map on assign_category."""

from __future__ import annotations

from dataclasses import replace

from spendings_tracker.app.errors import catalog_error
from spendings_tracker.domain.draft import (
    HandleChoice,
    apply_handle,
    make_draft_line,
    parse_amount,
)
from spendings_tracker.ports.persistence import PersistencePort, StoredDraft


def handle_suspect(
    persistence: PersistencePort,
    *,
    closer_identity: str,
    draft_line_id: str,
    choice: HandleChoice,
    amount: str | None = None,
    category_id: str | None = None,
) -> StoredDraft:
    settings = persistence.load_settings()
    if settings is None:
        raise catalog_error("save.no_draft")
    if closer_identity != settings.closer_identity:
        raise catalog_error("auth.not_closer")
    draft = persistence.load_draft()
    if draft is None:
        raise catalog_error("save.no_draft")
    found = next((line for line in draft.lines if line.id == draft_line_id), None)
    if found is None:
        raise catalog_error("draft.line_not_found")
    if choice is HandleChoice.ENTER_AMOUNT and parse_amount(amount) is None:
        raise catalog_error("handle.invalid_amount")
    if choice is HandleChoice.ASSIGN_CATEGORY:
        known = {category.id for category in settings.categories}
        if category_id is None or category_id not in known:
            raise catalog_error("handle.unknown_category")
    handled = apply_handle(
        make_draft_line(
            amount=found.amount,
            currency=found.currency,
            category_id=found.category_id,
            is_excluded=found.is_excluded,
            is_handled=found.is_handled,
        ),
        choice,
        amount=amount,
        category_id=category_id,
    )
    persistence.update_draft_line(
        replace(
            found,
            amount=handled.amount,
            category_id=handled.category_id,
            is_excluded=handled.is_excluded,
            is_handled=handled.is_handled,
        )
    )
    if choice is HandleChoice.ASSIGN_CATEGORY:
        persistence.upsert_shop_mapping(found.shop_display, category_id)
    updated = persistence.load_draft()
    if updated is None:
        raise catalog_error("save.no_draft")
    return updated
