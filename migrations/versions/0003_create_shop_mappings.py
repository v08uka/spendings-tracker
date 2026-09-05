"""Create shop mappings.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS shop_mappings (
    id TEXT NOT NULL,
    shop_key TEXT NOT NULL,
    shop_display TEXT NOT NULL,
    category_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_shop_mappings_shop_key
    ON shop_mappings (shop_key);

CREATE INDEX IF NOT EXISTS idx_shop_mappings_category_id
    ON shop_mappings (category_id);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS idx_shop_mappings_category_id;
DROP INDEX IF EXISTS uq_shop_mappings_shop_key;
DROP TABLE IF EXISTS shop_mappings;
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
