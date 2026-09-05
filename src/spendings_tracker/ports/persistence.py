"""Persistence port for settings, the shop map, drafts, and saved closes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Category:
    id: str
    settings_id: str
    name: str
    sort_order: int
    created_at: str


@dataclass(frozen=True)
class Settings:
    id: str
    closer_identity: str
    default_currency: str
    created_at: str
    categories: tuple[Category, ...]


@dataclass(frozen=True)
class ShopMapping:
    id: str
    shop_key: str
    shop_display: str
    category_id: str | None
    created_at: str


@dataclass(frozen=True)
class NewDraftLine:
    source_message_id: str
    source_line_index: int
    line_text: str
    shop_display: str
    shop_key: str
    amount: str | None
    currency: str
    category_id: str | None
    is_excluded: bool = False
    is_handled: bool = False


@dataclass(frozen=True)
class StoredDraftLine:
    id: str
    source_message_id: str
    source_line_index: int
    line_text: str
    shop_display: str
    shop_key: str
    amount: str | None
    currency: str
    category_id: str | None
    is_excluded: bool
    is_handled: bool


@dataclass(frozen=True)
class StoredEgressLine:
    id: str
    line_text: str
    draft_id: str | None
    monthly_close_id: str | None


@dataclass(frozen=True)
class StoredDraft:
    id: str
    utc_month: str
    lines: tuple[StoredDraftLine, ...]
    egress_lines: tuple[StoredEgressLine, ...]


@dataclass(frozen=True)
class StoredCloseLine:
    id: str
    line_text: str
    source_message_id: str
    source_line_index: int
    shop_display: str
    shop_key: str
    amount: str | None
    currency: str
    category_id: str | None


@dataclass(frozen=True)
class StoredMonthlyClose:
    id: str
    utc_month: str
    default_currency: str
    lines: tuple[StoredCloseLine, ...]
    egress_lines: tuple[StoredEgressLine, ...]


class PersistencePort(Protocol):
    def save_first_run(
        self,
        closer_identity: str,
        default_currency: str,
        category_names: list[str],
    ) -> Settings: ...

    def load_settings(self) -> Settings | None: ...

    def upsert_shop_mapping(
        self, shop_display: str, category_id: str | None
    ) -> ShopMapping: ...

    def find_shop_mapping(self, shop_display: str) -> ShopMapping | None: ...

    def list_shop_mappings(self) -> tuple[ShopMapping, ...]: ...

    def create_draft(
        self,
        utc_month: str,
        lines: list[NewDraftLine],
        egress_texts: list[str],
    ) -> StoredDraft: ...

    def load_draft(self) -> StoredDraft | None: ...

    def update_draft_line(self, line: StoredDraftLine) -> StoredDraftLine: ...

    def save_monthly_close(self, *, default_currency: str) -> StoredMonthlyClose: ...

    def load_monthly_close(self, utc_month: str) -> StoredMonthlyClose | None: ...

    def load_latest_monthly_close(self) -> StoredMonthlyClose | None: ...
