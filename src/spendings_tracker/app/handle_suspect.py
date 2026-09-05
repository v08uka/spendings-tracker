"""Handle one suspect line and grow the shop map on assign_category."""

from __future__ import annotations

from dataclasses import replace

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.draft import HandleChoice, apply_handle, make_draft_line
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
        raise AppError("save.no_draft", "There is no draft to save.")
    if closer_identity != settings.closer_identity:
        raise AppError("auth.not_closer", "You cannot use this bot.")
    draft = persistence.load_draft()
    if draft is None:
        raise AppError("save.no_draft", "There is no draft to save.")
    found = next((line for line in draft.lines if line.id == draft_line_id), None)
    if found is None:
        raise AppError(
            "draft.line_not_found",
            "That line is not on the in-progress draft.",
        )
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
        raise AppError("save.no_draft", "There is no draft to save.")
    return updated
