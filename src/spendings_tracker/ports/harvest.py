"""Harvest of a completed UTC month from already-existing family-group history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FamilyGroupMessage:
    id: str
    text: str


class HarvestPort(Protocol):
    def harvest_month(self, utc_month: str) -> list[FamilyGroupMessage]:
        """Read that month's family-group messages. No export file."""
        ...
