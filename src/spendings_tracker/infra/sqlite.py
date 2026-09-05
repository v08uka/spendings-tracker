"""SQLite persistence adapter. One writer on the state file."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.shop import shop_key
from spendings_tracker.infra.ulid import new_ulid
from spendings_tracker.ports.persistence import Category, Settings, ShopMapping


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SqlitePersistence:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def save_first_run(
        self,
        closer_identity: str,
        default_currency: str,
        category_names: list[str],
    ) -> Settings:
        created_at = _now()
        settings_id = new_ulid()
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM settings LIMIT 1").fetchone()
            if existing is not None:
                raise AppError("settings.already_exists")
            conn.execute(
                "INSERT INTO settings"
                " (id, closer_identity, default_currency, created_at)"
                " VALUES (?, ?, ?, ?)",
                (settings_id, closer_identity, default_currency, created_at),
            )
            categories: list[Category] = []
            for sort_order, name in enumerate(category_names):
                category = Category(
                    id=new_ulid(),
                    settings_id=settings_id,
                    name=name,
                    sort_order=sort_order,
                    created_at=created_at,
                )
                conn.execute(
                    "INSERT INTO categories"
                    " (id, settings_id, name, sort_order, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        category.id,
                        category.settings_id,
                        category.name,
                        category.sort_order,
                        category.created_at,
                    ),
                )
                categories.append(category)
        return Settings(
            id=settings_id,
            closer_identity=closer_identity,
            default_currency=default_currency,
            created_at=created_at,
            categories=tuple(categories),
        )

    def load_settings(self) -> Settings | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, closer_identity, default_currency, created_at FROM settings"
                " LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            category_rows = conn.execute(
                "SELECT id, settings_id, name, sort_order, created_at FROM categories"
                " WHERE settings_id = ? ORDER BY sort_order",
                (row["id"],),
            ).fetchall()
        categories = tuple(
            Category(
                id=item["id"],
                settings_id=item["settings_id"],
                name=item["name"],
                sort_order=item["sort_order"],
                created_at=item["created_at"],
            )
            for item in category_rows
        )
        return Settings(
            id=row["id"],
            closer_identity=row["closer_identity"],
            default_currency=row["default_currency"],
            created_at=row["created_at"],
            categories=categories,
        )

    def upsert_shop_mapping(
        self, shop_display: str, category_id: str | None
    ) -> ShopMapping:
        key = shop_key(shop_display)
        display = shop_display.strip()
        created_at = _now()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, shop_key, shop_display, category_id, created_at"
                " FROM shop_mappings WHERE shop_key = ?",
                (key,),
            ).fetchone()
            if existing is None:
                mapping = ShopMapping(
                    id=new_ulid(),
                    shop_key=key,
                    shop_display=display,
                    category_id=category_id,
                    created_at=created_at,
                )
                conn.execute(
                    "INSERT INTO shop_mappings"
                    " (id, shop_key, shop_display, category_id, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        mapping.id,
                        mapping.shop_key,
                        mapping.shop_display,
                        mapping.category_id,
                        mapping.created_at,
                    ),
                )
                return mapping
            conn.execute(
                "UPDATE shop_mappings SET shop_display = ?, category_id = ?"
                " WHERE shop_key = ?",
                (display, category_id, key),
            )
            return ShopMapping(
                id=existing["id"],
                shop_key=key,
                shop_display=display,
                category_id=category_id,
                created_at=existing["created_at"],
            )

    def find_shop_mapping(self, shop_display: str) -> ShopMapping | None:
        key = shop_key(shop_display)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, shop_key, shop_display, category_id, created_at"
                " FROM shop_mappings WHERE shop_key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return ShopMapping(
            id=row["id"],
            shop_key=row["shop_key"],
            shop_display=row["shop_display"],
            category_id=row["category_id"],
            created_at=row["created_at"],
        )
