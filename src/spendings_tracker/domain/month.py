"""Completed UTC calendar month rule."""

from __future__ import annotations

from datetime import UTC, datetime


def is_completed_utc_month(utc_month: str, *, now: datetime | None = None) -> bool:
    current = now if now is not None else datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    year_text, month_text = utc_month.split("-", maxsplit=1)
    year = int(year_text)
    month = int(month_text)
    return (year, month) < (current.year, current.month)
