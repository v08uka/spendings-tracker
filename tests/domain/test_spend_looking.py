from spendings_tracker.domain.spend_looking import (
    extract_spend_looking_lines,
    is_spend_looking,
)


def test_accepts_amount_like_number_plus_other_text() -> None:
    assert is_spend_looking("Test Shop 12.00")
    assert is_spend_looking("lidl 8")
    assert is_spend_looking("Other Shop 12,50")


def test_rejects_talk_without_amount_and_shop() -> None:
    assert not is_spend_looking("just chatting about dinner")
    assert not is_spend_looking("42")
    assert not is_spend_looking("12.00")
    assert not is_spend_looking("")
    assert not is_spend_looking("   ")


def test_splits_one_message_into_several_spend_looking_lines() -> None:
    lines = extract_spend_looking_lines("Test Shop 12.00\nOther Shop 8.50")

    assert [line.text for line in lines] == ["Test Shop 12.00", "Other Shop 8.50"]
    assert [line.source_line_index for line in lines] == [0, 1]


def test_splits_several_pairs_on_the_same_line() -> None:
    lines = extract_spend_looking_lines("Test Shop 12.00 Other Shop 8.50")

    assert len(lines) == 2
    assert lines[0].source_line_index == 0
    assert lines[1].source_line_index == 1
    assert is_spend_looking(lines[0].text)
    assert is_spend_looking(lines[1].text)


def test_ordinary_family_group_wording_needs_no_special_syntax() -> None:
    lines = extract_spend_looking_lines("Test Shop 12")

    assert len(lines) == 1
    assert lines[0].text == "Test Shop 12"
    assert is_spend_looking(lines[0].text)


def test_other_talk_in_a_message_is_not_extracted() -> None:
    lines = extract_spend_looking_lines("lol that was funny\nTest Shop 12.00\nok")

    assert [line.text for line in lines] == ["Test Shop 12.00"]
    assert lines[0].source_line_index == 0
