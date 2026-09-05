from __future__ import annotations

from datetime import UTC, datetime

import pytest

from spendings_tracker.app.errors import AppError
from spendings_tracker.app.harvest_month import harvest_month
from spendings_tracker.ports.harvest import FamilyGroupMessage
from spendings_tracker.ports.persistence import (
    Category,
    NewDraftLine,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredDraftLine,
    StoredEgressLine,
    StoredMonthlyClose,
)

NOW = datetime(2026, 9, 5, tzinfo=UTC)
GROCERIES = "cat-g"


class FakeHarvest:
    def __init__(
        self,
        messages: list[FamilyGroupMessage] | None = None,
        *,
        error: AppError | None = None,
    ) -> None:
        self.messages = messages or []
        self.error = error

    def harvest_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        if self.error is not None:
            raise self.error
        return list(self.messages)


class FakeModel:
    def __init__(self, names: list[str] | None = None) -> None:
        self.names = names or []
        self.sent: list[list[str]] = []

    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        self.sent.append(list(lines))
        return list(self.names)


class FakePersistence:
    def __init__(
        self, *, settings: Settings | None, mapping: ShopMapping | None = None
    ) -> None:
        self.settings = settings
        self.mapping = mapping
        self.draft: StoredDraft | None = None
        self.created: list[tuple[str, list[NewDraftLine], list[str]]] = []

    def save_first_run(self, closer_identity, default_currency, category_names):
        raise AssertionError("not used")

    def load_settings(self) -> Settings | None:
        return self.settings

    def upsert_shop_mapping(self, shop_display, category_id):
        raise AssertionError("not used")

    def find_shop_mapping(self, shop_display: str) -> ShopMapping | None:
        if self.mapping is None:
            return None
        from spendings_tracker.domain.shop import shop_key

        if shop_key(shop_display) == self.mapping.shop_key:
            return self.mapping
        return None

    def list_shop_mappings(self):
        return (self.mapping,) if self.mapping else ()

    def create_draft(self, utc_month, lines, egress_texts) -> StoredDraft:
        if self.draft is not None:
            raise AppError("harvest.draft_in_progress")
        stored_lines = tuple(
            StoredDraftLine(
                id=f"line-{index}",
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
            for index, line in enumerate(lines)
        )
        egress = tuple(
            StoredEgressLine(
                id=f"eg-{index}",
                line_text=text,
                draft_id="draft-1",
                monthly_close_id=None,
            )
            for index, text in enumerate(egress_texts)
        )
        self.draft = StoredDraft(
            id="draft-1",
            utc_month=utc_month,
            lines=stored_lines,
            egress_lines=egress,
        )
        self.created.append((utc_month, list(lines), list(egress_texts)))
        return self.draft

    def load_draft(self) -> StoredDraft | None:
        return self.draft

    def update_draft_line(self, line):
        raise AssertionError("not used")

    def save_monthly_close(self, *, default_currency: str) -> StoredMonthlyClose:
        raise AssertionError("not used")

    def load_monthly_close(self, utc_month: str):
        return None


def _settings() -> Settings:
    return Settings(
        id="set-1",
        closer_identity="10001",
        default_currency="EUR",
        created_at="2026-09-05T12:00:00Z",
        categories=(
            Category(
                id=GROCERIES,
                settings_id="set-1",
                name="Groceries",
                sort_order=0,
                created_at="2026-09-05T12:00:00Z",
            ),
        ),
    )


def test_refuses_incomplete_month() -> None:
    with pytest.raises(AppError) as err:
        harvest_month(
            FakePersistence(settings=_settings()),
            FakeHarvest([FamilyGroupMessage("1", "Test Shop 12")]),
            FakeModel(),
            "2026-09",
            now=NOW,
        )
    assert err.value.code == "harvest.incomplete_month"


def test_refuses_second_draft() -> None:
    store = FakePersistence(settings=_settings())
    store.draft = StoredDraft(id="d", utc_month="2026-07", lines=(), egress_lines=())
    with pytest.raises(AppError) as err:
        harvest_month(
            store,
            FakeHarvest([FamilyGroupMessage("1", "Test Shop 12")]),
            FakeModel(),
            "2026-08",
            now=NOW,
        )
    assert err.value.code == "harvest.draft_in_progress"


def test_unreadable_month_is_not_obtained() -> None:
    with pytest.raises(AppError) as err:
        harvest_month(
            FakePersistence(settings=_settings()),
            FakeHarvest(error=AppError("harvest.month_not_obtained")),
            FakeModel(),
            "2026-08",
            now=NOW,
        )
    assert err.value.code == "harvest.month_not_obtained"


def test_splits_pairs_skips_mapped_shop_and_sends_unmapped_only() -> None:
    mapping = ShopMapping(
        id="map-1",
        shop_key="test shop",
        shop_display="Test Shop",
        category_id=GROCERIES,
        created_at="2026-09-05T12:00:00Z",
    )
    store = FakePersistence(settings=_settings(), mapping=mapping)
    model = FakeModel(names=["Uncategorized"])
    result = harvest_month(
        store,
        FakeHarvest(
            [FamilyGroupMessage("msg-1", "Test Shop 12.00 Other Shop 8.50")]
        ),
        model,
        "2026-08",
        now=NOW,
    )

    assert [line.line_text for line in result.draft.lines] == [
        "Test Shop 12.00",
        "Other Shop 8.50",
    ]
    assert model.sent == [["Other Shop 8.50"]]
    assert [row.line_text for row in result.draft.egress_lines] == ["Other Shop 8.50"]
    assert result.draft.lines[0].category_id == GROCERIES
    assert result.draft.lines[1].category_id is None


def test_empty_spend_looking_month_is_saveable_empty_draft() -> None:
    store = FakePersistence(settings=_settings())
    result = harvest_month(
        store,
        FakeHarvest([FamilyGroupMessage("1", "lol dinner jokes")]),
        FakeModel(),
        "2026-08",
        now=NOW,
    )
    assert result.is_empty is True
    assert result.draft.lines == ()
    assert result.draft.egress_lines == ()
    assert result.suspect_count == 0


def test_source_line_index_is_per_message_pair_index() -> None:
    store = FakePersistence(settings=_settings())
    model = FakeModel(names=["Uncategorized", "Uncategorized", "Uncategorized"])
    result = harvest_month(
        store,
        FakeHarvest(
            [
                FamilyGroupMessage("msg-1", "Alpha Shop 1.00 Beta Shop 2.00"),
                FamilyGroupMessage("msg-2", "Gamma Shop 3.00"),
            ]
        ),
        model,
        "2026-08",
        now=NOW,
    )
    indexes = [
        (line.source_message_id, line.source_line_index)
        for line in result.draft.lines
    ]
    assert indexes == [("msg-1", 0), ("msg-1", 1), ("msg-2", 0)]


def test_invalid_utc_month_is_app_error_not_value_error() -> None:
    with pytest.raises(AppError) as err:
        harvest_month(
            FakePersistence(settings=_settings()),
            FakeHarvest([FamilyGroupMessage("1", "Test Shop 12")]),
            FakeModel(),
            "not-a-month",
            now=NOW,
        )
    assert err.value.message != err.value.code
    assert err.value.message


def test_parses_amount_first_known_currency_and_comma_decimal() -> None:
    store = FakePersistence(settings=_settings())
    model = FakeModel(names=["Uncategorized", "Uncategorized", "Uncategorized"])
    result = harvest_month(
        store,
        FakeHarvest(
            [
                FamilyGroupMessage("1", "12.00 Test Shop"),
                FamilyGroupMessage("2", "Cafe 8.00 VAT"),
                FamilyGroupMessage("3", "Bakery 12,50"),
            ]
        ),
        model,
        "2026-08",
        now=NOW,
    )
    first, vat_line, comma = result.draft.lines
    assert first.shop_display == "Test Shop"
    assert first.amount == "12.00"
    assert vat_line.currency == "EUR"
    assert vat_line.shop_display == "Cafe"
    assert comma.amount == "12.50"


def test_wrong_length_classify_is_model_unavailable() -> None:
    with pytest.raises(AppError) as err:
        harvest_month(
            FakePersistence(settings=_settings()),
            FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")]),
            FakeModel(names=["Groceries", "Transport"]),
            "2026-08",
            now=NOW,
        )
    assert err.value.code == "model.unavailable"
    assert err.value.message != err.value.code


def test_large_month_is_obtained_in_full() -> None:
    messages = [
        FamilyGroupMessage(str(i), f"Test Shop {i}.00") for i in range(501)
    ]
    store = FakePersistence(settings=_settings())
    model = FakeModel(names=["Uncategorized"] * 501)
    result = harvest_month(
        store, FakeHarvest(messages), model, "2026-08", now=NOW
    )
    assert len(result.draft.lines) == 501
    assert len(model.sent[0]) == 501
