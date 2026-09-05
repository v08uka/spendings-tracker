"""Language-model port. Only spend-looking lines may be sent."""

from __future__ import annotations

from typing import Protocol


class ModelPort(Protocol):
    def classify(
        self, lines: list[str], category_names: list[str]
    ) -> list[str]:
        """File each line into a confirmed name or Uncategorized."""
        ...
