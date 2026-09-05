"""Process entry. Construct adapters, inject them at ports, run until stop."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from spendings_tracker.infra.language_model import LanguageModel
from spendings_tracker.infra.sqlite import SqlitePersistence
from spendings_tracker.infra.telegram_bot import TelegramBot
from spendings_tracker.infra.telegram_harvest import TelegramHarvest


class NullFamilyGroupReader:
    def read_completed_month(self, utc_month: str) -> list:
        raise OSError("telegram user session is not logged in")


class NullVendor:
    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        return ["Uncategorized"] * len(lines)


def build_runtime(
    db_path: Path, session_path: Path, vendor: NullVendor | None = None
) -> TelegramBot:
    persistence = SqlitePersistence(db_path)
    harvest = TelegramHarvest(
        NullFamilyGroupReader(), session_path=session_path
    )
    model = LanguageModel(vendor or NullVendor())
    return TelegramBot(persistence, harvest, model)


def main(argv: list[str] | None = None) -> int:
    """Boot probe: construct adapters and inject them at ports."""
    from spendings_tracker import app, domain, infra, ports  # noqa: F401

    _ = argv if argv is not None else sys.argv[1:]
    db_path = Path(os.environ.get("SPENDINGS_DB_PATH", "data/spendings.sqlite"))
    session_path = Path(
        os.environ.get("TELEGRAM_SESSION_PATH", "data/telegram.session")
    )
    build_runtime(db_path, session_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
