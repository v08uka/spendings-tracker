from __future__ import annotations

import pytest

from spendings_tracker.app.errors import AppError
from spendings_tracker.infra.language_model import LanguageModel


class FakeVendor:
    def __init__(self, names: list[str] | None = None) -> None:
        self.names = names or []
        self.sent: list[list[str]] = []

    def classify(self, lines: list[str], category_names: list[str]) -> list[str]:
        self.sent.append(list(lines))
        return list(self.names)


def test_refuses_non_spend_looking_text_before_any_send() -> None:
    vendor = FakeVendor(names=["Groceries"])
    model = LanguageModel(vendor)

    with pytest.raises(AppError, match="harvest.egress_blocked"):
        model.classify(["just chatting about dinner"], ["Groceries"])

    assert vendor.sent == []


def test_sends_only_spend_looking_lines_and_files_known_categories() -> None:
    vendor = FakeVendor(names=["Groceries", "Uncategorized"])
    model = LanguageModel(vendor)

    filed = model.classify(
        ["Test Shop 12.00", "Other Shop 8"],
        ["Groceries", "Transport"],
    )

    assert vendor.sent == [["Test Shop 12.00", "Other Shop 8"]]
    assert filed == ["Groceries", "Uncategorized"]


def test_does_not_invent_category_names() -> None:
    vendor = FakeVendor(names=["Invented"])
    model = LanguageModel(vendor)

    filed = model.classify(["Test Shop 12.00"], ["Groceries"])

    assert filed == ["Uncategorized"]
