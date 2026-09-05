from __future__ import annotations

import pytest

from spendings_tracker.app.complete_first_run import (
    complete_first_run,
    require_first_run,
)
from spendings_tracker.app.errors import AppError
from spendings_tracker.ports.persistence import Category, Settings


class FakePersistence:
    def __init__(self) -> None:
        self.settings: Settings | None = None
        self.drafts_started = 0

    def save_first_run(
        self,
        closer_identity: str,
        default_currency: str,
        category_names: list[str],
    ) -> Settings:
        categories = tuple(
            Category(
                id=f"cat-{index}",
                settings_id="set-1",
                name=name,
                sort_order=index,
                created_at="2026-09-05T12:00:00Z",
            )
            for index, name in enumerate(category_names)
        )
        self.settings = Settings(
            id="set-1",
            closer_identity=closer_identity,
            default_currency=default_currency,
            created_at="2026-09-05T12:00:00Z",
            categories=categories,
        )
        return self.settings

    def load_settings(self) -> Settings | None:
        return self.settings

    def upsert_shop_mapping(self, shop_display: str, category_id: str | None):
        raise AssertionError("not used")

    def find_shop_mapping(self, shop_display: str):
        raise AssertionError("not used")


def test_confirm_records_currency_frozen_list_and_closer_pin() -> None:
    store = FakePersistence()

    result = complete_first_run(
        store,
        closer_identity="10001",
        default_currency="",
        category_names=["Groceries", "Transport"],
    )

    assert result.closer_identity == "10001"
    assert result.default_currency == "EUR"
    assert [category.name for category in result.categories] == [
        "Groceries",
        "Transport",
    ]
    assert store.settings is result


def test_empty_category_list_does_not_finish_first_run() -> None:
    store = FakePersistence()

    with pytest.raises(AppError) as err:
        complete_first_run(
            store,
            closer_identity="10001",
            default_currency="EUR",
            category_names=["Uncategorized"],
        )

    assert err.value.code == "first_run.empty_category_list"
    assert store.settings is None


def test_month_request_before_first_run_is_refused() -> None:
    store = FakePersistence()

    with pytest.raises(AppError) as err:
        require_first_run(store)

    assert err.value.code == "first_run.still_required"
    assert store.drafts_started == 0
