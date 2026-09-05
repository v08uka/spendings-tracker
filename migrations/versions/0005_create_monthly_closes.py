"""Create monthly closes and close lines.

Unique utc_month is the replace key (AC-19).

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS monthly_closes (
    id TEXT NOT NULL,
    utc_month TEXT NOT NULL,
    default_currency TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_monthly_closes_utc_month
    ON monthly_closes (utc_month);

CREATE TABLE IF NOT EXISTS monthly_close_lines (
    id TEXT NOT NULL,
    monthly_close_id TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    source_line_index INTEGER NOT NULL,
    line_text TEXT NOT NULL,
    shop_display TEXT NOT NULL,
    shop_key TEXT NOT NULL,
    amount TEXT,
    currency TEXT NOT NULL,
    category_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (monthly_close_id) REFERENCES monthly_closes (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_monthly_close_lines_monthly_close_id
    ON monthly_close_lines (monthly_close_id);

CREATE INDEX IF NOT EXISTS idx_monthly_close_lines_category_id
    ON monthly_close_lines (category_id);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_monthly_close_lines_category_id;
DROP INDEX IF EXISTS idx_monthly_close_lines_monthly_close_id;
DROP TABLE IF EXISTS monthly_close_lines;
DROP INDEX IF EXISTS uq_monthly_closes_utc_month;
DROP TABLE IF EXISTS monthly_closes;
"""


def _executescript(sql: str) -> None:
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            op.execute(text(statement))


def upgrade() -> None:
    _executescript(UPGRADE_SQL)


def downgrade() -> None:
    _executescript(DOWNGRADE_SQL)
