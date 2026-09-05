"""Telegram bot adapter for the closer's private chat."""

from __future__ import annotations

from spendings_tracker.app.complete_first_run import (
    complete_first_run,
    require_first_run,
)
from spendings_tracker.app.errors import AppError
from spendings_tracker.ports.closer_ui import BotReply
from spendings_tracker.ports.persistence import PersistencePort

PROPOSED_CATEGORIES = ["Groceries", "Transport"]
AUTH_MESSAGE = "You cannot use this bot."


class TelegramBot:
    def __init__(self, persistence: PersistencePort) -> None:
        self._persistence = persistence

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
        if settings is None:
            return self._first_run(user_id, chat_id, stripped)
        return BotReply(
            chat_id=chat_id,
            text=(
                "Ready\n"
                f"Default currency: {settings.default_currency}\n"
                "Category list: frozen\n"
                "Monthly closes can start."
            ),
            screen="SCR-02",
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
            return BotReply(
                chat_id=chat_id,
                text=(
                    "Ready\n"
                    f"Default currency: {settings.default_currency}\n"
                    "Category list: frozen\n"
                    "Monthly closes can start."
                ),
                screen="SCR-02",
            )
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
