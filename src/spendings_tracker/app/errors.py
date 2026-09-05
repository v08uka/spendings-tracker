"""One application error type.

Adapters translate vendor and Telegram failures into this.
"""

from __future__ import annotations

from typing import Any

CATALOG: dict[str, str] = {
    "first_run.still_required": "First-run setup is still required.",
    "first_run.empty_category_list": (
        "At least one category is required. Uncategorized does not count."
    ),
    "auth.not_closer": "You cannot use this bot.",
    "harvest.incomplete_month": "Only a completed UTC month can be requested.",
    "harvest.draft_in_progress": "Finish or replace the in-progress close first.",
    "harvest.month_not_obtained": "That month could not be obtained.",
    "harvest.egress_blocked": "Only spend-looking lines may leave the machine.",
    "save.no_draft": "There is no draft to save.",
    "save.unhandled_suspect": "Every suspect line must be handled before save.",
    "draft.line_not_found": "That line is not on the in-progress draft.",
    "model.unavailable": "The language-model service is unavailable.",
    "handle.invalid_amount": "Amount is required for this handle.",
    "handle.unknown_category": "That category is not on the confirmed list.",
    "handle.unknown_choice": "That is not a recognised handle choice.",
    "settings.already_exists": "Settings already exist.",
    "boot.missing_token": "TELEGRAM_BOT_TOKEN is required.",
    "boot.missing_session": "The Telegram user session is missing.",
}


class AppError(Exception):
    """Failure already translated out of an infrastructure adapter."""

    def __init__(
        self,
        code: str,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message if message else CATALOG.get(code, code)
        self.details = details or {}
        super().__init__(self.message)


def catalog_error(
    code: str, details: dict[str, Any] | None = None
) -> AppError:
    return AppError(code, CATALOG[code], details)
