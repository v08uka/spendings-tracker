"""One application error type.

Adapters translate vendor and Telegram failures into this.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Failure already translated out of an infrastructure adapter."""

    def __init__(
        self,
        code: str,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message or code
        self.details = details or {}
        super().__init__(self.message if message else code)
