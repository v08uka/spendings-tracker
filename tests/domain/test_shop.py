from spendings_tracker.domain.shop import shop_key, shops_match


def test_matches_after_trim_and_case_only() -> None:
    assert shop_key(" Lidl ") == "lidl"
    assert shop_key("LIDL") == "lidl"
    assert shops_match(" Lidl ", "lidl")


def test_different_remaining_spelling_is_a_different_shop() -> None:
    assert shop_key("Lidl Express") != shop_key("Lidl")
    assert shops_match("Lidl Express", "Lidl") is False
