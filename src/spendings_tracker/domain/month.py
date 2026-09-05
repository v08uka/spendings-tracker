"""Completed UTC calendar month rule."""

from __future__ import annotations

import re
from datetime import UTC, datetime

UTC_MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")


def is_utc_month(utc_month: str) -> bool:
    return UTC_MONTH.fullmatch(utc_month) is not None


def is_completed_utc_month(utc_month: str, *, now: datetime | None = None) -> bool:
    if not is_utc_month(utc_month):
        return False
    current = now if now is not None else datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    year_text, month_text = utc_month.split("-", maxsplit=1)
    year = int(year_text)
    month = int(month_text)
    return (year, month) < (current.year, current.month)
