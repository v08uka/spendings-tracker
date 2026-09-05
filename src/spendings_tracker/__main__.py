"""Process entry. Construct adapters, inject them at ports, run until stop."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from spendings_tracker.app.errors import catalog_error
from spendings_tracker.infra.language_model import LanguageModel
from spendings_tracker.infra.sqlite import SqlitePersistence
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.infra.telegram_harvest import TelegramHarvest
from spendings_tracker.infra.telegram_poll import run_until_stop
from spendings_tracker.infra.telegram_session import TelethonFamilyGroupReader
from spendings_tracker.infra.uncategorized_vendor import UncategorizedVendor


def build_runtime(
    db_path: Path,
    session_path: Path,
    vendor: UncategorizedVendor | None = None,
) -> TelegramBot:
    persistence = SqlitePersistence(db_path)
    harvest = TelegramHarvest(
        TelethonFamilyGroupReader(session_path),
        session_path=session_path,
    )
    model = LanguageModel(vendor or UncategorizedVendor())
    return TelegramBot(persistence, harvest, model)


def main(argv: list[str] | None = None) -> int:
    """Build adapters and long-poll Telegram until SIGINT/SIGTERM."""
    _ = argv if argv is not None else sys.argv[1:]
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise catalog_error("boot.missing_token")
    db_path = Path(os.environ.get("SPENDINGS_DB_PATH", "data/spendings.sqlite"))
    session_path = Path(
        os.environ.get("TELEGRAM_SESSION_PATH", "data/telegram.session")
    )
    if not session_path.exists():
        raise catalog_error("boot.missing_session")
    bot = build_runtime(db_path, session_path)
    run_until_stop(bot, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
