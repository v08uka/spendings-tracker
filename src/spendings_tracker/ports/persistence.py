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
