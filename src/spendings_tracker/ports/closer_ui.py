"""Closer private-chat UI port."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BotReply:
    chat_id: str
    text: str
    screen: str
    code: str | None = None


class CloserUiPort(Protocol):
    def handle_private(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        ...

    def handle_group(self, user_id: str, chat_id: str, text: str) -> BotReply | None:
        ...
