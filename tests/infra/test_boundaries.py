from pathlib import Path


def test_domain_and_app_do_not_import_telegram_or_telethon() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "spendings_tracker"
    forbidden = ("telegram", "telethon", "python_telegram_bot")
    for package in ("domain", "app"):
        for path in (root / package).rglob("*.py"):
            text = path.read_text()
            for name in forbidden:
                assert name not in text, f"{path} imports {name}"
