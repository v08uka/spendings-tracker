from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from spendings_tracker.infra.telegram_session import TelethonFamilyGroupReader


class _FakeMessage:
    def __init__(self, message_id: int, when: datetime, text: str) -> None:
        self.id = message_id
        self.date = when
        self.message = text


class _FakeClient:
    last: _FakeClient | None = None

    def __init__(self, *_args, **_kwargs) -> None:
        self.calls: list[dict[str, object]] = []
        type(self).last = self

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False

    def iter_messages(self, target, offset_date=None, reverse=False):
        self.calls.append(
            {"target": target, "offset_date": offset_date, "reverse": reverse}
        )
        # Telethon: reverse=True inverts offset_date (still exclusive).
        for message in _MONTH_FEED:
            when = message.date
            if reverse:
                if offset_date is not None and when <= offset_date:
                    continue
            elif offset_date is not None and when >= offset_date:
                continue
            yield message


_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = datetime(2026, 9, 1, tzinfo=UTC)
_MONTH_FEED = [
    _FakeMessage(1, _START - timedelta(hours=1), "July leftover"),
    *(
        _FakeMessage(100 + i, _START + timedelta(hours=i), f"Aug {i}")
        for i in range(501)
    ),
    _FakeMessage(999, _END, "September first"),
]


def test_reader_obtains_the_whole_completed_month(tmp_path: Path, monkeypatch) -> None:
    session = tmp_path / "telegram.session"
    session.write_text("session")
    monkeypatch.setattr("telethon.sync.TelegramClient", _FakeClient)
    reader = TelethonFamilyGroupReader(
        session,
        api_id="1",
        api_hash="hash",
        family_group="-100123",
    )

    obtained = reader.read_completed_month("2026-08")

    assert _FakeClient.last is not None
    call = _FakeClient.last.calls[0]
    assert call["reverse"] is True
    offset = call["offset_date"]
    assert offset is not None
    assert offset < _END
    assert offset <= _START
    texts = [row.text for row in obtained]
    assert "July leftover" not in texts
    assert "September first" not in texts
    assert len(obtained) == 501
    assert texts[0] == "Aug 0"
    assert texts[-1] == "Aug 500"
