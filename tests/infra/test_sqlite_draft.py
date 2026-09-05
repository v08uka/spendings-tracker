from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.sqlite import SqlitePersistence
from spendings_tracker.ports.persistence import NewDraftLine

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "spendings.sqlite"
    monkeypatch.setenv("SPENDINGS_DB_PATH", str(path))
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    command.upgrade(cfg, "head")
    return path


def _store(db_path: Path) -> tuple[SqlitePersistence, str]:
    store = SqlitePersistence(db_path)
    settings = store.save_first_run("10001", "EUR", ["Groceries"])
    return store, settings.categories[0].id


def test_round_trips_one_draft_with_several_lines_after_reconnect(
    db_path: Path,
) -> None:
    store, category_id = _store(db_path)
    store.create_draft(
        utc_month="2026-08",
        lines=[
            NewDraftLine(
                source_message_id="msg-1",
                source_line_index=0,
                line_text="Test Shop 12.00",
                shop_display="Test Shop",
                shop_key="test shop",
                amount="12.00",
                currency="EUR",
                category_id=category_id,
            ),
            NewDraftLine(
                source_message_id="msg-1",
                source_line_index=1,
                line_text="Other Shop 8.50",
                shop_display="Other Shop",
                shop_key="other shop",
                amount="8.50",
                currency="EUR",
                category_id=None,
            ),
        ],
        egress_texts=["Test Shop 12.00"],
    )

    reloaded = SqlitePersistence(db_path).load_draft()
    assert reloaded is not None
    assert reloaded.utc_month == "2026-08"
    assert [line.source_line_index for line in reloaded.lines] == [0, 1]
    assert [line.line_text for line in reloaded.lines] == [
        "Test Shop 12.00",
        "Other Shop 8.50",
    ]
    assert [row.line_text for row in reloaded.egress_lines] == ["Test Shop 12.00"]


def test_refuses_a_second_draft(db_path: Path) -> None:
    store, _ = _store(db_path)
    store.create_draft("2026-08", [], [])
    with pytest.raises(AppError) as err:
        store.create_draft("2026-07", [], [])
    assert err.value.code == "harvest.draft_in_progress"
    assert err.value.message == "Finish or replace the in-progress close first."


def test_save_replaces_close_for_same_month_and_copies_egress(db_path: Path) -> None:
    store, category_id = _store(db_path)
    store.create_draft(
        utc_month="2026-08",
        lines=[
            NewDraftLine(
                source_message_id="msg-1",
                source_line_index=0,
                line_text="Test Shop 12.00",
                shop_display="Test Shop",
                shop_key="test shop",
                amount="12.00",
                currency="EUR",
                category_id=category_id,
            )
        ],
        egress_texts=["Test Shop 12.00"],
    )
    first = store.save_monthly_close(default_currency="EUR")
    store.create_draft(
        utc_month="2026-08",
        lines=[
            NewDraftLine(
                source_message_id="msg-2",
                source_line_index=0,
                line_text="Test Shop 4.00",
                shop_display="Test Shop",
                shop_key="test shop",
                amount="4.00",
                currency="EUR",
                category_id=category_id,
            )
        ],
        egress_texts=["Test Shop 4.00"],
    )
    second = store.save_monthly_close(default_currency="EUR")

    loaded = store.load_monthly_close("2026-08")
    assert loaded is not None
    assert loaded.id == second.id
    assert loaded.id != first.id
    assert [line.line_text for line in loaded.lines] == ["Test Shop 4.00"]
    assert [row.line_text for row in loaded.egress_lines] == ["Test Shop 4.00"]
    assert store.load_draft() is None
