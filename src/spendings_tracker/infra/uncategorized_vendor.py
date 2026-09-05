"""Local model vendor: files every spend-looking line as Uncategorized."""

from __future__ import annotations

UNCATEGORIZED = "Uncategorized"


class UncategorizedVendor:
    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        return [UNCATEGORIZED] * len(lines)
