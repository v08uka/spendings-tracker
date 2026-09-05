"""SQLite persistence adapter. One writer on the state file."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from spendings_tracker.app.errors import catalog_error
from spendings_tracker.domain.shop import shop_key
from spendings_tracker.infra.ulid import new_ulid
from spendings_tracker.ports.persistence import (
    Category,
    NewDraftLine,
    Settings,
    ShopMapping,
    StoredCloseLine,
    StoredDraft,
    StoredDraftLine,
    StoredEgressLine,
    StoredMonthlyClose,
)


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

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_first_run(
        self,
        closer_identity: str,
        default_currency: str,
        category_names: list[str],
    ) -> Settings:
        created_at = _now()
        settings_id = new_ulid()
        with self._db() as conn:
            existing = conn.execute("SELECT id FROM settings LIMIT 1").fetchone()
            if existing is not None:
                raise catalog_error("settings.already_exists")
            categories: list[Category] = []
            try:
                conn.execute(
                    "INSERT INTO settings"
                    " (id, closer_identity, default_currency, created_at)"
                    " VALUES (?, ?, ?, ?)",
                    (settings_id, closer_identity, default_currency, created_at),
                )
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
            except sqlite3.IntegrityError as exc:
                raise catalog_error("first_run.empty_category_list") from exc
        return Settings(
            id=settings_id,
            closer_identity=closer_identity,
            default_currency=default_currency,
            created_at=created_at,
            categories=tuple(categories),
        )

    def load_settings(self) -> Settings | None:
        with self._db() as conn:
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
        with self._db() as conn:
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
        with self._db() as conn:
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

    def list_shop_mappings(self) -> tuple[ShopMapping, ...]:
        with self._db() as conn:
            rows = conn.execute(
                "SELECT id, shop_key, shop_display, category_id, created_at"
                " FROM shop_mappings ORDER BY shop_key"
            ).fetchall()
        return tuple(
            ShopMapping(
                id=row["id"],
                shop_key=row["shop_key"],
                shop_display=row["shop_display"],
                category_id=row["category_id"],
                created_at=row["created_at"],
            )
            for row in rows
        )

    def create_draft(
        self,
        utc_month: str,
        lines: list[NewDraftLine],
        egress_texts: list[str],
    ) -> StoredDraft:
        created_at = _now()
        draft_id = new_ulid()
        with self._db() as conn:
            if conn.execute("SELECT id FROM drafts LIMIT 1").fetchone() is not None:
                raise catalog_error("harvest.draft_in_progress")
            conn.execute(
                "INSERT INTO drafts (id, utc_month, created_at) VALUES (?, ?, ?)",
                (draft_id, utc_month, created_at),
            )
            stored_lines: list[StoredDraftLine] = []
            for line in lines:
                stored = StoredDraftLine(
                    id=new_ulid(),
                    source_message_id=line.source_message_id,
                    source_line_index=line.source_line_index,
                    line_text=line.line_text,
                    shop_display=line.shop_display,
                    shop_key=line.shop_key,
                    amount=line.amount,
                    currency=line.currency,
                    category_id=line.category_id,
                    is_excluded=line.is_excluded,
                    is_handled=line.is_handled,
                )
                conn.execute(
                    "INSERT INTO draft_lines ("
                    " id, draft_id, source_message_id, source_line_index,"
                    " line_text, shop_display, shop_key, amount, currency,"
                    " category_id, is_excluded, is_handled, created_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        stored.id,
                        draft_id,
                        stored.source_message_id,
                        stored.source_line_index,
                        stored.line_text,
                        stored.shop_display,
                        stored.shop_key,
                        stored.amount,
                        stored.currency,
                        stored.category_id,
                        int(stored.is_excluded),
                        int(stored.is_handled),
                        created_at,
                    ),
                )
                stored_lines.append(stored)
            egress: list[StoredEgressLine] = []
            for text in egress_texts:
                row = StoredEgressLine(
                    id=new_ulid(),
                    line_text=text,
                    draft_id=draft_id,
                    monthly_close_id=None,
                )
                conn.execute(
                    "INSERT INTO egress_lines"
                    " (id, draft_id, monthly_close_id, line_text, created_at)"
                    " VALUES (?, ?, NULL, ?, ?)",
                    (row.id, draft_id, text, created_at),
                )
                egress.append(row)
        return StoredDraft(
            id=draft_id,
            utc_month=utc_month,
            lines=tuple(stored_lines),
            egress_lines=tuple(egress),
        )

    def load_draft(self) -> StoredDraft | None:
        with self._db() as conn:
            draft = conn.execute(
                "SELECT id, utc_month FROM drafts LIMIT 1"
            ).fetchone()
            if draft is None:
                return None
            line_rows = conn.execute(
                "SELECT id, source_message_id, source_line_index, line_text,"
                " shop_display, shop_key, amount, currency, category_id,"
                " is_excluded, is_handled FROM draft_lines"
                " WHERE draft_id = ? ORDER BY source_line_index",
                (draft["id"],),
            ).fetchall()
            egress_rows = conn.execute(
                "SELECT id, line_text, draft_id, monthly_close_id"
                " FROM egress_lines WHERE draft_id = ?",
                (draft["id"],),
            ).fetchall()
        return StoredDraft(
            id=draft["id"],
            utc_month=draft["utc_month"],
            lines=tuple(_draft_line(row) for row in line_rows),
            egress_lines=tuple(_egress_line(row) for row in egress_rows),
        )

    def update_draft_line(self, line: StoredDraftLine) -> StoredDraftLine:
        with self._db() as conn:
            conn.execute(
                "UPDATE draft_lines SET amount = ?, currency = ?, category_id = ?,"
                " is_excluded = ?, is_handled = ? WHERE id = ?",
                (
                    line.amount,
                    line.currency,
                    line.category_id,
                    int(line.is_excluded),
                    int(line.is_handled),
                    line.id,
                ),
            )
        return line

    def save_monthly_close(self, *, default_currency: str) -> StoredMonthlyClose:
        draft = self.load_draft()
        if draft is None:
            raise catalog_error("save.no_draft")
        created_at = _now()
        close_id = new_ulid()
        with self._db() as conn:
            existing = conn.execute(
                "SELECT id FROM monthly_closes WHERE utc_month = ?",
                (draft.utc_month,),
            ).fetchone()
            if existing is not None:
                conn.execute(
                    "DELETE FROM monthly_closes WHERE id = ?", (existing["id"],)
                )
            conn.execute(
                "INSERT INTO monthly_closes"
                " (id, utc_month, default_currency, created_at)"
                " VALUES (?, ?, ?, ?)",
                (close_id, draft.utc_month, default_currency, created_at),
            )
            close_lines: list[StoredCloseLine] = []
            for line in draft.lines:
                if line.is_excluded:
                    continue
                stored = StoredCloseLine(
                    id=new_ulid(),
                    line_text=line.line_text,
                    source_message_id=line.source_message_id,
                    source_line_index=line.source_line_index,
                    shop_display=line.shop_display,
                    shop_key=line.shop_key,
                    amount=line.amount,
                    currency=line.currency,
                    category_id=line.category_id,
                )
                conn.execute(
                    "INSERT INTO monthly_close_lines ("
                    " id, monthly_close_id, source_message_id, source_line_index,"
                    " line_text, shop_display, shop_key, amount, currency,"
                    " category_id, created_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        stored.id,
                        close_id,
                        stored.source_message_id,
                        stored.source_line_index,
                        stored.line_text,
                        stored.shop_display,
                        stored.shop_key,
                        stored.amount,
                        stored.currency,
                        stored.category_id,
                        created_at,
                    ),
                )
                close_lines.append(stored)
            egress: list[StoredEgressLine] = []
            for row in draft.egress_lines:
                copied = StoredEgressLine(
                    id=new_ulid(),
                    line_text=row.line_text,
                    draft_id=None,
                    monthly_close_id=close_id,
                )
                conn.execute(
                    "INSERT INTO egress_lines"
                    " (id, draft_id, monthly_close_id, line_text, created_at)"
                    " VALUES (?, NULL, ?, ?, ?)",
                    (copied.id, close_id, copied.line_text, created_at),
                )
                egress.append(copied)
            conn.execute("DELETE FROM drafts WHERE id = ?", (draft.id,))
        return StoredMonthlyClose(
            id=close_id,
            utc_month=draft.utc_month,
            default_currency=default_currency,
            lines=tuple(close_lines),
            egress_lines=tuple(egress),
        )

    def load_monthly_close(self, utc_month: str) -> StoredMonthlyClose | None:
        with self._db() as conn:
            close = conn.execute(
                "SELECT id, utc_month, default_currency FROM monthly_closes"
                " WHERE utc_month = ?",
                (utc_month,),
            ).fetchone()
            if close is None:
                return None
            line_rows = conn.execute(
                "SELECT id, line_text, source_message_id, source_line_index,"
                " shop_display, shop_key, amount, currency, category_id"
                " FROM monthly_close_lines WHERE monthly_close_id = ?"
                " ORDER BY source_line_index",
                (close["id"],),
            ).fetchall()
            egress_rows = conn.execute(
                "SELECT id, line_text, draft_id, monthly_close_id"
                " FROM egress_lines WHERE monthly_close_id = ?",
                (close["id"],),
            ).fetchall()
        return StoredMonthlyClose(
            id=close["id"],
            utc_month=close["utc_month"],
            default_currency=close["default_currency"],
            lines=tuple(
                StoredCloseLine(
                    id=row["id"],
                    line_text=row["line_text"],
                    source_message_id=row["source_message_id"],
                    source_line_index=row["source_line_index"],
                    shop_display=row["shop_display"],
                    shop_key=row["shop_key"],
                    amount=row["amount"],
                    currency=row["currency"],
                    category_id=row["category_id"],
                )
                for row in line_rows
            ),
            egress_lines=tuple(_egress_line(row) for row in egress_rows),
        )

    def load_latest_monthly_close(self) -> StoredMonthlyClose | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT utc_month FROM monthly_closes ORDER BY utc_month DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return self.load_monthly_close(row["utc_month"])


def _draft_line(row: sqlite3.Row) -> StoredDraftLine:
    return StoredDraftLine(
        id=row["id"],
        source_message_id=row["source_message_id"],
        source_line_index=row["source_line_index"],
        line_text=row["line_text"],
        shop_display=row["shop_display"],
        shop_key=row["shop_key"],
        amount=row["amount"],
        currency=row["currency"],
        category_id=row["category_id"],
        is_excluded=bool(row["is_excluded"]),
        is_handled=bool(row["is_handled"]),
    )


def _egress_line(row: sqlite3.Row) -> StoredEgressLine:
    return StoredEgressLine(
        id=row["id"],
        line_text=row["line_text"],
        draft_id=row["draft_id"],
        monthly_close_id=row["monthly_close_id"],
    )
