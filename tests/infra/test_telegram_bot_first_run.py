from __future__ import annotations

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.ports.persistence import Category, Settings, ShopMapping


class StubHarvest:
    def harvest_month(self, utc_month: str):
        raise AssertionError("harvest must not run during first-run")


class StubModel:
    def classify(self, lines, category_names):
        raise AssertionError("model must not run during first-run")


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

    def load_latest_monthly_close(self):
        return None


def _bot(store: FakePersistence | None = None) -> TelegramBot:
    return TelegramBot(store or FakePersistence(), StubHarvest(), StubModel())


def _token(text: str, needle: str) -> str:
    start = 0
    while True:
        open_at = text.find("[", start)
        close_at = text.find("]", open_at + 1) if open_at >= 0 else -1
        if open_at < 0 or close_at < 0:
            raise AssertionError(f"no token {needle!r} in:\n{text}")
        token = text[open_at : close_at + 1]
        if needle in token:
            return token
        start = close_at + 1


def test_first_run_confirm_reaches_ready() -> None:
    bot = _bot()
    start = bot.handle_private("10001", "dm-1", "/start")
    assert start is not None
    assert start.screen == "SCR-01"
    keep = bot.handle_private("10001", "dm-1", _token(start.text, "Keep EUR"))
    assert keep is not None
    confirm = bot.handle_private("10001", "dm-1", _token(keep.text, "Confirm list"))

    assert "Keep EUR" in start.text
    assert "Change" in start.text
    assert "Confirm list" in start.text
    assert keep.screen == "SCR-01"
    assert confirm is not None
    assert confirm.screen == "SCR-02"
    assert "Monthly closes can start" in confirm.text
    assert "EUR" in confirm.text


def test_first_run_can_choose_a_currency_other_than_eur() -> None:
    store = FakePersistence()
    bot = _bot(store)
    start = bot.handle_private("10001", "dm-1", "/start")
    assert start is not None
    change = bot.handle_private("10001", "dm-1", _token(start.text, "Change"))
    assert change is not None
    typed = bot.handle_private("10001", "dm-1", "USD")
    assert typed is not None
    confirm = bot.handle_private("10001", "dm-1", _token(typed.text, "Confirm list"))

    assert "Keep EUR" in start.text
    assert change.screen == "SCR-01"
    assert typed.screen == "SCR-01"
    assert "USD" in typed.text
    assert confirm is not None
    assert confirm.screen == "SCR-02"
    assert store.settings is not None
    assert store.settings.default_currency == "USD"
    assert "USD" in confirm.text
    assert "Default currency: EUR" not in confirm.text


def test_empty_list_and_close_before_confirm_are_contract_errors() -> None:
    bot = _bot()
    start = bot.handle_private("10001", "dm-1", "/start")
    assert start is not None
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
    bot = _bot(store)
    start = bot.handle_private("10001", "dm-1", "/start")
    assert start is not None
    bot.handle_private("10001", "dm-1", _token(start.text, "Keep EUR"))
    bot.handle_private("10001", "dm-1", _token(start.text, "Confirm list"))

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
