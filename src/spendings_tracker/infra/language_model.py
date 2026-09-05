"""Language-model adapter. Re-checks the on-machine spend-looking gate."""

from __future__ import annotations

from typing import Protocol

from spendings_tracker.app.errors import AppError
from spendings_tracker.domain.spend_looking import is_spend_looking

EGRESS_BLOCKED = "harvest.egress_blocked"
UNCATEGORIZED = "Uncategorized"


class VendorClient(Protocol):
    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        ...


class LanguageModel:
    def __init__(self, vendor: VendorClient) -> None:
        self._vendor = vendor

    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        for line in lines:
            if not is_spend_looking(line):
                raise AppError(EGRESS_BLOCKED)
        allowed = set(category_names)
        try:
            names = self._vendor.classify(lines, category_names)
        except AppError:
            raise
        except Exception as exc:
            raise AppError("model.unavailable") from exc
        return [
            name if name in allowed else UNCATEGORIZED
            for name in names
        ]
