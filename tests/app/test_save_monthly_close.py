from __future__ import annotations

import pytest

from spendings_tracker.app.errors import AppError
from spendings_tracker.app.save_monthly_close import save_monthly_close
from spendings_tracker.ports.persistence import (
    Category,
    Settings,
    StoredCloseLine,
    StoredDraft,
    StoredDraftLine,
    StoredEgressLine,
    StoredMonthlyClose,
)

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


def _line(
    line_id: str,
    amount: str | None,
    *,
    currency: str = "EUR",
    excluded: bool = False,
    handled: bool = True,
    category_id: str | None = "cat-g",
) -> StoredDraftLine:
    return StoredDraftLine(
        id=line_id,
        source_message_id="msg-1",
        source_line_index=0,
        line_text="Test Shop 12.00",
        shop_display="Test Shop",
        shop_key="test shop",
        amount=amount,
        currency=currency,
        category_id=category_id,
        is_excluded=excluded,
        is_handled=handled,
    )


class FakePersistence:
    def __init__(self, draft: StoredDraft | None) -> None:
        self.draft = draft
        self.closes: dict[str, StoredMonthlyClose] = {}
        self.settings = SETTINGS

    def save_first_run(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_settings(self):
        return self.settings

    def upsert_shop_mapping(self, *args, **kwargs):
        raise AssertionError("not used")

    def find_shop_mapping(self, shop_display: str):
        return None

    def list_shop_mappings(self):
        return ()

    def create_draft(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_draft(self):
        return self.draft

    def update_draft_line(self, line):
        raise AssertionError("not used")

    def save_monthly_close(self, *, default_currency: str) -> StoredMonthlyClose:
        if self.draft is None:
            raise AppError("save.no_draft")
        previous = self.closes.get(self.draft.utc_month)
        close = StoredMonthlyClose(
            id="close-new" if previous else "close-1",
            utc_month=self.draft.utc_month,
            default_currency=default_currency,
            lines=tuple(
                StoredCloseLine(
                    id=f"cl-{line.id}",
                    line_text=line.line_text,
                    source_message_id=line.source_message_id,
                    source_line_index=line.source_line_index,
                    shop_display=line.shop_display,
                    shop_key=line.shop_key,
                    amount=line.amount,
                    currency=line.currency,
                    category_id=line.category_id,
                )
                for line in self.draft.lines
                if not line.is_excluded
            ),
            egress_lines=tuple(
                StoredEgressLine(
                    id=row.id,
                    line_text=row.line_text,
                    draft_id=None,
                    monthly_close_id="close-1",
                )
                for row in self.draft.egress_lines
            ),
        )
        self.closes[close.utc_month] = close
        self.draft = None
        return close

    def load_monthly_close(self, utc_month: str):
        return self.closes.get(utc_month)


def test_save_accepts_totals_and_omits_excluded() -> None:
    draft = StoredDraft(
        id="d1",
        utc_month="2026-08",
        lines=(
            _line("a", "12.00"),
            _line("b", "3.00", excluded=True),
            _line("c", "8.00", currency="USD"),
        ),
        egress_lines=(),
    )
    store = FakePersistence(draft)
    result = save_monthly_close(store)
    assert result.replaced is False
    assert result.totals == {"cat-g": "12.00"}
    assert [line.currency for line in result.close.lines if line.currency != "EUR"] == [
        "USD"
    ]


def test_refuses_no_draft_and_unhandled_suspect() -> None:
    with pytest.raises(AppError) as no_draft:
        save_monthly_close(FakePersistence(None))
    assert no_draft.value.code == "save.no_draft"

    suspect = StoredDraft(
        "d1",
        "2026-08",
        (_line("a", None, handled=False, category_id="cat-g"),),
        (),
    )
    with pytest.raises(AppError) as unhandled:
        save_monthly_close(FakePersistence(suspect))
    assert unhandled.value.code == "save.unhandled_suspect"


def test_save_of_empty_draft_accepts_empty_totals() -> None:
    store = FakePersistence(StoredDraft("d1", "2026-08", (), ()))
    result = save_monthly_close(store)
    assert result.replaced is False
    assert result.totals == {}
    assert result.close.lines == ()


def test_second_save_for_same_month_is_replaced() -> None:
    store = FakePersistence(
        StoredDraft("d1", "2026-08", (_line("a", "12.00"),), ())
    )
    first = save_monthly_close(store)
    store.draft = StoredDraft("d2", "2026-08", (_line("b", "4.00"),), ())
    second = save_monthly_close(store)
    assert first.replaced is False
    assert second.replaced is True
    assert store.load_monthly_close("2026-08") is second.close
