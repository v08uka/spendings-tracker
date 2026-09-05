"""Resume after an on-demand stop: settings, map, close, or in-progress draft."""

from __future__ import annotations

from dataclasses import dataclass

from spendings_tracker.ports.persistence import (
    PersistencePort,
    Settings,
    ShopMapping,
    StoredDraft,
    StoredMonthlyClose,
)


@dataclass(frozen=True)
class ResumeResult:
    kind: str
    settings: Settings | None
    draft: StoredDraft | None
    shop_mappings: tuple[ShopMapping, ...]
    saved_close: StoredMonthlyClose | None


def resume(persistence: PersistencePort) -> ResumeResult:
    settings = persistence.load_settings()
    mappings = persistence.list_shop_mappings()
    saved = persistence.load_latest_monthly_close()
    if settings is None:
        return ResumeResult(
            kind="first_run",
            settings=None,
            draft=None,
            shop_mappings=mappings,
            saved_close=saved,
        )
    draft = persistence.load_draft()
    if draft is not None:
        return ResumeResult(
            kind="draft",
            settings=settings,
            draft=draft,
            shop_mappings=mappings,
            saved_close=saved,
        )
    return ResumeResult(
        kind="ready",
        settings=settings,
        draft=None,
        shop_mappings=mappings,
        saved_close=saved,
    )
