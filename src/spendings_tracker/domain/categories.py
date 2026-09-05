"""Frozen confirmed category list; Uncategorized is not a member."""

UNCATEGORIZED = "uncategorized"


def confirmable_names(names: list[str]) -> list[str]:
    confirmed: list[str] = []
    seen: set[str] = set()
    for name in names:
        trimmed = name.strip()
        if not trimmed or trimmed.casefold() == UNCATEGORIZED:
            continue
        key = trimmed.casefold()
        if key in seen:
            continue
        seen.add(key)
        confirmed.append(trimmed)
    return confirmed
