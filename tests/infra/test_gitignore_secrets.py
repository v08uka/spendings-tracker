from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gitignore_covers_session_and_env_secrets() -> None:
    text = (ROOT / ".gitignore").read_text()
    assert "data/*.session" in text
    assert ".env" in text.splitlines()
