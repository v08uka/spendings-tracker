"""Create drafts and draft lines.

At most one drafts row is an app concern (AC-18), not a CHECK.
There is no unique on utc_month — a saved close for the same month may exist (AC-19).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS drafts (
    id TEXT NOT NULL,
    utc_month TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS draft_lines (
    id TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    source_line_index INTEGER NOT NULL,
    line_text TEXT NOT NULL,
    shop_display TEXT NOT NULL,
    shop_key TEXT NOT NULL,
    amount TEXT,
    currency TEXT NOT NULL,
    category_id TEXT,
    is_excluded INTEGER NOT NULL,
    is_handled INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (draft_id) REFERENCES drafts (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_draft_lines_draft_id
    ON draft_lines (draft_id);

CREATE INDEX IF NOT EXISTS idx_draft_lines_category_id
    ON draft_lines (category_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_draft_lines_draft_id_source
    ON draft_lines (draft_id, source_message_id, source_line_index);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS uq_draft_lines_draft_id_source;
DROP INDEX IF EXISTS idx_draft_lines_category_id;
DROP INDEX IF EXISTS idx_draft_lines_draft_id;
DROP TABLE IF EXISTS draft_lines;
DROP TABLE IF EXISTS drafts;
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
