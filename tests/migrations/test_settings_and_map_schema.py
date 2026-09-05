from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TABLES = ("settings", "categories", "shop_mappings")
EXPECTED_INDEXES = (
    "uq_settings_closer_identity",
    "idx_categories_settings_id",
    "uq_categories_settings_id_name",
    "uq_shop_mappings_shop_key",
    "idx_shop_mappings_category_id",
)


@pytest.fixture
def ephemeral_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    db_path = tmp_path / "spendings.sqlite"
    monkeypatch.setenv("SPENDINGS_DB_PATH", str(db_path))
    yield db_path


def _alembic_config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    return cfg


def _names(db_path: Path, kind: str) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type = ? AND name NOT LIKE 'sqlite_%'",
            (kind,),
        ).fetchall()
    return {row[0] for row in rows}


def test_upgrade_to_0003_creates_settings_categories_and_shop_mappings(
    ephemeral_db: Path,
) -> None:
    command.upgrade(_alembic_config(), "0003")

    tables = _names(ephemeral_db, "table")
    indexes = _names(ephemeral_db, "index")
    for name in EXPECTED_TABLES:
        assert name in tables
    for name in EXPECTED_INDEXES:
        assert name in indexes

    with sqlite3.connect(ephemeral_db) as conn:
        uncategorized = conn.execute(
            "SELECT COUNT(*) FROM categories WHERE name = 'Uncategorized'"
        ).fetchone()
    assert uncategorized is not None
    assert uncategorized[0] == 0


def test_downgrade_to_0001_removes_settings_categories_and_shop_mappings(
    ephemeral_db: Path,
) -> None:
    command.upgrade(_alembic_config(), "0003")
    command.downgrade(_alembic_config(), "0001")

    tables = _names(ephemeral_db, "table")
    indexes = _names(ephemeral_db, "index")
    for name in EXPECTED_TABLES:
        assert name not in tables
    for name in EXPECTED_INDEXES:
        assert name not in indexes
