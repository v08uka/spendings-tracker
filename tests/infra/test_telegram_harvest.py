from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.telegram_harvest import TelegramHarvest
from spendings_tracker.ports.harvest import FamilyGroupMessage, HarvestPort


class FakeReader:
    def __init__(
        self,
        messages: list[FamilyGroupMessage] | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.messages = messages or []
        self.error = error
        self.calls: list[str] = []

    def read_completed_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        self.calls.append(utc_month)
        if self.error is not None:
            raise self.error
        return list(self.messages)


def test_harvest_port_has_no_export_file_parameter() -> None:
    params = inspect.signature(HarvestPort.harvest_month).parameters
    assert "utc_month" in params
    assert all("export" not in name for name in params)


def test_returns_the_whole_month_including_more_than_500() -> None:
    messages = [
        FamilyGroupMessage(id=str(i), text=f"msg {i}") for i in range(501)
    ]
    reader = FakeReader(messages)
    harvest: HarvestPort = TelegramHarvest(
        reader, session_path=Path("/data/telegram.session")
    )

    obtained = harvest.harvest_month("2026-08")

    assert obtained == messages
    assert len(obtained) == 501
    assert reader.calls == ["2026-08"]


def test_unreadable_month_becomes_month_not_obtained() -> None:
    harvest = TelegramHarvest(
        FakeReader(error=OSError("session unreadable")),
        session_path=Path("/data/telegram.session"),
    )

    with pytest.raises(AppError) as err:
        harvest.harvest_month("2026-08")
    assert err.value.code == "harvest.month_not_obtained"
    assert err.value.message == "That month could not be obtained."


def test_month_with_no_family_group_messages_is_not_obtained() -> None:
    harvest = TelegramHarvest(
        FakeReader([]),
        session_path=Path("/data/telegram.session"),
    )

    with pytest.raises(AppError) as err:
        harvest.harvest_month("2026-08")
    assert err.value.code == "harvest.month_not_obtained"
    assert err.value.message == "That month could not be obtained."
