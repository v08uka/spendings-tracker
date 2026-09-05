"""Time-sortable ULID ids for persisted rows."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid(*, now: datetime | None = None) -> str:
    current = now if now is not None else datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    timestamp_ms = int(current.timestamp() * 1000)
    value = (timestamp_ms << 80) | secrets.randbits(80)
    chars: list[str] = []
    for _ in range(26):
        chars.append(CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def is_ulid(value: str) -> bool:
    return len(value) == 26 and all(char in CROCKFORD for char in value)
