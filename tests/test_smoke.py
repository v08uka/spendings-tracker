from spendings_tracker.__main__ import build_runtime, main, run_until_stop
from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.language_model import LanguageModel
from spendings_tracker.infra.telegram_harvest import TelegramHarvest
from spendings_tracker.infra.telegram_session import TelethonFamilyGroupReader
from spendings_tracker.infra.uncategorized_vendor import UncategorizedVendor


def test_app_boots(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    bot = build_runtime(tmp_path / "spendings.sqlite", tmp_path / "telegram.session")
    assert isinstance(bot._harvest, TelegramHarvest)
    assert isinstance(bot._harvest._reader, TelethonFamilyGroupReader)
    assert isinstance(bot._model, LanguageModel)
    assert isinstance(bot._model._vendor, UncategorizedVendor)
    assert callable(run_until_stop)


def test_main_requires_bot_token(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    try:
        main([])
    except AppError as err:
        assert err.code == "boot.missing_token"
        assert err.message != err.code
    else:
        raise AssertionError("main must not return after build_runtime without a token")


def test_run_until_stop_is_wired() -> None:
    seen: list[tuple[object, str]] = []

    def fake_poll(bot, token, stop=None) -> None:
        seen.append((bot, token))

    marker = object()
    run_until_stop(marker, "test-token", poll=fake_poll)
    assert seen == [(marker, "test-token")]
