"""Create settings and categories.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-05

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    id TEXT NOT NULL,
    closer_identity TEXT NOT NULL,
    default_currency TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_settings_closer_identity
    ON settings (closer_identity);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT NOT NULL,
    settings_id TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (settings_id) REFERENCES settings (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_categories_settings_id
    ON categories (settings_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_settings_id_name
    ON categories (settings_id, name);
"""

DOWNGRADE_SQL = """
DROP INDEX IF EXISTS uq_categories_settings_id_name;
DROP INDEX IF EXISTS idx_categories_settings_id;
DROP TABLE IF EXISTS categories;
DROP INDEX IF EXISTS uq_settings_closer_identity;
DROP TABLE IF EXISTS settings;
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
