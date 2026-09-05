"""On-machine spend-looking gate and shop-and-amount pair splitting."""

from __future__ import annotations

import re
from dataclasses import dataclass

_AMOUNT = re.compile(r"\d+(?:[.,]\d{1,2})?")
_OTHER_TEXT = re.compile(r"[A-Za-z]")


@dataclass(frozen=True)
class SpendLookingLine:
    text: str
    source_line_index: int


def is_spend_looking(text: str) -> bool:
    stripped = text.strip()
    if not stripped or _AMOUNT.search(stripped) is None:
        return False
    remainder = _AMOUNT.sub("", stripped)
    return _OTHER_TEXT.search(remainder) is not None


def extract_spend_looking_lines(message: str) -> list[SpendLookingLine]:
    pairs: list[str] = []
    for physical in message.splitlines():
        pairs.extend(_pairs_on_line(physical))
    found = [pair for pair in pairs if is_spend_looking(pair)]
    return [
        SpendLookingLine(text=text, source_line_index=index)
        for index, text in enumerate(found)
    ]


def _pairs_on_line(line: str) -> list[str]:
    matches = list(_AMOUNT.finditer(line))
    if not matches:
        return []
    if len(matches) == 1:
        stripped = line.strip()
        return [stripped] if stripped else []

    parts: list[str] = []
    start = 0
    for match in matches:
        part = line[start : match.end()].strip()
        if part:
            parts.append(part)
        start = match.end()
    trailing = line[start:].strip()
    if trailing and parts:
        parts[-1] = f"{parts[-1]} {trailing}"
    return parts
