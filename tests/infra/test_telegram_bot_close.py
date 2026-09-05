from __future__ import annotations

from datetime import UTC, datetime

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.ports.harvest import FamilyGroupMessage
from spendings_tracker.ports.persistence import (
    Category,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredDraftLine,
    StoredMonthlyClose,
)

NOW = datetime(2026, 9, 5, tzinfo=UTC)


class FakeHarvest:
    def __init__(self, messages=None, error: AppError | None = None) -> None:
        self.messages = messages or []
        self.error = error

    def harvest_month(self, utc_month: str):
        if self.error is not None:
            raise self.error
        return list(self.messages)


class FakeModel:
    def classify(self, lines, category_names):
        return ["Uncategorized"] * len(lines)


class FakePersistence:
    def __init__(self) -> None:
        self.settings: Settings | None = None
        self.draft: StoredDraft | None = None
        self.closes: dict[str, StoredMonthlyClose] = {}
        self.mappings: dict[str, ShopMapping] = {}

    def save_first_run(self, closer_identity, default_currency, category_names):
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

    def load_settings(self):
        return self.settings

    def upsert_shop_mapping(self, shop_display, category_id):
        mapping = ShopMapping(
            "m1", shop_display.lower(), shop_display, category_id, "t"
        )
        self.mappings[mapping.shop_key] = mapping
        return mapping

    def find_shop_mapping(self, shop_display):
        return None

    def list_shop_mappings(self):
        return tuple(self.mappings.values())

    def create_draft(self, utc_month, lines, egress_texts):
        stored = tuple(
            StoredDraftLine(
                id=f"l{index}",
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
        self.draft = StoredDraft("d1", utc_month, stored, ())
        return self.draft

    def load_draft(self):
        return self.draft

    def update_draft_line(self, line):
        if self.draft is None:
            raise AppError("save.no_draft")
        self.draft = StoredDraft(
            self.draft.id,
            self.draft.utc_month,
            tuple(line if item.id == line.id else item for item in self.draft.lines),
            self.draft.egress_lines,
        )
        return line

    def save_monthly_close(self, *, default_currency: str):
        if self.draft is None:
            raise AppError("save.no_draft")
        close = StoredMonthlyClose(
            "c1", self.draft.utc_month, default_currency, (), ()
        )
        self.closes[close.utc_month] = close
        self.draft = None
        return close

    def load_monthly_close(self, utc_month):
        return self.closes.get(utc_month)

    def load_latest_monthly_close(self):
        if not self.closes:
            return None
        return next(iter(self.closes.values()))


def _ready_bot(store: FakePersistence, harvest=None) -> TelegramBot:
    bot = TelegramBot(store, harvest=harvest, model=FakeModel(), now=NOW)
    bot.handle_private("10001", "dm-1", "/start")
    bot.handle_private("10001", "dm-1", "confirm Groceries")
    return bot


def test_close_success_and_harvest_errors_map_to_screens() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    success = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert success is not None
    assert success.screen == "SCR-04"
    assert "Private draft" in success.text
    assert bot.handle_group("10001", "group-1", "draft totals") is None

    missing = _ready_bot(
        FakePersistence(),
        FakeHarvest(error=AppError("harvest.month_not_obtained")),
    )
    failed = missing.handle_private("10001", "dm-1", "/close 2026-08")
    assert failed is not None
    assert failed.screen == "SCR-03"
    assert failed.code == "harvest.month_not_obtained"

    incomplete = _ready_bot(FakePersistence(), FakeHarvest([]))
    refused = incomplete.handle_private("10001", "dm-1", "/close 2026-09")
    assert refused is not None
    assert refused.screen == "SCR-02"
    assert refused.code == "harvest.incomplete_month"


def test_handle_choice_returns_updated_private_draft() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    reply = bot.handle_private("10001", "dm-1", "handle l0 exclude")
    assert reply is not None
    assert reply.screen == "SCR-04"
    assert store.draft is not None
    assert store.draft.lines[0].is_excluded is True


def test_save_success_and_refusals() -> None:
    store = FakePersistence()
    bot = _ready_bot(store, FakeHarvest([]))
    no_draft = bot.handle_private("10001", "dm-1", "/save")
    assert no_draft is not None
    assert no_draft.code == "save.no_draft"
    assert no_draft.screen == "SCR-02"

    store2 = FakePersistence()
    bot2 = _ready_bot(
        store2, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    bot2.handle_private("10001", "dm-1", "/close 2026-08")
    unhandled = bot2.handle_private("10001", "dm-1", "/save")
    assert unhandled is not None
    assert unhandled.code == "save.unhandled_suspect"
    assert unhandled.screen == "SCR-04"

    bot2.handle_private("10001", "dm-1", "handle l0 exclude")
    saved = bot2.handle_private("10001", "dm-1", "/save")
    assert saved is not None
    assert saved.screen == "SCR-06"
    assert "saved" in saved.text.lower()
