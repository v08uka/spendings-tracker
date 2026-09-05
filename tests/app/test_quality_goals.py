from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from spendings_tracker.__main__ import build_runtime
from spendings_tracker.app.harvest_month import harvest_month
from spendings_tracker.app.resume import resume
from spendings_tracker.infra.sqlite import SqlitePersistence
from spendings_tracker.infra.telegram_session import TelethonFamilyGroupReader
from spendings_tracker.infra.uncategorized_vendor import UncategorizedVendor
from spendings_tracker.ports.harvest import FamilyGroupMessage
from spendings_tracker.ports.persistence import NewDraftLine

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 5, tzinfo=UTC)


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "spendings.sqlite"
    monkeypatch.setenv("SPENDINGS_DB_PATH", str(path))
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    command.upgrade(cfg, "head")
    return path


class FakeHarvest:
    def __init__(self, messages: list[FamilyGroupMessage]) -> None:
        self.messages = messages

    def harvest_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        return list(self.messages)


class RecordingModel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        self.sent.extend(lines)
        return ["Uncategorized"] * len(lines)


def test_qg1_egress_equals_model_send_and_excludes_other_talk(
    db_path: Path,
) -> None:
    store = SqlitePersistence(db_path)
    store.save_first_run("10001", "EUR", ["Groceries"])
    model = RecordingModel()
    messages = [
        FamilyGroupMessage("1", "lol that was funny"),
        FamilyGroupMessage("2", "Test Shop 12.00"),
        FamilyGroupMessage("3", "ok see you"),
    ]
    result = harvest_month(
        store, FakeHarvest(messages), model, "2026-08", now=NOW
    )
    assert model.sent == ["Test Shop 12.00"]
    assert [row.line_text for row in result.draft.egress_lines] == model.sent
    assert all("lol" not in row.line_text for row in result.draft.egress_lines)


def test_qg2_five_hundred_messages_draft_within_180_seconds(
    db_path: Path,
) -> None:
    store = SqlitePersistence(db_path)
    store.save_first_run("10001", "EUR", ["Groceries"])
    messages = [
        FamilyGroupMessage(str(i), f"Test Shop {i}.00") for i in range(500)
    ]
    started = time.perf_counter()
    result = harvest_month(
        store, FakeHarvest(messages), RecordingModel(), "2026-08", now=NOW
    )
    elapsed = time.perf_counter() - started
    assert len(result.draft.lines) == 500
    assert elapsed <= 180


def test_qg2_more_than_500_is_complete_without_time_bound(
    db_path: Path,
) -> None:
    store = SqlitePersistence(db_path)
    store.save_first_run("10001", "EUR", ["Groceries"])
    messages = [
        FamilyGroupMessage(str(i), f"Test Shop {i}.00") for i in range(501)
    ]
    result = harvest_month(
        store, FakeHarvest(messages), RecordingModel(), "2026-08", now=NOW
    )
    assert len(result.draft.lines) == 501


def test_qg3_stop_start_against_real_sqlite_restores_state(
    db_path: Path,
) -> None:
    first = SqlitePersistence(db_path)
    settings = first.save_first_run("10001", "EUR", ["Groceries"])
    first.upsert_shop_mapping("Lidl", settings.categories[0].id)
    first.create_draft(
        "2026-08",
        [
            NewDraftLine(
                source_message_id="msg-1",
                source_line_index=0,
                line_text="Test Shop 12.00",
                shop_display="Test Shop",
                shop_key="test shop",
                amount="12.00",
                currency="EUR",
                category_id=settings.categories[0].id,
                is_handled=True,
            )
        ],
        [],
    )
    first.save_monthly_close(default_currency="EUR")
    first.create_draft(
        "2026-07",
        [
            NewDraftLine(
                source_message_id="msg-2",
                source_line_index=0,
                line_text="Other Shop 4.00",
                shop_display="Other Shop",
                shop_key="other shop",
                amount="4.00",
                currency="EUR",
                category_id=None,
                is_handled=True,
            )
        ],
        [],
    )

    later = SqlitePersistence(db_path)
    result = resume(later)
    assert result.kind == "draft"
    assert result.settings is not None
    assert result.settings.default_currency == "EUR"
    assert result.settings.categories[0].name == "Groceries"
    assert result.shop_mappings[0].shop_key == "lidl"
    assert result.saved_close is not None
    assert result.saved_close.utc_month == "2026-08"
    assert result.draft is not None
    assert result.draft.lines[0].is_handled is True


def test_build_runtime_constructs_and_injects_adapters(tmp_path: Path) -> None:
    bot = build_runtime(tmp_path / "spendings.sqlite", tmp_path / "telegram.session")
    assert bot._persistence is not None
    assert bot._harvest is not None
    assert bot._model is not None
    assert isinstance(bot._harvest._reader, TelethonFamilyGroupReader)
    assert isinstance(bot._model._vendor, UncategorizedVendor)
    assert type(bot._harvest._reader).__name__ != "NullFamilyGroupReader"
    assert type(bot._model._vendor).__name__ != "NullVendor"
