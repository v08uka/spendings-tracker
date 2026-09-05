"""One application error type.

Adapters translate vendor and Telegram failures into this.
"""


class AppError(Exception):
    """Failure already translated out of an infrastructure adapter."""
