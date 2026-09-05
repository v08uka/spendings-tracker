from spendings_tracker.domain.categories import confirmable_names


def test_refuses_an_empty_confirmed_list() -> None:
    assert confirmable_names([]) == []
    assert confirmable_names(["", "  "]) == []


def test_uncategorized_does_not_count() -> None:
    assert confirmable_names(["Uncategorized"]) == []
    assert confirmable_names(["uncategorized", "  Uncategorized  "]) == []


def test_keeps_at_least_one_confirmed_name() -> None:
    assert confirmable_names(["Groceries"]) == ["Groceries"]
    assert confirmable_names(["Uncategorized", "Groceries"]) == ["Groceries"]
