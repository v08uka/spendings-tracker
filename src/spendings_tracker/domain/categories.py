"""Frozen confirmed category list; Uncategorized is not a member."""

UNCATEGORIZED = "uncategorized"


def confirmable_names(names: list[str]) -> list[str]:
    confirmed: list[str] = []
    for name in names:
        trimmed = name.strip()
        if not trimmed or trimmed.casefold() == UNCATEGORIZED:
            continue
        confirmed.append(trimmed)
    return confirmed
