from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.sqlite import SqlitePersistence
from spendings_tracker.infra.ulid import is_ulid, new_ulid

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SqlitePersistence:
    db_path = tmp_path / "spendings.sqlite"
    monkeypatch.setenv("SPENDINGS_DB_PATH", str(db_path))
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    command.upgrade(cfg, "0003")
    return SqlitePersistence(db_path)


def test_ulid_is_time_sortable() -> None:
    earlier = new_ulid(now=datetime(2026, 1, 1, tzinfo=UTC))
    later = new_ulid(now=datetime(2026, 1, 2, tzinfo=UTC))
    assert is_ulid(earlier)
    assert is_ulid(later)
    assert earlier < later


def test_round_trips_settings_and_frozen_categories(store: SqlitePersistence) -> None:
    saved = store.save_first_run(
        closer_identity="10001",
        default_currency="EUR",
        category_names=["Groceries", "Transport"],
    )
    loaded = store.load_settings()

    assert loaded is not None
    assert loaded.closer_identity == "10001"
    assert loaded.default_currency == "EUR"
    names = [category.name for category in loaded.categories]
    assert names == ["Groceries", "Transport"]
    assert is_ulid(saved.id)
    assert all(is_ulid(category.id) for category in saved.categories)


def test_refuses_a_second_settings_row(store: SqlitePersistence) -> None:
    store.save_first_run("10001", "EUR", ["Groceries"])
    with pytest.raises(AppError) as err:
        store.save_first_run("10002", "USD", ["Other"])
    assert err.value.code == "settings.already_exists"
    assert err.value.message == "Settings already exist."


def test_shop_mapping_upserts_by_key_and_matches_after_trim_and_case(
    store: SqlitePersistence,
) -> None:
    settings = store.save_first_run("10001", "EUR", ["Groceries"])
    category_id = settings.categories[0].id

    first = store.upsert_shop_mapping(" Lidl ", category_id)
    again = store.upsert_shop_mapping("LIDL", category_id)
    found = store.find_shop_mapping(" lidl ")
    other = store.find_shop_mapping("Lidl Express")

    assert first.shop_key == "lidl"
    assert again.id == first.id
    assert found is not None
    assert found.category_id == category_id
    assert other is None
    assert is_ulid(first.id)
