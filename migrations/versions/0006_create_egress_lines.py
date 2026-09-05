"""Create egress lines.

Exactly one of draft_id / monthly_close_id is an app invariant.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS egress_lines (
    id TEXT NOT NULL,
    draft_id TEXT,
    monthly_close_id TEXT,
    line_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (draft_id) REFERENCES drafts (id) ON DELETE CASCADE,
    FOREIGN KEY (monthly_close_id) REFERENCES monthly_closes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_egress_lines_draft_id
    ON egress_lines (draft_id);

CREATE INDEX IF NOT EXISTS idx_egress_lines_monthly_close_id
    ON egress_lines (monthly_close_id);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_egress_lines_monthly_close_id;
DROP INDEX IF EXISTS idx_egress_lines_draft_id;
DROP TABLE IF EXISTS egress_lines;
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
