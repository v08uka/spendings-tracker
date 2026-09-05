"""User-session harvest reader. Session file lives on the data volume."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from spendings_tracker.app.errors import catalog_error
from spendings_tracker.ports.harvest import FamilyGroupMessage


class TelethonFamilyGroupReader:
    def __init__(
        self,
        session_path: Path,
        *,
        api_id: str | None = None,
        api_hash: str | None = None,
        family_group: str | None = None,
    ) -> None:
        self.session_path = session_path
        self._api_id = (
            api_id if api_id is not None else os.environ.get("TELEGRAM_API_ID", "")
        )
        self._api_hash = (
            api_hash
            if api_hash is not None
            else os.environ.get("TELEGRAM_API_HASH", "")
        )
        self._family_group = (
            family_group
            if family_group is not None
            else os.environ.get("TELEGRAM_FAMILY_GROUP", "")
        )

    def read_completed_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        if not self.session_path.exists():
            raise catalog_error("boot.missing_session")
        if not self._api_id or not self._api_hash:
            raise catalog_error("boot.missing_session")
        year_text, month_text = utc_month.split("-", maxsplit=1)
        year = int(year_text)
        month = int(month_text)
        start = datetime(year, month, 1, tzinfo=UTC)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            end = datetime(year, month + 1, 1, tzinfo=UTC)
        from telethon.sync import TelegramClient

        messages: list[FamilyGroupMessage] = []
        with TelegramClient(
            str(self.session_path.with_suffix("")),
            int(self._api_id),
            self._api_hash,
        ) as client:
            entity = self._family_group or None
            if entity is None or entity == "":
                raise OSError("TELEGRAM_FAMILY_GROUP is not set")
            target = int(entity) if entity.lstrip("-").isdigit() else entity
            for message in client.iter_messages(
                target, offset_date=end, reverse=True
            ):
                when = message.date
                if when is None:
                    continue
                if when.tzinfo is None:
                    when = when.replace(tzinfo=UTC)
                else:
                    when = when.astimezone(UTC)
                if when < start:
                    continue
                if when >= end:
                    break
                text = message.message or ""
                messages.append(FamilyGroupMessage(id=str(message.id), text=text))
        return messages
