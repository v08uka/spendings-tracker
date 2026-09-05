"""Telegram bot adapter for the closer's private chat."""

from __future__ import annotations

from datetime import datetime

from spendings_tracker.app.complete_first_run import (
    complete_first_run,
    require_first_run,
)
from spendings_tracker.app.errors import AppError
from spendings_tracker.app.handle_suspect import handle_suspect
from spendings_tracker.app.harvest_month import harvest_month
from spendings_tracker.app.save_monthly_close import save_monthly_close
from spendings_tracker.domain.draft import HandleChoice
from spendings_tracker.ports.closer_ui import BotReply
from spendings_tracker.ports.harvest import HarvestPort
from spendings_tracker.ports.model import ModelPort
from spendings_tracker.ports.persistence import PersistencePort

PROPOSED_CATEGORIES = ["Groceries", "Transport"]
AUTH_MESSAGE = "You cannot use this bot."
HARVEST_SCREENS = {
    "harvest.month_not_obtained": "SCR-03",
    "harvest.incomplete_month": "SCR-02",
    "harvest.draft_in_progress": "SCR-04",
    "harvest.egress_blocked": "SCR-02",
}


class TelegramBot:
    def __init__(
        self,
        persistence: PersistencePort,
        harvest: HarvestPort | None = None,
        model: ModelPort | None = None,
        *,
        now: datetime | None = None,
    ) -> None:
        self._persistence = persistence
        self._harvest = harvest
        self._model = model
        self._now = now

    def handle_group(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        return None

    def handle_private(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        settings = self._persistence.load_settings()
        if settings is not None and user_id != settings.closer_identity:
            return BotReply(
                chat_id=chat_id,
                text=AUTH_MESSAGE,
                screen="SCR-07",
                code="auth.not_closer",
            )
        stripped = text.strip()
        if stripped.startswith("/close"):
            return self._close(user_id, chat_id, stripped)
        if stripped.startswith("/save"):
            return self._save(chat_id)
        if stripped.startswith("handle "):
            return self._handle(user_id, chat_id, stripped)
        if settings is None:
            return self._first_run(user_id, chat_id, stripped)
        return self._ready(chat_id, settings.default_currency)

    def _close(self, user_id: str, chat_id: str, text: str) -> BotReply:
        try:
            require_first_run(self._persistence)
        except AppError as err:
            if err.code == "first_run.still_required":
                return BotReply(
                    chat_id=chat_id,
                    text=err.message,
                    screen="SCR-01",
                    code=err.code,
                )
            raise
        if self._harvest is None or self._model is None:
            settings = self._persistence.load_settings()
            currency = settings.default_currency if settings else "EUR"
            return self._ready(chat_id, currency)
        parts = text.split()
        utc_month = parts[1] if len(parts) > 1 else ""
        try:
            result = harvest_month(
                self._persistence,
                self._harvest,
                self._model,
                utc_month,
                now=self._now,
            )
        except AppError as err:
            return BotReply(
                chat_id=chat_id,
                text=err.message,
                screen=HARVEST_SCREENS.get(err.code, "SCR-02"),
                code=err.code,
            )
        label = "empty draft" if result.is_empty else "Private draft"
        return BotReply(
            chat_id=chat_id,
            text=f"{label} {utc_month}",
            screen="SCR-04",
        )

    def _handle(self, user_id: str, chat_id: str, text: str) -> BotReply:
        parts = text.split()
        line_id = parts[1] if len(parts) > 1 else ""
        choice_text = parts[2] if len(parts) > 2 else ""
        extra = parts[3] if len(parts) > 3 else None
        choice = HandleChoice(choice_text)
        amount = extra if choice is HandleChoice.ENTER_AMOUNT else None
        category_id = extra if choice is HandleChoice.ASSIGN_CATEGORY else None
        try:
            handle_suspect(
                self._persistence,
                closer_identity=user_id,
                draft_line_id=line_id,
                choice=choice,
                amount=amount,
                category_id=category_id,
            )
        except AppError as err:
            screen = "SCR-02" if err.code == "save.no_draft" else "SCR-05"
            return BotReply(
                chat_id=chat_id, text=err.message, screen=screen, code=err.code
            )
        return BotReply(
            chat_id=chat_id, text="Private draft updated", screen="SCR-04"
        )

    def _save(self, chat_id: str) -> BotReply:
        try:
            result = save_monthly_close(self._persistence)
        except AppError as err:
            screen = "SCR-02" if err.code == "save.no_draft" else "SCR-04"
            return BotReply(
                chat_id=chat_id, text=err.message, screen=screen, code=err.code
            )
        note = " replaced" if result.replaced else ""
        return BotReply(
            chat_id=chat_id,
            text=f"Monthly close saved{note}. Ready.",
            screen="SCR-06",
        )

    def _first_run(self, user_id: str, chat_id: str, text: str) -> BotReply:
        if text.startswith("confirm"):
            remainder = text[len("confirm") :]
            names = [
                part.strip() for part in remainder.split(",") if part.strip()
            ]
            try:
                settings = complete_first_run(
                    self._persistence,
                    closer_identity=user_id,
                    default_currency="EUR",
                    category_names=names,
                )
            except AppError as err:
                return BotReply(
                    chat_id=chat_id,
                    text=err.message,
                    screen="SCR-01",
                    code=err.code,
                )
            return self._ready(chat_id, settings.default_currency)
        proposed = "\n".join(f" • {name}" for name in PROPOSED_CATEGORIES)
        return BotReply(
            chat_id=chat_id,
            text=(
                "First-run setup\n"
                "Default currency: EUR\n"
                f"Categories:\n{proposed}"
            ),
            screen="SCR-01",
        )

    def _ready(self, chat_id: str, default_currency: str) -> BotReply:
        return BotReply(
            chat_id=chat_id,
            text=(
                "Ready\n"
                f"Default currency: {default_currency}\n"
                "Category list: frozen\n"
                "Monthly closes can start."
            ),
            screen="SCR-02",
        )
