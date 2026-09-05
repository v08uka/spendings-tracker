"""User-session harvest adapter. Session file lives on the data volume."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from spendings_tracker.app.errors import AppError
from spendings_tracker.ports.harvest import FamilyGroupMessage

MONTH_NOT_OBTAINED = "harvest.month_not_obtained"


class FamilyGroupReader(Protocol):
    def read_completed_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        """Return messages for the month, or raise if the month cannot be read."""
        ...


class TelegramHarvest:
    def __init__(self, reader: FamilyGroupReader, *, session_path: Path) -> None:
        self._reader = reader
        self.session_path = session_path

    def harvest_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        try:
            messages = self._reader.read_completed_month(utc_month)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                MONTH_NOT_OBTAINED, "That month could not be obtained."
            ) from exc
        if not messages:
            raise AppError(MONTH_NOT_OBTAINED, "That month could not be obtained.")
        return list(messages)
