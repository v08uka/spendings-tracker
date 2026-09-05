from __future__ import annotations

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.ports.persistence import Category, Settings, ShopMapping


class FakePersistence:
    def __init__(self) -> None:
        self.settings: Settings | None = None

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

    def upsert_shop_mapping(
        self, shop_display: str, category_id: str | None
    ) -> ShopMapping:
        raise AssertionError("not used")

    def find_shop_mapping(self, shop_display: str) -> ShopMapping | None:
        return None

    def list_shop_mappings(self) -> tuple[ShopMapping, ...]:
        return ()

    def create_draft(self, utc_month: str, lines, egress_texts):
        raise AssertionError("close must not start")

    def load_draft(self):
        return None

    def update_draft_line(self, line):
        raise AssertionError("not used")

    def save_monthly_close(self, *, default_currency: str):
        raise AssertionError("not used")

    def load_monthly_close(self, utc_month: str):
        return None


def test_first_run_confirm_reaches_ready() -> None:
    bot = TelegramBot(FakePersistence())
    start = bot.handle_private("10001", "dm-1", "/start")
    confirm = bot.handle_private("10001", "dm-1", "confirm Groceries, Transport")

    assert start is not None
    assert start.screen == "SCR-01"
    assert confirm is not None
    assert confirm.screen == "SCR-02"
    assert "Monthly closes can start" in confirm.text


def test_empty_list_and_close_before_confirm_are_contract_errors() -> None:
    bot = TelegramBot(FakePersistence())
    bot.handle_private("10001", "dm-1", "/start")
    empty = bot.handle_private("10001", "dm-1", "confirm")
    close = bot.handle_private("10001", "dm-1", "/close 2026-08")

    assert empty is not None
    assert empty.code == "first_run.empty_category_list"
    assert "Uncategorized does not count" in empty.text
    assert close is not None
    assert close.code == "first_run.still_required"
    assert "First-run setup is still required" in close.text


def test_non_closer_gets_auth_error_without_draft_or_close_detail() -> None:
    store = FakePersistence()
    bot = TelegramBot(store)
    bot.handle_private("10001", "dm-1", "/start")
    bot.handle_private("10001", "dm-1", "confirm Groceries")

    reply = bot.handle_private("10002", "dm-2", "/close 2026-08")
    group = bot.handle_group("10002", "group-1", "what about the draft totals")

    assert reply is not None
    assert reply.code == "auth.not_closer"
    assert reply.screen == "SCR-07"
    assert "You cannot use this bot" in reply.text
    lowered = reply.text.lower()
    assert "draft" not in lowered
    assert "close" not in lowered
    assert "total" not in lowered
    assert group is None


def test_app_error_still_has_not_closer_code() -> None:
    err = AppError("auth.not_closer", "You cannot use this bot.")
    assert err.code == "auth.not_closer"
    assert "draft" not in err.message
