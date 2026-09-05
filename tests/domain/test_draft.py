from spendings_tracker.domain.draft import (
    HandleChoice,
    apply_handle,
    can_save,
    default_currency_totals,
    is_clean,
    is_suspect,
    make_draft_line,
    other_currency_lines,
)

EUR = "EUR"
GROCERIES = "cat-groceries"


def test_classifies_suspect_versus_clean() -> None:
    clean = make_draft_line(amount="12.00", currency=EUR, category_id=GROCERIES)
    missing_amount = make_draft_line(amount=None, currency=EUR, category_id=GROCERIES)
    other_currency = make_draft_line(
        amount="12.00", currency="USD", category_id=GROCERIES
    )
    uncategorized = make_draft_line(amount="12.00", currency=EUR, category_id=None)

    assert is_clean(clean, default_currency=EUR)
    assert not is_suspect(clean, default_currency=EUR)
    assert is_suspect(missing_amount, default_currency=EUR)
    assert is_suspect(other_currency, default_currency=EUR)
    assert is_suspect(uncategorized, default_currency=EUR)


def test_excluded_line_is_not_a_suspect() -> None:
    excluded = make_draft_line(
        amount=None,
        currency=EUR,
        category_id=None,
        is_excluded=True,
        is_handled=True,
    )
    assert not is_suspect(excluded, default_currency=EUR)


def test_accepts_each_handle_choice() -> None:
    missing = make_draft_line(amount=None, currency=EUR, category_id=GROCERIES)
    uncategorized = make_draft_line(amount="12.00", currency=EUR, category_id=None)
    other = make_draft_line(amount="12.00", currency="USD", category_id=GROCERIES)
    drop = make_draft_line(amount="12.00", currency=EUR, category_id=GROCERIES)

    entered = apply_handle(missing, HandleChoice.ENTER_AMOUNT, amount="9.50")
    assigned = apply_handle(
        uncategorized, HandleChoice.ASSIGN_CATEGORY, category_id=GROCERIES
    )
    confirmed = apply_handle(uncategorized, HandleChoice.CONFIRM_UNCATEGORIZED)
    left = apply_handle(other, HandleChoice.LEAVE_OTHER_CURRENCY)
    excluded = apply_handle(drop, HandleChoice.EXCLUDE)

    assert entered.amount == "9.50" and entered.is_handled
    assert assigned.category_id == GROCERIES and assigned.is_handled
    assert confirmed.category_id is None and confirmed.is_handled
    assert left.currency == "USD" and left.is_handled
    assert excluded.is_excluded and excluded.is_handled


def test_save_requires_every_remaining_suspect_handled() -> None:
    clean = make_draft_line(amount="12.00", currency=EUR, category_id=GROCERIES)
    suspect = make_draft_line(amount=None, currency=EUR, category_id=GROCERIES)
    handled = apply_handle(suspect, HandleChoice.ENTER_AMOUNT, amount="4.00")

    assert can_save([clean, suspect], default_currency=EUR) is False
    assert can_save([clean, handled], default_currency=EUR) is True
    assert can_save([], default_currency=EUR) is True


def test_enter_amount_without_parseable_amount_does_not_set_handled() -> None:
    missing = make_draft_line(amount=None, currency=EUR, category_id=GROCERIES)

    for raw in (None, "", "abc"):
        result = apply_handle(missing, HandleChoice.ENTER_AMOUNT, amount=raw)
        assert result.is_handled is False
        assert result.amount is None


def test_can_save_rejects_handled_line_still_missing_amount() -> None:
    falsely_handled = make_draft_line(
        amount=None,
        currency=EUR,
        category_id=GROCERIES,
        is_handled=True,
    )
    assert can_save([falsely_handled], default_currency=EUR) is False


def test_totals_normalise_comma_decimals() -> None:
    line = make_draft_line(amount="12,50", currency=EUR, category_id=GROCERIES)
    totals = default_currency_totals([line], default_currency=EUR)
    assert totals == {GROCERIES: "12.50"}


def test_totals_omit_excluded_and_other_currency_lines() -> None:
    groceries = make_draft_line(amount="12.00", currency=EUR, category_id=GROCERIES)
    extra = make_draft_line(amount="3.00", currency=EUR, category_id=GROCERIES)
    usd = make_draft_line(amount="8.00", currency="USD", category_id=GROCERIES)
    excluded = apply_handle(extra, HandleChoice.EXCLUDE)

    totals = default_currency_totals(
        [groceries, extra, usd, excluded], default_currency=EUR
    )
    listed = other_currency_lines(
        [groceries, extra, usd, excluded], default_currency=EUR
    )

    assert totals == {GROCERIES: "15.00"}
    assert [line.currency for line in listed] == ["USD"]
