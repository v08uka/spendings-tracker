from datetime import UTC, datetime

from spendings_tracker.domain.month import is_completed_utc_month

NOW = datetime(2026, 9, 5, tzinfo=UTC)


def test_refuses_the_current_incomplete_utc_month() -> None:
    assert is_completed_utc_month("2026-09", now=NOW) is False


def test_accepts_a_completed_utc_month() -> None:
    assert is_completed_utc_month("2026-08", now=NOW) is True
    assert is_completed_utc_month("2025-12", now=NOW) is True


def test_refuses_a_future_utc_month() -> None:
    assert is_completed_utc_month("2026-10", now=NOW) is False


def test_invalid_month_does_not_raise_value_error() -> None:
    assert is_completed_utc_month("not-a-month", now=NOW) is False
    assert is_completed_utc_month("2026-13", now=NOW) is False
    assert is_completed_utc_month("", now=NOW) is False
