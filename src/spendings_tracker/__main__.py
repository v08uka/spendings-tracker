"""Process entry. Scaffold boots and exits; the first feature starts the bot."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Dry-run / boot probe: import layers so a missing package fails here."""
    from spendings_tracker import app, domain, infra, ports  # noqa: F401

    _ = argv if argv is not None else sys.argv[1:]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
