from __future__ import annotations

from datetime import UTC, datetime

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.shop import shop_key
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.ports.harvest import FamilyGroupMessage
from spendings_tracker.ports.persistence import (
    Category,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredDraftLine,
    StoredEgressLine,
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
        return self.mappings.get(shop_key(shop_display))

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
        egress = tuple(
            StoredEgressLine(
                id=f"e{index}",
                line_text=text,
                draft_id="d1",
                monthly_close_id=None,
            )
            for index, text in enumerate(egress_texts)
        )
        self.draft = StoredDraft("d1", utc_month, stored, egress)
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
    assert "2026-08" in success.text
    assert "Test Shop" in success.text
    assert "12.00" in success.text
    assert "Egress" in success.text
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


def _handle_pick(text: str, shop: str | None = None) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[ Handle:") and stripped.endswith("]"):
            if shop is None or f"Handle: {shop}" in stripped:
                return stripped
    raise AssertionError(f"no handle pick for {shop!r} in:\n{text}")


def _amount_from_prompt(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1].strip()
            if inner and inner[0].isdigit():
                return inner
    raise AssertionError(f"no amount pick in:\n{text}")


def test_draft_reply_shows_handle_picks_and_closer_saves_from_them() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    assert draft.screen == "SCR-04"
    assert "[ Handle: Test Shop ]" in draft.text
    picked = bot.handle_private("10001", "dm-1", _handle_pick(draft.text, "Test Shop"))
    assert picked is not None
    assert picked.screen == "SCR-05"
    assert "Test Shop" in picked.text
    handled = bot.handle_private("10001", "dm-1", "[ Exclude from the close ]")
    assert handled is not None
    assert handled.screen == "SCR-04"
    saved = bot.handle_private("10001", "dm-1", "/save")
    assert saved is not None
    assert saved.screen == "SCR-06"
    assert store.draft is None


def test_assign_category_from_scr05_grows_map_for_later_close() -> None:
    store = FakePersistence()
    harvest = FakeHarvest([FamilyGroupMessage("1", "Lidl 12.00")])
    bot = _ready_bot(store, harvest)
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    picked = bot.handle_private("10001", "dm-1", _handle_pick(draft.text, "Lidl"))
    assert picked is not None
    assert picked.screen == "SCR-05"
    assign = bot.handle_private("10001", "dm-1", "[ Assign category ]")
    assert assign is not None
    assert assign.screen == "SCR-05"
    assert "Assign a confirmed category" in assign.text
    assert "[ Groceries ]" in assign.text
    assert "Uncategorized is not on this list" in assign.text
    assigned = bot.handle_private("10001", "dm-1", "[ Groceries ]")
    assert assigned is not None
    assert assigned.screen == "SCR-04"
    assert "Groceries" in assigned.text
    saved = bot.handle_private("10001", "dm-1", "/save")
    assert saved is not None
    assert saved.screen == "SCR-06"
    harvest.messages = [
        FamilyGroupMessage("2", " lidl 5.00"),
        FamilyGroupMessage("3", "Lidl Express 3.00"),
    ]
    later = bot.handle_private("10001", "dm-1", "/close 2026-07")
    assert later is not None
    assert later.screen == "SCR-04"
    assert "[ Handle: Lidl Express ]" in later.text
    assert "[ Handle: lidl ]" not in later.text
    assert "Groceries" in later.text


def test_handle_choice_returns_updated_private_draft() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    reply = bot.handle_private("10001", "dm-1", "[ Exclude from the close ]")
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

    bot2.handle_private("10001", "dm-1", _handle_pick(unhandled.text))
    bot2.handle_private("10001", "dm-1", "[ Exclude from the close ]")
    saved = bot2.handle_private("10001", "dm-1", "/save")
    assert saved is not None
    assert saved.screen == "SCR-06"
    assert "saved" in saved.text.lower()
    assert "totals" in saved.text.lower() or "EUR" in saved.text


def test_close_renders_empty_draft_copy_and_save_accepts_empty_totals() -> None:
    store = FakePersistence()
    bot = _ready_bot(store, FakeHarvest([FamilyGroupMessage("1", "lol dinner jokes")]))
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    assert draft.screen == "SCR-04"
    assert "No spend-looking lines" in draft.text
    assert "empty" in draft.text.lower()
    saved = bot.handle_private("10001", "dm-1", "/save")
    assert saved is not None
    assert saved.screen == "SCR-06"
    assert "saved" in saved.text.lower()


def test_save_same_month_twice_shows_replaced_note() -> None:
    store = FakePersistence()
    harvest = FakeHarvest([FamilyGroupMessage("1", "lol dinner jokes")])
    bot = _ready_bot(store, harvest)
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    first = bot.handle_private("10001", "dm-1", "/save")
    assert first is not None
    assert first.screen == "SCR-06"
    assert "replaced" not in first.text.lower()
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    second = bot.handle_private("10001", "dm-1", "/save")
    assert second is not None
    assert second.screen == "SCR-06"
    assert "replaced" in second.text.lower()


def test_second_close_while_draft_exists_is_busy_on_scr04() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    busy = bot.handle_private("10001", "dm-1", "/close 2026-07")
    assert busy is not None
    assert busy.screen == "SCR-04"
    assert busy.code == "harvest.draft_in_progress"
    assert "Finish or replace the in-progress close first" in busy.text


def test_egress_blocked_stays_on_ready() -> None:
    bot = _ready_bot(
        FakePersistence(),
        FakeHarvest(
            error=AppError(
                "harvest.egress_blocked",
                "Only spend-looking lines may leave the machine.",
            )
        ),
    )
    reply = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert reply is not None
    assert reply.screen == "SCR-02"
    assert reply.code == "harvest.egress_blocked"
    assert "Only spend-looking lines may leave the machine" in reply.text


def test_resume_on_start_shows_in_progress_draft_not_ready() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    bot.handle_private("10001", "dm-1", "[ Exclude from the close ]")
    resumed = bot.handle_private("10001", "dm-1", "/start")
    assert resumed is not None
    assert resumed.screen == "SCR-04"
    assert "Private draft" in resumed.text
    assert "Test Shop" in resumed.text
    assert store.draft is not None
    assert store.draft.lines[0].is_handled is True


def test_pick_suspect_builds_scr05_then_returns_updated_draft() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    picked = bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    assert picked is not None
    assert picked.screen == "SCR-05"
    assert "Test Shop" in picked.text
    lowered = picked.text.lower()
    assert "enter amount" in lowered
    assert "assign category" in lowered
    assert "confirm uncategorized" in lowered
    assert "leave other currency" in lowered
    assert "exclude" in lowered
    asked = bot.handle_private("10001", "dm-1", "[ Enter amount ]")
    assert asked is not None
    assert asked.screen == "SCR-05"
    assert "Enter the amount" in asked.text
    assert "Amount is required" not in asked.text
    missing = bot.handle_private("10001", "dm-1", "not-a-number")
    assert missing is not None
    assert missing.screen == "SCR-05"
    assert "Amount is required" in missing.text
    handled = bot.handle_private("10001", "dm-1", "[ Exclude from the close ]")
    assert handled is not None
    assert handled.screen == "SCR-04"
    assert "Private draft" in handled.text


def test_enter_amount_from_scr05_prompt_updates_picked_line() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store,
        FakeHarvest(
            [
                FamilyGroupMessage("1", "Cafe 1.00"),
                FamilyGroupMessage("2", "Cafe 2.00"),
            ]
        ),
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    assert draft.screen == "SCR-04"
    picked = bot.handle_private("10001", "dm-1", _handle_pick(draft.text, "Cafe"))
    assert picked is not None
    assert picked.screen == "SCR-05"
    assert "Cafe" in picked.text
    prompt = bot.handle_private("10001", "dm-1", "[ Enter amount ]")
    assert prompt is not None
    assert prompt.screen == "SCR-05"
    assert "Enter the amount" in prompt.text
    assert "Cafe" in prompt.text
    amount = _amount_from_prompt(prompt.text)
    updated = bot.handle_private("10001", "dm-1", amount)
    assert updated is not None
    assert updated.screen == "SCR-04"
    assert "Private draft" in updated.text
    assert amount in updated.text
    assert store.draft is not None
    assert store.draft.lines[0].amount == amount
    assert store.draft.lines[0].is_handled is True
    assert store.draft.lines[1].amount == "2.00"
    assert store.draft.lines[1].is_handled is False


def test_exclude_after_enter_amount_prompt_still_resumes_on_start() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    picked = bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    assert picked is not None
    prompt = bot.handle_private("10001", "dm-1", "[ Enter amount ]")
    assert prompt is not None
    assert prompt.screen == "SCR-05"
    assert "Enter the amount" in prompt.text
    excluded = bot.handle_private("10001", "dm-1", "[ Exclude from the close ]")
    assert excluded is not None
    assert excluded.screen == "SCR-04"
    assert "Private draft" in excluded.text
    resumed = bot.handle_private("10001", "dm-1", "/start")
    assert resumed is not None
    assert resumed.screen == "SCR-04"
    assert "Private draft" in resumed.text
    assert "Amount is required" not in resumed.text
    leftover = bot.handle_private("10001", "dm-1", "99.00")
    assert leftover is not None
    assert leftover.screen == "SCR-04"
    assert "Private draft" in leftover.text
    assert store.draft is not None
    assert store.draft.lines[0].is_excluded is True
    assert store.draft.lines[0].amount == "12.00"


def test_start_during_amount_prompt_resumes_and_ignores_later_number() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    prompt = bot.handle_private("10001", "dm-1", "[ Enter amount ]")
    assert prompt is not None
    assert "Enter the amount" in prompt.text
    resumed = bot.handle_private("10001", "dm-1", "/start")
    assert resumed is not None
    assert resumed.screen == "SCR-04"
    assert "Private draft" in resumed.text
    assert "Amount is required" not in resumed.text
    leftover = bot.handle_private("10001", "dm-1", "99.00")
    assert leftover is not None
    assert leftover.screen == "SCR-04"
    assert leftover.code != "handle.invalid_amount"
    assert store.draft is not None
    assert store.draft.lines[0].amount == "12.00"
    assert store.draft.lines[0].is_handled is False


def test_start_during_assign_does_not_apply_later_category_pick() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    draft = bot.handle_private("10001", "dm-1", "/close 2026-08")
    assert draft is not None
    bot.handle_private("10001", "dm-1", _handle_pick(draft.text))
    asked = bot.handle_private("10001", "dm-1", "[ Assign category ]")
    assert asked is not None
    assert "Groceries" in asked.text
    resumed = bot.handle_private("10001", "dm-1", "/start")
    assert resumed is not None
    assert resumed.screen == "SCR-04"
    leftover = bot.handle_private("10001", "dm-1", "[ Groceries ]")
    assert leftover is not None
    assert leftover.screen == "SCR-04"
    assert leftover.code != "handle.unknown_category"
    assert store.draft is not None
    assert store.draft.lines[0].category_id is None
    assert store.draft.lines[0].is_handled is False
    assert store.mappings == {}


def test_malformed_close_and_unknown_handle_are_app_errors() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    bare = bot.handle_private("10001", "dm-1", "/close")
    assert bare is not None
    assert bare.code is not None
    assert bare.text != bare.code
    bad_month = bot.handle_private("10001", "dm-1", "/close not-a-month")
    assert bad_month is not None
    assert bad_month.code is not None
    assert bad_month.text != bad_month.code
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    unknown = bot.handle_private("10001", "dm-1", "handle l0 not_a_choice")
    assert unknown is not None
    assert unknown.code == "handle.unknown_choice"
    assert unknown.screen == "SCR-05"
    assert unknown.text != unknown.code


def test_non_closer_handle_and_save_are_auth_errors() -> None:
    store = FakePersistence()
    bot = _ready_bot(
        store, FakeHarvest([FamilyGroupMessage("1", "Test Shop 12.00")])
    )
    bot.handle_private("10001", "dm-1", "/close 2026-08")
    handle = bot.handle_private("10002", "dm-2", "handle l0 exclude")
    save = bot.handle_private("10002", "dm-2", "/save")
    assert handle is not None
    assert handle.code == "auth.not_closer"
    assert handle.screen == "SCR-07"
    assert "draft" not in handle.text.lower()
    assert save is not None
    assert save.code == "auth.not_closer"
    assert "draft" not in save.text.lower()
