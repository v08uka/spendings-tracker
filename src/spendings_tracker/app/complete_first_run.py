"""Complete first-run: confirm currency, frozen categories, and closer pin."""

from __future__ import annotations

from spendings_tracker.app.errors import catalog_error
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
        raise catalog_error(EMPTY_LIST)
    currency = default_currency.strip() or DEFAULT_CURRENCY
    return persistence.save_first_run(closer_identity, currency, names)


def require_first_run(persistence: PersistencePort) -> Settings:
    settings = persistence.load_settings()
    if settings is None:
        raise catalog_error(STILL_REQUIRED)
    return settings
