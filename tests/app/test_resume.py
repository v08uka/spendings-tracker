from spendings_tracker.app.resume import resume
from spendings_tracker.ports.persistence import (
    Category,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredDraftLine,
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
MAPPING = ShopMapping(
    id="map-1",
    shop_key="lidl",
    shop_display="Lidl",
    category_id="cat-g",
    created_at="2026-09-05T12:00:00Z",
)
CLOSE = StoredMonthlyClose(
    id="c1", utc_month="2026-07", default_currency="EUR", lines=(), egress_lines=()
)


class FakePersistence:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        draft: StoredDraft | None = None,
        mappings: tuple[ShopMapping, ...] = (),
        close: StoredMonthlyClose | None = None,
    ) -> None:
        self.settings = settings
        self.draft = draft
        self.mappings = mappings
        self.close = close

    def save_first_run(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_settings(self):
        return self.settings

    def upsert_shop_mapping(self, *args, **kwargs):
        raise AssertionError("not used")

    def find_shop_mapping(self, shop_display: str):
        return None

    def list_shop_mappings(self):
        return self.mappings

    def create_draft(self, *args, **kwargs):
        raise AssertionError("not used")

    def load_draft(self):
        return self.draft

    def update_draft_line(self, line):
        raise AssertionError("not used")

    def save_monthly_close(self, *, default_currency: str):
        raise AssertionError("not used")

    def load_monthly_close(self, utc_month: str):
        return self.close if self.close and self.close.utc_month == utc_month else None

    def load_latest_monthly_close(self):
        return self.close


def test_missing_settings_is_first_run_not_an_error() -> None:
    result = resume(FakePersistence())
    assert result.kind == "first_run"
    assert result.settings is None


def test_ready_after_stop_keeps_settings_map_and_saved_close() -> None:
    store = FakePersistence(
        settings=SETTINGS, mappings=(MAPPING,), close=CLOSE
    )
    result = resume(store)
    assert result.kind == "ready"
    assert result.settings == SETTINGS
    assert result.shop_mappings == (MAPPING,)
    assert result.saved_close == CLOSE


def test_in_progress_draft_includes_handles_without_first_run() -> None:
    handled = StoredDraftLine(
        id="l1",
        source_message_id="msg-1",
        source_line_index=0,
        line_text="Test Shop 12.00",
        shop_display="Test Shop",
        shop_key="test shop",
        amount="12.00",
        currency="EUR",
        category_id="cat-g",
        is_excluded=False,
        is_handled=True,
    )
    draft = StoredDraft("d1", "2026-08", (handled,), ())
    result = resume(FakePersistence(settings=SETTINGS, draft=draft))
    assert result.kind == "draft"
    assert result.draft is not None
    assert result.draft.lines[0].is_handled is True
    assert result.settings is SETTINGS
