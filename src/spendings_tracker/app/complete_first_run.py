"""Complete first-run: confirm currency, frozen categories, and closer pin."""

from __future__ import annotations

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.categories import confirmable_names
from spendings_tracker.ports.persistence import PersistencePort, Settings

DEFAULT_CURRENCY = "EUR"
EMPTY_LIST = "first_run.empty_category_list"
STILL_REQUIRED = "first_run.still_required"


def complete_first_run(
    persistence: PersistencePort,
    *,
    closer_identity: str,
    default_currency: str,
    category_names: list[str],
) -> Settings:
    names = confirmable_names(category_names)
    if not names:
        raise AppError(
            EMPTY_LIST,
            "At least one category is required. Uncategorized does not count.",
        )
    currency = default_currency.strip() or DEFAULT_CURRENCY
    return persistence.save_first_run(closer_identity, currency, names)


def require_first_run(persistence: PersistencePort) -> Settings:
    settings = persistence.load_settings()
    if settings is None:
        raise AppError(STILL_REQUIRED, "First-run setup is still required.")
    return settings
