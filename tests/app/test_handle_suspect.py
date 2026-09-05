from __future__ import annotations

from dataclasses import replace

import pytest

from spendings_tracker.app.errors import AppError
from spendings_tracker.app.handle_suspect import handle_suspect
from spendings_tracker.domain.draft import HandleChoice
from spendings_tracker.ports.persistence import (
    Category,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredDraftLine,
)


def _line(
    line_id: str,
    shop: str,
    *,
    amount: str | None = None,
    category_id: str | None = None,
) -> StoredDraftLine:
    return StoredDraftLine(
        id=line_id,
        source_message_id="msg-1",
        source_line_index=0,
        line_text=f"{shop} 12.00",
        shop_display=shop,
        shop_key=shop.lower(),
        amount=amount,
        currency="EUR",
        category_id=category_id,
        is_excluded=False,
        is_handled=False,
    )


class FakePersistence:
    def __init__(self, *, settings: Settings | None, draft: StoredDraft | None) -> None:
        self.settings = settings
        self.draft = draft
        self.mappings: dict[str, ShopMapping] = {}

    def save_first_run(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_settings(self) -> Settings | None:
        return self.settings

    def upsert_shop_mapping(
        self, shop_display: str, category_id: str | None
    ) -> ShopMapping:
        from spendings_tracker.domain.shop import shop_key

        key = shop_key(shop_display)
        mapping = ShopMapping(
            id="map-1",
            shop_key=key,
            shop_display=shop_display.strip(),
            category_id=category_id,
            created_at="2026-09-05T12:00:00Z",
        )
        self.mappings[key] = mapping
        return mapping

    def find_shop_mapping(self, shop_display: str) -> ShopMapping | None:
        from spendings_tracker.domain.shop import shop_key

        return self.mappings.get(shop_key(shop_display))

    def list_shop_mappings(self):
        return tuple(self.mappings.values())

    def create_draft(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_draft(self) -> StoredDraft | None:
        return self.draft

    def update_draft_line(self, line: StoredDraftLine) -> StoredDraftLine:
        if self.draft is None:
            raise AppError("save.no_draft")
        updated = []
        for existing in self.draft.lines:
            updated.append(line if existing.id == line.id else existing)
        self.draft = replace(self.draft, lines=tuple(updated))
        return line

    def save_monthly_close(self, *, default_currency: str):
        raise AssertionError("not used")

    def load_monthly_close(self, utc_month: str):
        return None


SETTINGS = Settings(
    id="set-1",
    closer_identity="10001",
    default_currency="EUR",
    created_at="2026-09-05T12:00:00Z",
    categories=(
        Category(
            id="cat-g",
            settings_id="set-1",
            name="Groceries",
            sort_order=0,
            created_at="2026-09-05T12:00:00Z",
        ),
    ),
)


def test_persists_each_handle_choice() -> None:
    missing = _line("l1", "Test Shop", amount=None, category_id="cat-g")
    store = FakePersistence(
        settings=SETTINGS,
        draft=StoredDraft("d1", "2026-08", (missing,), ()),
    )
    updated = handle_suspect(
        store,
        closer_identity="10001",
        draft_line_id="l1",
        choice=HandleChoice.ENTER_AMOUNT,
        amount="9.50",
    )
    assert updated.lines[0].amount == "9.50"
    assert updated.lines[0].is_handled


def test_assign_category_upserts_map_but_not_other_spelling() -> None:
    lidl = _line("l1", "Lidl", amount="12.00")
    store = FakePersistence(
        settings=SETTINGS,
        draft=StoredDraft("d1", "2026-08", (lidl,), ()),
    )
    handle_suspect(
        store,
        closer_identity="10001",
        draft_line_id="l1",
        choice=HandleChoice.ASSIGN_CATEGORY,
        category_id="cat-g",
    )
    assert store.find_shop_mapping(" LIDEL ") is None
    assert store.find_shop_mapping("Lidl") is not None
    assert store.find_shop_mapping("Lidl Express") is None


def test_missing_draft_or_line_returns_contract_codes() -> None:
    empty = FakePersistence(settings=SETTINGS, draft=None)
    with pytest.raises(AppError) as no_draft:
        handle_suspect(
            empty,
            closer_identity="10001",
            draft_line_id="missing",
            choice=HandleChoice.EXCLUDE,
        )
    assert no_draft.value.code == "save.no_draft"

    lined = _line("l1", "Test Shop", amount="12.00")
    store = FakePersistence(
        settings=SETTINGS,
        draft=StoredDraft("d1", "2026-08", (lined,), ()),
    )
    with pytest.raises(AppError) as missing:
        handle_suspect(
            store,
            closer_identity="10001",
            draft_line_id="nope",
            choice=HandleChoice.EXCLUDE,
        )
    assert missing.value.code == "draft.line_not_found"
